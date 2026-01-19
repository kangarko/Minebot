from logging import Logger

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TicketChannel
from database.schemas import TicketChannelSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class TicketChannelRepository:
    """
    Repository for handling TicketChannel database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with a database session."""
        self.session: AsyncSession = session
        logger.debug("Initialized TicketChannelRepository with session")

    async def get_by_id(self, channel_id: int) -> TicketChannel | None:
        """Get a ticket channel by ID."""
        logger.debug(f"Fetching ticket channel with ID: {channel_id}")
        result: Result[tuple[TicketChannel]] = await self.session.execute(
            select(TicketChannel).where(TicketChannel.id == channel_id)
        )
        channel = result.scalars().first()
        logger.debug(f"Ticket channel with ID {channel_id} found: {channel is not None}")
        return channel

    async def get_by_owner_id(self, owner_id: int) -> list[TicketChannel]:
        """Get all ticket channels for a specific owner."""
        logger.debug(f"Fetching ticket channels for owner ID: {owner_id}")
        result: Result[tuple[TicketChannel]] = await self.session.execute(
            select(TicketChannel).where(TicketChannel.owner_id == owner_id)
        )
        channels = list(result.scalars().all())
        logger.debug(f"Found {len(channels)} ticket channels for owner ID: {owner_id}")
        return channels

    async def get_by_category(self, category: str) -> list[TicketChannel]:
        """Get all ticket channels for a specific category."""
        logger.debug(f"Fetching ticket channels for category: {category}")
        result: Result[tuple[TicketChannel]] = await self.session.execute(
            select(TicketChannel).where(TicketChannel.category == category)
        )
        channels = list(result.scalars().all())
        logger.debug(f"Found {len(channels)} ticket channels for category: {category}")
        return channels

    async def create(self, channel_schema: TicketChannelSchema) -> TicketChannel:
        """Create a new ticket channel."""
        logger.debug(f"Creating new ticket channel for owner ID: {channel_schema.owner_id}")
        # Convert schema to model
        ticket_channel = TicketChannel(
            id=channel_schema.id,
            owner_id=channel_schema.owner_id,
            category=channel_schema.category,
        )

        self.session.add(ticket_channel)
        await self.session.flush()
        logger.debug(f"Created ticket channel with details: {vars(ticket_channel)}")
        return ticket_channel

    async def update(
        self, channel_id: int, channel_schema: TicketChannelSchema
    ) -> TicketChannel | None:
        """Update an existing ticket channel."""
        logger.debug(f"Attempting to update ticket channel ID: {channel_id}")
        ticket_channel: TicketChannel | None = await self.get_by_id(channel_id)
        if not ticket_channel:
            logger.debug(f"Ticket channel ID {channel_id} not found for update")
            return None

        # Update fields
        ticket_channel.owner_id = channel_schema.owner_id
        ticket_channel.category = channel_schema.category

        await self.session.flush()
        logger.debug(f"Updated ticket channel with details: {vars(ticket_channel)}")
        return ticket_channel

    async def delete(self, channel_id: int) -> bool:
        """Delete a ticket channel by ID."""
        logger.debug(f"Attempting to delete ticket channel ID: {channel_id}")
        ticket_channel: TicketChannel | None = await self.get_by_id(channel_id)
        if not ticket_channel:
            logger.debug(f"Ticket channel ID {channel_id} not found for deletion")
            return False

        await self.session.delete(ticket_channel)
        await self.session.flush()
        logger.debug(f"Successfully deleted ticket channel ID: {channel_id}")
        return True
