from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from research_audit_kit.integrity.policy import IntegrityPolicy


@pytest.fixture
def policy() -> IntegrityPolicy:
    return IntegrityPolicy.from_dict(
        {
            "policy": {
                "id": "test-policy",
                "include_patterns": ["**/*.py", "**/*.csv", "**/*.md"],
                "exclude_patterns": ["out/**"],
                "volatile_patterns": ["**/.DS_Store", "**/*.tmp"],
                "required_files": ["README.md"],
                "unexpected_scientific_file_policy": "fail",
            }
        }
    )


@pytest.fixture
def clean_repo(tmp_path: Path) -> Path:
    source = Path(__file__).parent / "fixtures" / "clean_repo"
    target = tmp_path / "repository"
    shutil.copytree(source, target)
    return target


@pytest.fixture
def conditional_rows() -> list[dict[str, str]]:
    return [
        {"architecture": "compact", "optimizer": "adam", "momentum": "0.0", "depth": "3"},
        {"architecture": "compact", "optimizer": "sgd", "momentum": "0.8", "depth": "3"},
        {"architecture": "wide", "optimizer": "adam", "momentum": "0.0", "depth": "5"},
        {"architecture": "wide", "optimizer": "sgd", "momentum": "0.9", "depth": "5"},
    ]


@pytest.fixture
def conditional_schema() -> dict:
    return {
        "branches": {
            "adaptive": {"when": {"optimizer": ["adam"]}, "require": {"momentum": [0.0]}},
            "stochastic": {"when": {"optimizer": ["sgd"]}, "require": {"momentum": {"min": 0.5}}},
        }
    }

