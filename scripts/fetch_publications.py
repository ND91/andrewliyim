#!/usr/bin/env python3
"""
fetch_publications.py
─────────────────────
Fetches works from ORCID and enriches them via CrossRef, then merges
any new entries into publications.json — preserving all existing data
(especially manually-set `featured: true` flags).

Run from the repo root:
    python scripts/fetch_publications.py

Scheduled weekly by .github/workflows/update-publications.yml
"""

import json, re, sys, time
from pathlib import Path
import requests

ORCID_ID = "0000-0002-0754-0953"
ORCID_API = f"https://pub.orcid.org/v3.0/{ORCID_ID}"
CROSSREF_API = "https://api.crossref.org/works"
PUB_JSON = Path("publications.json")
DELAY = 1.0   # seconds between CrossRef requests

HEADERS_ORCID = {
    "Accept": "application/json",
    "User-Agent": "andrew-liyim-site/1.0 (mailto:a.y.li-yim@amsterdamumc.nl)",
}
HEADERS_CR = {
    "User-Agent": "andrew-liyim-site/1.0 (mailto:a.y.li-yim@amsterdamumc.nl)",
}

ANDREW_RE = re.compile(
    r"li[\s\-]?yim|a\.?\s*y\.?\s*f?\.?\s*li|yim,\s*a", re.I
)

# ── ORCID ──────────────────────────────────────────────────────────────────

def orcid_works():
    r = requests.get(f"{ORCID_API}/works", headers=HEADERS_ORCID, timeout=30)
    r.raise_for_status()
    groups = r.json().get("group", [])
    works = []
    for g in groups:
        s = (g.get("work-summary") or [{}])[0]
        doi = _doi_from_ext(g.get("external-ids", {}) or s.get("external-ids", {}))
        year_v = ((s.get("publication-date") or {}).get("year") or {}).get("value")
        year = int(year_v) if year_v else 0
        title_obj = (s.get("title") or {}).get("title") or {}
        title = title_obj.get("value", "").strip()
        journal_obj = s.get("journal-title") or {}
        journal = journal_obj.get("value", "").strip()
        works.append({"put_code": s.get("put-code"), "title": title,
                      "year": year, "doi": doi, "journal": journal})
    return sorted(works, key=lambda w: w["year"], reverse=True)

def _doi_from_ext(ext):
    for item in (ext.get("external-id") or []):
        if (item.get("external-id-type") or "").lower() == "doi":
            v = (item.get("external-id-value") or "").strip()
            v = re.sub(r"^https?://doi\.org/", "", v)
            if v: return v
    return ""

# ── CrossRef ───────────────────────────────────────────────────────────────

def crossref(doi):
    if not doi: return None
    try:
        r = requests.get(f"{CROSSREF_API}/{doi}", headers=HEADERS_CR, timeout=30)
        if r.status_code == 404: return None
        r.raise_for_status()
        return r.json().get("message")
    except Exception as e:
        print(f"  [CrossRef] {doi}: {e}", file=sys.stderr)
        return None

def cr_authors(msg):
    out = []
    for a in (msg.get("author") or []):
        family = a.get("family", "").strip()
        given  = a.get("given", "").strip()
        if not family: continue
        initials = "".join(g[0]+"." for g in given.split() if g) if given else ""
        name = f"{family}, {initials}" if initials else family
        # Mark Andrew
        if ANDREW_RE.search(f"{family} {given}"):
            name = f"A.Y.F. Li Yim*"
        out.append(name)
    return out

def cr_abstract(msg):
    raw = msg.get("abstract", "")
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)).strip()

def cr_journal(msg):
    titles = msg.get("container-title") or []
    return titles[0] if titles else ""

def cr_volume(msg):  return msg.get("volume", "") or ""
def cr_pages(msg):   return msg.get("page", "") or ""
def cr_month(msg):
    issued = (msg.get("issued") or {}).get("date-parts") or [[]]
    parts = issued[0] if issued else []
    if len(parts) >= 2:
        import calendar
        return calendar.month_name[parts[1]]
    return ""

# ── Slug ───────────────────────────────────────────────────────────────────

def make_slug(work):
    words = re.sub(r"[^\w\s]", "", work["title"].lower()).split()
    stop  = {"a","an","the","of","in","on","for","and","with","to","is","by"}
    kw    = next((w for w in words if w not in stop), str(work["put_code"]))
    base  = f"{work['year']}-{kw}"[:60]
    return re.sub(r"[^a-z0-9\-]", "-", re.sub(r"-+", "-", base)).strip("-")

# ── Main ───────────────────────────────────────────────────────────────────

def main():
    # Load existing publications, index by DOI and title
    existing = json.loads(PUB_JSON.read_text()) if PUB_JSON.exists() else []
    existing_dois   = {p["doi"].lower(): p for p in existing if p.get("doi")}
    existing_titles = {p["title"].lower(): p for p in existing}

    print(f"[INFO] {len(existing)} existing publications in {PUB_JSON}")

    orcid_list = orcid_works()
    print(f"[ORCID] {len(orcid_list)} works found")

    added = 0
    for work in orcid_list:
        doi = (work["doi"] or "").lower()
        title = work["title"].lower()

        if doi and doi in existing_dois:
            continue
        if title and title in existing_titles:
            continue

        print(f"\n  [{work['year']}] {work['title'][:70]}…")

        authors, abstract, journal = [], "", work["journal"]
        volume, pages, month = "", "", ""

        if work["doi"]:
            msg = crossref(work["doi"])
            if msg:
                cr_a = cr_authors(msg)
                if cr_a:       authors = cr_a
                if cr_journal(msg): journal = cr_journal(msg)
                volume = cr_volume(msg)
                pages = cr_pages(msg)
                month = cr_month(msg)
                abstract = cr_abstract(msg)
                print(f"    → CrossRef: {len(authors)} authors")
            time.sleep(DELAY)

        if not authors:
            authors = ["et al."]

        entry = {
            "id": make_slug(work),
            "year": work["year"],
            "featured": False,      # ← set manually in publications.json
            "lead": any(ANDREW_RE.search(a) and "*" in a for a in authors),
            "title": work["title"],
            "authors": ", ".join(authors),
            "journal": journal,
            "volume": volume,
            "pages": pages,
            "month": month,
            "doi": work["doi"],
        }

        existing.append(entry)
        if doi:   existing_dois[doi] = entry
        if title: existing_titles[title] = entry
        added += 1
        print(f"    ✓ Added: {entry['id']}")

    if added:
        # Sort newest first
        existing.sort(key=lambda p: (-(p.get("year") or 0), p.get("title","")))
        PUB_JSON.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
        print(f"\n[DONE] {added} new publication(s) added to {PUB_JSON}")
    else:
        print("\n[DONE] No new publications found.")

if __name__ == "__main__":
    main()
