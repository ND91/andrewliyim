# Andrew Y.F. Li Yim — Personal Website

Hugo-based CV website hosted on GitHub Pages, with automated weekly
publication updates pulled from ORCID and enriched via CrossRef.

---

## 🗂 Repository Structure

```
.
├── .github/
│   └── workflows/
│       ├── deploy.yml                  # Build & deploy to GitHub Pages
│       └── update-publications.yml     # Weekly ORCID → Hugo sync
├── config/
│   └── _default/
│       ├── hugo.yaml                   # Hugo core config
│       ├── params.yaml                 # Site appearance & features
│       └── menus.yaml                  # Navigation links
├── content/
│   ├── _index.md                       # Home page (all sections defined here)
│   ├── authors/
│   │   └── admin/
│   │       └── _index.md               # Your bio, affiliations, links
│   └── publication/
│       ├── _index.md                   # Publications list page
│       └── <slug>/
│           └── index.md                # One folder per publication
├── scripts/
│   ├── fetch_publications.py           # ORCID + CrossRef fetcher
│   └── requirements.txt
├── static/
│   └── uploads/
│       └── cv.pdf                      # ← Place your CV PDF here
├── assets/
│   └── media/
│       └── avatar.jpg                  # ← Place your profile photo here
└── go.mod                              # Hugo Modules dependency file
```

---

## 🚀 One-Time Setup (do this once)

### 1. Create the GitHub repository

```bash
# On GitHub: create a new public repo named:
#   YOUR-USERNAME.github.io          (for a user/org site, lives at root URL)
# OR any name, e.g. "academic-website" (lives at YOUR-USERNAME.github.io/academic-website)

git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
cd YOUR-REPO-NAME
```

### 2. Copy these files into the repo

```bash
cp -r /path/to/this/package/* .
```

### 3. Edit the three placeholder values

| File | Line to change |
|------|---------------|
| `config/_default/hugo.yaml` | `baseURL: 'https://YOUR-GITHUB-USERNAME.github.io/'` |
| `config/_default/params.yaml` | `url: 'https://github.com/YOUR-GITHUB-USERNAME/YOUR-REPO-NAME'` |
| `go.mod` | `module github.com/YOUR-GITHUB-USERNAME/YOUR-REPO-NAME` |
| `content/authors/admin/_index.md` | GitHub profile URL in `profiles:` section |

### 4. Add your profile photo

Place a square photo (min 400×400 px) at:
```
assets/media/avatar.jpg
```

### 5. Add your CV PDF (optional)

```
static/uploads/cv.pdf
```

### 6. Enable GitHub Pages

1. Push to `main`
2. In your repo → **Settings → Pages**
3. Under *Source*, select **"GitHub Actions"**
4. The first deploy will start automatically within ~2 minutes.

### 7. Set up the PAT for automated publication updates

The weekly publication bot needs a Personal Access Token to push commits
(the default `GITHUB_TOKEN` cannot trigger other workflows):

1. GitHub → **Settings → Developer settings → Personal access tokens (classic)**
2. Generate new token → scope: **`repo`** → copy value
3. Your repo → **Settings → Secrets and variables → Actions**
4. **New repository secret** → Name: `GH_PAT`, Value: *paste token*

---

## 🔄 How the Auto-Update Works

```
Every Monday 05:00 UTC
        ↓
GitHub Actions runs update-publications.yml
        ↓
fetch_publications.py queries ORCID public API
        ↓
For each new work, CrossRef API enriches:
  • Full author list
  • Abstract (JATS-cleaned)
  • Journal name
        ↓
New index.md files written to content/publication/<slug>/
        ↓
Git commit + push (only if changes detected)
        ↓
deploy.yml triggered → Hugo builds → GitHub Pages updated
```

You can also trigger it manually at any time:
**Actions tab → "Update Publications" → Run workflow**

---

## ✏️ Customising the Home Page

All home page sections are controlled in `content/_index.md`.
Each `block:` entry maps to a HugoBlox component. To reorder sections,
change the `weight:` values. To hide a section, delete its block.

Key sections:
| Block ID | What it shows |
|----------|--------------|
| `#about` | Bio pulled from `content/authors/admin/_index.md` |
| `#research` | Research focus cards |
| `#featured-pubs` | Publications with `featured: true` |
| `#experience` | Work history from `admin/_index.md` |
| `#teaching` | Free-text teaching/supervision section |
| `#contact` | Contact form + address |

### Marking a publication as "Featured"

Edit `content/publication/<slug>/index.md` and set:
```yaml
featured: true
```
This publication will then appear in the highlighted section on the home page.

---

## 🎨 Changing the Colour Accent

In `config/_default/params.yaml`:
```yaml
appearance:
  color: emerald    # Options: emerald, rose, indigo, orange, pink, sky, violet
```

---

## 🛠 Running Locally

```bash
# Install Hugo extended (v0.128+) from https://gohugo.io/installation/
# Install Go 1.22+ from https://go.dev/

hugo server -D
# → open http://localhost:1313
```

---

## ⚖️ License

This repository uses a dual license:

| What | License |
|------|---------|
| Code, config, scripts, workflows | [MIT License](LICENSE) |
| Content (bio, publications, text, images) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

See [LICENSE](LICENSE) for full terms.

---

## 📦 Dependencies

| Tool | Purpose |
|------|---------|
| [Hugo extended](https://gohugo.io) | Static site generator |
| [HugoBlox Academic CV](https://hugoblox.com/templates/details/academic-cv/) | Theme |
| [ORCID public API](https://pub.orcid.org) | Publication source |
| [CrossRef REST API](https://api.crossref.org) | Metadata enrichment |
| Python 3.11 + `requests` | Fetch script runtime |
| GitHub Actions | CI/CD + weekly update cron |
| GitHub Pages | Free hosting |
