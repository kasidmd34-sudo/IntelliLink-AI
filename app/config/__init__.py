"""
Configuration module for IntelliLink AI backend.
Provides cached access to runtime settings and environment parameters.
"""

from app.config.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]