# BL-BE-64: market_analysis 체인이 사용자 프로필을 조회하여 맞춤 분석을 제공한다

> **담당**: 이승욱 | **단계**: 2단계 | **주차**: Week 2~3 | **상태**: ✅ 완료

## 배경

현재 `market_analysis` 체인은 모든 사용자에게 동일한 분석을 제공한다.
LangChain Tool로 `get_user_profile`을 추가하면 사용자 취향(관심 섹터, 투자 성향)을
반영한 맞춤형 분석이 가능하다.
`user_profile` DB 구현(BL-BE-62) 완료 전까지 `MockUserProfileRepository`를 사용한다.

## Success Criteria

- [x] `get_user_profile(user_id)` LangChain Tool이 `user_profile` 도메인 Repository를 호출한다
- [x] `market_analysis` UseCase가 프로필 정보를 컨텍스트에 포함하여 맞춤 분석을 제공한다
- [x] 프로필 조회 실패 시(미가입, 빈 프로필) 기본 분석으로 fallback된다
- [x] Tool 호출 로그가 aemit() 이벤트로 기록된다

## 구현 파일

| 파일 | 역할 |
|------|------|
| `adapter/outbound/tool/get_user_profile_tool.py` | LangChain `@tool` — MockRepo 호출 |
| `application/usecase/analyze_market_query_usecase.py` | UseCase — 프로필 조회 후 context_builder 에 전달 |
| `application/usecase/user_profile_repository_port.py` | Port — Repository 추상화 |
| `adapter/inbound/api/market_analysis_router.py` | `/ask` 엔드포인트 — aemit 로그 + MockRepo 주입 |
| `app/infrastructure/log_context.py` | 공유 aemit 유틸리티 (신규) |

## Mock 데이터 (DB 구현 전)

`MockUserProfileRepository` (3건: account_id=1,2,3) 사용.
BL-BE-62 완료 후 `UserProfileRepositoryImpl`로 교체 — UseCase·Tool 코드 수정 불필요.

## To-do

- [x] `GetUserProfileTool` LangChain Tool 구현
- [x] Tool이 `user_profile` Repository를 내부 호출하도록 구현
- [x] `market_analysis` UseCase에 프로필 컨텍스트 반영
- [x] 프로필 없는 경우 fallback 처리
- [x] `aemit()` 로그 추가 (`market_analysis_router.py` `/ask` 엔드포인트)
