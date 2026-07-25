from pathlib import Path

import pytest

from research_audit_kit.exceptions import UnsupportedFormatError
from research_audit_kit.io.csv_io import read_csv_rows, write_csv_rows
from research_audit_kit.io.yaml_io import read_yaml


def test_empty_csv_rejected(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(UnsupportedFormatError):
        read_csv_rows(path)


def test_duplicate_csv_columns_rejected(tmp_path):
    path = tmp_path / "duplicate.csv"
    path.write_text("id,id\na,b\n")
    with pytest.raises(UnsupportedFormatError):
        read_csv_rows(path)


def test_csv_formula_injection_is_neutralized(tmp_path):
    path = tmp_path / "report.csv"
    write_csv_rows(path, [{"value": "=1+1"}, {"value": "-4.2"}, {"value": "@cmd"}], ["value"])
    text = path.read_text()
    assert "'=1+1" in text
    assert "-4.2" in text
    assert "'@cmd" in text


def test_yaml_safe_load_rejects_python_construction(tmp_path):
    path = tmp_path / "unsafe.yaml"
    path.write_text("!!python/object/apply:os.system ['echo unsafe']")
    with pytest.raises(Exception) as error:
        read_yaml(path)
    assert "ConstructorError" in type(error.value).__name__

