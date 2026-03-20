#!/usr/bin/env python3
"""
fetch_publications.py
─────────────────────
Fetches publications for Andrew Y.F. Li Yim from ORCID and enriches them
with full metadata from CrossRef. Generates Hugo-compatible Markdown files
in content/publication/.

Sources
  • ORCID public API  — primary source of work records
  • CrossRef REST API — abstract, full author list, journal details

Usage
  python scripts/fetch_publications.py
  (run from the repository root)

Scheduling
  Called weekly by .github/workflows/update-publications.yml
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

ORCID_ID = "0000-0002-0754-0953"
ORCID_API = f"https://pub.orcid.org/v3.0/{ORCID_ID}"
CROSSREF_API = "https://api.crossref.org/works"

# Path relative to repo root where Hugo publication files live
PUB_DIR = Path("content/publication")

# HTTP headers for ORCID (JSON) and CrossRef (polite pool)
ORCID_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "andrew-liyim-website/1.0 (https://github.com/your-repo; mailto:a.y.li-yim@amsterdamumc.nl)",
}
CROSSREF_HEADERS = {
    "User-Agent": "andrew-liyim-website/1.0 (https://github.com/your-repo; mailto:a.y.li-yim@amsterdamumc.nl)",
}

# Mapping from ORCID work type to HugoBlox publication_types values
ORCID_TYPE_MAP = {
    "journal-article": "article-journal",
    "conference-paper": "paper-conference",
    "book-chapter": "chapter",
    "book": "book",
    "edited-book": "book",
    "dissertation": "thesis",
    "preprint": "article",
    "data-set": "dataset",
    "software": "software",
    "other": "article",
}

# Rate-limit pause between CrossRef requests (seconds) — be polite
CROSSREF_DELAY = 1.0


# ──────────────────────────────────────────────────────────────────────────────
# ORCID HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def orcid_get(endpoint: str) -> Optional[dict]:
    """GET from ORCID public API, return parsed JSON or None on failure."""
    url = f"{ORCID_API}/{endpoint}"
    try:
        r = requests.get(url, headers=ORCID_HEADERS, timeout=30)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"  [ORCID] Error fetching {endpoint}: {e}", file=sys.stderr)
        return None


def fetch_orcid_works() -> list[dict]:
    """
    Return a list of work summary dicts from ORCID, each containing at
    minimum: put_code, title, year, doi, work_type, journal.
    """
    data = orcid_get("works")
    if not data:
        return []

    works = []
    groups = data.get("group", [])
    print(f"[ORCID] Found {len(groups)} work groups.")

    for group in groups:
        summaries = group.get("work-summary", [])
        if not summaries:
            continue

        # Take the first (preferred) summary in each group
        s = summaries[0]
        put_code = s.get("put-code")
        if put_code is None:
            continue

        # Title
        title_obj = s.get("title", {}).get("title", {})
        title = title_obj.get("value", "").strip() if title_obj else ""

        # Year
        pub_date = s.get("publication-date") or {}
        year_obj = pub_date.get("year") or {}
        year = int(year_obj.get("value", 0)) if year_obj.get("value") else 0

        # DOI (from external IDs)
        doi = extract_doi_from_external_ids(
            group.get("external-ids", {}) or
            s.get("external-ids", {}) or {}
        )

        # Journal
        journal_obj = s.get("journal-title") or {}
        journal = journal_obj.get("value", "").strip()

        # Work type
        work_type = ORCID_TYPE_MAP.get(
            (s.get("type") or "other").lower().replace(" ", "-"),
            "article-journal"
        )

        works.append({
            "put_code": put_code,
            "title": title,
            "year": year,
            "doi": doi,
            "journal": journal,
            "work_type": work_type,
        })

    # Sort newest first
    works.sort(key=lambda w: w["year"], reverse=True)
    return works


def fetch_orcid_work_detail(put_code: int) -> Optional[dict]:
    """Fetch full work detail from ORCID for a single put-code."""
    return orcid_get(f"work/{put_code}")


def extract_doi_from_external_ids(ext_ids: dict) -> str:
    """Pull DOI string from ORCID external-ids structure."""
    for item in (ext_ids.get("external-id") or []):
        if (item.get("external-id-type") or "").lower() == "doi":
            val = (item.get("external-id-value") or "").strip()
            # Normalise: strip leading "https://doi.org/" if present
            val = re.sub(r"^https?://doi\.org/", "", val)
            if val:
                return val
    return ""


def extract_authors_from_orcid(work_detail: dict) -> list[str]:
    """
    Parse contributor list from a full ORCID work detail response.
    Returns a list of formatted author strings.
    """
    contributors = (
        (work_detail.get("contributors") or {})
        .get("contributor") or []
    )
    authors = []
    for c in contributors:
        credit_name = (c.get("credit-name") or {}).get("value", "").strip()
        if credit_name:
            authors.append(credit_name)
    return authors


# ──────────────────────────────────────────────────────────────────────────────
# CROSSREF HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def fetch_crossref(doi: str) -> Optional[dict]:
    """Fetch metadata for a DOI from CrossRef. Returns the 'message' dict."""
    if not doi:
        return None
    url = f"{CROSSREF_API}/{doi}"
    try:
        r = requests.get(url, headers=CROSSREF_HEADERS, timeout=30)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        data = r.json()
        return data.get("message")
    except requests.RequestException as e:
        print(f"  [CrossRef] Error for DOI {doi}: {e}", file=sys.stderr)
        return None


def crossref_authors(message: dict) -> list[str]:
    """Extract author list from CrossRef message as 'Lastname, Initials'."""
    authors = []
    for a in message.get("author") or []:
        given = a.get("given", "").strip()
        family = a.get("family", "").strip()
        if family:
            initials = " ".join(
                g[0] + "." for g in given.split() if g
            ) if given else ""
            authors.append(f"{family}{', ' + initials if initials else ''}")
    return authors


def crossref_abstract(message: dict) -> str:
    """Clean JATS-tagged abstract from CrossRef."""
    raw = message.get("abstract", "")
    # Remove JATS XML tags like <jats:p>, <jats:italic>, etc.
    clean = re.sub(r"<[^>]+>", " ", raw)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


# ──────────────────────────────────────────────────────────────────────────────
# SLUG & FILE HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def make_slug(work: dict) -> str:
    """
    Generate a filesystem-safe slug for a publication folder name.
    Format: {first-author-family}-{year}-{first-content-word}
    Falls back to put_code if title/author are unavailable.
    """
    title_words = re.sub(r"[^\w\s]", "", work.get("title", "")).lower().split()
    # Skip common stop words for the title part
    STOPWORDS = {"a", "an", "the", "of", "in", "on", "for", "and", "with",
                 "to", "is", "are", "by", "from", "at", "as"}
    content_words = [w for w in title_words if w not in STOPWORDS]
    title_part = content_words[0] if content_words else str(work["put_code"])

    year = work.get("year", "0000")
    slug = f"{year}-{title_part}"[:80]
    # Make filesystem-safe
    slug = re.sub(r"[^a-z0-9\-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def author_list_yaml(authors: list[str]) -> str:
    """Format author list as YAML list, replacing Andrew's name with 'admin'."""
    ANDREW_PATTERNS = [
        r"li[\s\-]?yim",
        r"a\.?\s*y\.?\s*f\.?\s*li",
        r"andrew.*yim",
        r"yim,\s*a",
    ]
    lines = []
    for author in authors:
        is_andrew = any(
            re.search(p, author.lower()) for p in ANDREW_PATTERNS
        )
        lines.append("  - admin" if is_andrew else f"  - '{author}'")
    return "\n".join(lines)


