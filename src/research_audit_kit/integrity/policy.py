"""Policy loading and task-independent file classification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from ..exceptions import PolicyError
from ..io.yaml_io import read_yaml


def _matches(path: str, pattern: str) -> bool:
    normalized = path.replace("\\", "/")
    return fnmatch(normalized, pattern) or (
        pattern.startswith("**/") and fnmatch(normalized, pattern[3:])
    )


@dataclass(frozen=True)
class IntegrityPolicy:
    policy_id: str
    include_patterns: tuple[str, ...] = ("**/*",)
    exclude_patterns: tuple[str, ...] = ()
    volatile_patterns: tuple[str, ...] = ()
    required_files: tuple[str, ...] = ()
    warning_only_classes: tuple[str, ...] = ("volatile_metadata",)
    failure_classes: tuple[str, ...] = ("scientific_asset",)
    unexpected_scientific_file_policy: str = "fail"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "IntegrityPolicy":
        if not isinstance(value, dict):
            raise PolicyError("policy document must be a mapping")
        body = value.get("policy", value)
        if not isinstance(body, dict) or not body.get("id"):
            raise PolicyError("policy.id is required")
        unexpected = body.get("unexpected_scientific_file_policy", "fail")
        if unexpected not in {"fail", "warn", "ignore"}:
            raise PolicyError("unexpected_scientific_file_policy must be fail, warn, or ignore")
        return cls(
            policy_id=str(body["id"]),
            include_patterns=tuple(body.get("include_patterns", ["**/*"])),
            exclude_patterns=tuple(body.get("exclude_patterns", [])),
            volatile_patterns=tuple(body.get("volatile_patterns", [])),
            required_files=tuple(body.get("required_files", [])),
            warning_only_classes=tuple(body.get("warning_only_classes", ["volatile_metadata"])),
            failure_classes=tuple(body.get("failure_classes", ["scientific_asset"])),
            unexpected_scientific_file_policy=unexpected,
            metadata=dict(body.get("metadata", {})),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "IntegrityPolicy":
        return cls.from_dict(read_yaml(path))

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["id"] = value.pop("policy_id")
        for key in (
            "include_patterns",
            "exclude_patterns",
            "volatile_patterns",
            "required_files",
            "warning_only_classes",
            "failure_classes",
        ):
            value[key] = list(value[key])
        return {"policy": value}

    def classify(self, relative_path: str) -> tuple[str, str]:
        if any(_matches(relative_path, pattern) for pattern in self.volatile_patterns):
            return "volatile_metadata", "matched volatile pattern"
        if any(_matches(relative_path, pattern) for pattern in self.exclude_patterns):
            if "cache" in relative_path or "__pycache__" in relative_path:
                return "cache", "matched excluded cache pattern"
            if relative_path.endswith((".tmp", ".temp")):
                return "temporary_file", "matched excluded temporary pattern"
            return "generated_artifact", "matched exclude pattern"
        if any(_matches(relative_path, pattern) for pattern in self.include_patterns):
            return "scientific_asset", "matched include pattern"
        return "unclassified_file", "no policy pattern matched"
