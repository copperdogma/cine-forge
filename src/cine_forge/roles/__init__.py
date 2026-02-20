"""AI role runtime and definitions package."""

from .canon import CanonGate, CanonGateError, assert_director_can_override
from .communication import ConversationManager
from .runtime import RoleCatalog, RoleContext, RoleRuntimeError
from .suggestion import SuggestionManager

__all__ = [
    "CanonGate",
    "CanonGateError",
    "ConversationManager",
    "RoleCatalog",
    "RoleContext",
    "RoleRuntimeError",
    "SuggestionManager",
    "assert_director_can_override",
]
