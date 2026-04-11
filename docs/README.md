# Backend Docs Guide

`alpha-terminal-ai-server/docs`의 문서를 빠르게 찾기 위한 인덱스입니다.

## 주요 폴더

| 경로 | 용도 |
|---|---|
| `backlog/` | 백엔드 백로그 구현 문서 (`BL-BE-*`) |
| `deployment/` | AWS/EC2/GitHub Actions/Docker 배포 문서 |
| `db/` | Alembic/DB 작업 가이드 |
| `bruno/` | API 테스트 컬렉션 |
| `meta/` | 세션 메모, 작업 로그 |
| `fixtures/` | 테스트용 원본 데이터 |
| `migrations/` | 수동 SQL 마이그레이션 파일 |

## 먼저 볼 문서

- 역할/책임: `TEAM-ROLE-2.0.md`
- 배포 흐름: `deployment/CICD-GITHUB-ACTIONS.md`
- EC2 PostgreSQL: `deployment/EC2-POSTGRES.md`
- AWS 초기 구축: `deployment/AWS_DEPLOYMENT_AND_DOMAIN.md`
- 최근 장애 기록: `ISSUE-04-news-saved-500-aws.md`

## 장애/이슈 문서

- `ISSUE-04-news-saved-500-aws.md`
- `ISSUE-03-logout-401.md`
- `ISSUE-02-register-cors-redirect.md`
- `fix-account-session-incomplete.md`

## 아키텍처/참고 문서

- `TEAM-ROLE-2.0.md`
- `2026-03-21-architecture-cleanup-and-fixes.md`
- `raw_article_schema.md`
- `USER-PROFILE-MOCK.md`
- `krx_market_sync.md`
- `frontend_kakao_auth_integration.md`
- `git_push_conflict_resolution.md`

## 테스트 메모

- `test_01_saved_article_analysis.md`
- `test_02_redis_session.md`
- `test_03_kakao_oauth.md`
- `test_04_kakao_user_info.md`
- `test_05_kakao_token_exchange.md`
- `test_06_bulk_analysis.md`
- `test_07_kakao_user_info.md`
- `test_08_kakao_account_check.md`
- `test_09_account_register.md`
- `test_10_kakao_login_session.md`

## ADAIS 관련 문서

- `adais_13_normalized_article_schema.md`
- `adais_14_stock_normalizer_skeleton.md`
- `adais_15_fixture_normalization.md`
- `adais_16_ai_summary_response_schema.md`
- `adais_17_fixture_summary_tagging.md`
- `adais_19_stock_analyzer_skeleton.md`
- `adais_20_keyword_extraction.md`
- `adais_21_sentiment_analysis.md`
- `adais_22_risk_tagging.md`
- `adais_23_analysis_integration.md`

## 정리 규칙

- 새 구현 문서는 가능하면 `backlog/`, `deployment/`, `db/`, `meta/` 같은 목적 폴더에 먼저 넣습니다.
- 일회성 장애 기록은 `ISSUE-*` 형식으로 루트에 두되, 이 인덱스에 바로 추가합니다.
- 테스트 실행 메모는 `test_*` 형식을 유지하고, 필요 시 추후 `tests/` 하위 폴더로 이동합니다.
- 루트에는 장기적으로 참고할 문서만 남기고, 범주가 명확한 문서는 가능한 기존 폴더를 재사용합니다.
