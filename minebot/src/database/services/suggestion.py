from logging import Logger

from database import get_db_session
from database.models import Suggestion
from database.repositories import SuggestionRepository
from database.schemas import SuggestionSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class SuggestionService:
    """
    Service for suggestion-related business logic and operations.
    """

    @staticmethod
    async def get_suggestion(suggestion_id: int) -> SuggestionSchema | None:
        """
        Get a suggestion by ID.

        Args:
            suggestion_id: The suggestion ID

        Returns:
            SuggestionSchema or None if the suggestion doesn't exist
        """
        logger.debug(f"Getting suggestion with ID: {suggestion_id}")
        async with get_db_session() as session:
            repository = SuggestionRepository(session)
            suggestion: Suggestion | None = await repository.get_by_id(suggestion_id)
            if suggestion:
                logger.debug(f"Found suggestion: {suggestion}")
                return SuggestionSchema.model_validate(suggestion)
            logger.debug(f"No suggestion found with ID: {suggestion_id}")
            return None

    @staticmethod
    async def get_suggestions_by_user(user_id: int) -> list[SuggestionSchema]:
        """
        Get all suggestions from a specific user.

        Args:
            user_id: The Discord user ID

        Returns:
            List of SuggestionSchema objects
        """
        logger.debug(f"Getting suggestions for user with ID: {user_id}")
        async with get_db_session() as session:
            repository = SuggestionRepository(session)
            suggestions: list[Suggestion] = await repository.get_by_user_id(user_id)
            logger.debug(f"Found {len(suggestions)} suggestions for user {user_id}")
            return [SuggestionSchema.model_validate(suggestion) for suggestion in suggestions]

    @staticmethod
    async def get_suggestions_by_staff(staff_id: int) -> list[SuggestionSchema]:
        """
        Get all suggestions handled by a specific staff member.

        Args:
            staff_id: The Discord staff member ID

        Returns:
            List of SuggestionSchema objects
        """
        logger.debug(f"Getting suggestions handled by staff with ID: {staff_id}")
        async with get_db_session() as session:
            repository = SuggestionRepository(session)
            suggestions: list[Suggestion] = await repository.get_by_staff_id(staff_id)
            logger.debug(f"Found {len(suggestions)} suggestions handled by staff {staff_id}")
            return [SuggestionSchema.model_validate(suggestion) for suggestion in suggestions]

    @staticmethod
    async def get_suggestions_by_status(status: str) -> list[SuggestionSchema]:
        """
        Get all suggestions with a specific status.

        Args:
            status: The suggestion status (e.g., "pending", "approved", "rejected")

        Returns:
            List of SuggestionSchema objects
        """
        logger.debug(f"Getting suggestions with status: {status}")
        async with get_db_session() as session:
            repository = SuggestionRepository(session)
            suggestions: list[Suggestion] = await repository.get_by_status(status)
            logger.debug(f"Found {len(suggestions)} suggestions with status {status}")
            return [SuggestionSchema.model_validate(suggestion) for suggestion in suggestions]

    @staticmethod
    async def create_or_update_suggestion(suggestion_data: SuggestionSchema) -> SuggestionSchema:
        """
        Create a new suggestion or update if it already exists.

        Args:
            suggestion_data: The suggestion data to create or update

        Returns:
            The created/updated suggestion schema
        """
        logger.debug(f"Creating or updating suggestion: {suggestion_data}")
        async with get_db_session() as session:
            repository = SuggestionRepository(session)

            # Check if we have an ID and if it exists in the database
            if suggestion_data.id is not None:
                logger.debug(f"Checking if suggestion with ID {suggestion_data.id} exists")
                existing_suggestion: Suggestion | None = await repository.get_by_id(suggestion_data.id)
                if existing_suggestion:
                    logger.debug(f"Updating existing suggestion with ID: {suggestion_data.id}")
                    updated_suggestion: Suggestion | None = await repository.update(
                        suggestion_data.id, suggestion_data
                    )
                    logger.debug(f"Updated suggestion: {updated_suggestion}")
                    return SuggestionSchema.model_validate(updated_suggestion)

            # If no ID or record doesn't exist, create a new one
            logger.debug("Creating new suggestion")
            new_suggestion: Suggestion = await repository.create(suggestion_data)
            logger.debug(f"Created new suggestion with ID: {new_suggestion.id}")
            return SuggestionSchema.model_validate(new_suggestion)

    @staticmethod
    async def delete_suggestion(suggestion_id: int) -> bool:
        """
        Delete a suggestion by ID.

        Args:
            suggestion_id: The suggestion ID

        Returns:
            True if the suggestion was deleted, False otherwise
        """
        logger.debug(f"Attempting to delete suggestion with ID: {suggestion_id}")
        async with get_db_session() as session:
            repository = SuggestionRepository(session)
            result = await repository.delete(suggestion_id)
            logger.debug(f"Deletion result for suggestion {suggestion_id}: {result}")
            return result