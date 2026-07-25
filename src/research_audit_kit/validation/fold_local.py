"""Fold-local preprocessing metadata contracts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from ..constants import STATUS_FAIL, STATUS_PASS

COMPONENTS = {"scaler", "feature_selector", "hyperparameter_tuner", "calibrator"}


def audit_fold_local_metadata(
    records: Iterable[Mapping[str, Any]], train_ids: Iterable[str], test_ids: Iterable[str]
) -> dict[str, Any]:
    materialized = list(records)
    if not materialized:
        return {"status": "UNVERIFIED_FROM_METADATA", "components": {}}
    train = {str(value) for value in train_ids}
    test = {str(value) for value in test_ids}
    results: dict[str, str] = {}
    for record in materialized:
        component = str(record.get("component", ""))
        if component not in COMPONENTS:
            continue
        fitted = {str(value) for value in record.get("fitted_on", [])}
        if not fitted:
            results[component] = "UNVERIFIED_FROM_METADATA"
        elif fitted & test:
            results[component] = STATUS_FAIL
        elif fitted <= train:
            results[component] = STATUS_PASS
        else:
            results[component] = "UNVERIFIED_FROM_METADATA"
    status = STATUS_FAIL if STATUS_FAIL in results.values() else (
        "UNVERIFIED_FROM_METADATA" if not results or "UNVERIFIED_FROM_METADATA" in results.values() else STATUS_PASS
    )
    return {"status": status, "components": results}
