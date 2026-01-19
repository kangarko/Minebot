from logging import Logger

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TicketInfo
from database.schemas import TicketInfoSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class TicketInfoRepository:
    """
    Repository for handling TicketInfo database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with a database session."""
        self.session: AsyncSession = session
        logger.debug("Initialized TicketInfoRepository with session")

    async def get_by_id(self, ticket_id: int) -> TicketInfo | None:
        """Get a ticket by ID."""
        logger.debug(f"Fetching ticket info with ID: {ticket_id}")
        result: Result[tuple[TicketInfo]] = await self.session.execute(
            select(TicketInfo).where(TicketInfo.id == ticket_id)
        )
        ticket = result.scalars().first()
        logger.debug(f"Ticket info with ID {ticket_id} found: {ticket is not None}")
        return ticket

    async def get_by_channel_id(self, channel_id: int) -> TicketInfo | None:
        """Get a ticket by channel ID."""
        logger.debug(f"Fetching ticket info with channel ID: {channel_id}")
        result: Result[tuple[TicketInfo]] = await self.session.execute(
            select(TicketInfo).where(TicketInfo.channel_id == channel_id)
        )
        ticket = result.scalars().first()
        logger.debug(f"Ticket info with channel ID {channel_id} found: {ticket is not None}")
        return ticket

    async def get_by_message_id(self, message_id: int) -> TicketInfo | None:
        """Get a ticket by message ID."""
        logger.debug(f"Fetching ticket info with message ID: {message_id}")
        result: Result[tuple[TicketInfo]] = await self.session.execute(
            select(TicketInfo).where(TicketInfo.message_id == message_id)
        )
        ticket = result.scalars().first()
        logger.debug(f"Ticket info with message ID {message_id} found: {ticket is not None}")
        return ticket

    async def create(self, ticket_schema: TicketInfoSchema) -> TicketInfo:
        """Create a new ticket info entry."""
        logger.debug(
            f"Creating new ticket info with channel ID: {ticket_schema.channel_id}, message ID: {ticket_schema.message_id}"
        )
        # Convert schema to model
        ticket_info = TicketInfo(
            id=ticket_schema.id,
            channel_id=ticket_schema.channel_id,
            message_id=ticket_schema.message_id,
        )

        self.session.add(ticket_info)
        await self.session.flush()
        logger.debug(f"Created ticket info with details: {vars(ticket_info)}")
        return ticket_info

    async def update(self, ticket_id: int, ticket_schema: TicketInfoSchema) -> TicketInfo | None:
        """Update an existing ticket info entry."""
        logger.debug(f"Attempting to update ticket info with ID: {ticket_id}")
        ticket_info: TicketInfo | None = await self.get_by_id(ticket_id)
        if not ticket_info:
            logger.debug(f"Ticket info with ID {ticket_id} not found for update")
            return None

        # Update fields
        ticket_info.channel_id = ticket_schema.channel_id
        ticket_info.message_id = ticket_schema.message_id

        await self.session.flush()
        logger.debug(f"Updated ticket info with details: {vars(ticket_info)}")
        return ticket_info

    async def delete(self, ticket_id: int) -> bool:
        """Delete a ticket info entry by ID."""
        logger.debug(f"Attempting to delete ticket info with ID: {ticket_id}")
        ticket_info: TicketInfo | None = await self.get_by_id(ticket_id)
        if not ticket_info:
            logger.debug(f"Ticket info with ID {ticket_id} not found for deletion")
            return False

        await self.session.delete(ticket_info)
        await self.session.flush()
        logger.debug(f"Successfully deleted ticket info with ID: {ticket_id}")
        return True
