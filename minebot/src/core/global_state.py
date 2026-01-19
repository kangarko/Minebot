import hikari
import lightbulb

from data_types import TimedDict, TimedSet


class BotState:
    """Manages the Discord bot client state."""

    _bot: hikari.GatewayBot | None = None
    _client: lightbulb.Client | None = None
    _member: hikari.Member | None = None

    @staticmethod
    def set_bot(bot: hikari.GatewayBot) -> None:
        """Set the Hikari bot instance."""
        BotState._bot = bot

    @staticmethod
    def get_bot() -> hikari.GatewayBot:
        """Get the Hikari bot instance."""
        if BotState._bot is None:
            raise ValueError("Bot has not been set.")
        return BotState._bot

    @staticmethod
    def set_client(client: lightbulb.Client) -> None:
        """Set the Lightbulb client instance."""
        BotState._client = client

    @staticmethod
    def get_client() -> lightbulb.Client:
        """Get the Lightbulb client instance."""
        if BotState._client is None:
            raise ValueError("Client has not been set.")
        return BotState._client

    @staticmethod
    def set_member(member: hikari.Member) -> None:
        """Set the bot's member instance."""
        BotState._member = member

    @staticmethod
    def get_member() -> hikari.Member:
        """Get the bot's member instance."""
        if BotState._member is None:
            raise ValueError("Member has not been set.")
        return BotState._member


class GuildState:
    _locale: hikari.Locale | None = None
    _booster_role: hikari.Role | None = None

    @staticmethod
    def set_locale(locale: hikari.Locale) -> None:
        """Set the locale for the guild."""
        GuildState._locale = locale

    @staticmethod
    def get_locale() -> hikari.Locale:
        """Get the locale for the guild."""
        if GuildState._locale is None:
            raise ValueError("Locale has not been set.")
        return GuildState._locale

    @staticmethod
    def set_booster_role(role: hikari.Role | None) -> None:
        """Set the booster role for the guild."""
        GuildState._booster_role = role

    @staticmethod
    def get_booster_role() -> hikari.Role | None:
        """Get the booster role for the guild."""
        return GuildState._booster_role


class CommandState:
    """Manages command synchronization state."""

    _sync_state: dict[str, dict[str, bool]] = {}

    @staticmethod
    def add_sync_state(
        command_name: str, minecraft_to_discord: bool, discord_to_minecraft: bool
    ) -> None:
        """Add a command to the synchronization state."""
        CommandState._sync_state[command_name] = {
            "minecraft_to_discord": minecraft_to_discord,
            "discord_to_minecraft": discord_to_minecraft,
        }

    @staticmethod
    def get_command_sync_state(command_name: str) -> dict[str, bool] | None:
        """Get the synchronization state for a command."""
        return CommandState._sync_state.get(command_name)

    @staticmethod
    def is_minecraft_to_discord(command_name: str) -> bool:
        """Check if the command syncs from Minecraft to Discord."""
        return CommandState._sync_state.get(command_name, {}).get("minecraft_to_discord", False)

    @staticmethod
    def is_discord_to_minecraft(command_name: str) -> bool:
        """Check if the command syncs from Discord to Minecraft."""
        return CommandState._sync_state.get(command_name, {}).get("discord_to_minecraft", False)


class MinecraftState:
    """Manages Minecraft-related state data."""

    _minecraft_servers: list[str] = []
    _online_players: TimedSet[str] = TimedSet[str](10)
    _player_uuids: TimedDict[str, str] = TimedDict[str, str](10)
    _player_servers: TimedDict[str, str] = TimedDict[str, str](10)

    @staticmethod
    def add_server(servers: str | list[str]) -> None:
        """Add Minecraft server(s) to the list."""
        if isinstance(servers, str):
            MinecraftState._minecraft_servers.append(servers)
        else:
            MinecraftState._minecraft_servers.extend(servers)

    @staticmethod
    def get_servers() -> list[str]:
        """Get the list of Minecraft servers."""
        return (
            MinecraftState._minecraft_servers.copy()
        )  # Return a copy to prevent external modification

    @staticmethod
    def contains_server(server: str) -> bool:
        """Check if a Minecraft server is in the list."""
        return server in MinecraftState._minecraft_servers

    @staticmethod
    def clear_servers() -> None:
        """Clear the list of Minecraft servers."""
        MinecraftState._minecraft_servers.clear()

    @staticmethod
    def add_online_player(player: str) -> None:
        """Add a player to the online players set."""
        MinecraftState._online_players.add(player)

    @staticmethod
    def check_player_online(player: str) -> bool:
        """Check if a player is online."""
        return MinecraftState._online_players.contains(player)

    @staticmethod
    def add_player_uuid(username: str, uuid: str) -> None:
        """Add a player's UUID to the dictionary."""
        MinecraftState._player_uuids[username] = uuid

    @staticmethod
    def get_player_uuid(username: str) -> str | None:
        """Get a player's UUID by username."""
        return MinecraftState._player_uuids.get(username)

    @staticmethod
    def add_player_server(username: str, server: str) -> None:
        """Add a player's server to the dictionary."""
        MinecraftState._player_servers[username] = server

    @staticmethod
    def get_player_server(username: str) -> str | None:
        """Get a player's server by username."""
        return MinecraftState._player_servers.get(username)


