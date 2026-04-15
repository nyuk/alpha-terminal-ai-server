# BL-BE-74 — 투자 판단 의견 산출 (Deterministic Rule Engine + LLM rationale)

## 개요

Retrieval 단계에서 수집한 YouTube 감성 신호와 뉴스 이벤트 신호를 결합하여
direction / confidence / verdict 를 deterministic rule 기반으로 산출하고,
LLM은 rationale(reasons, risk_factors) 생성에만 사용한다.

---

## Success Criteria

- `direction` = news_score(impact 가중합) > threshold → bullish / bearish / neutral
- `confidence` = sigmoid(W1 * |news_score| + W2 * |sentiment_score|), 0~1 정규화
- `verdict` = bullish+confidence>0.6 → buy / bearish+confidence>0.6 → sell / else → hold
- direction·confidence·verdict는 동일 입력에 항상 동일 결과 (deterministic)
- LLM은 reasons·risk_factors 생성에만 개입
- 신호 부족(이벤트 0건, 댓글 0건) 시 verdict=hold, confidence≤0.3 보수적 fallback
- 결과는 JSON 직렬화 가능한 구조로 Synthesis Agent에 전달
- 중간 과정 aemit() 으로 실시간 출력

---

## 결과 스키마

```json
{
    "direction": "bullish | bearish | neutral",
    "confidence": 0.73,
    "verdict": "buy | hold | sell",
    "reasons": {
        "positive": ["긍정 근거 1", ...],
        "negative": ["부정 근거 1", ...]
    },
    "risk_factors": ["리스크 1", ...]
}
```

---

## 규칙

```
impact weights: high=3.0, medium=2.0, low=1.0
news_score = Σ pos_impact - Σ neg_impact
direction: news_score > 2.0 → bullish / < -2.0 → bearish / else → neutral
confidence = sigmoid(1.0 * |news_score| + 0.5 * |sentiment_score|)
verdict: (bullish AND confidence>0.6) → buy
         (bearish AND confidence>0.6) → sell
         else → hold
```

---

## To-Do

- [x] `InvestmentAgentState` 에 `youtube_signal`, `news_signal`, `investment_verdict` 필드 추가
- [x] 핸들러 반환 타입을 `tuple[str, Optional[dict]]`로 변경하여 신호를 state 에 전달
- [x] `investment_decision_analyzer.py`: deterministic engine + LLM rationale
- [x] `analysis_node.py`: 신호 읽어 verdict 산출 → analysis에 포함
- [x] `investment_graph_builder.py`: initial_state 신규 필드 초기화

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `adapter/outbound/agent/investment_agent_state.py` | 신규 signal·verdict 필드 |
| `adapter/outbound/agent/investment_decision_analyzer.py` | deterministic engine + LLM rationale |
| `adapter/outbound/agent/retrieval_node.py` | 핸들러 tuple 반환, 신호 수집 |
| `adapter/outbound/agent/analysis_node.py` | analyzer 호출, verdict → analysis |
| `domains/news_search/adapter/.../investment_news_source.py` | tuple 반환 |
| `infrastructure/langgraph/investment_graph_builder.py` | initial_state 추가 필드 |

---

## 구현 완료일

2026-04-15
