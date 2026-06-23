"""Persistent storage for research outputs."""

from .database import Vault
from .repository import VaultRepository

__all__ = ["Vault", "VaultRepository"]
