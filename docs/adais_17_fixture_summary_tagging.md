# fixture 기반 요약/태깅 초안 구현

작성자: 이승욱 (R3 AI 처리기)
작성일: 2026-03-17
관련 백로그: ADAIS-17

---

## 목적

`normalized_article` fixture를 입력으로 받아
요약(summary), 태그(tags), 신뢰도(confidence) 결과를 생성한다.

실제 수집기(R1), 정규화기(R2) 없이도 R3 파이프라인을 검증할 수 있다.

---

## 입력 fixture (normalized_article 기준)

ADAIS-15에서 확정된 `normalized_article` 스키마를 입력으로 사용한다.

```json
{
  "id": "uuid",
  "stock_symbol": "005930",
  "source_type": "DISCLOSURE",
  "source_name": "DART",
  "title": "삼성전자 유상증자 결정 공시",
  "body": "삼성전자는 운영자금 확보를 위해 보통주 1,000만 주에 대한 유상증자를 결정했다.",
  "category": "DISCLOSURE_CAPITAL",
  "published_at": "2026-03-15T08:30:00+09:00",
  "lang": "ko",
  "content_quality": "VALID"
}
```

---

## 요약 결과 예시

### DISCLOSURE_CAPITAL (유상증자)

```json
{
  "summary": "삼성전자는 운영자금 확보를 위해 보통주 1,000만 주 규모의 유상증자를 결정했다고 공시했다. 신주 발행가는 주당 65,000원이며 납입기일은 2026년 4월 15일이다.",
  "tags": [
    { "label": "유상증자", "category": "CAPITAL" },
    { "label": "신주발행", "category": "CAPITAL" },
    { "label": "운영자금조달", "category": "CAPITAL" }
  ],
  "sentiment": "NEUTRAL",
  "sentiment_score": 0.1,
  "confidence": 0.95
}
```

### DISCLOSURE_EARNINGS (실적)

```json
{
  "summary": "SK하이닉스는 2025년 4분기 매출 17조 8,000억 원, 영업이익 8조 1,000억 원을 기록했다고 공시했다. HBM3E 수요 증가에 힘입어 전년 동기 대비 매출 42%, 영업이익 125% 증가했다.",
  "tags": [
    { "label": "실적호조", "category": "EARNINGS" },
    { "label": "HBM3E수요", "category": "PRODUCT" },
    { "label": "영업이익증가", "category": "EARNINGS" }
  ],
  "sentiment": "POSITIVE",
  "sentiment_score": 0.85,
  "confidence": 0.93
}
```

### NEWS (뉴스)

```json
{
  "summary": "삼성전자가 AI 반도체 경쟁력 강화를 위해 올해 설비 투자를 10조 원 추가 확대한다. HBM4 양산 시점을 2026년 하반기로 앞당기고 평택 P4 공장 증설을 가속화한다.",
  "tags": [
    { "label": "설비투자확대", "category": "CAPITAL" },
    { "label": "HBM4양산", "category": "PRODUCT" },
    { "label": "AI반도체", "category": "INDUSTRY" }
  ],
  "sentiment": "POSITIVE",
  "sentiment_score": 0.75,
  "confidence": 0.88
}
```

---

## confidence 값 기준 검증

| fixture 유형 | 예상 confidence 범위 | 이유 |
|-------------|---------------------|------|
| DART 공시 | 0.90 ~ 0.98 | 공식 문서, 구조적 명확성 |
| 뉴스 기사 | 0.80 ~ 0.92 | 기자 해석 포함 가능 |
| 짧은 본문 (<50자) | 0.50 ~ 0.75 | 정보 부족 |

---

## 응답 구조 검증 체크리스트

- [ ] `summary` 필드: 문자열, 1~3문장
- [ ] `tags` 필드: 배열, 각 항목에 `label`과 `category` 포함
- [ ] `tags[].category`: 허용 enum 값 중 하나 (CAPITAL/EARNINGS/PRODUCT/MANAGEMENT/INDUSTRY/RISK/OTHER)
- [ ] `sentiment`: POSITIVE | NEGATIVE | NEUTRAL 중 하나
- [ ] `sentiment_score`: -1.0 ~ 1.0 범위
- [ ] `confidence`: 0.0 ~ 1.0 범위
- [ ] 투자 추천/비추천 표현 미포함

---

## 구현 완료 사항

- OpenAI gpt-5-mini Responses API 사용 (`client.responses.create`)
- DART 공시(DISCLOSURE_CAPITAL, DISCLOSURE_EARNINGS)와 뉴스(NEWS) 모두 처리 가능
- confidence 기준: DART 공시 0.90~0.98, 뉴스 0.80~0.92
- 투자 추천/비추천 표현 프롬프트 레벨에서 금지 지시 포함
- API: `POST /analyzer/articles`

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-17 | 이승욱 | 최초 작성 |
| 2026-03-17 | 이승욱 | 구현 완료 |
