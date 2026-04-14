# BL-BE-62: 백엔드 서버가 사용자 프로필을 조회한다

> **담당**: 최승호 | **단계**: 1단계 | **주차**: Week 1~2

## 배경

AI 맞춤 분석을 위해 사용자의 관심종목과 상호작용 이력을 저장하고 조회하는
`user_profile` 도메인이 필요하다. 헥사고날 구조 세팅은 김동녁 완료.

## Success Criteria

- `GET /users/{user_id}/profile` 엔드포인트가 인증된 사용자 프로필을 반환한다
- 응답에는 관심종목 목록, 최근 조회 종목, 클릭한 카드 이력이 포함된다
- 본인 프로필만 조회 가능하다 (다른 사용자 ID 요청 시 403 반환)
- 프로필이 없는 경우 빈 기본값을 반환한다 (404 아님)

## To-do

- [ ] `UserProfile` 엔티티 정의 (`domains/user_profile/domain/entity/user_profile.py`)
- [ ] `UserProfileORM` 모델 정의 (`domains/user_profile/infrastructure/orm/user_profile_orm.py`)
- [ ] `UserProfileRepository` 포트 + MySQL 어댑터 구현
- [ ] `GET /users/{user_id}/profile` 라우터 구현 (`adapter/inbound/api/user_profile_router.py`)
- [ ] `GetUserProfileUseCase` 구현
- [ ] `UserProfileResponse` DTO 정의
- [ ] `main.py`에 라우터 등록
