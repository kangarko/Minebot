import asyncio
import inspect
import json
from logging import Logger
from typing import Any, Callable

from pydantic import BaseModel, ValidationError
from websockets import ServerConnection

from core import GlobalState
from debug import get_logger
from model import WebSocketKeys
from settings import Settings

from .action_registry import action_handlers
from .schemas.response import AuthenticateSchema

logger: Logger = get_logger(__name__)

authenticated_client: dict[int, tuple[ServerConnection, AuthenticateSchema]] = {}


async def handle_connection(websocket: ServerConnection) -> None:
    """
    Handle an incoming WebSocket connection.

    This function processes messages from connected clients, dispatches them
    to the appropriate action handler based on the action type in the message.

    Clients must authenticate within 3 seconds or will be disconnected.
    Only authentication messages are allowed for non-authenticated clients.

    Args:
        websocket: The WebSocket connection object.
    """
    allowed_ip = Settings.get(WebSocketKeys.ALLOWED_IP)
    client_ip = websocket.remote_address[0] if websocket.remote_address else None
    client_id = id(websocket)

    # Validate client IP against allowed IP
    if allowed_ip and client_ip != allowed_ip:
        logger.warning(f"Rejected connection from unauthorized IP: {client_ip} [id={client_id}]")
        await websocket.close(1008, "Connection not allowed from this IP")
        return

    # Check if client is already authenticated (shouldn't happen, but handling it)
    if client_id in authenticated_client:
        logger.warning(f"Client already authenticated [id={client_id}]")
        await websocket.close(1008, "Connection already exists")
        return

    # Keep connections at debug level
    logger.debug(f"WebSocket connection established [id={client_id}]")

    # Set authentication deadline
    auth_deadline = asyncio.create_task(asyncio.sleep(3))
    auth_complete = False

    try:
        async for message in websocket:
            # Check if client is authenticated or attempting to authenticate
            if not auth_complete and auth_deadline.done():
                logger.warning(f"Client failed to authenticate within time limit [id={client_id}]")
                await websocket.close(1008, "Authentication timeout")
                return

            try:
                data: dict[str, Any] = json.loads(message)
                action: Any | None = data.get("action")

                if not action:
                    logger.warning(f"Received message without action type [client={client_id}]")
                    continue

                # If not authenticated, only allow authentication messages
                if client_id not in authenticated_client and action != "authenticate":
                    logger.warning(
                        f"Unauthenticated client attempting action: {action} [client={client_id}]"
                    )
                    continue

                # Use debug level for routine message handling
                logger.debug(f"Received '{action}' action [client={client_id}]")

                action_info: dict[str, Any] | None = action_handlers.get(action)
                if action_info:
                    handler: Callable | None = action_info.get("handler")
                    schema: type[BaseModel] | None = action_info.get("schema")
                    signature: inspect.Signature | None = action_info.get("signature")

                    if handler and schema:
                        try:
                            # Create parameters based on function signature
                            validated_data = schema(**data)
                            kwargs = {}

                            if signature:
                                param_names = signature.parameters.keys()

                                # Only pass parameters that the handler function expects
                                if "websocket" in param_names:
                                    kwargs["websocket"] = websocket
                                if "data" in param_names:
                                    kwargs["data"] = validated_data
                                if "bot" in param_names and (bot := GlobalState.bot.get_bot()):
                                    kwargs["bot"] = bot
                                if "client" in param_names and (
                                    client := GlobalState.bot.get_client()
                                ):
                                    kwargs["client"] = client

                            await handler(**kwargs)

                            # Mark authentication as complete if this was an auth request and it succeeded
                            if action == "authenticate" and client_id in authenticated_client:
                                auth_complete = True
                                auth_deadline.cancel()
                        except ValidationError as e:
                            logger.error(
                                f"Validation error for action '{action}' [client={client_id}]: {e}"
                            )
                            continue

                else:
                    logger.warning(f"No handler registered for action: {action}")

            except json.JSONDecodeError:
                logger.error(f"Received invalid JSON [client={client_id}]: {message[:100]}")
            except Exception as e:
                logger.error(
                    f"Error processing message [client={client_id}]: {str(e)}", exc_info=True
                )

    except Exception as e:
        logger.error(f"WebSocket connection error [client={client_id}]: {str(e)}", exc_info=True)
    finally:
        # Clean up authentication deadline if it exists
        if not auth_deadline.done():
            auth_deadline.cancel()

        # Remove client from authenticated clients if present
        if client_id in authenticated_client:
            del authenticated_client[client_id]

        GlobalState.minecraft.clear_servers()

        # Keep connections at debug level, not info
        logger.debug(f"WebSocket connection closed [id={client_id}]")
