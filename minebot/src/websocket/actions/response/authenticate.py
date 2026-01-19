from logging import Logger

from websockets import ServerConnection

from core import GlobalState
from debug import get_logger
from model import WebSocketKeys
from settings import Settings

from ...action_registry import websocket_action
from ...listener import authenticated_client
from ...schemas.response import AuthenticateSchema

logger: Logger = get_logger(__name__)


@websocket_action("authenticate", AuthenticateSchema)
async def authenticate(websocket: ServerConnection, data: AuthenticateSchema) -> None:
    client_id = id(websocket)
    auth_password: str = Settings.get(WebSocketKeys.PASSWORD)

    # Validate the provided password agains stored password
    if data.password != auth_password:
        logger.warning(f"Authentication failed for client [id={client_id}]: Invalid credentials")
        await websocket.close(1008, "Authentication failed: Invalid credentials provided")
        return

    # Store the authenticated client
    authenticated_client[client_id] = (websocket, data)

    # Update the Minecraft server list
    GlobalState.minecraft.add_server(data.server_list + ["all"])

    logger.info(
        f"Client [id={client_id}] authenticated successfully (server_list={data.server_list})"
    )
