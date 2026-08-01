# Sentinel AI Governance

FastAPI-based governance platform. This README covers local development, Docker, and Vercel container deployment.

## Quick requirements

- Python 3.11 (recommended)
- Conda (for the provided Dockerfile) or Docker
- Docker (for local container testing)
- Vercel account (for production deploy)

## Local development (Conda)

1. Create & activate conda env:

```bash
conda create -y -n sentinel python=3.11
conda activate sentinel
pip install -r requirements.txt
```

2. Run the app locally:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/health to verify.

## Docker (Container build used by Vercel)

Build and run the image locally:

```bash
docker build -t sentinel-ai-governance .
docker run --rm -p 8000:8000 sentinel-ai-governance
```

If the container fails, check the container logs for missing environment variables or runtime errors.

## Vercel deployment (Container)

This repository contains `vercel.json` that instructs Vercel to build the repository using the `Dockerfile` (container deployment).

Steps:

- Commit and push your branch to the repo.
- In Vercel dashboard, import the repository and select the `main` branch.
- Add required environment variables in the Vercel project settings (see list below).
- Deploy via the Vercel UI or locally with:

```bash
vercel --prod
```

Vercel will build the container using the included `Dockerfile` and run the container.

## Serverless fallback

A minimal serverless endpoint `api/health.py` is provided as a fallback when not deploying the container.

## Environment variables (recommended)

At minimum configure these in Vercel (and locally):

- `SECRET_KEY` (string)
- `DATABASE_URL` (e.g. postgres://user:pass@host:port/db)
- `JWT_SECRET`
- `GEMINI_API_KEY` (if using Gemini LLM)
- `DEBUG` (set `false` in production)
- `LOG_LEVEL` (optional)

Notes:

- Do not use SQLite for production on Vercel — use an external managed Postgres or equivalent.
- The current `Dockerfile` uses a Conda base (larger image). For smaller builds, consider switching to `python:3.11-slim` and using `pip` only.

## Troubleshooting

- Container build is large due to Conda; allow extra time on first build.
- If ports or DB connections fail on Vercel, ensure environment variables and network access (managed DB) are configured.
- Check app logs in Vercel dashboard for runtime errors.

## Next steps I can do for you

- Convert `Dockerfile` to a smaller `python:3.11-slim` image (faster builds).
- Run a local Docker build and capture logs to debug the previous `docker run` failure.

## End-to-end overview

- **Source**: Developers push code to `main` (or PR branches) in GitHub.
- **CI**: Run tests, linting, and build container (recommended: GitHub Actions) on PRs.
- **Build**: Vercel builds the container using `Dockerfile` and `vercel.json` (or uses serverless for small endpoints).
- **Run**: The container runs the FastAPI app; environment variables are injected from Vercel project settings.
- **Data**: Use a managed Postgres instance (set `DATABASE_URL`) — migrations are applied with Alembic.
- **Observability**: Forward logs to a central log provider and configure health checks (`/health`).

## Architecture & components

- **FastAPI**: HTTP API + templated UI served by Jinja2.
- **Uvicorn**: ASGI server used inside the container.
- **Database**: SQLAlchemy + async drivers; Alembic for migrations.
- **LLM**: Gemini (via `google-generativeai`) configured with `GEMINI_API_KEY`.
- **Websockets**: Real-time events handled by the project's websocket module.

## CI/CD recommendations

- Add a GitHub Actions workflow to run tests and build the Docker image on PRs. Example jobs:
  - `lint` — run `ruff`/`flake8`/`black` (optional)
  - `test` — run `pytest -q`
  - `build` — build Docker image and publish (optional for Vercel)
- Protect `main` branch and require passing checks before merge.

## Database migrations & seed

- Run migrations locally with Alembic before deploying or include migration step in CI:

```bash
alembic upgrade head
```

- Seed initial data (employees, settings) using `database/seed.py` or `app.database.seed` helper (the project contains `database/seed.py`).

## Testing

- Run unit tests:

```bash
pytest tests -q
```

- Aim for CI to run tests on every PR.

## Monitoring & logging

- Configure `LOG_LEVEL` and a remote log sink (Datadog, LogDNA, Papertrail).
- Use the `/health` endpoint for basic uptime checks.

## Security & secrets

- Keep secrets in Vercel environment variables, never in the repo.
- Rotate `SECRET_KEY` and `JWT_SECRET` regularly.
- Use HTTPS (Vercel uses TLS by default) and validate external DB connections.

## Performance & scaling

- Container-based deployment: scale by increasing replicas or using Vercel's concurrency settings.
- Offload heavy LLM calls to async background tasks or external worker queues.

## Innovation & extension points

- Add modular policy engines in `engines/` to experiment with governance rules.
- Swap LLM providers by abstracting LLM calls in `services/llm_service.py`.
- Add A/B testing for policy thresholds by storing experiment configs in the `settings` table.

## Postscript (PS)

- This repository is configured to deploy on Vercel using a Docker container. If you prefer faster builds, I recommend converting to a `python:3.11-slim` image (smaller and quicker). For full serverless conversion, we'd need to rewrite persistent-file and DB usage to external services only.

## Production deployment checklist

- [ ] Configure managed Postgres and set `DATABASE_URL` in Vercel.
- [ ] Add `SECRET_KEY`, `JWT_SECRET`, `GEMINI_API_KEY` in Vercel secrets.
- [ ] Set `DEBUG=false` in production.
- [ ] Run Alembic migrations after deploy (or include migration step in startup if safe).
- [ ] Configure logging/monitoring and health checks.

## Contact / help

If you want, I can:

- Convert the Dockerfile to a slim image.
- Create GitHub Actions workflows for CI.
- Run a local Docker build and troubleshoot the failure you saw.

* I’ll add the [vercel.json](<vscode-file://vscode-app/c:/Users/NISHAKART/AppData/Local/Programs/Microsoft%20VS%20Code/e4c7e7b1d6/resources/app/out/vs/code/electron-browser/workbench/workbench.html>) proxy rewrite and move static assets to Vercel (Hybrid, quick).
