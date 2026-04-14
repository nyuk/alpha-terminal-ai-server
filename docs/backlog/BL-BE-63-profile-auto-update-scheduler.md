# BL-BE-63: 백엔드 서버가 자정마다 사용자 프로필을 자동 업데이트한다

> **담당**: 이하연 | **단계**: 1단계 | **주차**: Week 1~2

## 배경

사용자의 관심종목 클릭·조회 데이터를 매일 자정 집계하여 `user_profile`을 갱신한다.
AI 맞춤 분석 품질을 높이기 위한 데이터 축적 배치 작업이다.

## Success Criteria

- 매일 자정(00:00 KST) APScheduler가 전체 사용자 프로필을 자동 업데이트한다
- 당일 클릭·조회 이력을 집계하여 관심도 점수(interest_score)를 갱신한다
- 배치 실행 시작/완료/오류 로그가 남는다
- 배치 실패 시 다음 자정 실행에 영향을 주지 않는다

## To-do

- [ ] APScheduler 의존성 추가 (`requirements.txt`)
- [ ] `ProfileUpdateScheduler` 구현 (`domains/user_profile/adapter/outbound/scheduler/profile_update_scheduler.py`)
- [ ] 사용자 클릭 이력 집계 쿼리 구현
- [ ] `interest_score` 계산 로직 구현 (클릭 수, 조회 시간 가중치)
- [ ] `main.py`에 스케줄러 시작/종료 lifespan 등록
- [ ] 배치 실행 로그 테스트