class TasksState:
    """Manages scheduled tasks for the bot."""

    _tasks: dict[tuple[int, str], lightbulb.Task] = {}

    @staticmethod
    def _get_key(user: hikari.User | int, punishment_type: str) -> tuple[int, str]:
        """Convert user to ID and create a task dictionary key."""
        user_id = user.id if isinstance(user, hikari.User) else user
        return (user_id, punishment_type)

    @staticmethod
    def has_task(user: hikari.User | int, punishment_type: str) -> bool:
        """Check if a task exists for the given user and punishment type."""
        return TasksState._get_key(user, punishment_type) in TasksState._tasks

    @staticmethod
    def get_task(user: hikari.User | int, punishment_type: str) -> lightbulb.Task | None:
        """Get a task for a user and punishment type if it exists."""
        key = TasksState._get_key(user, punishment_type)
        return TasksState._tasks.get(key)

    @staticmethod
    def add_task(user: hikari.User | int, punishment_type: str, task: lightbulb.Task) -> bool:
        """
        Add a task to the state.

        Args:
            user: User object or user ID
            punishment_type: Type of punishment associated with the task
            task: The scheduled task object

        Returns:
            bool: True if task was added, False if a task already exists
        """
        key = TasksState._get_key(user, punishment_type)
        if key in TasksState._tasks:
            return False
        TasksState._tasks[key] = task
        return True

    @staticmethod
    def add_or_refresh_task(
        user: hikari.User | int, punishment_type: str, task: lightbulb.Task
    ) -> None:
        """Add a new task or refresh an existing one without raising errors."""
        key = TasksState._get_key(user, punishment_type)
        # Cancel existing task if present
        existing_task = TasksState._tasks.get(key)
        if existing_task and not existing_task.cancelled:
            existing_task.cancel()
        # Add new task
        TasksState._tasks[key] = task

    @staticmethod
    def refresh_task(user: hikari.User | int, punishment_type: str, task: lightbulb.Task) -> bool:
        """
        Refresh an existing task for a user and punishment type.

        Returns:
            bool: True if task was refreshed, False if task doesn't exist
        """
        key = TasksState._get_key(user, punishment_type)
        if key not in TasksState._tasks:
            return False
        TasksState._tasks[key] = task
        return True

    @staticmethod
    def cancel_task(user: hikari.User | int, punishment_type: str) -> bool:
        """
        Cancel a task for a user and punishment type.

        Returns:
            bool: True if task was cancelled, False if task doesn't exist
        """
        key = TasksState._get_key(user, punishment_type)
        if key not in TasksState._tasks:
            return False

        task = TasksState._tasks[key]
        if not task.cancelled:
            task.cancel()
        del TasksState._tasks[key]
        return True

    @staticmethod
    def remove_task(user: hikari.User | int, punishment_type: str) -> bool:
        """
        Safely remove a task entry without canceling it.

        Useful when a task completes naturally but needs to be removed from state tracking.

        Args:
            user: User object or user ID
            punishment_type: Type of punishment associated with the task

        Returns:
            bool: True if task was removed, False if task doesn't exist
        """
        key = TasksState._get_key(user, punishment_type)
        if key not in TasksState._tasks:
            return False

        del TasksState._tasks[key]
        return True

    @staticmethod
    def get_all_tasks_for_user(user: hikari.User | int) -> dict[str, lightbulb.Task]:
        """Get all tasks associated with a specific user."""
        user_id = user.id if isinstance(user, hikari.User) else user
        return {
            punishment_type: task
            for (uid, punishment_type), task in TasksState._tasks.items()
            if uid == user_id
        }


class GlobalState:
    """Global state manager for the bot."""

    bot: BotState = BotState()
    guild: GuildState = GuildState()
    commands: CommandState = CommandState()
    minecraft: MinecraftState = MinecraftState()
    tasks: TasksState = TasksState()
