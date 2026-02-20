"""AI role runtime and definitions package."""

from .canon import CanonGate, CanonGateError, assert_director_can_override
from .runtime import RoleCatalog, RoleContext, RoleRuntimeError

__all__ = [
    "CanonGate",
    "CanonGateError",
    "RoleCatalog",
    "RoleContext",
    "RoleRuntimeError",
    "assert_director_can_override",
]
