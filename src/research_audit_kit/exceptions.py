"""Package-specific exceptions."""


class AuditError(Exception):
    """Base class for controlled audit failures."""


class PolicyError(AuditError):
    """Raised when a policy is missing required semantics."""


class UnsafePathError(AuditError):
    """Raised when a path escapes its declared root."""


class BaselineExistsError(AuditError):
    """Raised when a baseline would be silently overwritten."""


class InputValidationError(AuditError):
    """Raised for invalid user data or configuration."""

