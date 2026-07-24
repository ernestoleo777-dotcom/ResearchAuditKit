from research_audit_kit.integrity.baseline import freeze_baseline
from research_audit_kit.integrity.verification import verify_baseline, write_verification


def _freeze(clean_repo, policy, tmp_path):
    baseline = tmp_path / "baseline.csv"
    freeze_baseline(clean_repo, policy, baseline)
    return baseline


def test_clean_verification_passes(clean_repo, policy, tmp_path):
    assert verify_baseline(clean_repo, _freeze(clean_repo, policy, tmp_path))["gate_status"] == "PASS"


def test_scientific_change_fails(clean_repo, policy, tmp_path):
    baseline = _freeze(clean_repo, policy, tmp_path)
    (clean_repo / "analysis.py").write_text("changed = True\n")
    assert verify_baseline(clean_repo, baseline)["gate_status"] == "FAIL"


def test_missing_scientific_file_fails(clean_repo, policy, tmp_path):
    baseline = _freeze(clean_repo, policy, tmp_path)
    (clean_repo / "analysis.py").unlink()
    assert verify_baseline(clean_repo, baseline)["counts"]["MISSING"] == 1


def test_verification_outputs_machine_files(clean_repo, policy, tmp_path):
    result = verify_baseline(clean_repo, _freeze(clean_repo, policy, tmp_path))
    paths = write_verification(result, tmp_path / "verification")
    assert all(path.exists() for path in paths)

