import json
from logging import Logger
from typing import Any

from pydantic import BaseModel
from websockets import ConnectionClosed

from debug import get_logger

from .listener import authenticated_client

logger: Logger = get_logger(__name__)


class WebSocketManager:
    @staticmethod
    async def send_message(data: dict[str, Any] | BaseModel) -> bool:
        """
        Send a message to the authenticated WebSocket client.

        Args:
            data: The data to send as a dictionary or a Pydantic BaseModel

        Returns:
            True if the message was sent successfully, False otherwise
        """
        if not authenticated_client:
            logger.warning("WebSocket message not sent: No authenticated clients connected")
            return False

        client_id = next(iter(authenticated_client.keys()))
        websocket, _ = authenticated_client[client_id]

        try:
            # Convert BaseModel to dict before serializing
            if isinstance(data, BaseModel):
                message = data.model_dump_json()
            else:
                message = json.dumps(data)

            await websocket.send(message)
            logger.debug(f"Message successfully sent to client {client_id}")
            return True
        except ConnectionClosed:
            logger.warning(
                f"Failed to send message to client {client_id}: WebSocket connection closed"
            )
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {str(e)}", exc_info=True)

        return False
