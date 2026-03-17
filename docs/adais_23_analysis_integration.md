# article_analysis 통합 저장/반환

작성자: 이승욱 (R3 AI 처리기)
작성일: 2026-03-17
관련 백로그: ADAIS-23

---

## Backlog Title

R3 AI 처리기가 article_analysis를 통합 저장하고 반환한다

---

## Success Criteria

- 키워드 추출, 감정 분석, 리스크 태그, 요약을 한 번의 API 호출로 처리한다
- 분석 결과가 DB에 저장되며 중복 분석을 방지한다
- ORM Model이 Domain Entity와 분리되어 있다
- `GET /analyzer/articles/{id}/analysis` API가 동작한다

---

## Todo

- [ ] ArticleAnalysisORM 모델 작성 (infrastructure/orm)
- [ ] ArticleAnalysisMapper 작성 (ORM ↔ Domain Entity)
- [ ] ArticleAnalysisRepositoryPort (ABC) 정의
- [ ] ArticleAnalysisRepositoryImpl 구현 (중복 저장 방지 로직 포함)
- [ ] AnalyzeArticleUseCase 통합 (키워드+감정+리스크+요약 합산)

---

## 구현 위치 (예정)

| 레이어 | 파일 |
|--------|------|
| Infrastructure ORM | `infrastructure/orm/article_analysis_orm.py` |
| Infrastructure Mapper | `infrastructure/mapper/article_analysis_mapper.py` |
| Application Port | `application/usecase/article_analysis_repository_port.py` |
| Application UseCase | `application/usecase/analyze_article_usecase.py` (통합 확장) |
| Outbound Persistence | `adapter/outbound/persistence/article_analysis_repository_impl.py` |
| Inbound Adapter | `adapter/inbound/api/analyzer_router.py` (추가) |

## API 엔드포인트 (예정)

```
GET /analyzer/articles/{id}/analysis
```

## 응답 구조

ADAIS-16에서 정의한 `ArticleAnalysisResponse` 스키마를 따른다.

```json
{
  "article_id": "uuid",
  "summary": "...",
  "tags": [...],
  "sentiment": "POSITIVE",
  "sentiment_score": 0.75,
  "confidence": 0.92,
  "analyzer_version": "analyzer-v1.0.0"
}
```

## 중복 분석 방지 규칙

- 동일 `article_id`로 분석 결과가 이미 존재하면 DB에서 조회하여 반환한다
- 존재하지 않을 경우에만 OpenAI API를 호출하고 저장한다

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-17 | 이승욱 | 최초 작성 |
