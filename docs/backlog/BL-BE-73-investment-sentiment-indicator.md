# BL-BE-73 — 투자 심리 지표 산출 (YouTube 댓글 + 뉴스 감성 분석)

## 개요

투자 판단 워크플로우 Retrieval 단계에서 수집된 YouTube 댓글과 뉴스 기사를 LLM으로 분석하여
구조화된 투자 심리 지표를 산출하고 retrieval_data에 포함시킨다.

---

## Success Criteria

- YouTube 댓글 → `sentiment_distribution`, `sentiment_score`, `bullish_keywords`, `bearish_keywords`, `topics`, `volume` 산출
- 뉴스 기사 → `positive_events`, `negative_events`, `keywords` 산출
- 분석 실패 시 빈 지표 반환, 상위 호출부에서 처리 가능
- 50~250건 댓글 기준 10초 이내 완료
- 산출된 지표가 retrieval_data에 포함되어 Analysis Agent에 전달됨
- aemit()으로 지표 내용 실시간 출력

---

## 지표 스키마

### YouTube
```json
{
    "sentiment_distribution": {"positive": 0.40, "neutral": 0.35, "negative": 0.25},
    "sentiment_score": 0.15,
    "bullish_keywords": ["매수", "상승", "호재"],
    "bearish_keywords": ["하락", "리스크", "우려"],
    "topics": ["방산", "수출", "실적"],
    "volume": 150
}
```

### 뉴스
```json
{
    "positive_events": [{"event": "방산 수출 수주 증가", "impact": "high"}],
    "negative_events": [{"event": "원자재 가격 상승", "impact": "medium"}],
    "keywords": ["방산", "수출", "수주"]
}
```

---

## To-Do

- [x] `sentiment_analyzer.py`: `analyze_youtube_comments()` + `analyze_news_articles()` LLM 분석 모듈 구현
- [x] `_handle_youtube()`: 댓글 수집 후 YouTube 심리 지표 산출 → retrieval_data 포함
- [x] `investment_news_source.py`: 기사 수집 후 뉴스 심리 지표 산출 → retrieval_data 포함
- [x] 분석 실패 시 빈 지표 fallback 적용
- [x] aemit()으로 지표 실시간 출력

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `adapter/outbound/agent/sentiment_analyzer.py` | LLM 기반 YouTube/뉴스 심리 분석 |
| `adapter/outbound/agent/retrieval_node.py` | `_handle_youtube` YouTube 지표 연동 |
| `domains/news_search/adapter/outbound/external/investment_news_source.py` | 뉴스 지표 연동 |

---

## 구현 완료일

2026-04-15
