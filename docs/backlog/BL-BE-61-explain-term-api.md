# BL-BE-61: 백엔드 서버가 주식 용어를 AI로 쉽게 설명한다

> **담당**: 김동녁 | **단계**: 0단계 | **주차**: Week 1

## 배경

뉴스·공시 카드에 등장하는 PER, EPS, 유동비율 등 전문 금융 용어를 일반 사용자가 이해하기 어렵다.
클릭 한 번으로 용어의 의미를 AI가 쉽게 설명해주는 API가 필요하다.

## Success Criteria

- `POST /market-analysis/explain-term` 엔드포인트가 `{"term": "PER"}` 요청을 받아 쉬운 설명을 반환한다
- LangChain 체인이 금융 용어 사전 데이터를 참고하여 2~3문장 분량의 한국어 설명을 생성한다
- 주요 금융 용어(PER, EPS, ROE, 유동비율, 부채비율 등 20개 이상)에 대한 사전 데이터가 구축된다
- 미등록 용어도 LLM이 일반 지식으로 설명할 수 있다
- 투자 추천·비추천 표현은 절대 포함하지 않는다

## To-do

- [ ] `POST /market-analysis/explain-term` 라우터 추가 (`adapter/inbound/api/market_analysis_router.py`)
- [ ] `ExplainTermRequest`, `ExplainTermResponse` DTO 정의 (`application/request`, `application/response`)
- [ ] LangChain 기반 용어 설명 체인 구현 (`adapter/outbound/external/explain_term_chain.py`)
- [ ] 주요 금융 용어 사전 데이터 구축 (dict 또는 JSON 파일, 20개 이상)
- [ ] 용어 사전 데이터를 체인 프롬프트에 주입하는 로직 구현
- [ ] UseCase 구현 (`application/usecase/explain_term_usecase.py`)
