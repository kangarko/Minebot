"""
WebSocket action handling package for the minebot system.

This package provides action handlers and processors for the WebSocket server,
enabling real-time communication capabilities between the bot and external services.
Actions are registered and dispatched through this system, allowing for modular
and extensible message handling.
"""

from . import event, request, response

__all__: list[str] = ["request", "response", "event"]
