from research_audit_kit.validation.fold_local import audit_fold_local_metadata


def test_missing_metadata_unverified():
    assert audit_fold_local_metadata([], ["a"], ["b"])["status"] == "UNVERIFIED_FROM_METADATA"


def test_fold_local_passes():
    records = [{"component": "scaler", "fitted_on": ["a", "b"]}, {"component": "calibrator", "fitted_on": ["a"]}]
    assert audit_fold_local_metadata(records, ["a", "b"], ["c"])["status"] == "PASS"


def test_test_fit_fails():
    records = [{"component": "feature_selector", "fitted_on": ["test-row"]}]
    assert audit_fold_local_metadata(records, ["train-row"], ["test-row"])["status"] == "FAIL"