def yaml_block_scalar(text: str, indent: int = 2) -> str:
    """Wrap long text as a YAML literal block scalar."""
    if not text:
        return "''"
    pad = " " * indent
    lines = text.split("\n")
    return "|\n" + "\n".join(pad + l for l in lines)


# ──────────────────────────────────────────────────────────────────────────────
# MARKDOWN GENERATION
# ──────────────────────────────────────────────────────────────────────────────

def build_markdown(work: dict, authors: list[str], abstract: str,
                   journal: str) -> str:
    """Render a Hugo-compatible publication Markdown file."""
    title = work["title"].replace("'", "''")   # Escape single quotes in YAML
    year = work.get("year", datetime.now().year)
    doi = work.get("doi", "")
    pub_type = work.get("work_type", "article-journal")

    # Date string — use January 1 of the publication year as default
    date_str = f"{year}-01-01"

    author_yaml = author_list_yaml(authors)
    abstract_yaml = yaml_block_scalar(abstract, indent=2) if abstract else "''"

    pub_short = re.sub(r"\(.*?\)", "", journal).strip()

    lines = [
        "---",
        f"title: >",
        f"  {title}",
        "",
        "authors:",
        author_yaml,
        "",
        f"date: '{date_str}'",
    ]

    if doi:
        lines.append(f"doi: '{doi}'")
    else:
        lines.append("doi: ''")

    lines += [
        "",
        "publication_types:",
        f"  - '{pub_type}'",
        "",
        f"publication: '*{journal}*'" if journal else "publication: ''",
        f"publication_short: '*{pub_short}*'" if pub_short else "publication_short: ''",
        "",
        f"abstract: {abstract_yaml}",
        "",
        "featured: false",
        "",
        "tags: []",
        "",
        "image:",
        "  caption: ''",
        "  focal_point: ''",
        "  preview_only: false",
        "---",
        "",
    ]

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def load_existing_dois() -> set[str]:
    """Collect DOIs that already have a markdown file, to avoid duplicates."""
    dois = set()
    for md_file in PUB_DIR.rglob("index.md"):
        content = md_file.read_text(encoding="utf-8")
        m = re.search(r"^doi:\s*['\"]?([^'\"\n]+)['\"]?", content, re.MULTILINE)
        if m:
            doi = m.group(1).strip()
            if doi:
                dois.add(doi.lower())
    return dois


