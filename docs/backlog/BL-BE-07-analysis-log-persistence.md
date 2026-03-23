# BL-BE-07

**Backlog Type**
Behavior Backlog

**Backlog Title**
시스템이 AI 분석 로그를 데이터베이스에 영속적으로 저장한다

**Status**
완료 (2026-03-23)

**배경**
기존 분석 로그(_analysis_log_registry)는 서버 메모리에만 저장되어 서버 재시작 시 모두 사라졌다.
사용자가 재로그인해도 이전 AI 분석 로그를 조회할 수 있도록 DB에 영속적으로 저장해야 한다.

**Success Criteria**
- 파이프라인 실행 후 생성된 분석 로그가 DB에 저장된다
- GET /pipeline/logs 가 DB에서 분석 로그를 조회하여 반환한다
- 서버 재시작 후에도 기존 분석 로그가 유지된다
- 로그는 최신순으로 반환되며 최대 50건을 반환한다

**Todo**
1. [x] AnalysisLogORM을 정의한다 (`infrastructure/orm/analysis_log_orm.py`)
2. [x] AnalysisLogRepositoryPort를 정의한다 (`application/usecase/analysis_log_repository_port.py`)
3. [x] AnalysisLogRepositoryImpl(DB)을 구현한다 (`adapter/outbound/persistence/analysis_log_repository_impl.py`)
4. [x] RunPipelineUseCase에서 분석 완료 시 AnalysisLogResponse를 생성하여 결과에 포함한다
5. [x] pipeline_router의 _analysis_log_registry(인메모리)를 DB 저장/조회로 교체한다
6. [x] main.py에 AnalysisLogORM import를 추가하여 서버 시작 시 테이블이 자동 생성되도록 한다

**DB 마이그레이션**

대상 테이블: `analysis_logs` (신규 생성)

테이블 스키마:
```sql
CREATE TABLE analysis_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    analyzed_at DATETIME    NOT NULL,
    symbol      VARCHAR(20) NOT NULL,
    name        VARCHAR(100) NOT NULL,
    summary     TEXT        NOT NULL,
    tags        JSON        NULL,
    sentiment   VARCHAR(20) NOT NULL,
    sentiment_score FLOAT   NOT NULL,
    confidence  FLOAT       NOT NULL
);
```

생성 방식: `main.py` 서버 기동 시 `Base.metadata.create_all(bind=engine)` 자동 실행
실행일: 2026-03-23
실행 결과: 성공

**변경된 파일**

신규 생성:
- `app/domains/pipeline/infrastructure/orm/analysis_log_orm.py`
- `app/domains/pipeline/application/usecase/analysis_log_repository_port.py`
- `app/domains/pipeline/adapter/outbound/persistence/analysis_log_repository_impl.py`

수정:
- `app/domains/pipeline/application/usecase/run_pipeline_usecase.py`
  - `execute()` 시그니처에 `account_id: Optional[int] = None` 추가
  - 분석 완료 시 `AnalysisLogResponse` 생성 및 `logs` 리스트 반환
- `app/domains/pipeline/adapter/inbound/api/pipeline_router.py`
  - `_analysis_log_registry` (인메모리 dict) 제거
  - `account_id` Cookie 추출 추가
  - `AnalysisLogRepositoryImpl(db).save_all()` 호출로 DB 저장
  - `GET /pipeline/logs` → DB 조회로 교체
- `main.py`
  - `AnalysisLogORM` import 추가 (`# noqa: F401`)
