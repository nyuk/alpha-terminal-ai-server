# BL-BE-69 — Retrieval Agent: required_data 기반 데이터 소스 라우팅

## 개요

Retrieval Agent가 Orchestrator로부터 전달받은 공유 State의 `parsed_query.required_data` 배열을 읽어
호출할 데이터 소스를 결정하고, 병렬로 수집한 결과를 하나의 `retrieved_data`로 병합한다.

---

## 배경

기존 Retrieval Agent는 항상 고정된 데이터 소스를 호출했다.
Orchestrator가 `parsed_query.required_data`에 필요한 소스를 명시하므로,
Retrieval Agent는 이 배열을 기반으로 동적으로 호출 소스를 결정해야 한다.

---

## Success Criteria

- Retrieval Agent는 `parsed_query.required_data` 배열을 순회해 호출할 데이터 소스를 결정한다
- `required_data`에 `"뉴스"`가 포함되면 기존 SERP API 인프라를 재사용해 구글 뉴스를 수집한다
- `required_data`에 `"YouTube 영상"`이 포함되면 기존 YouTube 검색 인프라를 호출하고 결과를 State에 적재한다
- 두 소스 모두 해당되면 `asyncio.gather`로 병렬 호출하고 결과를 하나의 `retrieved_data`로 합쳐 기록한다
- 등록되지 않은 소스(`"재무"`, `"시장_데이터"` 등)는 현재 무시하고 로그에 기록하며 `SOURCE_REGISTRY` 확장으로 향후 추가 가능하다
- 단일 소스 호출 실패 시 해당 소스만 실패 메시지로 대체하고 나머지 소스는 정상 수집을 계속한다 (부분 실패 허용)
- `aemit()`으로 흐름 로그를 SSE 스트림에 실시간 출력한다

---

## 설계

### SOURCE_REGISTRY 패턴

```python
SOURCE_REGISTRY: dict[str, SourceFactory] = {
    "뉴스":         lambda kw, q, c: _handle_news(kw),
    "YouTube 영상": lambda kw, q, c: _handle_youtube(kw, q, c),
    "종목":         lambda kw, q, c: _handle_stock(kw),  # 향후 구현
}
```

- `key`: `required_data` 식별자 (Query Parser 프롬프트 목록과 동일)
- `value`: async handler factory — `(keyword, query, company) → Coroutine[str]`
- 새 소스 추가 시 핸들러 함수 작성 + `SOURCE_REGISTRY`에 한 줄만 추가하면 자동 병렬화 적용

### 병렬 실행 전략

```
required_data = ["뉴스", "YouTube 영상"]
  →  asyncio.gather(
       wait_for(_handle_news,    timeout=30s),
       wait_for(_handle_youtube, timeout=30s),
     )
  →  소요 시간 ≈ max(뉴스 시간, YouTube 시간) + 오버헤드
```

### 부분 실패 정책

- 각 소스는 `asyncio.wait_for` 래핑으로 30초 타임아웃
- 타임아웃 또는 예외 → 해당 소스만 실패 메시지 문자열 반환 (예외 전파 X)
- `asyncio.gather`는 항상 완료 → 성공 소스 결과는 정상 병합

### Query Parser 연동

- `query_parser.py`의 `SOURCE_REGISTRY` (설명용)와 `retrieval_node.py`의 `SOURCE_REGISTRY` (핸들러용) 키를 동일하게 유지
- Query Parser 프롬프트가 `SOURCE_REGISTRY.keys()`를 직접 참조해 LLM 응답 키를 강제함

---

## To-Do

- [x] `parsed_query.required_data` 배열을 순회하며 데이터 소스별 호출 여부를 판별하는 라우팅 로직 구현
- [x] `"뉴스"` → SERP API `SerpNewsSearchAdapter` 연결 및 State 적재
- [x] `"YouTube 영상"` → `YouTubeApiAdapter.collect_from_channels` + DB 저장 연결
- [x] 복수 소스 수집 결과를 `required_data` 순서대로 하나의 `retrieved_data`로 병합
- [x] 소스별 30초 타임아웃 + 부분 실패 허용 예외 처리
- [x] `aemit()` 기반 실시간 흐름 로그 (SSE 스트림 출력)
- [x] 미등록 소스는 로그에 기록 후 건너뜀 (향후 `SOURCE_REGISTRY` 확장 구조 열어둠)

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `adapter/outbound/agent/retrieval_node.py` | Retrieval 노드 진입점 + SOURCE_REGISTRY + 병렬 실행 |
| `adapter/outbound/agent/query_parser.py` | required_data 키 정의 + LLM 파싱 |
| `domains/news_search/adapter/outbound/external/serp_news_search_adapter.py` | SERP API 뉴스 어댑터 |
| `domains/youtube/adapter/outbound/external/youtube_api_adapter.py` | YouTube API 어댑터 |
| `infrastructure/repository/investment_youtube_repository.py` | YouTube 수집 결과 DB 저장 |

---

## 구현 완료일

2026-04-15
