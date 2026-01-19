from logging import Logger
from typing import TypeVar, cast

import hikari
import lightbulb

from core import GlobalState
from debug import get_logger

logger: Logger = get_logger(__name__)

T = TypeVar("T", bound=hikari.PartialChannel)


class ChannelHelper:
    _client: lightbulb.Client | None = None

    @classmethod
    def _get_client(cls) -> lightbulb.Client:
        """Get and cache the client if not already cached."""
        if cls._client is None:
            logger.debug("Caching client instance")
            cls._client = GlobalState.bot.get_client()
        else:
            logger.debug("Using cached client instance")
        return cls._client

    @staticmethod
    async def fetch_channel(
        channel_id: int,
        channel_type: type[T] = hikari.PartialChannel,
    ) -> T:
        """
        Fetches a Discord channel by ID and verifies its type.

        Args:
            channel_id (int): The ID of the channel to fetch
            channel_type (type[hikari.PartialChannel]): The expected channel type

        Returns:
            T: The fetched channel, cast to the specified type

        Raises:
            ValueError: If the channel doesn't exist or isn't of the expected type
            Exception: If an unexpected error occurs during the fetch operation
        """
        try:
            channel = await ChannelHelper._get_client().rest.fetch_channel(channel_id)

            if isinstance(channel, channel_type):
                logger.debug(f"Fetched channel {channel_id} of type {channel_type.__name__}")
                return cast(T, channel)

            logger.warning(
                f"Channel {channel_id} exists but is of type {type(channel).__name__}, expected {channel_type.__name__}"
            )
            raise ValueError(
                f"Channel {channel_id} is not of expected type {channel_type.__name__}"
            )

        except hikari.NotFoundError:
            logger.warning(f"Channel with ID {channel_id} not found")
            raise ValueError(f"Channel with ID {channel_id} not found")
        except Exception as e:
            logger.error(f"Unexpected error fetching channel {channel_id}: {e}")
            raise
