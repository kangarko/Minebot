from logging import Logger

from core import GlobalState
from debug import get_logger

from ...action_registry import websocket_action
from ...schemas.response import PlayerServerCheckSchema

logger: Logger = get_logger(__name__)


@websocket_action("player-server-check", PlayerServerCheckSchema)
async def player_server_check(data: PlayerServerCheckSchema) -> None:
    logger.debug(
        f"Received player status check request: username={data.username}, uuid={data.uuid}, server={data.server}"
    )

    # Validate the provided username or UUID
    if data.server:
        if data.username:
            GlobalState.minecraft.add_player_server(
                data.username, data.server
            )  # Assign server to username
        if data.uuid:
            GlobalState.minecraft.add_player_server(data.uuid, data.server)  # Assign server to UUID
