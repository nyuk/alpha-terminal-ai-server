# BL-BE-71 — 투자 워크플로우 관심 종목 뉴스 본문 수집

## 개요

투자 판단 워크플로우의 Retrieval 단계에서 SERP API로 종목 관련 뉴스를 검색하고,
각 뉴스 링크에서 본문을 수집하여 MySQL + PostgreSQL에 저장한다.
수집된 본문 요약은 Retrieval Agent의 `retrieval_data`에 포함되어 Analysis Agent에 전달된다.

---

## 배경

기존 `_handle_news()`는 SERP API 뉴스 목록(제목·스니펫)만 반환하고 본문은 수집하지 않아
Analysis Agent에 전달되는 정보가 얕았다. 기존 `ArticleContentFetcher(trafilatura)` 인프라를
재사용하여 실제 본문까지 수집하고, news 도메인 DB(`investment_news`, `investment_news_contents`)에 저장한다.

---

## Success Criteria

- news 도메인에서 구현하며, 투자 판단 워크플로우 Retrieval 단계에서 재사용한다
- 입력은 `parsed_query.company` (종목명)이며, 없으면 기본 방산 키워드로 fallback한다
- SERP API로 뉴스 목록 검색 → 각 링크에서 `ArticleContentFetcher`로 본문 추출
- 메타데이터(제목·출처·링크·게시시간)는 MySQL `investment_news`에 저장
- 본문(JSONB)은 PostgreSQL `investment_news_contents`에 cross-DB 키(MySQL PK = `article_id`)로 저장
- 개별 뉴스 본문 수집 실패 시 해당 뉴스만 제외하고 나머지 계속 진행 (부분 실패 허용)
- 수집된 메타데이터 + 본문 요약이 하나의 텍스트로 합쳐져 `retrieval_data`에 적재된다

---

## To-Do

- [x] MySQL ORM `InvestmentNewsORM` (`investment_news` 테이블) 생성
- [x] PostgreSQL ORM `InvestmentNewsContentORM` (`investment_news_contents` 테이블, JSONB) 생성
- [x] `investment_news_source.py`: SERP 검색 → 본문 수집 → DB 저장 → 포맷 텍스트 반환
- [x] `retrieval_node._handle_news()` 를 새 서비스로 교체하고 company 파라미터 전달
- [x] `main.py` 에 신규 ORM 2개 임포트 등록
- [x] 본문 수집 실패 시 부분 실패 허용 + traceback 로깅 적용

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `domains/news_search/infrastructure/orm/investment_news_orm.py` | MySQL 뉴스 메타데이터 ORM |
| `domains/news_search/infrastructure/orm/investment_news_content_orm.py` | PG 뉴스 본문 JSONB ORM |
| `domains/news_search/adapter/outbound/external/investment_news_source.py` | 수집·저장·포맷 서비스 |
| `domains/investment/adapter/outbound/agent/retrieval_node.py` | `_handle_news()` 교체 |
| `infrastructure/external/article_content_fetcher.py` | 기존 trafilatura 본문 추출기 (재사용) |
| `main.py` | ORM 임포트 등록 |

---

## 구현 완료일

2026-04-15
