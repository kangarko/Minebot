"""
Settings package for Minebot, providing configuration management utilities.

This package centralizes all settings functionality, including loading,
saving, and managing configuration files in a structured and efficient manner.
"""

from .json_wrapper import Localization, Settings

__all__: list[str] = ["Localization", "Settings"]
