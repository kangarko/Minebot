from logging import Logger

from database import get_db_session
from database.models import TicketChannel
from database.repositories import TicketChannelRepository
from database.schemas import TicketChannelSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class TicketChannelService:
    """
    Service for ticket channel-related business logic and operations.
    """

    @staticmethod
    async def get_ticket_channel(channel_id: int) -> TicketChannelSchema | None:
        """
        Get a ticket channel by ID.

        Args:
            channel_id: The Discord channel ID

        Returns:
            TicketChannelSchema or None if the ticket channel doesn't exist
        """
        logger.debug(f"Getting ticket channel with ID: {channel_id}")
        async with get_db_session() as session:
            repository = TicketChannelRepository(session)
            ticket_channel: TicketChannel | None = await repository.get_by_id(channel_id)
            if ticket_channel:
                logger.debug(f"Found ticket channel: {ticket_channel}")
                return TicketChannelSchema.model_validate(ticket_channel)
            logger.debug(f"No ticket channel found with ID: {channel_id}")
            return None

    @staticmethod
    async def get_ticket_channels_by_owner(owner_id: int) -> list[TicketChannelSchema]:
        """
        Get all ticket channels owned by a specific user.

        Args:
            owner_id: The Discord user ID of the owner

        Returns:
            List of TicketChannelSchema objects
        """
        logger.debug(f"Getting ticket channels for owner with ID: {owner_id}")
        async with get_db_session() as session:
            repository = TicketChannelRepository(session)
            ticket_channels: list[TicketChannel] = await repository.get_by_owner_id(owner_id)
            logger.debug(f"Found {len(ticket_channels)} ticket channels for owner {owner_id}")
            return [TicketChannelSchema.model_validate(channel) for channel in ticket_channels]

    @staticmethod
    async def get_ticket_channels_by_category(category: str) -> list[TicketChannelSchema]:
        """
        Get all ticket channels for a specific category.

        Args:
            category: The category identifier for the ticket channels

        Returns:
            List of TicketChannelSchema objects
        """
        logger.debug(f"Getting ticket channels for category: {category}")
        async with get_db_session() as session:
            repository = TicketChannelRepository(session)
            ticket_channels: list[TicketChannel] = await repository.get_by_category(category)
            logger.debug(f"Found {len(ticket_channels)} ticket channels for category {category}")
            return [TicketChannelSchema.model_validate(channel) for channel in ticket_channels]

    @staticmethod
    async def create_or_update_ticket_channel(
        channel_data: TicketChannelSchema,
    ) -> TicketChannelSchema:
        """
        Create a new ticket channel or update if it already exists.

        Args:
            channel_data: The ticket channel data to create or update

        Returns:
            The created/updated ticket channel schema
        """
        logger.debug(f"Creating or updating ticket channel: {channel_data}")
        async with get_db_session() as session:
            repository = TicketChannelRepository(session)
            existing_channel: TicketChannel | None = await repository.get_by_id(channel_data.id)

            if existing_channel:
                logger.debug(f"Updating existing ticket channel with ID: {channel_data.id}")
                updated_channel: TicketChannel | None = await repository.update(
                    channel_data.id, channel_data
                )
                logger.debug(f"Updated ticket channel: {updated_channel}")
                return TicketChannelSchema.model_validate(updated_channel)
            else:
                logger.debug(f"Creating new ticket channel with ID: {channel_data.id}")
                new_channel: TicketChannel = await repository.create(channel_data)
                logger.debug(f"Created new ticket channel: {new_channel}")
                return TicketChannelSchema.model_validate(new_channel)

    @staticmethod
    async def delete_ticket_channel(channel_id: int) -> bool:
        """
        Delete a ticket channel by ID.

        Args:
            channel_id: The Discord channel ID

        Returns:
            True if the ticket channel was deleted, False otherwise
        """
        logger.debug(f"Attempting to delete ticket channel with ID: {channel_id}")
        async with get_db_session() as session:
            repository = TicketChannelRepository(session)
            result = await repository.delete(channel_id)
            logger.debug(f"Deletion result for ticket channel {channel_id}: {result}")
            return result
