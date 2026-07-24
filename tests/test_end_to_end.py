from pathlib import Path

from research_audit_kit.integrity.baseline import freeze_baseline
from research_audit_kit.integrity.hashing import relative_file_set_hash
from research_audit_kit.integrity.inventory import build_inventory
from research_audit_kit.integrity.verification import verify_baseline


def test_end_to_end_integrity_workflow(clean_repo, policy, tmp_path):
    before = build_inventory(clean_repo, policy)
    baseline = tmp_path / "portable.csv"
    freeze_baseline(clean_repo, policy, baseline)
    result = verify_baseline(clean_repo, baseline)
    assert before
    assert result["gate_status"] == "PASS"


def test_audited_source_fixture_is_not_modified(clean_repo, policy, tmp_path):
    paths = [path.relative_to(clean_repo).as_posix() for path in clean_repo.rglob("*") if path.is_file()]
    before = relative_file_set_hash(clean_repo, paths)
    build_inventory(clean_repo, policy)
    after = relative_file_set_hash(clean_repo, paths)
    assert before == after


def test_repository_contains_no_serialized_models():
    root = Path(__file__).parents[1]
    short_suffix = "*." + "pkl"
    long_suffix = "*." + "pickle"
    assert not list(root.rglob(short_suffix))
    assert not list(root.rglob(long_suffix))


def test_clean_room_documents_have_no_absolute_home_paths():
    root = Path(__file__).parents[1]
    texts = "\n".join(path.read_text(errors="ignore") for path in root.rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".yaml", ".csv", ".toml"})
    home_prefix = "/" + "Users" + "/"
    assert home_prefix not in texts
