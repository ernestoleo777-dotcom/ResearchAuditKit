import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.validation.split_manifest import build_split_manifest, dataset_hash


ROWS = [
    {"row_id": "r1", "architecture": "compact", "group": "g1"},
    {"row_id": "r2", "architecture": "wide", "group": "g2"},
]


def test_dataset_hash_deterministic():
    assert dataset_hash(ROWS) == dataset_hash(ROWS)


def test_split_manifest_fields():
    result = build_split_manifest(ROWS, [{"row_id": "r1", "role": "train"}, {"row_id": "r2", "role": "test"}], id_column="row_id", coordinate_columns=["architecture"], split_family="holdout", fold_id="f0", seed=9, group_column="group")
    assert result[0]["dataset_hash"] == result[1]["dataset_hash"]
    assert all(len(row["coordinate_id"]) == 16 for row in result)


def test_unknown_assignment_fails():
    with pytest.raises(InputValidationError):
        build_split_manifest(ROWS, [{"row_id": "missing", "role": "test"}], id_column="row_id", coordinate_columns=["architecture"], split_family="holdout", fold_id="f0", seed=9)


def test_duplicate_ids_fail():
    with pytest.raises(InputValidationError):
        build_split_manifest([ROWS[0], ROWS[0]], [], id_column="row_id", coordinate_columns=["architecture"], split_family="holdout", fold_id="f0", seed=9)

