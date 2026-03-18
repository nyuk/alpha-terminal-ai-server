# Git Push 충돌 해결 기록

작성자: 이승욱
작성일: 2026-03-17

---

## 발생 상황

`feature/r2-normalizer` 브랜치를 origin(fork)에 푸시할 때 non-fast-forward 오류 발생.

```
! [rejected] feature/r2-normalizer -> feature/r2-normalizer (non-fast-forward)
Updates were rejected because the tip of your current branch is behind its remote counterpart.
```

---

## 원인

| 구분 | 상태 |
|------|------|
| 로컬 `feature/r2-normalizer` | `feature/r2-normalizer-new`에서 이름 변경 + upstream/main rebase 완료 |
| origin `feature/r2-normalizer` | PR #3에서 사용했던 구버전 브랜치 (revert 이후에도 remote에 잔존) |

브랜치 이름은 같지만 커밋 이력이 달라서 fast-forward 불가.

---

## 해결 방법

`--force-with-lease` 옵션으로 강제 푸시.

```bash
git push origin feature/r2-normalizer --force-with-lease
```

### `--force` vs `--force-with-lease` 차이

| 옵션 | 설명 |
|------|------|
| `--force` | 원격 상태 무관하게 무조건 덮어씀 (위험) |
| `--force-with-lease` | 로컬이 마지막으로 fetch한 상태와 원격이 일치할 때만 강제 푸시 (안전) |

> 다른 사람이 같은 브랜치에 push한 경우 `--force-with-lease`도 거부됨 → 협업 시 안전한 선택.

---

## 주의사항

- 이 브랜치는 **개인 fork**의 feature 브랜치이므로 강제 푸시가 안전함
- `main` 또는 팀 공유 브랜치에는 절대 force push 금지
- 브랜치 이름 변경 시 remote에 동일 이름의 구버전이 있는지 사전 확인 필요

---

## 관련 이력

- PR #3: https://github.com/EDDI-RobotAcademy/alpha-desk-ai-server/pull/3 (revert됨)
- PR #13: https://github.com/EDDI-RobotAcademy/alpha-desk-ai-server/pull/13 (현재)
