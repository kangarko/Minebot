"""
Debug package for Minebot, providing logging utilities and debugging tools.

This package centralizes all debugging functionality including the setup of
logging, colored console output, and utility functions for debug operations.
"""

from debug.debugger import (
    ColoredFormatter,
    get_logger,
    setup_logging,
)

__all__: list[str] = [
    "ColoredFormatter",
    "get_logger",
    "setup_logging",
]
