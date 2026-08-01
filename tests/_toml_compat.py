# SPDX-License-Identifier: Apache-2.0
"""Test-only TOML parser compatibility for Python 3.10 and newer."""

from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError as exc:
    if exc.name != "tomllib":
        raise
    import tomli as tomllib

    TOML_BACKEND = "tomli"
else:
    TOML_BACKEND = "tomllib"
