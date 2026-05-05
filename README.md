# StockBrief API Server

FastAPI backend for a personal stock-watchlist briefing service.

StockBrief collects news, disclosures, and market data for registered watchlist symbols, normalizes raw articles, and creates fact-based AI summaries with risk tags. It must not provide investment recommendations.

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

## API Keys

Start with the minimum set:

- `OPENAI_API_KEY`: required for AI summaries and briefing answers.
- `DART_API_KEY`: required for Korean disclosure and listed-company sync.
- `KAKAO_CLIENT_ID`, `KAKAO_CLIENT_SECRET`, `KAKAO_REDIRECT_URI`: required only if you use Kakao login.

Optional by feature:

- `SERP_API_KEY`: Google News/Search collection through SerpApi.
- `FINNHUB_API_KEY`: market data.
- `TWELVE_DATA_API_KEY`: alternate market data.
- `YOUTUBE_API_KEY`: YouTube video/comment collection.
- `DATA_GO_KR_SERVICE_KEY`: Korean public-data endpoints.
- `NAVER_CLIENT_ID`, `NAVER_SECRET`: Naver API features.

For a no-key first run, leave external API keys blank and keep these flags disabled:

```env
STOCK_AUTO_SYNC_ENABLED=false
PIPELINE_SCHEDULER_ENABLED=false
PROFILE_SCHEDULER_ENABLED=false
PROACTIVE_BRIEFING_SCHEDULER_ENABLED=false
```

See [Personal Setup](./docs/PERSONAL_SETUP.md) for key issuance links and manual setup steps.

## Notes

- GitHub Actions deployment is manual-only (`workflow_dispatch`) until a personal production target is configured.
- Keep `.env` private. Rotate keys before pushing to a new personal remote if any key was shared during the team project.
- The highest-priority product path is `watchlist -> collector -> normalizer -> analyzer -> dashboard`.
