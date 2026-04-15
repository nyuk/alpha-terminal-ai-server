# BL-BE-65: 백엔드 서버가 사용자 취향 기반 맞춤 프롬프트를 생성한다

> **담당**: 이승욱 | **단계**: 2단계 | **주차**: Week 2~3 | **상태**: ✅ 완료

## 배경

`get_user_profile` Tool로 조회한 사용자 취향 데이터를 프롬프트에 반영하여
AI 분석의 개인화 수준을 높인다.

## Success Criteria

- [x] 사용자 관심 섹터, 투자 스타일, 위험 허용도가 프롬프트 컨텍스트에 주입된다
- [x] 동일 질문에도 투자 성향에 따라 다른 분석 관점이 적용된다
- [x] 프롬프트에 투자 추천·비추천 표현이 포함되지 않는다
- [x] 개인화 적용 여부가 응답 메타데이터에 포함된다 (`is_personalized: true/false`)

## 구현 내용

### 프로필 → 컨텍스트 변환
`domain/service/context_builder_service.py`:
- `UserProfile` 수신 시 `[사용자 투자 성향]` 블록을 컨텍스트 상단에 추가
- 투자스타일, 위험허용도, 관심섹터, 분석선호, 관심키워드 포함

### 개인화 프롬프트 템플릿
`adapter/outbound/external/langchain_qa_adapter.py`:
- `_SYSTEM_PROMPT`에 "투자 성향에 맞춰 분석 관점을 조정하라" 지시 포함
- `[사용자 투자 성향]` 마커 감지 → `is_personalized=True` 자동 설정

### 응답 DTO
- `AnalysisAnswer.is_personalized: bool`
- `AnalysisAnswerResponse.is_personalized: bool = False`

### 빈 프로필 fallback
- `MockUserProfileRepository.get_by_account_id()` → `None` 반환 시
- `context_builder.build()` — 프로필 블록 없이 관심종목만 포함
- `is_personalized=False` 반환

## 구현 파일

| 파일 | 역할 |
|------|------|
| `domain/service/context_builder_service.py` | 프로필 → 프롬프트 컨텍스트 변환 |
| `adapter/outbound/external/langchain_qa_adapter.py` | 개인화 마커 감지 + LLM 호출 |
| `domain/entity/analysis_answer.py` | `is_personalized` 필드 |
| `application/response/analysis_response.py` | `is_personalized` DTO 필드 |

## To-do

- [x] 사용자 프로필 → 프롬프트 컨텍스트 변환 함수 구현 (`context_builder_service.py`)
- [x] 기존 `market_analysis` 프롬프트 템플릿에 개인화 섹션 추가
- [x] `is_personalized` 필드를 응답 DTO에 추가
- [x] 빈 프로필 사용자 대상 기본 프롬프트 유지 확인
