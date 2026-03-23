# BL-BE-08

**Backlog Type**
Bug Fix Backlog

**Backlog Title**
시스템이 AI 분석 로그와 요약을 사용자별로 분리하여 표시한다

**Status**
완료 (2026-03-23)

**배경 / 버그 설명**
BL-BE-07에서 분석 로그를 DB에 저장하도록 구현했으나,
analysis_logs 테이블에 account_id 컬럼이 없어 모든 사용자의 로그가 공유된다.
또한 _summary_registry가 서버 전역 dict이므로 다른 사용자의 요약이 노출된다.

재현 시나리오:
1. btdlm 계정으로 로그인 후 한화에어로스페이스(012450) 등록 및 AI 분석 실행
2. 로그아웃 후 lubh 계정으로 로그인
3. 대시보드에서 btdlm의 AI 분석 로그와 요약이 표시됨 (버그)

**Root Cause**
1. analysis_logs 테이블에 account_id 컬럼 부재 → 전체 사용자 로그 반환
2. _summary_registry가 dict[str, StockSummaryResponse] (전역) → 전체 사용자 요약 공유

**Success Criteria**
- GET /pipeline/logs 는 로그인한 사용자의 분석 로그만 반환한다
- GET /pipeline/summaries 는 로그인한 사용자의 요약만 반환한다
- 로그아웃 후 다른 계정으로 로그인하면 이전 사용자의 로그/요약이 보이지 않는다

**Todo**
1. [x] analysis_logs 테이블에 account_id 컬럼 추가 (DB 마이그레이션)
2. [x] AnalysisLogORM에 account_id 필드 추가
3. [x] AnalysisLogResponse에 account_id 필드 추가 (Optional[int])
4. [x] AnalysisLogRepositoryPort.save_all(), find_recent()에 account_id 파라미터 추가
5. [x] AnalysisLogRepositoryImpl — save 시 account_id 저장, find_recent 시 account_id 필터링
6. [x] RunPipelineUseCase — AnalysisLogResponse 생성 시 account_id 포함
7. [x] pipeline_router — save_all, find_recent 호출 시 account_id 전달
8. [x] _summary_registry를 dict[Optional[int], dict[str, StockSummaryResponse]]로 변경하여 사용자별 분리

**DB 마이그레이션**

대상 테이블: `analysis_logs`

```sql
ALTER TABLE analysis_logs ADD COLUMN account_id INT NULL;
```

실행일: 2026-03-23
실행 결과: 성공

**변경된 파일**
- `app/domains/pipeline/infrastructure/orm/analysis_log_orm.py`
- `app/domains/pipeline/application/response/analysis_log_response.py`
- `app/domains/pipeline/application/usecase/analysis_log_repository_port.py`
- `app/domains/pipeline/adapter/outbound/persistence/analysis_log_repository_impl.py`
- `app/domains/pipeline/application/usecase/run_pipeline_usecase.py`
- `app/domains/pipeline/adapter/inbound/api/pipeline_router.py`
