from types import SimpleNamespace

from app.domains.pipeline.application.usecase.run_pipeline_usecase import _has_non_empty_summary


def test_has_non_empty_summary_rejects_blank_analysis_result():
    analysis = SimpleNamespace(summary="  ")

    assert _has_non_empty_summary((analysis, "NEWS", None, None, None)) is False


def test_has_non_empty_summary_accepts_populated_analysis_result():
    analysis = SimpleNamespace(summary="요약")

    assert _has_non_empty_summary((analysis, "NEWS", None, None, None)) is True
