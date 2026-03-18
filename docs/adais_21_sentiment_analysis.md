# normalized_article 감정 분석

작성자: 이승욱 (R3 AI 처리기)
작성일: 2026-03-17
관련 백로그: ADAIS-21

---

## Backlog Title

R3 AI 처리기가 normalized_article의 감정을 분석한다

---

## Success Criteria

- normalized_article을 입력으로 받아 감정 분석 결과를 반환한다
- sentiment: POSITIVE | NEGATIVE | NEUTRAL 중 하나를 반환한다
- sentiment_score: -1.0 ~ 1.0 범위를 반환한다
- `GET /analyzer/articles/{id}/sentiment` API가 동작한다

---

## Todo

- [ ] SentimentAnalysisPort (ABC) 정의
- [ ] SentimentAnalysisUseCase 구현
- [ ] OpenAI 감정 분석 프롬프트 작성
- [ ] OpenAISentimentAdapter 구현 (gpt-5-mini)
- [ ] sentiment router 구현 및 main.py 등록

---

## 구현 위치 (예정)

| 레이어 | 파일 |
|--------|------|
| Application Port | `application/usecase/sentiment_analysis_port.py` |
| Application UseCase | `application/usecase/analyze_sentiment_usecase.py` |
| Outbound Adapter | `adapter/outbound/external/openai_sentiment_adapter.py` |
| Inbound Adapter | `adapter/inbound/api/analyzer_router.py` (추가) |

## API 엔드포인트 (예정)

```
GET /analyzer/articles/{id}/sentiment
```

## sentiment 기준

| 값 | 설명 |
|----|------|
| `POSITIVE` | 긍정적 내용 (실적 호조, 투자 확대 등) |
| `NEGATIVE` | 부정적 내용 (실적 하락, 소송, 리스크 등) |
| `NEUTRAL` | 중립적 내용 (단순 공시, 인사 발령 등) |

---

## 구현 완료

| 레이어 | 파일 |
|--------|------|
| Application Port | `application/usecase/sentiment_analysis_port.py` |
| Application UseCase | `application/usecase/analyze_sentiment_usecase.py` |
| Application Response | `application/response/sentiment_analysis_response.py` |
| Outbound Adapter | `adapter/outbound/external/openai_sentiment_adapter.py` |
| Inbound Adapter | `adapter/inbound/api/analyzer_router.py` (GET /analyzer/articles/{id}/sentiment 추가) |

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-17 | 이승욱 | 최초 작성 |
| 2026-03-18 | 이승욱 | 구현 완료 |
