from logging import Logger

from core import GlobalState
from debug import get_logger

from ...action_registry import websocket_action
from ...schemas.response import PlayerStatusCheckSchema

logger: Logger = get_logger(__name__)


@websocket_action("player-status-check", PlayerStatusCheckSchema)
async def player_status_check(data: PlayerStatusCheckSchema) -> None:
    logger.debug(
        f"Received player status check request: username={data.username}, uuid={data.uuid}, online={data.online}"
    )

    # Validate the provided username or UUID
    if data.online and data.username and data.uuid:
        GlobalState.minecraft.add_online_player(data.username)  # Assign username to online players
        GlobalState.minecraft.add_online_player(data.uuid)  # Assign UUID to online players
        GlobalState.minecraft.add_player_uuid(data.username, data.uuid)  # Map username to UUID
