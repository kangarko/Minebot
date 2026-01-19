from logging import Logger

from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from database.models import User
from database.schemas import UserSchema
from debug import get_logger

logger: Logger = get_logger(__name__)


class UserRepository:
    """
    Repository for handling User database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with a database session."""
        self.session: AsyncSession = session
        logger.debug("Initialized UserRepository with session")

    async def get_by_id(self, user_id: int) -> User | None:
        """Get a user by ID."""
        logger.debug(f"Fetching user with ID: {user_id}")
        result: Result[tuple[User]] = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()
        logger.debug(f"User with ID {user_id} found: {user is not None}")
        return user

    async def get_by_minecraft_username(self, minecraft_username: str) -> User | None:
        """Get a user by their Minecraft username."""
        logger.debug(f"Fetching user with Minecraft username: {minecraft_username}")
        result: Result[tuple[User]] = await self.session.execute(
            select(User).where(User.minecraft_username == minecraft_username)
        )
        user = result.scalars().first()
        logger.debug(f"User with Minecraft username {minecraft_username} found: {user is not None}")
        return user

    async def create(self, user_schema: UserSchema) -> User:
        """Create a new user."""
        logger.debug(
            f"Creating new user with ID: {user_schema.id}, minecraft username: {user_schema.minecraft_username}"
        )
        # Convert schema to model
        user = User(
            id=user_schema.id,
            locale=user_schema.locale,
            minecraft_username=user_schema.minecraft_username,
            minecraft_uuid=user_schema.minecraft_uuid,
            reward_inventory=user_schema.reward_inventory,
        )

        self.session.add(user)
        await self.session.flush()
        logger.debug(f"Created user with details: {vars(user)}")
        return user

    async def update(self, user_id: int, user_schema: UserSchema) -> User | None:
        """Update an existing user."""
        logger.debug(f"Attempting to update user with ID: {user_id}")
        user: User | None = await self.get_by_id(user_id)
        if not user:
            logger.debug(f"User with ID {user_id} not found for update")
            return None

        # Check if there are any changes
        has_changes: bool = (
            user.locale != user_schema.locale
            or user.minecraft_username != user_schema.minecraft_username
            or user.minecraft_uuid != user_schema.minecraft_uuid
            or user.reward_inventory != user_schema.reward_inventory
        )

        if not has_changes:
            logger.debug(f"No changes detected for user with ID: {user_id}")
            return user

        # Update fields
        user.locale = user_schema.locale
        user.minecraft_username = user_schema.minecraft_username
        user.minecraft_uuid = user_schema.minecraft_uuid
        user.reward_inventory = user_schema.reward_inventory

        await self.session.flush()
        logger.debug(f"Updated user with details: {vars(user)}")
        return user

    async def delete(self, user_id: int) -> bool:
        """Delete a user by ID."""
        logger.debug(f"Attempting to delete user with ID: {user_id}")
        user: User | None = await self.get_by_id(user_id)
        if not user:
            logger.debug(f"User with ID {user_id} not found for deletion")
            return False

        await self.session.delete(user)
        await self.session.flush()
        logger.debug(f"Successfully deleted user with ID: {user_id}")
        return True

    async def add_item(self, user_id: int, server: str, items: str | list[str]) -> bool:
        """
        Add one or more items to the user's inventory for a specific server.

        Args:
            user_id: The Discord user ID
            server: The server name
            items: The item(s) to add (can be a string or a list of strings)

        Returns:
            True if the item(s) were added successfully, False otherwise
        """
        logger.debug(f"Adding item(s) to user {user_id} on server {server}: {items}")

        user: User | None = await self.get_by_id(user_id)
        if not user:
            logger.debug(f"User with ID {user_id} not found for adding items")
            return False

        # Normalize input to always be a list
        item_list: list[str] = [items] if isinstance(items, str) else items

        # Initialize inventory if None or get existing
        data: dict[str, list] = user.reward_inventory or {}

        # Get username and UUID once for all replacements
        username: str = user.minecraft_username or ""
        uuid: str = user.minecraft_uuid or ""

        # Process all items in one pass with more efficient replacement
        processed_items: list[str] = [
            item.replace("{minecraft_username}", username).replace("{minecraft_uuid}", uuid)
            if isinstance(item, str)
            else item
            for item in item_list
        ]

        # Update inventory efficiently
        if server not in data:
            data[server] = processed_items
        else:
            data[server].extend(processed_items)

        user.reward_inventory = data
        flag_modified(user, "reward_inventory")
        await self.session.flush()

        logger.debug(
            f"Added items to user {user_id} inventory on server {server}: {processed_items}"
        )
        return True
