from research_audit_kit.integrity.hashing import (
    manifest_self_exclusions,
    sha256_bytes,
    sha256_file,
    stable_object_hash,
)


def test_hash_deterministic():
    assert sha256_bytes(b"evidence") == sha256_bytes(b"evidence")


def test_file_hash_changes(tmp_path):
    path = tmp_path / "asset.txt"
    path.write_text("before")
    before = sha256_file(path)
    path.write_text("after")
    assert sha256_file(path) != before


def test_stable_object_hash_ignores_dict_order():
    assert stable_object_hash({"a": 1, "b": 2}) == stable_object_hash({"b": 2, "a": 1})


def test_manifest_self_exclusion():
    excluded = manifest_self_exclusions("manifest.csv")
    assert {"manifest.csv", "manifest.csv.sha256", "manifest.csv.tmp"} <= excluded

