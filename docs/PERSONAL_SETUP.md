# StockBrief Personal Setup

This project is configured as a personal stock-watchlist briefing tool. It summarizes facts from news, disclosures, reports, and market data. It must not recommend buying, selling, holding, or ranking stocks as investment picks.

## Required First

1. Create your own `.env` from `.env.example`.
2. Keep external API keys blank until you personally issue them.
3. Start only MySQL, Redis, and PostgreSQL for the first local boot.
4. Enable collectors and schedulers only after the relevant keys are present.

## Minimum Useful Keys

| Key | Needed For | Where To Issue |
| --- | --- | --- |
| `OPENAI_API_KEY` | AI summaries, risk briefings, Q&A | https://platform.openai.com/api-keys |
| `DART_API_KEY` | Korean company/disclosure data | https://opendart.fss.or.kr/uss/umt/EgovMberInsertView.do |
| `SERP_API_KEY` | Google News/Search collection | https://serpapi.com/ |
| `DATA_GO_KR_SERVICE_KEY` | Korean stock prices and public data | https://www.data.go.kr/ |
| `YOUTUBE_API_KEY` | YouTube Data API video/comment collection | https://console.cloud.google.com/apis/library/youtube.googleapis.com |

## Optional Keys

| Key | Needed For |
| --- | --- |
| `ALPHA_VANTAGE_API_KEY` | US daily price data for the heatmap |
| `TWELVE_DATA_API_KEY` | Alternate US price data if you already have a Twelve Data key |
| `FINNHUB_API_KEY` | Optional US symbol search and Finnhub news collection |
| `NAVER_CLIENT_ID`, `NAVER_SECRET` | Naver API integrations |
| `TWITTER_BEARER_TOKEN` | X/Twitter collection if re-enabled |
| `KAKAO_CLIENT_ID`, `KAKAO_CLIENT_SECRET` | Kakao OAuth, only if you decide to re-enable Kakao login |

## Personal Login

Kakao login is not required for personal use. The frontend login button calls:

```text
POST /account/personal-login
```

The backend creates or reuses one local account and sets the normal auth cookies.

```env
PERSONAL_AUTH_ENABLED=true
PERSONAL_AUTH_EMAIL=me@stockbrief.local
PERSONAL_AUTH_NICKNAME=StockBrief User
```

Set `PERSONAL_AUTH_ENABLED=false` before exposing the service outside your own local network.

## Local First-Run Policy

Keep these disabled until the keys are ready:

```env
STOCK_AUTO_SYNC_ENABLED=false
PIPELINE_SCHEDULER_ENABLED=false
PROFILE_SCHEDULER_ENABLED=false
PROACTIVE_BRIEFING_SCHEDULER_ENABLED=false
```

After issuing `DART_API_KEY`, you can enable `STOCK_AUTO_SYNC_ENABLED=true` or trigger stock sync manually through the stock API. After issuing `OPENAI_API_KEY`, you can use the AI summary and briefing paths. Turn on scheduled collection only after verifying manual collection works.

## Market Data Plan

- Korean stocks: use `DATA_GO_KR_SERVICE_KEY`. The app already routes KOSPI/KOSDAQ/KONEX daily price heatmap data through data.go.kr.
- US stocks: use `ALPHA_VANTAGE_API_KEY` first. If it is empty but `TWELVE_DATA_API_KEY` exists, the app falls back to Twelve Data.
- Keep unofficial no-key sources out of the default path unless you are only doing quick local experiments.

## Safety Rules

- Do not commit `.env`.
- Do not reuse team, class, or shared API keys.
- Rotate any key that may have been pasted into chat, logs, screenshots, or Git history.
- Keep all AI prompts and UI labels fact-based: summary, briefing, source, risk, disclosure, market data.
- Avoid user-facing labels such as recommendation, buy, sell, hold, signal, or target price.
