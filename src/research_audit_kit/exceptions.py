# SPDX-License-Identifier: Apache-2.0
"""Package-specific exceptions."""


class AuditError(Exception):
    """Base class for controlled audit failures."""


class ConfigurationError(AuditError):
    """Raised when configuration is invalid or incomplete."""


class PolicyError(ConfigurationError):
    """Raised when a policy is missing required semantics."""


class RequiredFilePathError(PolicyError):
    """Raised when one policy.required_files entry is unsafe."""

    def __init__(self, *, index: int, reason_code: str):
        self.index = index
        self.reason_code = reason_code
        self.error_code = f"POLICY_REQUIRED_FILE_PATH_{reason_code}"
        super().__init__(
            f"{self.error_code}: policy.required_files[{index}]: invalid non-confined path"
        )


class UnsafePathError(AuditError):
    """Raised when a path escapes its declared root."""


class BaselineExistsError(AuditError):
    """Raised when a baseline would be silently overwritten."""


class InputValidationError(AuditError):
    """Raised for invalid user data or configuration."""


class IntegrityFailure(AuditError):
    """Raised when governed bytes change during an integrity operation."""


class UnsupportedFormatError(AuditError):
    """Raised when an input format cannot be safely interpreted."""


class InternalInvariantError(AuditError):
    """Raised when an internal contract is violated."""
