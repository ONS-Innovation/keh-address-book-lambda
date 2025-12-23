# Documentation

We use MkDocs with the Material theme.

## Prerequisites

- Python and Poetry installed.
- Install docs dependencies (Material, mkdocstrings) via Poetry’s `docs` group.

```bash
make install-docs
```

## Local preview

```bash
make docs-serve
```

Alternatively:

```bash
poetry run mkdocs serve
```

Open: http://localhost:8000

## Build static site

```bash
make docs-build
```

Alternatively:

```bash
poetry run mkdocs build
```

Outputs are written to the local `site/` folder.

## Deploy

Deployment is automated to GitHub Pages via `.github/workflows/docs.yml`. Pushes to `main` that change `docs/**` or `mkdocs.yml` will build and deploy.

```bash
make docs-deploy
```

Alternatively:

```bash
poetry run mkdocs gh-deploy --force
```

Ensure GitHub Pages is enabled in repository settings (Source: GitHub Actions).

## Troubleshooting

- Command not found: `make mkdocs-serve`
  - Use `make docs-serve` (the target is named `docs-serve`).
- Missing assets (logo/favicon)
  - `mkdocs.yml` has logo/favicon commented out. Add files under `docs/assets/` and uncomment.
- Nav entries show 404
  - Ensure files exist under `docs/` matching `mkdocs.yml` nav paths.
- Material theme features not present
  - Confirm `make install-docs` ran and Poetry installed the `docs` group.

## Navigation

Top-level pages:

- Home (`index.md`)
- FAQ (`faq.md`)
- Technical Documentation
  - Overview
  - The Process
  - Logging
