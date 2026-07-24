from research_audit_kit.integrity.baseline import freeze_baseline
from research_audit_kit.integrity.verification import verify_baseline
from research_audit_kit.integrity.volatility import is_volatile, volatile_gate_effect


def test_volatile_change_warns(tmp_path, policy):
    (tmp_path / "README.md").write_text("repo")
    (tmp_path / ".DS_Store").write_text("one")
    baseline = tmp_path.parent / "volatile-baseline.csv"
    freeze_baseline(tmp_path, policy, baseline)
    (tmp_path / ".DS_Store").write_text("two")
    result = verify_baseline(tmp_path, baseline)
    assert result["gate_status"] == "PASS_WITH_WARNINGS"


def test_volatile_helpers(policy):
    assert is_volatile(".DS_Store", policy)
    assert volatile_gate_effect(True) == "VOLATILE_WARNING"

