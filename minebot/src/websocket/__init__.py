"""
WebSocket package for providing real-time communication capabilities.

This package provides a WebSocket server implementation that allows
for bidirectional communication between the bot and external services.
It includes an action-based system for handling different message types
and a manager for the server lifecycle.
"""

from . import actions, schemas
from .action_registry import action_handlers, websocket_action
from .listener import authenticated_client, handle_connection
from .manager import WebSocketManager
from .server import WebSocketServer

__all__: list[str] = [
    "actions",
    "schemas",
    "action_handlers",
    "websocket_action",
    "authenticated_client",
    "handle_connection",
    "WebSocketManager",
    "WebSocketServer",
]
