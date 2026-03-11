# xiaoCornell.github.io

GitHub Pages source for Xiao Wang's personal homepage, migrated from the original Google Sites pages.

## Files

- `index.html`: landing page
- `cv.html`: CV / experience / service
- `publications.html`: publication list
- `seminars.html`: talks and presentations
- `styles.css`, `script.js`: shared site assets

## Local preview

From this directory:

```powershell
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Publish

1. Create an empty GitHub repository named `xiaoCornell.github.io`.
2. From this folder, run:

```powershell
git init -b main
git add .
git commit -m "Initial GitHub Pages site"
git remote add origin git@github.com:xiaoCornell/xiaoCornell.github.io.git
git push -u origin main
```
