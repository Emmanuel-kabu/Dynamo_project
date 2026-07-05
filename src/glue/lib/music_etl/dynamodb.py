"""DynamoDB serialization helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def to_dynamodb_value(value: Any) -> Any:
    """Convert Python values into boto3 DynamoDB-compatible values.

    boto3's high-level Table API accepts native Python types, but floats are not
    accepted because DynamoDB requires exact numeric representation.
    """

    if isinstance(value, float):
        return Decimal(str(round(value, 6)))
    if isinstance(value, dict):
        return {key: to_dynamodb_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_dynamodb_value(item) for item in value]
    return value


def remove_nulls(item: dict[str, Any]) -> dict[str, Any]:
    """Remove null attributes before writing to DynamoDB."""

    return {key: value for key, value in item.items() if value is not None}
