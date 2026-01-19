import inspect
from logging import Logger
from typing import Any, Callable

from pydantic import BaseModel

from debug import get_logger

logger: Logger = get_logger(__name__)

# Dictionary to store action handlers
action_handlers: dict[str, dict[str, Any]] = {}


def websocket_action(
    action_name: str, schema: type[BaseModel], should_load_hook: bool = True
) -> Callable:
    """
    Decorator function to register action handlers.

    Args:
        action_name (str): The name of the action to register the handler for.
        schema (type[BaseModel]): The Pydantic model class for validating the action data.
        should_load_hook (bool, optional): Flag to control if the handler should be registered.
            Defaults to True.

    Returns:
        Callable: A decorator function that registers the decorated function as an action handler.
    """

    def decorator(func: Callable) -> Callable:
        if should_load_hook:
            if action_name in action_handlers:
                logger.warning(f"Overriding existing handler for WebSocket action: {action_name}")

            action_handlers[action_name] = {
                "handler": func,
                "schema": schema,
                "signature": inspect.signature(func),
            }

            # Only log at debug level instead of info to reduce noise
            logger.debug(
                f"WebSocket action '{action_name}' registered: {func.__module__}.{func.__name__}"
            )
        return func

    return decorator
