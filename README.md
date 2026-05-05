# Alpha Terminal AI Server

FastAPI backend for a personal stock-watchlist briefing service.

The service collects news, disclosures, and market data for registered watchlist symbols, normalizes raw articles, and creates fact-based AI summaries with risk tags. It must not provide investment recommendations.

## Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- MySQL, Redis, PostgreSQL/pgvector
- OpenAI API
- APScheduler

## Local Setup

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
copy .env.example .env
```

Fill `.env` with local database credentials and API keys.

Start infrastructure:

```powershell
docker compose up -d mysql redis postgres
```

Run the API:

```powershell
$env:PYTHONPATH='.'
venv\Scripts\python main.py
```

API server: http://localhost:33333

## Validation

```powershell
venv\Scripts\python -m pytest -q
```

Current baseline: `19 passed`.

## Notes

- GitHub Actions deployment is manual-only (`workflow_dispatch`) until a personal production target is configured.
- Keep `.env` private. Rotate keys before pushing to a new personal remote if any key was shared during the team project.
- The highest-priority product path is `watchlist -> collector -> normalizer -> analyzer -> dashboard`.
