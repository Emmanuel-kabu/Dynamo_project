import pytest
from music_etl.reports import CheckResult, build_validation_report, count_check, pass_check


def test_count_check_fails_when_observed_exceeds_threshold():
    result = count_check(
        pillar="completeness",
        name="missing_required_columns",
        observed=1,
        threshold=0,
    )

    assert result.status == "FAIL"
    assert result.pillar == "completeness"


def test_pass_check_builds_explicit_pass():
    result = pass_check(pillar="accuracy", name="reconciliation")

    assert result.status == "PASS"
    assert result.name == "reconciliation"


def test_unknown_quality_pillar_is_rejected():
    with pytest.raises(ValueError, match="Unknown quality pillar"):
        CheckResult(
            pillar="freshness",
            name="not_a_supported_project_pillar",
            status="PASS",
            observed=0,
            threshold=0,
        )


def test_validation_report_collects_failed_checks():
    checks = [
        pass_check(pillar="completeness", name="columns_present"),
        count_check(pillar="consistency", name="missing_song_refs", observed=2, threshold=0),
    ]

    report = build_validation_report(
        execution_id="exec-1",
        bucket="bucket",
        stream_key="raw/streams/2024/06/25/streams.csv",
        row_counts={"streams": 3, "songs": 3, "users": 3},
        checks=checks,
    )

    assert report["status"] == "FAIL"
    assert report["metrics"]["streams"]["row_count"] == 3
    assert [check["name"] for check in report["failed_checks"]] == ["missing_song_refs"]
