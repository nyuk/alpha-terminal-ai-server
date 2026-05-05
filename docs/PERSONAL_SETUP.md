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
| `KAKAO_CLIENT_ID` | Kakao login REST API key | https://developers.kakao.com/ |
| `KAKAO_CLIENT_SECRET` | Kakao login token exchange when client secret is enabled | https://developers.kakao.com/ |

## Optional Keys

| Key | Needed For |
| --- | --- |
| `SERP_API_KEY` | SerpApi Google News/Search collection |
| `FINNHUB_API_KEY` | Market quote and financial data |
| `TWELVE_DATA_API_KEY` | Alternate market quote and financial data |
| `YOUTUBE_API_KEY` | YouTube Data API video/comment collection |
| `DATA_GO_KR_SERVICE_KEY` | Korean public-data portal endpoints |
| `NAVER_CLIENT_ID`, `NAVER_SECRET` | Naver API integrations |
| `TWITTER_BEARER_TOKEN` | X/Twitter collection if re-enabled |

## Local First-Run Policy

Keep these disabled until the keys are ready:

```env
STOCK_AUTO_SYNC_ENABLED=false
PIPELINE_SCHEDULER_ENABLED=false
PROFILE_SCHEDULER_ENABLED=false
PROACTIVE_BRIEFING_SCHEDULER_ENABLED=false
```

After issuing `DART_API_KEY`, you can enable `STOCK_AUTO_SYNC_ENABLED=true` or trigger stock sync manually through the stock API. After issuing `OPENAI_API_KEY`, you can use the AI summary and briefing paths. Turn on scheduled collection only after verifying manual collection works.

## Kakao Login Checklist

For local development, register these values in Kakao Developers:

```text
Site domain: http://localhost:3000
Redirect URI: http://localhost:33333/kakao-authentication/request-access-token-after-redirection
```

Then set:

```env
KAKAO_CLIENT_ID=<REST API key>
KAKAO_CLIENT_SECRET=<client secret if enabled>
KAKAO_REDIRECT_URI=http://localhost:33333/kakao-authentication/request-access-token-after-redirection
FRONTEND_AUTH_CALLBACK_URL=http://localhost:3000/auth-callback
```

## Safety Rules

- Do not commit `.env`.
- Do not reuse team, class, or shared API keys.
- Rotate any key that may have been pasted into chat, logs, screenshots, or Git history.
- Keep all AI prompts and UI labels fact-based: summary, briefing, source, risk, disclosure, market data.
- Avoid user-facing labels such as recommendation, buy, sell, hold, signal, or target price.
