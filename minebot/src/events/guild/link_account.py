from logging import Logger

import hikari
import lightbulb

from database.schemas import UserSchema
from database.services import UserService
from debug import get_logger
from helper import CommandHelper
from model import CommandsKeys
from model.schemas import LoggedRewardableCommandConfig, UserReward
from settings import Settings

helper: CommandHelper = CommandHelper(CommandsKeys.LINK_ACCOUNT)
loader: lightbulb.Loader = helper.get_loader()

logger: Logger = get_logger(__name__)


@loader.listener(hikari.MemberCreateEvent)
async def on_member_create(event: hikari.MemberCreateEvent) -> None:
    # Get user data and check if they exist in our system
    user_data: UserSchema | None = await UserService.get_user(event.user_id)
    if not user_data:
        return

    # Get reward configuration
    data: LoggedRewardableCommandConfig = Settings.get(CommandsKeys.LINK_ACCOUNT)
    rewards: UserReward | None = data.reward

    # Check if rewards exist and are not items
    if not rewards or rewards.mode not in ["ROLE", "BOTH"] or not rewards.role:
        return

    # Handle both single role_id and list of role_ids
    role_ids: list[int] = [rewards.role] if isinstance(rewards.role, int) else rewards.role

    # Add role rewards with proper error handling
    for role_id in role_ids:
        try:
            role: hikari.Role = await event.app.rest.fetch_role(event.guild_id, role_id)
            if role:
                await event.member.add_role(role, reason="Link account reward")
                logger.debug(
                    f"Link Account Reward: Added role '{role.name}' (ID: {role_id}) to member {event.member.display_name} (ID: {event.user_id})"
                )
        except hikari.NotFoundError:
            logger.warning(
                f"Link Account Reward Failed: Role ID {role_id} not found in guild '{event.guild_id}'. Check if the role still exists."
            )
        except Exception as e:
            logger.error(
                f"Link Account Reward Error: Failed to add role ID {role_id} to {event.member.display_name} (ID: {event.user_id}). Error: {type(e).__name__}: {e}"
            )
