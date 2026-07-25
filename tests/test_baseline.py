from pathlib import Path

import pytest

from research_audit_kit.exceptions import BaselineExistsError
from research_audit_kit.integrity.baseline import freeze_baseline


def test_baseline_is_portable(clean_repo, policy, tmp_path):
    target = tmp_path / "baseline.csv"
    freeze_baseline(clean_repo, policy, target)
    assert str(clean_repo) not in target.read_text()


def test_baseline_companion_exists(clean_repo, policy, tmp_path):
    target = tmp_path / "baseline.csv"
    result = freeze_baseline(clean_repo, policy, target)
    assert target.with_name("baseline.csv.sha256").exists()
    assert len(result["baseline_sha256"]) == 64


def test_baseline_overwrite_protected(clean_repo, policy, tmp_path):
    target = tmp_path / "baseline.csv"
    freeze_baseline(clean_repo, policy, target)
    with pytest.raises(BaselineExistsError):
        freeze_baseline(clean_repo, policy, target)


def test_baseline_force_records_overwrite(clean_repo, policy, tmp_path):
    target = tmp_path / "baseline.csv"
    freeze_baseline(clean_repo, policy, target)
    assert freeze_baseline(clean_repo, policy, target, force=True)["forced_overwrite"] is True
    assert ",true\n" in target.read_text()


def test_baseline_inside_root_excludes_itself(clean_repo, policy):
    target = clean_repo / "manifest.csv"
    freeze_baseline(clean_repo, policy, target)
    text = target.read_text()
    assert "manifest.csv,\n" not in text


def test_nested_baseline_excludes_self_and_companion(clean_repo, policy):
    target = clean_repo / "audit-output" / "baseline.csv"
    target.parent.mkdir()
    freeze_baseline(clean_repo, policy, target)
    text = target.read_text()
    assert "audit-output/baseline.csv" not in text
    assert "audit-output/baseline.csv.sha256" not in text
