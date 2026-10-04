# Expertak · Accounting & e-invoicing platform

Web platform for Colombian accounting firms that manage many client companies at once. It turns the DIAN's massive Excel exports (tens of thousands of documents across dozens of companies) into consolidated reports, a purchases panel and per-company analysis, and it is adding **DIAN electronic invoicing** (Annex v1.9) so invoices can be issued from the same place.

**[▶ Try the live demo](https://rlover06.github.io/expertak-erp/)** — runs entirely in the browser with fictional data (no backend, nothing is sent to the DIAN). Upload the sample Excel from the banner, filter the report and issue a test invoice.

## Features

**Import & analysis**
- Upload DIAN bulk exports and consolidated workbooks (`.xlsx`) with strict validation of columns, types and row-level errors.
- Batch inserts with transactions and duplicate detection by composite business key.
- Multi-company: filter everything by client company (NIT) and period.
- Consolidated report, purchases panel and pivot-style summaries by company, document type and issuer/recipient.

**Electronic invoicing (DIAN) — in progress**
- Invoice drafts, emission and status tracking per company (`/api/v1/fe/*`).
- CUFE calculation (SHA-384) following §11.2 of the DIAN technical annex, so the code can be verified without waiting for the DIAN response.
- Preflight checks before sending: signing certificate, DIAN engine service, environment variables and invoice payload.
- Per-company configuration (resolution, prefix, numbering) for multi-issuer firms.

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11, FastAPI, pandas + openpyxl, SQLAlchemy |
| Database | PostgreSQL on Supabase (MariaDB supported for local use) |
| Frontend | Svelte 4 + Vite |
| Infrastructure | Docker Compose |
| Legacy | PHP 8 importer (first version, kept in `api/`, `includes/`, `public/`) |

## Project structure

```
backend/app/main.py            FastAPI app: import, reports, consolidated data, pivots
backend/app/routers/           Electronic invoicing endpoints (/api/v1/fe)
backend/app/dian/              CUFE, invoice mapping, preflight checks, emitter
frontend/src/components/       Upload, reports, purchases panel, invoice form
sql/                           Supabase schemas and migrations (fictional pilot seed data)
docs/                          Architecture, DIAN invoicing notes and roadmap
```

## Demo mode

`npm run build:demo` (or `npm run dev:demo`) in `frontend/` builds the app with `VITE_DEMO=true`: an axios adapter (`src/services/demo.js`) answers the API calls in the browser with fictional companies and documents, parses uploaded Excel files with SheetJS and simulates invoice emission (including the CUFE hash). GitHub Actions publishes it to GitHub Pages on every push.

## Getting started

```bash
cp backend/.env.example backend/.env   # add your DATABASE_URL (Supabase or MariaDB)
docker compose up -d                   # backend on :8000, frontend on :80
```

API docs at `http://localhost:8000/docs`. For a manual setup without Docker see [docs/SETUP_FASTAPI_SVELTE.md](docs/SETUP_FASTAPI_SVELTE.md); the DIAN workflow is described in [docs/EMISION_FE.md](docs/EMISION_FE.md) and [docs/ROADMAP_FE.md](docs/ROADMAP_FE.md).

> This repository contains code only. Client data, database dumps and DIAN credentials are never committed; company names and NITs in the docs and seed files are fictional.

## Author

Built by [Over Regino](https://github.com/RLover06), math and physics teacher and developer, Montería, Colombia.