def main():
    print("=" * 60)
    print("  Publication updater — ORCID → Hugo")
    print(f"  ORCID: {ORCID_ID}")
    print(f"  Output: {PUB_DIR.resolve()}")
    print("=" * 60)

    PUB_DIR.mkdir(parents=True, exist_ok=True)
    existing_dois = load_existing_dois()
    print(f"\n[INFO] {len(existing_dois)} publications already in content/.")

    works = fetch_orcid_works()
    if not works:
        print("[ERROR] No works retrieved from ORCID. Exiting.")
        sys.exit(1)

    print(f"[ORCID] Retrieved {len(works)} works total.")

    new_count = 0
    for work in works:
        doi = work.get("doi", "").lower()
        title = work.get("title", "")

        print(f"\n  [{work['year']}] {title[:70]}...")

        # Skip if we already have this DOI
        if doi and doi in existing_dois:
            print("    → Already exists (by DOI). Skipping.")
            continue

        # Enrich from CrossRef
        authors = []
        abstract = ""
        journal = work.get("journal", "")

        if doi:
            print(f"    → Fetching CrossRef metadata for DOI: {doi}")
            cr = fetch_crossref(doi)
            if cr:
                cr_authors = crossref_authors(cr)
                if cr_authors:
                    authors = cr_authors
                cr_abstract = crossref_abstract(cr)
                if cr_abstract:
                    abstract = cr_abstract
                cr_journal = (
                    (cr.get("container-title") or [""])[0]
                    or journal
                )
                if cr_journal:
                    journal = cr_journal
                print(f"    → CrossRef: {len(authors)} authors, "
                      f"abstract={'yes' if abstract else 'no'}")
            time.sleep(CROSSREF_DELAY)

        # Fallback: fetch ORCID work detail for authors
        if not authors:
            print("    → Fetching ORCID work detail for authors...")
            detail = fetch_orcid_work_detail(work["put_code"])
            if detail:
                authors = extract_authors_from_orcid(detail)
            if not authors:
                # Last resort: anonymous
                authors = ["et al."]

        work["journal"] = journal

        # Build slug and output path
        slug = make_slug(work)
        pub_folder = PUB_DIR / slug
        if pub_folder.exists():
            # Folder already exists (slug collision) — append put_code
            slug = f"{slug}-{work['put_code']}"
            pub_folder = PUB_DIR / slug

        pub_folder.mkdir(parents=True, exist_ok=True)
        md_path = pub_folder / "index.md"

        # Write the markdown file
        md_content = build_markdown(work, authors, abstract, journal)
        md_path.write_text(md_content, encoding="utf-8")

        if doi:
            existing_dois.add(doi)

        print(f"    ✓ Written to {md_path}")
        new_count += 1

    print(f"\n{'=' * 60}")
    print(f"  Done. {new_count} new publication(s) added.")
    print("=" * 60)


if __name__ == "__main__":
    main()
