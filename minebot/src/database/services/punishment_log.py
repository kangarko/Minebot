from logging import Logger

from database import get_db_session
from database.models import PunishmentLog
from database.repositories import PunishmentLogRepository
from database.schemas import PunishmentLogSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class PunishmentLogService:
    """
    Service for punishment log-related business logic and operations.
    """

    @staticmethod
    async def get_punishment_log(log_id: int) -> PunishmentLogSchema | None:
        """
        Get a punishment log by ID.

        Args:
            log_id: The punishment log ID

        Returns:
            PunishmentLogSchema or None if the log doesn't exist
        """
        logger.debug(f"Getting punishment log with ID: {log_id}")
        async with get_db_session() as session:
            repository = PunishmentLogRepository(session)
            log: PunishmentLog | None = await repository.get_by_id(log_id)
            if log:
                logger.debug(f"Found punishment log: {log}")
                return PunishmentLogSchema.model_validate(log)
            logger.debug(f"No punishment log found with ID: {log_id}")
            return None

    @staticmethod
    async def get_punishment_logs_by_user(user_id: int) -> list[PunishmentLogSchema]:
        """
        Get all punishment logs for a specific user.

        Args:
            user_id: The Discord user ID

        Returns:
            List of PunishmentLogSchema objects
        """
        logger.debug(f"Getting punishment logs for user with ID: {user_id}")
        async with get_db_session() as session:
            repository = PunishmentLogRepository(session)
            logs: list[PunishmentLog] = await repository.get_by_user_id(user_id)
            logger.debug(f"Found {len(logs)} punishment logs for user {user_id}")
            return [PunishmentLogSchema.model_validate(log) for log in logs]

    @staticmethod
    async def get_punishment_logs_by_staff(staff_id: int) -> list[PunishmentLogSchema]:
        """
        Get all punishment logs issued by a specific staff.

        Args:
            staff_id: The Discord moderator ID

        Returns:
            List of PunishmentLogSchema objects
        """
        logger.debug(f"Getting punishment logs for staff with ID: {staff_id}")
        async with get_db_session() as session:
            repository = PunishmentLogRepository(session)
            logs: list[PunishmentLog] = await repository.get_by_staff_id(staff_id)
            logger.debug(f"Found {len(logs)} punishment logs for staff {staff_id}")
            return [PunishmentLogSchema.model_validate(log) for log in logs]

    @staticmethod
    async def get_punishment_logs_by_type(punishment_type: str) -> list[PunishmentLogSchema]:
        """
        Get all punishment logs of a specific type.

        Args:
            punishment_type: The type of punishment (e.g., "ban", "mute")

        Returns:
            List of PunishmentLogSchema objects
        """
        logger.debug(f"Getting punishment logs of type: {punishment_type}")
        async with get_db_session() as session:
            repository = PunishmentLogRepository(session)
            logs: list[PunishmentLog] = await repository.get_by_punishment_type(punishment_type)
            logger.debug(f"Found {len(logs)} punishment logs of type {punishment_type}")
            return [PunishmentLogSchema.model_validate(log) for log in logs]

    @staticmethod
    async def create_or_update_punishment_log(log_data: PunishmentLogSchema) -> PunishmentLogSchema:
        """
        Create a new punishment log or update if it already exists.

        Args:
            log_data: The punishment log data to create or update

        Returns:
            The created/updated punishment log schema
        """
        logger.debug(f"Creating or updating punishment log: {log_data}")
        async with get_db_session() as session:
            repository = PunishmentLogRepository(session)

            # Check if we have an ID and if it exists in the database
            if log_data.id is not None:
                logger.debug(f"Checking if punishment log with ID {log_data.id} exists")
                existing_log: PunishmentLog | None = await repository.get_by_id(log_data.id)
                if existing_log:
                    logger.debug(f"Updating existing punishment log with ID: {log_data.id}")
                    updated_log: PunishmentLog | None = await repository.update(
                        log_data.id, log_data
                    )
                    logger.debug(f"Updated punishment log: {updated_log}")
                    return PunishmentLogSchema.model_validate(updated_log)

            # If no ID or record doesn't exist, create a new one
            logger.debug("Creating new punishment log")
            new_log: PunishmentLog = await repository.create(log_data)
            logger.debug(f"Created new punishment log with ID: {new_log.id}")
            return PunishmentLogSchema.model_validate(new_log)

    @staticmethod
    async def delete_punishment_log(log_id: int) -> bool:
        """
        Delete a punishment log by ID.

        Args:
            log_id: The punishment log ID

        Returns:
            True if the log was deleted, False otherwise
        """
        logger.debug(f"Attempting to delete punishment log with ID: {log_id}")
        async with get_db_session() as session:
            repository = PunishmentLogRepository(session)
            result = await repository.delete(log_id)
            logger.debug(f"Deletion result for punishment log {log_id}: {result}")
            return result

    @staticmethod
    async def get_filtered_punishment_logs(
        user_id: int | None = None,
        staff_id: int | None = None,
        punishment_type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        get_latest: bool = False,
    ) -> None | PunishmentLogSchema | list[PunishmentLogSchema]:
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
            Single PunishmentLogSchema if get_latest=True, otherwise list of PunishmentLogSchema objects.
            If get_latest=True and no logs found, returns None.
        """
        logger.debug(
            f"Getting filtered punishment logs with filters: "
            f"user_id={user_id}, staff_id={staff_id}, "
            f"punishment_type={punishment_type}, limit={limit}, offset={offset}, "
            f"get_latest={get_latest}"
        )

        async with get_db_session() as session:
            repository = PunishmentLogRepository(session)

            if get_latest:
                log = await repository.get_latest_filtered_log(
                    user_id=user_id, staff_id=staff_id, punishment_type=punishment_type
                )

                if log:
                    logger.debug(f"Found latest punishment log with ID: {log.id}")
                    return PunishmentLogSchema.model_validate(log)
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
                return [PunishmentLogSchema.model_validate(log) for log in logs]
