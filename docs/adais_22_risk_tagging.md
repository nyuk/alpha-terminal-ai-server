# normalized_article 리스크 태그 생성

작성자: 이승욱 (R3 AI 처리기)
작성일: 2026-03-17
관련 백로그: ADAIS-22

---

## Backlog Title

R3 AI 처리기가 normalized_article의 리스크 태그를 생성한다

---

## Success Criteria

- normalized_article을 입력으로 받아 리스크 태그를 생성할 수 있다
- 태그는 사실 기반으로만 생성되며 투자 의견을 포함하지 않는다
- tags[].category가 RISK enum 값을 포함한다
- `GET /analyzer/articles/{id}/risk-tags` API가 동작한다

---

## Todo

- [ ] RiskTaggingPort (ABC) 정의
- [ ] RiskTaggingUseCase 구현
- [ ] OpenAI 리스크 태그 프롬프트 작성 (투자 의견 금지 지시 포함)
- [ ] OpenAIRiskTagAdapter 구현 (gpt-5-mini)
- [ ] risk-tags router 구현 및 main.py 등록

---

## 구현 위치 (예정)

| 레이어 | 파일 |
|--------|------|
| Application Port | `application/usecase/risk_tagging_port.py` |
| Application UseCase | `application/usecase/generate_risk_tags_usecase.py` |
| Outbound Adapter | `adapter/outbound/external/openai_risk_tag_adapter.py` |
| Inbound Adapter | `adapter/inbound/api/analyzer_router.py` (추가) |

## API 엔드포인트 (예정)

```
GET /analyzer/articles/{id}/risk-tags
```

## 리스크 태그 규칙

- 사실 기반으로만 태그를 생성한다
- 투자 추천/비추천 표현 절대 금지
- `tags[].category`는 `RISK`로 고정

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-17 | 이승욱 | 최초 작성 |
