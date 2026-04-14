# BL-BE-68: 백엔드 서버가 NORMAL/ADMIN 역할 기반 권한을 관리한다

> **담당**: 김동녁 | **단계**: 관리자 기능 | **주차**: Week 2~3

## 배경

6차 회의 결정: 서비스 성장 지표 모니터링을 위한 관리자 기능이 필요하다.
가입 시 관리자 코드 입력 시 ADMIN 권한이 부여되며, 일반 사용자는 NORMAL이다.
ADMIN은 대시보드(Retention, Dwell Time, CTR) 조회 권한을 갖는다.

## Success Criteria

- `users` 테이블에 `role` 컬럼이 추가된다 (`NORMAL` | `ADMIN`, 기본값 `NORMAL`)
- 회원가입 API에서 관리자 코드(`ADMIN_SECRET_CODE` 환경변수) 입력 시 `ADMIN` 역할로 저장된다
- `GET /admin/dashboard/stats` 엔드포인트는 `ADMIN` 역할만 접근 가능하다 (NORMAL 시 403)
- 관리자 대시보드 통계 API가 아래 지표를 반환한다:
  - Retention D-1 ~ D-14: 가입 후 N일 뒤 재방문 비율
  - Dwell Time: 사용자 평균 체류 시간
  - CTR: 카드 클릭률 (클릭 수 / 노출 수)

## To-do

- [ ] `users` 테이블 `role` 컬럼 추가 마이그레이션
- [ ] `UserRole` Enum 정의 (`NORMAL`, `ADMIN`)
- [ ] 회원가입 UseCase에 관리자 코드 검증 로직 추가
- [ ] `ADMIN_SECRET_CODE` 환경변수 추가 (`infrastructure/config/settings.py`)
- [ ] `require_admin` 의존성 함수 구현 (ADMIN 아니면 403)
- [ ] `GET /admin/dashboard/stats` 라우터 + UseCase 구현
  - Retention 집계 쿼리
  - Dwell Time 집계 쿼리
  - CTR 집계 쿼리
- [ ] `AdminDashboardStatsResponse` DTO 정의
