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

## Scheduled sync

GitHub Actions runs the publication sync automatically every Monday at `13:17 UTC`, and you can also trigger it manually from the Actions tab.

## Publish

GitHub Pages deploys automatically when changes are pushed to `main`.
