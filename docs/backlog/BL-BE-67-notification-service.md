# BL-BE-67: 백엔드 서버가 사용자 알림을 저장하고 조회한다

> **담당**: 김민식 | **단계**: 3단계 | **주차**: Week 3~4

## 배경

능동형 추천 에이전트(BL-BE-66)가 생성한 알림을 저장하고,
FE가 읽지 않은 알림 수와 목록을 조회할 수 있는 API가 필요하다.

## Success Criteria

- `POST/notifications` — notifications 테이블에 알림이 저장된다 (user_id, title, body, is_read, created_at)
- `GET /notifications` — 로그인 사용자의 알림 목록을 최신순으로 반환한다
- `PATCH /notifications/{id}/read` — 특정 알림을 읽음 처리한다
- `PATCH /notifications/read-all` — 전체 알림을 읽음 처리한다
- `GET /notifications/unread-count` — 읽지 않은 알림 수를 반환한다

## To-do

- [ ] `Notification` 엔티티 + `NotificationORM` 모델 정의
- [ ] `notifications` 테이블 마이그레이션
- [ ] `NotificationRepository` MySQL 어댑터 구현
- [ ] `GET /notifications` 라우터 구현
- [ ] `PATCH /notifications/{id}/read` 라우터 구현
- [ ] `PATCH /notifications/read-all` 라우터 구현
- [ ] `GET /notifications/unread-count` 라우터 구현
- [ ] `main.py`에 라우터 등록
