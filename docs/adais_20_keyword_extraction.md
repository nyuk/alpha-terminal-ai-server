# normalized_article 핵심 키워드 추출

작성자: 이승욱 (R3 AI 처리기)
작성일: 2026-03-17
관련 백로그: ADAIS-20

---

## Backlog Title

R3 AI 처리기가 normalized_article의 핵심 키워드를 추출한다

---

## Success Criteria

- normalized_article을 입력으로 받아 핵심 키워드를 추출할 수 있다
- OpenAI gpt-5-mini Responses API를 사용한다
- 키워드는 최대 5개, 한글 키워드로 반환된다
- `GET /analyzer/articles/{id}/keywords` API가 동작한다

---

## Todo

- [ ] KeywordExtractionPort (ABC) 정의
- [ ] KeywordExtractionUseCase 구현
- [ ] OpenAI 키워드 추출 프롬프트 작성
- [ ] OpenAIKeywordAdapter 구현 (gpt-5-mini)
- [ ] keywords router 구현 및 main.py 등록

---

## 구현 위치 (예정)

| 레이어 | 파일 |
|--------|------|
| Application Port | `application/usecase/keyword_extraction_port.py` |
| Application UseCase | `application/usecase/extract_keywords_usecase.py` |
| Outbound Adapter | `adapter/outbound/external/openai_keyword_adapter.py` |
| Inbound Adapter | `adapter/inbound/api/analyzer_router.py` (추가) |

## API 엔드포인트 (예정)

```
GET /analyzer/articles/{id}/keywords
```

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-17 | 이승욱 | 최초 작성 |
