from logging import Logger

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TemporaryAction
from database.schemas import TemporaryActionSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class TemporaryActionRepository:
    """
    Repository for handling TemporaryAction database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with a database session."""
        self.session: AsyncSession = session
        logger.debug("Initialized TemporaryActionRepository with session")

    async def get_by_id(self, action_id: int) -> TemporaryAction | None:
        """Get a temporary action by ID."""
        logger.debug(f"Fetching temporary action with ID: {action_id}")
        result: Result[tuple[TemporaryAction]] = await self.session.execute(
            select(TemporaryAction).where(TemporaryAction.id == action_id)
        )
        action = result.scalars().first()
        logger.debug(f"Temporary action with ID {action_id} found: {action is not None}")
        return action

    async def get_by_user_id(self, user_id: int) -> list[TemporaryAction]:
        """Get all temporary actions for a specific user."""
        logger.debug(f"Fetching temporary actions for user ID: {user_id}")
        result: Result[tuple[TemporaryAction]] = await self.session.execute(
            select(TemporaryAction).where(TemporaryAction.user_id == user_id)
        )
        actions = list(result.scalars().all())
        logger.debug(f"Found {len(actions)} temporary actions for user ID: {user_id}")
        return actions

    async def get_by_punishment_type(self, punishment_type: str) -> list[TemporaryAction]:
        """Get all temporary actions of a specific type."""
        logger.debug(f"Fetching temporary actions of type: {punishment_type}")
        result: Result[tuple[TemporaryAction]] = await self.session.execute(
            select(TemporaryAction).where(TemporaryAction.punishment_type == punishment_type)
        )
        actions = list(result.scalars().all())
        logger.debug(f"Found {len(actions)} temporary actions of type: {punishment_type}")
        return actions

    async def get_all(self) -> list[TemporaryAction]:
        """Get all temporary actions."""
        logger.debug("Fetching all temporary actions")
        result: Result[tuple[TemporaryAction]] = await self.session.execute(select(TemporaryAction))
        actions = list(result.scalars().all())
        logger.debug(f"Found {len(actions)} temporary actions in total")
        return actions

    async def create(self, action_schema: TemporaryActionSchema) -> TemporaryAction:
        """Create a new temporary action."""
        logger.debug(
            f"Creating new temporary action for user ID: {action_schema.user_id}, type: {action_schema.punishment_type}"
        )
        # Convert schema to model
        temporary_action = TemporaryAction(
            id=action_schema.id,
            user_id=action_schema.user_id,
            punishment_type=action_schema.punishment_type,
            created_at=action_schema.created_at,
            expires_at=action_schema.expires_at,
            refresh_at=action_schema.refresh_at,
        )

        self.session.add(temporary_action)
        await self.session.flush()
        logger.debug(f"Created temporary action with details: {vars(temporary_action)}")
        return temporary_action

    async def update(
        self, action_id: int, action_schema: TemporaryActionSchema
    ) -> TemporaryAction | None:
        """Update an existing temporary action."""
        logger.debug(f"Attempting to update temporary action ID: {action_id}")
        temporary_action: TemporaryAction | None = await self.get_by_id(action_id)
        if not temporary_action:
            logger.debug(f"Temporary action ID {action_id} not found for update")
            return None

        # Update fields
        temporary_action.user_id = action_schema.user_id
        temporary_action.punishment_type = action_schema.punishment_type
        temporary_action.created_at = action_schema.created_at
        temporary_action.expires_at = action_schema.expires_at
        temporary_action.refresh_at = action_schema.refresh_at

        await self.session.flush()
        logger.debug(f"Updated temporary action with details: {vars(temporary_action)}")
        return temporary_action

    async def delete(self, action_id: int) -> bool:
        """Delete a temporary action by ID."""
        logger.debug(f"Attempting to delete temporary action ID: {action_id}")
        temporary_action: TemporaryAction | None = await self.get_by_id(action_id)
        if not temporary_action:
            logger.debug(f"Temporary action ID {action_id} not found for deletion")
            return False

        await self.session.delete(temporary_action)
        await self.session.flush()
        return True

    async def get_latest_filtered_log(
        self,
        user_id: int | None = None,
        staff_id: int | None = None,
        punishment_type: str | None = None,
    ) -> TemporaryAction | None:
        """
        Get the latest (highest ID) punishment log matching the filters.

        Args:
            user_id: Optional filter by user ID
            staff_id: Optional filter by staff ID
            punishment_type: Optional filter by punishment type

        Returns:
            A single PunishmentLog object or None if no matching logs
        """
        from sqlalchemy import desc, select

        logger.debug(
            f"Getting latest punishment log with filters: user_id={user_id}, "
            f"staff_id={staff_id}, punishment_type={punishment_type}"
        )

        query = select(TemporaryAction)

        # Apply filters
        if user_id is not None:
            query = query.where(TemporaryAction.user_id == user_id)

        if staff_id is not None:
            query = query.where(TemporaryAction.staff_id == staff_id)

        if punishment_type is not None:
            query = query.where(TemporaryAction.punishment_type == punishment_type)

        # Get the highest ID (most recent log)
        query = query.order_by(desc(TemporaryAction.id)).limit(1)

        result = await self.session.execute(query)
        log = result.scalars().first()

        if log:
            logger.debug(f"Found latest log with ID: {log.id}")
        else:
            logger.debug("No matching logs found")

        return log

    async def get_filtered_logs(
        self,
        user_id: int | None = None,
        staff_id: int | None = None,
        punishment_type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[TemporaryAction]:
        """
        Get punishment logs with custom filtering.

        Args:
            user_id: Optional filter by user ID
            staff_id: Optional filter by staff ID
            punishment_type: Optional filter by punishment type
            limit: Optional limit on the number of results
            offset: Optional offset for pagination

        Returns:
            List of PunishmentLog objects matching the criteria
        """
        from sqlalchemy import desc, select

        logger.debug(
            f"Building filtered query with parameters: user_id={user_id}, "
            f"staff_id={staff_id}, punishment_type={punishment_type}"
        )

        query = select(TemporaryAction)

        # Apply filters
        if user_id is not None:
            query = query.where(TemporaryAction.user_id == user_id)

        if staff_id is not None:
            query = query.where(TemporaryAction.staff_id == staff_id)

        if punishment_type is not None:
            query = query.where(TemporaryAction.punishment_type == punishment_type)

        # Order by ID descending (newest first)
        query = query.order_by(desc(TemporaryAction.id))

        # Apply pagination
        if limit is not None:
            query = query.limit(limit)

        if offset is not None:
            query = query.offset(offset)

        logger.debug("Executing filtered punishment logs query")
        result = await self.session.execute(query)
        logs = list(result.scalars().all())
        logger.debug(f"Found {len(logs)} logs matching the filter criteria")

        return logs
