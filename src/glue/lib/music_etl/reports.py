"""Validation report helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from music_etl.constants import QUALITY_PILLARS


@dataclass(frozen=True)
class CheckResult:
    """Machine-readable result for one data quality check."""

    pillar: str
    name: str
    status: str
    observed: int | float | str
    threshold: int | float | str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.pillar not in QUALITY_PILLARS:
            raise ValueError(f"Unknown quality pillar: {self.pillar}")
        if self.status not in {"PASS", "FAIL", "WARN"}:
            raise ValueError(f"Unsupported check status: {self.status}")


def count_check(
    *,
    pillar: str,
    name: str,
    observed: int | float,
    threshold: int | float = 0,
    fail_when: str = "gt",
    details: dict[str, Any] | None = None,
) -> CheckResult:
    """Build a count-based validation result.

    `fail_when` supports `gt`, `gte`, `lt`, and `lte`.
    """

    comparators = {
        "gt": observed > threshold,
        "gte": observed >= threshold,
        "lt": observed < threshold,
        "lte": observed <= threshold,
    }
    if fail_when not in comparators:
        raise ValueError(f"Unsupported comparator: {fail_when}")

    return CheckResult(
        pillar=pillar,
        name=name,
        status="FAIL" if comparators[fail_when] else "PASS",
        observed=observed,
        threshold=threshold,
        details=details or {},
    )


def pass_check(
    *,
    pillar: str,
    name: str,
    observed: int | float | str = 0,
    threshold: int | float | str = 0,
    details: dict[str, Any] | None = None,
) -> CheckResult:
    """Build an explicit passing validation result."""

    return CheckResult(
        pillar=pillar,
        name=name,
        status="PASS",
        observed=observed,
        threshold=threshold,
        details=details or {},
    )


def build_validation_report(
    *,
    execution_id: str,
    bucket: str,
    stream_key: str,
    row_counts: dict[str, int],
    checks: list[CheckResult],
) -> dict[str, Any]:
    """Create the canonical validation report payload."""

    failed = [check for check in checks if check.status == "FAIL"]
    return {
        "execution_id": execution_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "FAIL" if failed else "PASS",
        "source": {
            "bucket": bucket,
            "stream_key": stream_key,
        },
        "metrics": {
            dataset: {"row_count": row_count}
            for dataset, row_count in sorted(row_counts.items())
        },
        "checks": [asdict(check) for check in checks],
        "failed_checks": [asdict(check) for check in failed],
    }
