# Publishing

Nothing here has been done. Local commits publish nothing.

1. Read `docs/FINAL_AUDIT.md`, the README and `docs/fans.md`. Review `git diff origin/main...HEAD`.
2. Run the commands in `docs/REPRODUCING.md`. Keep raw data, virtual environments and secrets out of Git; no blanket right to redistribute the provider's bulk data is assumed.
3. Push the branch without force: `git push -u origin finish/final-release`; open a pull request; check that the research-invariants workflow is green on Ubuntu, Windows and macOS.
4. Site: static files in `site/` (no build step beyond `scripts/build_site.py`). Preview locally with `.venv/bin/python -m http.server 8000 --directory site`, then open `http://localhost:8000/`. To serve it on GitHub Pages, set Settings → Pages → Source to **GitHub Actions**; `.github/workflows/pages.yml` uploads `site/` after a merge to `main` that touches it.
5. Article: paste `docs/medium_article_outline.md` into Medium; upload the figures it names from `figures/`.
