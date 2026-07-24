from research_audit_kit.validation.leakage import audit_split_leakage, file_overlap


DATA = [
    {"row_id": "a", "group": "g1", "time": "2025-01-01", "branch": "left"},
    {"row_id": "b", "group": "g1", "time": "2025-01-02", "branch": "right"},
    {"row_id": "c", "group": "g2", "time": "2025-01-03", "branch": "left"},
]


def test_clean_split_passes():
    manifest = [{"row_id": "a", "coordinate_id": "x", "role": "train"}, {"row_id": "c", "coordinate_id": "z", "role": "test"}]
    result = audit_split_leakage(DATA, manifest, id_column="row_id")
    assert result["status"] == "PASS"


def test_coordinate_overlap_fails():
    manifest = [{"row_id": "a", "coordinate_id": "x", "role": "train"}, {"row_id": "b", "coordinate_id": "x", "role": "test"}]
    result = audit_split_leakage(DATA, manifest, id_column="row_id")
    assert result["issues"]["coordinate_overlap"] == ["x"]


def test_group_and_temporal_leakage():
    manifest = [{"row_id": "b", "coordinate_id": "b", "role": "train"}, {"row_id": "a", "coordinate_id": "a", "role": "test"}]
    result = audit_split_leakage(DATA, manifest, id_column="row_id", group_column="group", time_column="time")
    assert result["issues"]["group_overlap"] == ["g1"]
    assert result["issues"]["temporal_leakage"] is True


def test_calibration_overlap():
    manifest = [{"row_id": "c", "coordinate_id": "c", "role": "calibration"}, {"row_id": "c", "coordinate_id": "c", "role": "test"}]
    result = audit_split_leakage(DATA, manifest, id_column="row_id")
    assert result["issues"]["calibration_test_overlap"] == ["c"]


def test_file_overlap():
    assert file_overlap(["a.csv", "b.csv"], ["b.csv", "c.csv"]) == ["b.csv"]

