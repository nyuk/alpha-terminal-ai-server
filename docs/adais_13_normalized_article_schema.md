# normalized_article 스키마 정의

작성자: 이승욱 (R2 정규화기)
작성일: 2026-03-16
관련 백로그: ADAIS-13

---

## 목적

`normalized_article`은 R2 정규화기의 출력이자 R3 AI 처리기의 단일 입력이다.

`raw_article`의 원문 데이터를 표준 포맷으로 정제하여 저장한다.

---

## 필드 목록

| 필드 | 타입 | Nullable | 설명 |
|---|---|---|---|
| `id` | UUID | NO | 내부 식별자 |
| `raw_article_id` | UUID | NO | 원본 raw_article 참조 (역추적용) |
| `stock_symbol` | str | NO | 표준 종목 코드 (예: `005930`) |
| `source_type` | enum | NO | `DISCLOSURE` \| `NEWS` \| `REPORT` |
| `source_name` | str | NO | `DART` 고정 또는 뉴스 소스명 |
| `title` | str | NO | 정제된 제목 |
| `body` | str | NO | 정제된 본문 |
| `category` | enum | NO | 카테고리 (아래 정의 참고) |
| `published_at` | datetime | NO | 정규화된 발행 시각 (KST) |
| `lang` | str | NO | `ko` \| `en` |
| `content_quality` | enum | NO | `VALID` \| `INVALID` |
| `normalized_at` | datetime | NO | 정규화 처리 시각 |
| `normalizer_version` | str | NO | 예: `normalizer-v1.0.0` |

---

## category 기준

MVP 단계에서는 아래 5개 값만 사용한다.

| 값 | 대상 |
|---|---|
| `DISCLOSURE_CAPITAL` | 유상증자, 무상증자 등 자본 관련 공시 |
| `DISCLOSURE_EARNINGS` | 실적 발표, 영업실적 공시 |
| `DISCLOSURE_OTHER` | 기타 DART 공시 |
| `NEWS` | 뉴스 전체 (MVP에서 세분화 없음) |
| `UNKNOWN` | 분류 불가 |

### 분류 규칙

- `source_type`이 `NEWS`이면 → `NEWS` 고정
- `source_type`이 `REPORT`이면 → `DISCLOSURE_OTHER` (MVP에서 세분화 없음)
- `source_type`이 `DISCLOSURE`이면 → 제목 키워드 기반 분류
  - 제목에 `증자`, `전환사채`, `신주` 포함 → `DISCLOSURE_CAPITAL`
  - 제목에 `실적`, `영업이익`, `매출` 포함 → `DISCLOSURE_EARNINGS`
  - 그 외 → `DISCLOSURE_OTHER`
- 분류 불가 시 → `UNKNOWN`

---

## source_name 규칙

| source_type | source_name |
|---|---|
| `DART` | `"DART"` 고정 |
| `NEWS` | 수집기가 제공한 소스명 그대로 사용 (예: `"연합뉴스"`) |

---

## published_at 정규화 기준

- **기준 timezone**: KST (UTC+9) 통일
- **포맷**: ISO 8601 — `2026-03-15T08:30:00+09:00`
- timezone 정보 없는 경우 → KST로 간주하여 `+09:00` 추가
- raw_article의 `published_at` 값을 기준으로 변환

---

## content_quality 기준

| 값 | 조건 |
|---|---|
| `VALID` | 본문 존재 + 10자 이상 + 특수문자만으로 구성되지 않음 |
| `INVALID` | 본문 없음 또는 10자 미만 또는 의미없는 내용 |

`content_quality`가 `INVALID`인 경우에도 저장은 진행한다.
R3는 `VALID`인 항목만 처리한다.

---

## raw_article → normalized_article 필드 매핑

| normalized_article | raw_article |
|---|---|
| `raw_article_id` | `id` |
| `stock_symbol` | `symbol` |
| `source_type` | `source_type` (그대로 전달: `DISCLOSURE` \| `NEWS` \| `REPORT`) |
| `source_name` | `source_name` |
| `title` | `title` (정제 후) |
| `body` | `body_text` (정제 후) |
| `published_at` | `published_at` (KST 정규화) |
| `lang` | `lang` |

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|---|---|---|
| 2026-03-16 | 이승욱 | 최초 작성 |
| 2026-03-16 | 이승욱 | 공용 스키마 확정 반영 (fixture 필드명 확정) |
| 2026-03-16 | 이승욱 | source_type enum 확정 반영 (DISCLOSURE\|NEWS\|REPORT), 변환 로직 제거 |
