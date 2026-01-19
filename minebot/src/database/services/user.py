from logging import Logger

from database import get_db_session
from database.models import User
from database.repositories import UserRepository
from database.schemas import UserSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class UserService:
    """
    Service for user-related business logic and operations.
    """

    @staticmethod
    async def get_user(user_id: int) -> UserSchema | None:
        """
        Get a user by ID.

        Args:
            user_id: The Discord user ID

        Returns:
            UserSchema or None if the user doesn't exist
        """
        logger.debug(f"Getting user with ID: {user_id}")
        async with get_db_session() as session:
            repository = UserRepository(session)
            user: User | None = await repository.get_by_id(user_id)
            if user:
                logger.debug(f"Found user with ID {user_id}: {user}")
                return UserSchema.model_validate(user)
            logger.debug(f"No user found with ID: {user_id}")
            return None

    @staticmethod
    async def get_user_by_minecraft_username(minecraft_username: str) -> UserSchema | None:
        """
        Get a user by their Minecraft username.

        Args:
            minecraft_username: The Minecraft username

        Returns:
            UserSchema or None if the user doesn't exist
        """
        logger.debug(f"Getting user with Minecraft username: {minecraft_username}")
        async with get_db_session() as session:
            repository = UserRepository(session)
            user: User | None = await repository.get_by_minecraft_username(minecraft_username)
            if user:
                logger.debug(f"Found user with Minecraft username {minecraft_username}: {user}")
                return UserSchema.model_validate(user)
            logger.debug(f"No user found with Minecraft username: {minecraft_username}")
            return None

    @staticmethod
    async def create_or_update_user(
        user_data: UserSchema, preserve_existing: bool = True
    ) -> UserSchema:
        """
        Create a new user or update if it already exists.

        Args:
            user_data: The user data to create or update
            preserve_existing: If True (default), preserve existing non-null values when updating

        Returns:
            The created/updated user schema
        """
        logger.debug(f"Creating or updating user: {user_data}")
        async with get_db_session() as session:
            repository = UserRepository(session)
            existing_user: User | None = await repository.get_by_id(user_data.id)

            if not existing_user:
                logger.debug(f"Creating new user with ID: {user_data.id}")
                new_user: User = await repository.create(user_data)
                logger.debug(f"Created new user: {new_user}")
                return UserSchema.model_validate(new_user)

            # Handle existing user update
            logger.debug(f"Updating existing user with ID: {user_data.id}")

            # If preserving existing values, only update fields if they're null
            if preserve_existing:
                user_data = UserSchema(
                    id=user_data.id,
                    locale=user_data.locale,
                    minecraft_username=user_data.minecraft_username
                    or existing_user.minecraft_username,
                    minecraft_uuid=user_data.minecraft_uuid or existing_user.minecraft_uuid,
                    reward_inventory=user_data.reward_inventory or existing_user.reward_inventory,
                )

            updated_user: User | None = await repository.update(user_data.id, user_data)

            if updated_user != existing_user:
                logger.debug(f"Updated user: {updated_user}")
            else:
                logger.debug("No changes were made to the user")

            return UserSchema.model_validate(updated_user)

    @staticmethod
    async def delete_user(user_id: int) -> bool:
        """
        Delete a user by ID.

        Args:
            user_id: The Discord user ID

        Returns:
            True if the user was deleted, False otherwise
        """
        logger.debug(f"Attempting to delete user with ID: {user_id}")
        async with get_db_session() as session:
            repository = UserRepository(session)
            result = await repository.delete(user_id)
            logger.debug(f"Deletion result for user {user_id}: {result}")
            return result

    @staticmethod
    async def add_item(user_id: int, server: str, items: str | list[str]) -> bool:
        """
        Add an item to the user's inventory.

        Args:
            user_id: The Discord user ID
            server: The server name
            items: The item(s) to add

        Returns:
            True if the item was added, False otherwise
        """
        logger.debug(f"Adding item(s) to inventory for user {user_id}: {items}")
        async with get_db_session() as session:
            repository = UserRepository(session)
            result: bool = await repository.add_item(user_id, server, items)
            logger.debug(f"Add item result for user {user_id}: {result}")
            return result
