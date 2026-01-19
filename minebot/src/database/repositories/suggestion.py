from logging import Logger

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Suggestion
from database.schemas import SuggestionSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class SuggestionRepository:
    """
    Repository for handling Suggestion database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with a database session."""
        self.session: AsyncSession = session
        logger.debug("Initialized SuggestionRepository with session")

    async def get_by_id(self, suggestion_id: int) -> Suggestion | None:
        """Get a suggestion by ID."""
        logger.debug(f"Fetching suggestion with ID: {suggestion_id}")
        result: Result[tuple[Suggestion]] = await self.session.execute(
            select(Suggestion).where(Suggestion.id == suggestion_id)
        )
        suggestion: Suggestion | None = result.scalars().first()
        logger.debug(f"Suggestion with ID {suggestion_id} found: {suggestion is not None}")
        return suggestion

    async def get_by_user_id(self, user_id: int) -> list[Suggestion]:
        """Get all suggestions from a specific user."""
        logger.debug(f"Fetching suggestions for user ID: {user_id}")
        result: Result[tuple[Suggestion]] = await self.session.execute(
            select(Suggestion).where(Suggestion.user_id == user_id)
        )
        suggestions = list(result.scalars().all())
        logger.debug(f"Found {len(suggestions)} suggestions for user ID: {user_id}")
        return suggestions

    async def get_by_staff_id(self, staff_id: int) -> list[Suggestion]:
        """Get all suggestions handled by a specific staff member."""
        logger.debug(f"Fetching suggestions handled by staff ID: {staff_id}")
        result: Result[tuple[Suggestion]] = await self.session.execute(
            select(Suggestion).where(Suggestion.staff_id == staff_id)
        )
        suggestions = list(result.scalars().all())
        logger.debug(f"Found {len(suggestions)} suggestions handled by staff ID: {staff_id}")
        return suggestions

    async def get_by_status(self, status: str) -> list[Suggestion]:
        """Get all suggestions with a specific status."""
        logger.debug(f"Fetching suggestions with status: {status}")
        result: Result[tuple[Suggestion]] = await self.session.execute(
            select(Suggestion).where(Suggestion.status == status)
        )
        suggestions = list(result.scalars().all())
        logger.debug(f"Found {len(suggestions)} suggestions with status: {status}")
        return suggestions

    async def create(self, suggestion_schema: SuggestionSchema) -> Suggestion:
        """Create a new suggestion."""
        logger.debug(f"Creating new suggestion for user ID: {suggestion_schema.user_id}")
        # Convert schema to model
        suggestion = Suggestion(
            id=suggestion_schema.id,
            user_id=suggestion_schema.user_id,
            staff_id=suggestion_schema.staff_id,
            suggestion=suggestion_schema.suggestion,
            status=suggestion_schema.status,
        )

        self.session.add(suggestion)
        await self.session.flush()
        logger.debug(f"Created suggestion with details: {vars(suggestion)}")
        return suggestion

    async def update(
        self, suggestion_id: int, suggestion_schema: SuggestionSchema
    ) -> Suggestion | None:
        """Update an existing suggestion."""
        logger.debug(f"Attempting to update suggestion ID: {suggestion_id}")
        suggestion: Suggestion | None = await self.get_by_id(suggestion_id)
        if not suggestion:
            logger.debug(f"Suggestion ID {suggestion_id} not found for update")
            return None

        # Update fields
        suggestion.user_id = suggestion_schema.user_id
        suggestion.staff_id = suggestion_schema.staff_id
        suggestion.suggestion = suggestion_schema.suggestion
        suggestion.status = suggestion_schema.status

        await self.session.flush()
        logger.debug(f"Updated suggestion with details: {vars(suggestion)}")
        return suggestion

    async def delete(self, suggestion_id: int) -> bool:
        """Delete a suggestion by ID."""
        logger.debug(f"Attempting to delete suggestion ID: {suggestion_id}")
        suggestion: Suggestion | None = await self.get_by_id(suggestion_id)
        if not suggestion:
            logger.debug(f"Suggestion ID {suggestion_id} not found for deletion")
            return False

        await self.session.delete(suggestion)
        await self.session.flush()
        logger.debug(f"Deleted suggestion ID: {suggestion_id}")
        return True
