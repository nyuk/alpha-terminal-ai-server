# stock_normalizer 도메인 뼈대 생성

작성자: 이승욱 (R2 정규화기)
작성일: 2026-03-18
관련 백로그: ADAIS-14

---

## Backlog Title

stock_normalizer 도메인 뼈대 생성 [ADAIS-14]

---

## Success Criteria

- stock_normalizer 기본 구조가 생성되어 있다
- 현재 프로젝트 패턴과 일치한다
- 이후 구현 파일 추가가 가능하다

---

## Todo

- [x] app/domains/stock_normalizer 생성
- [x] domain 디렉토리 생성
- [x] application 디렉토리 생성
- [x] adapter 디렉토리 생성
- [x] infrastructure 디렉토리 생성
- [x] `__init__.py` 파일 추가

---

## 디렉토리 구조

```
app/domains/stock_normalizer/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entity/
│   │   ├── __init__.py
│   │   ├── raw_article.py
│   │   ├── normalized_article.py
│   │   └── normalized_disclosure.py
│   ├── value_object/
│   │   └── __init__.py
│   └── service/
│       ├── __init__.py
│       └── article_normalizer_service.py
├── application/
│   ├── __init__.py
│   ├── usecase/
│   │   ├── __init__.py
│   │   ├── normalize_raw_article_usecase.py
│   │   ├── normalized_article_repository_port.py
│   │   ├── normalize_disclosure_usecase.py
│   │   └── normalized_disclosure_repository_port.py
│   ├── request/
│   │   ├── __init__.py
│   │   ├── normalize_raw_article_request.py
│   │   └── normalize_disclosure_request.py
│   └── response/
│       ├── __init__.py
│       ├── normalize_raw_article_response.py
│       └── normalize_disclosure_response.py
├── adapter/
│   ├── __init__.py
│   ├── inbound/
│   │   ├── __init__.py
│   │   └── api/
│   │       ├── __init__.py
│   │       └── normalizer_router.py
│   └── outbound/
│       ├── __init__.py
│       └── persistence/
│           ├── __init__.py
│           ├── normalized_article_repository_impl.py
│           └── normalized_disclosure_repository_impl.py
└── infrastructure/
    ├── __init__.py
    ├── orm/
    │   └── __init__.py
    └── mapper/
        └── __init__.py
```

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-18 | 이승욱 | 최초 작성 (구현 완료 후 문서화) |
