# Andrew Y.F. Li Yim — Personal Academic Website

A lightweight, dependency-free static site. Two files are all that matter:

| File | Purpose |
|---|---|
| `index.html` | The entire website — HTML, CSS, and JS in one file |
| `publications.json` | All publications, auto-updated weekly from ORCID |

## Local preview

No build step needed. Just open `index.html` in a browser.
For the publications to load correctly (fetch requires a server):

```bash
python -m http.server 8000
# → open http://localhost:8000
```

## Marking publications as Featured

Open `publications.json` and set `"featured": true` on any entry.
Those publications will appear in the **Selected** view on the homepage.
The **All** view shows every publication, with "Selected" badges on featured ones.

## Deployment (GitHub Pages)

1. Push this folder to a GitHub repo
2. Repo → **Settings → Pages → Source: GitHub Actions**
3. The site deploys automatically on every push

## Auto-updating publications

Every Monday at 05:00 UTC, the `update-publications.yml` workflow:
- Queries your ORCID profile for new works
- Enriches metadata via CrossRef (journal, volume, pages, authors)
- Commits any new entries to `publications.json`
- Triggers a redeploy

New entries are added with `"featured": false` — you manually promote
them to featured by editing `publications.json`.

For the update commit to trigger the deploy workflow, add a Personal
Access Token (`repo` scope) as a repo secret named `GH_PAT`.

## License

Code: MIT · Content: CC BY 4.0 — see LICENSE
