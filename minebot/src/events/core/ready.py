from logging import Logger
from typing import Sequence

import hikari
import lightbulb
import toolbox

from core import GlobalState
from debug import get_logger
from helper.punishment import PunishmentHelper
from model import SecretKeys
from settings import Settings

REQUIRED_PERMISSIONS = 1829587348619263  # Administrator permissions value

loader = lightbulb.Loader()
logger: Logger = get_logger(__name__)


@loader.listener(hikari.ShardReadyEvent)
async def on_ready(event: hikari.ShardReadyEvent) -> None:
    try:
        # Fetch and validate default guild
        guild: hikari.Guild = await event.app.rest.fetch_guild(
            Settings.get(SecretKeys.DEFAULT_GUILD)
        )
        if guild is None:
            logger.critical("Failed to retrieve the guild.")
            raise Exception("Failed to retrieve the guild.")
        logger.info(f"Bot connected to guild: {guild.name} (ID: {guild.id})")

        # Set guild language
        preferred_locale = hikari.Locale(guild.preferred_locale)
        GlobalState.guild.set_locale(preferred_locale)
        logger.info(f"Guild language set to: {preferred_locale}")

        # Verify bot member
        my_member: hikari.Member | None = guild.get_my_member()
        if my_member is None:
            logger.critical("Failed to retrieve bot member.")
            raise Exception("Failed to retrieve bot member.")

        GlobalState.bot.set_member(my_member)

        # Check permissions
        if toolbox.calculate_permissions(my_member).value != REQUIRED_PERMISSIONS:
            logger.critical("Bot does not have administrator permissions.")
            raise Exception("Bot does not have administrator permissions.")
        logger.info("Bot has the required administrator permissions.")

        # Set booster role
        guild_roles: Sequence[hikari.Role] = await guild.fetch_roles()
        GlobalState.guild.set_booster_role(
            next((r for r in guild_roles if r.is_premium_subscriber_role), None)
        )

        # Schedule punishment tasks
        await PunishmentHelper.schedule_punishment_tasks()

        logger.info("Bot is ready and fully operational.")
    except Exception as e:
        logger.critical(f"An error occurred during the ready event: {e}", exc_info=True)
        raise
