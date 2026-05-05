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

Current baseline: `14 passed`.

## API Keys

For your current personal setup, use these first:

- `OPENAI_API_KEY`: required for AI summaries and briefing answers.
- `DART_API_KEY`: required for Korean disclosure and listed-company sync.
- `SERP_API_KEY`: Google News/Search collection through SerpApi.
- `DATA_GO_KR_SERVICE_KEY`: Korean stock price and public-data endpoints.
- `YOUTUBE_API_KEY`: YouTube video/comment collection.

Optional by feature:

- `ALPHA_VANTAGE_API_KEY`: US daily market data for the heatmap.
- `TWELVE_DATA_API_KEY`: alternate US market data if you already have it.
- `FINNHUB_API_KEY`: optional US symbol search and Finnhub news collection.
- `NAVER_CLIENT_ID`, `NAVER_SECRET`: Naver API features.
- `KAKAO_CLIENT_ID`, `KAKAO_CLIENT_SECRET`, `KAKAO_REDIRECT_URI`: optional only if Kakao login is re-enabled.

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
