"""
WebSocket event actions package for the minebot system.

This package contains handlers for outgoing WebSocket event actions,
allowing the minebot to broadcast updates and notifications to connected clients.
Event handlers publish messages to appropriate channels when significant
changes occur within the bot, enabling real-time monitoring and reactive
programming by external services.
"""

from .command_executed import command_executed

__all__: list[str] = ["command_executed"]
