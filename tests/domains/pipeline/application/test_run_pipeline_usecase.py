from types import SimpleNamespace

from app.domains.pipeline.application.usecase.run_pipeline_usecase import _choose_representative_article


def test_choose_representative_article_prefers_real_dart_filing_url():
    financial_report = SimpleNamespace(
        source_type="REPORT",
        url="https://dart.fss.or.kr/",
    )
    disclosure = SimpleNamespace(
        source_type="DISCLOSURE",
        url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20260430001606",
    )

    selected = _choose_representative_article([financial_report, disclosure])

    assert selected is disclosure


def test_choose_representative_article_falls_back_to_first_article():
    financial_report = SimpleNamespace(
        source_type="REPORT",
        url="https://dart.fss.or.kr/",
    )

    selected = _choose_representative_article([financial_report])

    assert selected is financial_report
