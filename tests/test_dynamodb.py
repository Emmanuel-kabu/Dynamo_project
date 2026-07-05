from decimal import Decimal

from music_etl.dynamodb import remove_nulls, to_dynamodb_value


def test_to_dynamodb_value_converts_floats_to_decimal():
    item = to_dynamodb_value({"ratio": 1.23456789, "nested": [2.5]})

    assert item["ratio"] == Decimal("1.234568")
    assert item["nested"] == [Decimal("2.5")]


def test_remove_nulls_keeps_falsey_non_null_values():
    item = remove_nulls({"none": None, "zero": 0, "false": False, "empty": ""})

    assert item == {"zero": 0, "false": False, "empty": ""}
