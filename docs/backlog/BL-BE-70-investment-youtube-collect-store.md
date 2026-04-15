# BL-BE-70 — 투자 워크플로우 YouTube 데이터 수집 및 저장

## 개요

투자 판단 워크플로우에서 Query Parser가 모든 데이터 소스를 누락 없이 인식하고,
YouTube 수집 결과(영상 + 댓글)를 MySQL + PostgreSQL에 안정적으로 저장한다.

---

## 배경

- Query Parser `DEFAULT_SOURCES`가 `["뉴스", "YouTube 영상"]`만 포함해 `"종목"` 소스가 fallback에서 누락됨
- 저장 실패 시 traceback 미출력으로 원인 진단 어려움
- `published_at` 문자열을 datetime으로 변환하는 헬퍼가 없어 MySQL DateTime 컬럼 저장 실패 가능
- MySQL(`investment_youtube_logs`, `investment_youtube_videos`)과 PostgreSQL(`investment_youtube_video_comments`) 테이블에 row 적재 검증 필요

---

## Success Criteria

- Query Parser가 `"뉴스"`, `"YouTube 영상"`, `"종목"` 모두를 선택지로 인식하여 `required_data`에 누락 없이 포함한다
- 검증 시 `SOURCE_REGISTRY`에 실제 등록된 키만 통과하며, 결과가 비거나 미구현 키만 있으면 `["뉴스", "YouTube 영상", "종목"]` 전체로 fallback한다
- 데이터 저장 중 예외 발생 시 콘솔에 `traceback.print_exc()`가 출력되어 원인 진단이 즉시 가능하다
- 워크플로우 1회 실행 시 세 테이블(`investment_youtube_logs`, `investment_youtube_videos`, `investment_youtube_video_comments`)에 모두 row가 적재된다

---

## To-Do

- [x] Query Parser 프롬프트에 소스별 설명·선택 기준을 명시하고 예시를 보강한다
- [x] `DEFAULT_SOURCES`를 `["뉴스", "YouTube 영상", "종목"]`으로 업데이트한다
- [x] `_parse_published_at()` 헬퍼를 `investment_youtube_repository.py`에 도입하고 영상 저장 시 적용한다
- [x] 저장 실패 시 `traceback.print_exc()` 진단 로깅을 전 경로에 적용한다
- [x] `main.py`에 Investment ORM 3개 임포트 등록 및 `create_all` 포함 확인

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `adapter/outbound/agent/query_parser.py` | SOURCE_REGISTRY 키 정의, 프롬프트, fallback |
| `infrastructure/repository/investment_youtube_repository.py` | MySQL + PG 저장, traceback 로깅, `_parse_published_at` |
| `infrastructure/orm/investment_youtube_log_orm.py` | MySQL 로그 테이블 ORM |
| `infrastructure/orm/investment_youtube_video_orm.py` | MySQL 영상 테이블 ORM |
| `infrastructure/orm/investment_youtube_comment_orm.py` | PostgreSQL 댓글 테이블 ORM |
| `main.py` | ORM 임포트 등록, `Base.metadata.create_all` |

---

## 구현 완료일

2026-04-15
