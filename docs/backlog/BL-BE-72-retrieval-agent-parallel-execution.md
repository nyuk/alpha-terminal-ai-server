# BL-BE-72 — Retrieval Agent 데이터 소스 병렬 실행

## 개요

Retrieval Agent가 `parsed_query.required_data`에 포함된 데이터 소스 핸들러(뉴스, YouTube, 종목 등)를
`asyncio.gather`로 동시에 실행하여 전체 소요 시간을 단일 소스 기준으로 줄인다.

---

## 배경

데이터 소스가 늘어남에 따라 순차 실행 시 뉴스 + YouTube + 종목 각각 수십 초씩 소요되어
Retrieval 단계 전체가 수 분에 달할 수 있다.
`asyncio.gather`로 병렬화하면 전체 소요 시간 ≈ max(단일 소스 시간) + 소규모 오버헤드로 줄어든다.

---

## Success Criteria

- `parsed_query.required_data`에 포함된 핸들러를 순차가 아닌 동시에 실행한다
- 전체 소요 시간 ≈ max(단일 소스 시간) + 오버헤드
- 결과는 `required_data` 명시 순서대로 `retrieval_data`에 병합된다
- 한 핸들러의 예외·타임아웃이 다른 핸들러 실행을 중단시키지 않는다 (부분 실패 허용)
- 소스당 최대 30초 타임아웃, 초과 시 해당 소스만 실패 메시지로 대체
- `[Retrieval][소스명]` prefix 로그로 병렬 환경에서도 소스별 추적 가능
- `SOURCE_REGISTRY` 인터페이스 변경 없이 병렬화 적용 — 새 소스 추가 시 추가 작업 불필요

---

## 설계

### 병렬화 구조

```python
# 코루틴 생성 (required_data 순서)
coroutines = [SOURCE_REGISTRY[key](keyword, query, company) for key in active_keys]

# asyncio.gather 병렬 실행 + 소스별 타임아웃
results = await asyncio.gather(
    *[_run_with_timeout(key, coro, HANDLER_TIMEOUT)
      for key, coro in zip(active_keys, coroutines)]
)
```

### _run_with_timeout

```python
async def _run_with_timeout(source_key, coro, timeout) -> str:
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return f"=== {source_key} 수집 타임아웃 ({timeout}s) ==="
    except Exception:
        return f"=== {source_key} 수집 실패 ==="
```

- `asyncio.gather`는 항상 완료 → 성공 소스 결과 보존
- 예외는 `_run_with_timeout` 내에서 흡수 → 전파 없음

### 결과 병합

```python
def _merge_results(keys_in_order, results) -> str:
    sections = [r for r in results if r]
    return "\n\n".join(sections) if sections else "수집된 데이터 없음"
```

- `required_data` 배열 순서 = `results` 배열 순서 → 일관성 유지

### 로그 구조

```
[Retrieval] ▶ 시작 | keyword=한화에어로스페이스
[Retrieval]   수집 소스: ['뉴스', 'YouTube 영상', '종목']
[Retrieval] ⚡ 3개 소스 병렬 실행 (timeout=30s)
[Retrieval][뉴스] ▶ ...
[Retrieval][YouTube] ▶ ...
[Retrieval][종목] 향후 구현 예정
[Retrieval] ⚡ 병렬 실행 완료 | 소요=18.3s   ← max(뉴스, YouTube) ≈ 단일 소스 시간
[Retrieval]   ✓ [뉴스] 3820자
[Retrieval]   ✓ [YouTube 영상] 1240자
[Retrieval]   ✓ [종목] 22자
[Retrieval] ◀ 완료 | 총 5082자
```

---

## To-Do

- [x] `SOURCE_REGISTRY` 핸들러를 `asyncio.gather`로 병렬화
- [x] `_run_with_timeout`: 소스별 30초 타임아웃 + 부분 실패 처리
- [x] `_merge_results`: `required_data` 순서 보장 병합 포맷터
- [x] `[Retrieval][소스명]` prefix 로그로 병렬 추적 가능하게 구성
- [x] `elapsed` 시간 측정 로그로 병렬화 효과 검증

---

## 관련 파일

| 파일 | 역할 |
|------|------|
| `adapter/outbound/agent/retrieval_node.py` | `asyncio.gather` 병렬화, `_run_with_timeout`, `_merge_results`, 진입점 |

---

## 구현 완료일

2026-04-15
