# BL-BE-64: market_analysis 체인이 사용자 프로필을 조회하여 맞춤 분석을 제공한다

> **담당**: 이승욱 | **단계**: 2단계 | **주차**: Week 2~3

## 배경

현재 `market_analysis` 체인은 모든 사용자에게 동일한 분석을 제공한다.
LangChain Tool로 `get_user_profile`을 추가하면 사용자 취향(관심 섹터, 투자 성향)을
반영한 맞춤형 분석이 가능하다.

## Success Criteria

- `get_user_profile(user_id)` LangChain Tool이 `user_profile` 도메인 API를 호출한다
- `market_analysis` 에이전트가 분석 전 해당 Tool을 실행하여 프로필 정보를 컨텍스트에 포함한다
- 프로필 조회 실패 시(미가입, 빈 프로필) 기본 분석으로 fallback된다
- Tool 호출 로그가 SSE `{"type": "log"}` 이벤트로 전달된다

## To-do

- [ ] `GetUserProfileTool` LangChain Tool 구현 (`domains/market_analysis/adapter/outbound/tools/get_user_profile_tool.py`)
- [ ] Tool이 `user_profile` REST API 또는 Repository를 내부 호출하도록 구현
- [ ] `market_analysis` 체인 에이전트에 Tool 바인딩
- [ ] 프로필 없는 경우 fallback 처리
- [ ] `aemit()` 로그 추가
