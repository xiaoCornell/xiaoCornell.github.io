# xiaoCornell.github.io

GitHub Pages source for Xiao Wang's personal homepage, migrated from the original Google Sites pages.

## Files

- `index.html`: landing page
- `cv.html`: CV / experience / service
- `publications.html`: generated publication list
- `seminars.html`: talks and presentations
- `styles.css`, `script.js`: shared site assets
- `templates/publications.html.tpl`: publications page template
- `tools/sync_inspire_publications.py`: INSPIRE-HEP sync script
- `data/publications.json`: generated publication data
- `.github/workflows/sync-inspire-publications.yml`: scheduled sync workflow
- `tools/generate_arxiv_daily.py`: arXiv daily digest generator
- `arxiv_daily_config.json`: arXiv daily configuration
- `arxiv_daily/`: generated daily digest archive
- `.github/workflows/update-arxiv-daily.yml`: scheduled arXiv daily workflow

## Local preview

From this directory:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Manual publication sync

Run this from the repository root:

```powershell
python tools/sync_inspire_publications.py
```

This will:

- fetch the author profile from INSPIRE-HEP
- query publications using the official INSPIRE BAI identifier
- regenerate `data/publications.json`
- regenerate `publications.html`

## Manual arXiv daily generation

Run this from the repository root:

```powershell
python -m pip install -r requirements-arxiv-daily.txt
python tools/generate_arxiv_daily.py
```

This will regenerate `arxiv_daily/latest.html`, `arxiv_daily/index.html`, and the per-date archive directory.

## Scheduled sync

GitHub Actions runs the publication sync automatically every Monday at `13:17 UTC`, and you can also trigger it manually from the Actions tab.

A separate workflow updates the arXiv daily archive every day at `13:15 UTC`.

## Publish

GitHub Pages deploys automatically when changes are pushed to `main`.