from logging import Logger

import hikari

from core import GlobalState
from debug import get_logger
from model import SecretKeys
from settings import Settings

logger: Logger = get_logger(__name__)


class UserHelper:
    @staticmethod
    async def fetch_user(user_id: int) -> hikari.User | None:
        """Fetch a user by their ID."""
        logger.debug(f"Fetching user with ID: {user_id}")

        try:
            user = await GlobalState.bot.get_bot().rest.fetch_user(user_id)
            logger.debug(f"Found user: {user.username} (ID: {user.id})")
            return user

        except hikari.NotFoundError:
            logger.debug(f"User with ID {user_id} not found")
            return None

        except hikari.ForbiddenError:
            logger.debug(f"Permission denied when fetching user {user_id}")
            return None

        except Exception as e:
            logger.debug(f"Error fetching user {user_id}: {type(e).__name__}")
            return None

    @staticmethod
    async def fetch_member(user: hikari.User | int) -> hikari.Member | None:
        """Fetch a member from the default guild."""
        user_id = user.id if isinstance(user, hikari.User) else user
        guild_id = Settings.get(SecretKeys.DEFAULT_GUILD)

        logger.debug(f"Fetching member {user_id} from guild {guild_id}")

        try:
            member = await GlobalState.bot.get_bot().rest.fetch_member(guild_id, user)
            logger.debug(f"Found member: {user_id}")
            return member

        except hikari.NotFoundError:
            logger.debug(f"Member {user_id} not found")
            return None

        except hikari.ForbiddenError:
            logger.debug(f"Permission denied when fetching member {user_id}")
            return None

        except Exception as e:
            logger.debug(f"Error fetching member {user_id}: {type(e).__name__}")
            return None
