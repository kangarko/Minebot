from logging import Logger

from database import get_db_session
from database.models import TemporaryAction
from database.repositories import TemporaryActionRepository
from database.schemas import TemporaryActionSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class TemporaryActionService:
    """
    Service for temporary action-related business logic and operations.
    """

    @staticmethod
    async def get_temporary_action(action_id: int) -> TemporaryActionSchema | None:
        """
        Get a temporary action by ID.

        Args:
            action_id: The temporary action ID

        Returns:
            TemporaryActionSchema or None if the action doesn't exist
        """
        logger.debug(f"Getting temporary action with ID: {action_id}")
        async with get_db_session() as session:
            repository = TemporaryActionRepository(session)
            action: TemporaryAction | None = await repository.get_by_id(action_id)
            if action:
                logger.debug(f"Found temporary action: {action}")
                return TemporaryActionSchema.model_validate(action)
            logger.debug(f"No temporary action found with ID: {action_id}")
            return None

    @staticmethod
    async def get_temporary_actions_by_user(user_id: int) -> list[TemporaryActionSchema]:
        """
        Get all temporary actions for a specific user.

        Args:
            user_id: The Discord user ID

        Returns:
            List of TemporaryActionSchema objects
        """
        logger.debug(f"Getting temporary actions for user with ID: {user_id}")
        async with get_db_session() as session:
            repository = TemporaryActionRepository(session)
            actions: list[TemporaryAction] = await repository.get_by_user_id(user_id)
            logger.debug(f"Found {len(actions)} temporary actions for user {user_id}")
            return [TemporaryActionSchema.model_validate(action) for action in actions]

    @staticmethod
    async def get_temporary_actions_by_type(punishment_type: str) -> list[TemporaryActionSchema]:
        """
        Get all temporary actions of a specific type.

        Args:
            punishment_type: The type of punishment (e.g., "ban", "mute")

        Returns:
            List of TemporaryActionSchema objects
        """
        logger.debug(f"Getting temporary actions of type: {punishment_type}")
        async with get_db_session() as session:
            repository = TemporaryActionRepository(session)
            actions: list[TemporaryAction] = await repository.get_by_punishment_type(
                punishment_type
            )
            logger.debug(f"Found {len(actions)} temporary actions of type {punishment_type}")
            return [TemporaryActionSchema.model_validate(action) for action in actions]

    @staticmethod
    async def get_all_temporary_actions() -> list[TemporaryActionSchema]:
        """
        Get all temporary actions.

        Returns:
            List of all TemporaryActionSchema objects
        """
        logger.debug("Getting all temporary actions")
        async with get_db_session() as session:
            repository = TemporaryActionRepository(session)
            actions: list[TemporaryAction] = await repository.get_all()
            logger.debug(f"Found {len(actions)} total temporary actions")
            return [TemporaryActionSchema.model_validate(action) for action in actions]

    @staticmethod
    async def create_or_update_temporary_action(
        action_data: TemporaryActionSchema,
    ) -> TemporaryActionSchema:
        """
        Create a new temporary action or update if it already exists.

        Args:
            action_data: The temporary action data to create or update

        Returns:
            The created/updated temporary action schema
        """
        logger.debug(f"Creating or updating temporary action: {action_data}")
        async with get_db_session() as session:
            repository = TemporaryActionRepository(session)

            # Check if we have an ID and if it exists in the database
            if action_data.id is not None:
                logger.debug(f"Checking if temporary action with ID {action_data.id} exists")
                existing_action: TemporaryAction | None = await repository.get_by_id(action_data.id)
                if existing_action:
                    logger.debug(f"Updating existing temporary action with ID: {action_data.id}")
                    updated_action: TemporaryAction | None = await repository.update(
                        action_data.id, action_data
                    )
                    logger.debug(f"Updated temporary action: {updated_action}")
                    return TemporaryActionSchema.model_validate(updated_action)

            # If no ID or record doesn't exist, create a new one
            logger.debug("Creating new temporary action")
            new_action: TemporaryAction = await repository.create(action_data)
            logger.debug(f"Created new temporary action with ID: {new_action.id}")
            return TemporaryActionSchema.model_validate(new_action)

    @staticmethod
    async def delete_temporary_action(action_id: int) -> bool:
        """
        Delete a temporary action by ID.

        Args:
            action_id: The temporary action ID

        Returns:
            True if the action was deleted, False otherwise
        """
        logger.debug(f"Attempting to delete temporary action with ID: {action_id}")
        async with get_db_session() as session:
            repository = TemporaryActionRepository(session)
            result = await repository.delete(action_id)
            logger.debug(f"Deletion result for temporary action {action_id}: {result}")
            return result

    @staticmethod
    async def get_filtered_temporoary_action_logs(
        user_id: int | None = None,
        staff_id: int | None = None,
        punishment_type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        get_latest: bool = False,
    ) -> None | TemporaryActionSchema | list[TemporaryActionSchema]:
        """
        Get punishment logs with custom filtering.

        Args:
            user_id: Optional filter by user ID
            staff_id: Optional filter by staff ID
            punishment_type: Optional filter by punishment type
            limit: Optional limit on the number of results
            offset: Optional offset for pagination
            get_latest: If True, returns only the most recent log (not a list)

        Returns:
            Single TemporaryActionSchema if get_latest=True, otherwise list of TemporaryActionSchema objects.
            If get_latest=True and no logs found, returns None.
        """
        logger.debug(
            f"Getting filtered punishment logs with filters: "
            f"user_id={user_id}, staff_id={staff_id}, "
            f"punishment_type={punishment_type}, limit={limit}, offset={offset}, "
            f"get_latest={get_latest}"
        )

        async with get_db_session() as session:
            repository = TemporaryActionRepository(session)

            if get_latest:
                log = await repository.get_latest_filtered_log(
                    user_id=user_id, staff_id=staff_id, punishment_type=punishment_type
                )

                if log:
                    logger.debug(f"Found latest punishment log with ID: {log.id}")
                    return TemporaryActionSchema.model_validate(log)
                else:
                    logger.debug("No matching logs found for latest filter")
                    return None
            else:
                logs = await repository.get_filtered_logs(
                    user_id=user_id,
                    staff_id=staff_id,
                    punishment_type=punishment_type,
                    limit=limit,
                    offset=offset,
                )

                logger.debug(f"Found {len(logs)} punishment logs matching filters")
                return [TemporaryActionSchema.model_validate(log) for log in logs]
