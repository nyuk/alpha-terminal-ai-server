# AI 요약 응답 스키마 정의

작성자: 이승욱 (R3 AI 처리기)
작성일: 2026-03-17
관련 백로그: ADAIS-16

---

## 목적

R3 AI 처리기의 출력 스키마를 정의한다.

FE 대시보드와의 연동 기준으로 사용한다.

---

## 응답 구조

```json
{
  "article_id": 1,
  "summary": "삼성전자가 AI 반도체 경쟁력 강화를 위해 설비 투자를 10조 원 확대하고 HBM4 양산 시점을 앞당긴다고 발표했다.",
  "tags": [
    { "label": "설비투자확대", "category": "CAPITAL" },
    { "label": "HBM4양산", "category": "PRODUCT" },
    { "label": "AI반도체경쟁", "category": "INDUSTRY" }
  ],
  "sentiment": "POSITIVE",
  "sentiment_score": 0.75,
  "confidence": 0.92,
  "analyzer_version": "analyzer-v1.0.0"
}
```

---

## 필드 목록

| 필드 | 타입 | Nullable | 설명 |
|------|------|----------|------|
| `article_id` | str | NO | 분석 대상 normalized_article id |
| `summary` | str | NO | 사실 기반 요약문 (1~3문장) |
| `tags` | array | NO | 태그 목록 (빈 배열 가능) |
| `tags[].label` | str | NO | 태그명 (한글 키워드) |
| `tags[].category` | str | NO | 태그 카테고리 enum |
| `sentiment` | str | NO | `POSITIVE` \| `NEGATIVE` \| `NEUTRAL` |
| `sentiment_score` | float | NO | -1.0(부정) ~ 1.0(긍정) |
| `confidence` | float | NO | AI 분석 신뢰도 0.0 ~ 1.0 |
| `analyzer_version` | str | NO | 예: `analyzer-v1.0.0` |

---

## tags 구조

### category enum

| 값 | 설명 |
|----|------|
| `CAPITAL` | 자본 변동 관련 (증자, 감자, 배당 등) |
| `EARNINGS` | 실적 관련 (매출, 영업이익 등) |
| `PRODUCT` | 제품/서비스 관련 |
| `MANAGEMENT` | 경영진/조직 변경 |
| `INDUSTRY` | 산업/시장 동향 |
| `RISK` | 리스크 관련 (소송, 규제, 사고 등) |
| `OTHER` | 기타 |

---

## confidence 기준

| 범위 | 의미 |
|------|------|
| 0.9 ~ 1.0 | 높은 신뢰도 — 본문 명확, 분석 근거 충분 |
| 0.7 ~ 0.9 | 보통 신뢰도 — 일부 모호한 표현 포함 |
| 0.0 ~ 0.7 | 낮은 신뢰도 — 본문 부족 또는 분석 불확실 |

---

## summary 작성 규칙

- 사실 기반으로만 작성한다
- 투자 추천/비추천 표현 절대 금지
- 1~3문장 이내로 작성한다
- 원문의 핵심 내용을 그대로 요약한다

**금지 표현 예시**
- "매수를 고려할 만한 호재입니다" ❌
- "주가 상승이 예상됩니다" ❌

**허용 표현 예시**
- "삼성전자가 설비 투자를 10조 원 확대한다고 발표했다" ✅
- "SK하이닉스는 4분기 영업이익 8조 원을 기록했다고 공시했다" ✅

---

## 구현 파일 목록

| 레이어 | 파일 |
|--------|------|
| Domain Entity | `app/domains/stock_analyzer/domain/entity/analyzed_article.py` |
| Domain Entity | `app/domains/stock_analyzer/domain/entity/tag_item.py` |
| Application Request | `app/domains/stock_analyzer/application/request/analyze_article_request.py` |
| Application Response | `app/domains/stock_analyzer/application/response/article_analysis_response.py` |
| Application Port | `app/domains/stock_analyzer/application/usecase/article_analyzer_port.py` |
| Application UseCase | `app/domains/stock_analyzer/application/usecase/analyze_article_usecase.py` |
| Outbound Adapter | `app/domains/stock_analyzer/adapter/outbound/external/openai_analyzer_adapter.py` |
| Inbound Adapter | `app/domains/stock_analyzer/adapter/inbound/api/analyzer_router.py` |

## API 엔드포인트

```
POST /analyzer/articles
```

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-17 | 이승욱 | 최초 작성 |
| 2026-03-17 | 이승욱 | 구현 완료 — OpenAI gpt-5-mini 기반, POST /analyzer/articles |
