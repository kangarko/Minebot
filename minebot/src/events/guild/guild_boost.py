from logging import Logger
from typing import Sequence

import hikari
import lightbulb

from core import GlobalState
from debug import get_logger
from helper import EventHelper, MessageHelper, MinecraftHelper
from model import EventsKeys, MessageKeys
from model.schemas import GuildBoostEvent, UserReward
from settings import Settings

helper: EventHelper = EventHelper(EventsKeys.GUILD_BOOST)
loader: lightbulb.Loader = helper.get_loader()

logger: Logger = get_logger(__name__)


async def find_booster_role(guild: hikari.GatewayGuild) -> hikari.Role | None:
    """
    Finds and returns the server booster role.

    Args:
        guild: The guild to search for the booster role in

    Returns:
        The booster role if found, None otherwise
    """
    try:
        guild_roles: Sequence[hikari.Role] = await guild.fetch_roles()
        return next((r for r in guild_roles if r.is_premium_subscriber_role), None)
    except Exception as e:
        logger.error(f"Failed to fetch guild roles: {e}")
        return None


@loader.listener(hikari.MemberUpdateEvent)
async def on_guild_boost(event: hikari.MemberUpdateEvent) -> None:
    """
    Event handler for detecting when a user boosts the server and processing rewards.

    Args:
        event: The member update event containing old and new member data
    """
    # Skip if we don't have old member data for comparison
    if not event.old_member:
        logger.debug("Skipping member update event - missing old member data")
        return

    guild: hikari.GatewayGuild | None = event.get_guild()
    if not guild:
        logger.warning(f"Unable to get guild for member update event (user: {event.member.id})")
        return

    BOOSTER_ROLE = GlobalState.guild.get_booster_role()

    # Find and cache the booster role if needed
    if not BOOSTER_ROLE:
        logger.info("Booster role not cached, attempting to find it")
        GlobalState.guild.set_booster_role(await find_booster_role(guild))
        BOOSTER_ROLE = GlobalState.guild.get_booster_role()
        if not BOOSTER_ROLE:
            logger.error(f"Couldn't find booster role in guild {guild.id}")
            return
        logger.info(f"Cached booster role: {BOOSTER_ROLE.name} ({BOOSTER_ROLE.id})")

    # Get role IDs
    old_role_ids = set(event.old_member.role_ids)
    new_role_ids = set(event.member.role_ids)

    # Check if user just received the booster role
    if BOOSTER_ROLE.id in new_role_ids and BOOSTER_ROLE.id not in old_role_ids:
        logger.info(f"User {event.member.username} (ID: {event.member.id}) boosted the server")

        try:
            # Get configured boost rewards
            data: GuildBoostEvent = Settings.get(EventsKeys.GUILD_BOOST)
            rewards: UserReward | None = data.reward

            if not rewards:
                logger.warning("No rewards configured for server boosting")
                return

            # Process rewards
            logger.debug(f"Processing rewards for booster {event.member.username}: {rewards}")
            await MinecraftHelper.add_rewards(event.member, rewards)

            # Send confirmation to log channel
            await MessageHelper(
                MessageKeys.events.GUILD_BOOST_LOG_SUCCESS,
                discord_username=event.member.username,
                disord_user_id=event.member.id,
                discord_user_mention=event.member.mention,
            ).send_to_log_channel(helper)

            logger.info(f"Successfully processed boost rewards for {event.member.username}")
        except Exception as e:
            logger.error(f"Error processing boost rewards: {e}", exc_info=True)

            # Attempt to send error to log channel
            try:
                await MessageHelper(
                    MessageKeys.error.UNKNOWN,
                ).send_to_log_channel(helper)
            except Exception as log_error:
                logger.error(f"Failed to send error to log channel: {log_error}")
