from logging import Logger

from database import get_db_session
from database.models import TicketInfo
from database.repositories import TicketInfoRepository
from database.schemas import TicketInfoSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class TicketInfoService:
    """
    Service for ticket information related business logic and operations.
    """

    @staticmethod
    async def get_ticket_by_id(ticket_id: int) -> TicketInfoSchema | None:
        """
        Get a ticket by ID.

        Args:
            ticket_id: The ticket ID

        Returns:
            TicketInfoSchema or None if the ticket doesn't exist
        """
        logger.debug(f"Getting ticket with ID: {ticket_id}")
        async with get_db_session() as session:
            repository = TicketInfoRepository(session)
            ticket_info: TicketInfo | None = await repository.get_by_id(ticket_id)
            if ticket_info:
                logger.debug(f"Found ticket with ID {ticket_id}: {ticket_info}")
                return TicketInfoSchema.model_validate(ticket_info)
            logger.debug(f"No ticket found with ID: {ticket_id}")
            return None

    @staticmethod
    async def get_ticket_by_channel_id(channel_id: int) -> TicketInfoSchema | None:
        """
        Get a ticket by channel ID.

        Args:
            channel_id: The Discord channel ID

        Returns:
            TicketInfoSchema or None if the ticket doesn't exist
        """
        logger.debug(f"Getting ticket by channel ID: {channel_id}")
        async with get_db_session() as session:
            repository = TicketInfoRepository(session)
            ticket_info: TicketInfo | None = await repository.get_by_channel_id(channel_id)
            if ticket_info:
                logger.debug(f"Found ticket for channel {channel_id}: {ticket_info}")
                return TicketInfoSchema.model_validate(ticket_info)
            logger.debug(f"No ticket found for channel ID: {channel_id}")
            return None

    @staticmethod
    async def get_ticket_by_message_id(message_id: int) -> TicketInfoSchema | None:
        """
        Get a ticket by message ID.

        Args:
            message_id: The Discord message ID

        Returns:
            TicketInfoSchema or None if the ticket doesn't exist
        """
        logger.debug(f"Getting ticket by message ID: {message_id}")
        async with get_db_session() as session:
            repository = TicketInfoRepository(session)
            ticket_info: TicketInfo | None = await repository.get_by_message_id(message_id)
            if ticket_info:
                logger.debug(f"Found ticket for message {message_id}: {ticket_info}")
                return TicketInfoSchema.model_validate(ticket_info)
            logger.debug(f"No ticket found for message ID: {message_id}")
            return None

    @staticmethod
    async def create_or_update_ticket(ticket_data: TicketInfoSchema) -> TicketInfoSchema:
        """
        Create a new ticket or update if it already exists.

        Args:
            ticket_data: The ticket data to create or update

        Returns:
            The created/updated ticket schema
        """
        logger.debug(f"Creating or updating ticket: {ticket_data}")
        async with get_db_session() as session:
            repository = TicketInfoRepository(session)
            existing_ticket: TicketInfo | None = await repository.get_by_id(ticket_data.id)

            if existing_ticket:
                logger.debug(f"Updating existing ticket with ID: {ticket_data.id}")
                updated_ticket: TicketInfo | None = await repository.update(
                    ticket_data.id, ticket_data
                )
                logger.debug(f"Updated ticket: {updated_ticket}")
                return TicketInfoSchema.model_validate(updated_ticket)
            else:
                logger.debug(f"Creating new ticket with data: {ticket_data}")
                new_ticket: TicketInfo = await repository.create(ticket_data)
                logger.debug(f"Created new ticket with ID: {new_ticket.id}")
                return TicketInfoSchema.model_validate(new_ticket)

    @staticmethod
    async def delete_ticket(ticket_id: int) -> bool:
        """
        Delete a ticket by ID.

        Args:
            ticket_id: The ticket ID

        Returns:
            True if the ticket was deleted, False otherwise
        """
        logger.debug(f"Attempting to delete ticket with ID: {ticket_id}")
        async with get_db_session() as session:
            repository = TicketInfoRepository(session)
            result = await repository.delete(ticket_id)
            logger.debug(f"Deletion result for ticket {ticket_id}: {result}")
            return result
