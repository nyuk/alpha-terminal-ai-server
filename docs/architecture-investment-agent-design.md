# 투자 판단 워크플로우 — 에이전트 설계 결정 기록

작성일: 2026-04-14

---

## 현재 구조: LangGraph 멀티스텝 워크플로우

```
START
  ↓
Orchestrator (LLM) ─── 라우팅 결정 ───→ Retrieval (API 직접 호출)
                                      → Analysis  (LLM)
                                      → Synthesis (LLM)
                                      → END
```

### 노드별 역할

| 노드 | LLM 사용 | 역할 |
|---|---|---|
| Orchestrator | ✓ | 현재 상태 파악 → 다음 실행 에이전트 결정 |
| Retrieval | ✗ | SERP/YouTube API 직접 호출 (도구 실행기) |
| Analysis | ✓ | 수집 데이터 기반 종목 전망·리스크·투자 포인트 분석 |
| Synthesis | ✓ | 분석 결과를 사용자 친화적 응답으로 종합 |

엄밀히는 **LangGraph 기반 Orchestrator-Worker 패턴**이며,
마케팅 용어인 "멀티에이전트"와 학술적 정의 사이 어딘가에 위치한다.

---

## Retrieval: API 직접 호출 vs LLM 포함의 차이

### 현재 방식 — API 직접 호출

```python
keyword = company if company else query  # 예: "삼성전자"
adapter.search(keyword=keyword, page_size=5)
```

- 검색어: Query Parser가 추출한 `company` 또는 원본 `query` 고정
- 검색 범위: 코드에 하드코딩 (뉴스 5건, YouTube 최근 7일)
- 결과가 부족해도 재검색 없음

**흐름:** 사용자 질문 → 키워드 추출 → API 1회 호출 → 끝

---

### LLM 포함 방식 — 검색 전략을 AI가 결정

```
사용자: "삼성전자 HBM 관련 최근 이슈 알려줘"

LLM이 판단:
  → 검색어 1: "삼성전자 HBM 수율"
  → 검색어 2: "HBM 시장 경쟁 SK하이닉스"
  → 검색어 3: "삼성전자 엔비디아 납품"
  → YouTube는 최근 30일치로 확장
  → 뉴스 결과 빈약하면 재검색 판단
```

**흐름:** 사용자 질문 → LLM이 수집 전략 수립 → 전략에 따라 API 반복 호출

---

### 비교

| 항목 | 직접 호출 (현재) | LLM 포함 |
|---|---|---|
| 검색어 | 종목명 고정 | 질문 맥락에 맞게 다양하게 생성 |
| 검색 범위 | 하드코딩 | 질문 성격에 따라 동적 조절 |
| 재검색 | 불가 | 결과 품질 보고 재시도 가능 |
| 소스 선택 | required_data 고정 | 뉴스/리포트/공시 등 동적 판단 |
| LLM 비용 | API 비용만 | API + LLM 추가 비용 |
| 속도 | 빠름 | 느림 (LLM 호출 추가) |

---

## 왜 현재는 직접 호출로 충분한가

대부분의 투자 질문은 단순한 패턴:
- `"삼성전자 지금 사도 될까?"` → "삼성전자"로 검색하면 충분
- `"방산주 전망 알려줘"` → 원본 쿼리로 검색하면 충분

키워드가 명확하게 식별되는 경우, LLM 전략 수립은 비용 대비 효과가 낮다.

---

## LLM 포함이 필요한 시점

다음 요구사항이 생기면 LangGraph Tool Calling 패턴으로 Retrieval 노드 고도화를 고려한다:

1. **복합 검색어 필요**: "HBM 수율 문제와 엔비디아 관계" 같은 질문에서 여러 검색어 생성
2. **재검색 루프**: 수집 결과가 빈약할 때 검색어를 바꿔 재시도
3. **소스 동적 선택**: 질문 성격에 따라 뉴스 / 공시 / 애널리스트 리포트 선택
4. **검색 범위 조절**: 급등 이슈는 최근 3일, 장기 전망은 3개월치

---

## 관련 파일

```
app/domains/investment/adapter/outbound/agent/
  ├ orchestrator_node.py   — LLM 라우팅
  ├ retrieval_node.py      — API 직접 호출 (SOURCE_REGISTRY 패턴)
  ├ analysis_node.py       — LLM 분석
  ├ synthesis_node.py      — LLM 종합
  ├ query_parser.py        — 자연어 → company/intent/required_data
  └ log_context.py         — SSE 스트리밍용 요청별 로그 큐

app/domains/investment/infrastructure/langgraph/
  └ investment_graph_builder.py  — StateGraph 빌드 및 워크플로우 진입점
```
