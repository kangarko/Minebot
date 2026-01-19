import os
from logging import Logger
from pathlib import Path
from typing import cast

import chat_exporter
import hikari
import lightbulb
from github import Auth, Github
from github.GithubException import GithubException
from github.Repository import Repository

from core import GlobalState
from database.schemas import TicketChannelSchema, TicketInfoSchema
from database.services import TicketChannelService, TicketInfoService
from debug import get_logger
from helper import MessageHelper
from model import (
    MessageKeys,
    ModalKeys,
    SecretKeys,
    SystemsKeys,
    TicketCreationMethod,
    TicketCreationStyle,
    TicketTranscriptFormat,
    TicketTranscriptUploadMethod,
)
from model.schemas import (
    BasicTicketModal,
    ChannelTicketCategory,
    DiscordMessage,
    GithubTicketTranscription,
    ThreadTicketCategory,
    TicketCreation,
    TicketSystem,
    TicketTranscription,
)
from settings import Localization, Settings

logger: Logger = get_logger(__name__)

# Type definitions for cleaner code
CategoryType = ChannelTicketCategory | ThreadTicketCategory
ChannelType = hikari.TextableGuildChannel | hikari.GuildTextChannel | hikari.GuildThreadChannel


class TicketHelper:
    """
    Helper class for ticket system operations in Discord servers.

    This class manages the creation, configuration, and management of support tickets,
    including transcript generation and archival. It supports both channel-based and
    thread-based ticket systems with customizable permissions and categories.
    """

    # Cache variables
    _client: lightbulb.Client | None = None
    _guild_id: int | None = None
    _everyone_overwrites: hikari.PermissionOverwrite | None = None

    # Configuration storage
    _system_enabled: bool = False
    _categories: dict[str, CategoryType] = {}
    _creation: TicketCreation | None = None
    _transcript: TicketTranscription | None = None
    _startup_channel: hikari.TextableGuildChannel | None = None
    _log_channel: hikari.TextableGuildChannel | None = None
    _creation_method: TicketCreationMethod | None = None
    _creation_style: TicketCreationStyle | None = None
    _transcript_file_format: TicketTranscriptFormat | None = None
    _transcript_upload_method: TicketTranscriptUploadMethod | None = None
    _max_ticket_per_user: int | None = None

    # Github repository for transcript upload
    _transcript_github_repo: Repository | None = None
    _transcript_github_repo_branch: str | None = None

    @classmethod
    def _get_client(cls) -> lightbulb.Client:
        """Get and cache the bot client instance if not already cached."""
        if cls._client is None:
            cls._client = GlobalState.bot.get_client()
            logger.debug("Bot instance cached")
        return cls._client

    @classmethod
    async def initialize(cls) -> bool:
        """
        Initialize ticket system settings from configuration.

        Returns:
            bool: True if initialization was successful, False otherwise
        """
        from helper import ChannelHelper

        try:
            system_data: TicketSystem | None = Settings.get(SystemsKeys.TICKET)

            if system_data is None:
                logger.debug("[System: ticket] Ticket system is not enabled")
                return True

            # Load and validate localization data
            system_modals: dict[str, dict[str, BasicTicketModal]] = Localization.get(
                ModalKeys.TICKET_MODALS, locale="all"
            )
            system_creations: dict[str, dict[str, DiscordMessage]] = Localization.get(
                MessageKeys.systems.TICKET_SYSTEM_CREATIONS, locale="all"
            )

            # Ensure all categories exist in localization data for all locales
            categories = system_data.categories or {}
            for locale, data in system_modals.items():
                if missing := set(categories) - set(data):
                    raise RuntimeError(f"Missing categories in modals localization: {missing}")

            for locale, data in system_creations.items():
                if missing := set(categories) - set(data):
                    raise RuntimeError(f"Missing categories in creations localization: {missing}")

            # Set up required guild ID
            cls._guild_id = Settings.get(SecretKeys.DEFAULT_GUILD)
            if not cls._guild_id:
                raise RuntimeError("Default guild ID not configured")

            # Set up base permissions
            cls._everyone_overwrites = hikari.PermissionOverwrite(
                id=cls._guild_id,
                type=hikari.PermissionOverwriteType.ROLE,
                deny=hikari.Permissions.all_permissions(),
            )

            # Store configuration
            cls._system_enabled = True
            cls._categories = categories
            cls._creation = system_data.creation
            cls._transcript = system_data.transcript

            # Initialize log channel
            cls._log_channel = await ChannelHelper.fetch_channel(
                system_data.log, hikari.TextableGuildChannel
            )
            if not cls._log_channel:
                raise RuntimeError("Log channel not found in guild")

            # Detect settings from first category
            if not cls._categories:
                raise RuntimeError("No ticket categories configured")

            first_category = next(iter(cls._categories.values()))
            cls._creation_method = (
                TicketCreationMethod.CHANNEL
                if isinstance(first_category, ChannelTicketCategory)
                else TicketCreationMethod.THREAD
            )
            cls._creation_style = (
                TicketCreationStyle.BUTTON
                if first_category.category_button_style
                else TicketCreationStyle.DROPDOWN
            )

            # Set max tickets per user
            cls._max_ticket_per_user = system_data.creation.max_tickets_per_user

            # Initialize transcript settings
            await cls._initialize_transcript_settings()

            # Import ticket menu components
            from components.menus.ticket import TicketButtonMenu, TicketDropdownMenu

            # Select appropriate menu based on creation style
            if cls._creation_style == TicketCreationStyle.BUTTON:
                menu = TicketButtonMenu()
            elif cls._creation_style == TicketCreationStyle.DROPDOWN:
                menu = TicketDropdownMenu()
            else:
                raise RuntimeError(f"Unsupported ticket creation style: {cls._creation_style}")

            # Set up or recover ticket info
            await cls._setup_ticket_info(system_data, menu)

            menu.attach_persistent(cls._get_client(), timeout=None)

            # Import ticket inner menu
            from components.menus.ticket import TicketInnerMenu

            menu = TicketInnerMenu()

            menu.attach_persistent(cls._get_client(), timeout=None)

            logger.info(f"[System: ticket] Initialized with {len(cls._categories)} categories")
            return True

        except RuntimeError as e:
            raise RuntimeError(f"Failed to initialize ticket system: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize ticket system: {e}") from e

    @classmethod
    async def _setup_ticket_info(
        cls, system_data: TicketSystem, menu: lightbulb.components.Menu
    ) -> None:
        """Set up or recover ticket info from database."""
        info_channel = await TicketInfoService.get_ticket_by_id(1)

        if info_channel is None:
            # Create new ticket info if it doesn't exist
            await cls._create_new_ticket_info(system_data.creation.channel_id, menu)
        else:
            # Try to recover existing ticket info
            try:
                cls._startup_channel = await cls._fetch_and_verify_channel(
                    info_channel.channel_id, info_channel.message_id
                )
            except (hikari.NotFoundError, RuntimeError):
                # Recreate ticket info if channel or message not found
                await cls._create_new_ticket_info(system_data.creation.channel_id, menu)

    @classmethod
    async def _create_new_ticket_info(
        cls, channel_id: int, menu: lightbulb.components.Menu
    ) -> None:
        """Create a new ticket info entry with startup message."""
        message = await MessageHelper(MessageKeys.systems.TICKET_SYSTEM_STARTUP).send_to_channel(
            channel_id, components=menu
        )

        if not message:
            raise RuntimeError("Failed to send startup message to ticket channel")

        await TicketInfoService.create_or_update_ticket(
            TicketInfoSchema(id=1, channel_id=message.channel_id, message_id=message.id)
        )

        from helper import ChannelHelper

        cls._startup_channel = await ChannelHelper.fetch_channel(
            message.channel_id, hikari.TextableGuildChannel
        )

    @classmethod
    async def _fetch_and_verify_channel(
        cls, channel_id: int, message_id: int
    ) -> hikari.TextableGuildChannel:
        """Fetch and verify a channel and its message exist."""
        from helper import ChannelHelper

        channel = await ChannelHelper.fetch_channel(channel_id, hikari.TextableGuildChannel)
        if not channel:
            raise RuntimeError(f"Channel {channel_id} not found")

        await cls._get_client().rest.fetch_message(channel, message_id)
        return channel

    @classmethod
    async def _initialize_transcript_settings(cls) -> None:
        """Initialize transcript-related settings for ticket archiving."""
        if not cls._transcript:
            return

        # Determine transcript format based on file extension
        cls._transcript_file_format = (
            TicketTranscriptFormat.TEXT
            if cls._transcript.file_name.endswith(".txt")
            else TicketTranscriptFormat.HTML
        )

        # Determine upload method based on configuration type
        cls._transcript_upload_method = (
            TicketTranscriptUploadMethod.GITHUB
            if isinstance(cls._transcript.upload, GithubTicketTranscription)
            else TicketTranscriptUploadMethod.DISCORD
        )

        # Set up GitHub connection if using GitHub upload
        if cls._transcript_upload_method == TicketTranscriptUploadMethod.GITHUB:
            github_config = cast(GithubTicketTranscription, cls._transcript.upload)
            try:
                github = Github(auth=Auth.Token(github_config.token))
                cls._transcript_github_repo = github.get_repo(github_config.repository)
                cls._transcript_github_repo_branch = github_config.branch
                logger.debug(f"Connected to GitHub repo: {github_config.repository}")
            except GithubException as e:
                logger.error(f"Failed to connect to GitHub repository: {e}")
                # Continue without GitHub integration, will fall back to Discord upload

    @classmethod
    async def create_ticket_channel(
        cls, category: CategoryType, owner: hikari.User
    ) -> ChannelType | None:
        """
        Create a new ticket channel or thread based on the specified category.

        Args:
            category: The category configuration for the ticket
            owner: The user who will own the ticket

        Returns:
            The created channel/thread or None if creation failed
        """
        if not cls._system_enabled:
            logger.warning("Ticket system is disabled")
            return None

        # Format channel name
        channel_name = category.channel_format.format(
            ticket_category=category.category_name,
            ticket_owner_discord_username=owner.username,
            ticket_owner_discord_user_id=owner.id,
        )

        # Create the appropriate channel type based on category
        channel = (
            await cls._create_channel_ticket(category, channel_name, owner)
            if isinstance(category, ChannelTicketCategory)
            else await cls._create_thread_ticket(category, channel_name, owner)
        )

        if channel:
            await cls._register_ticket_in_database(channel, owner, category)

        return channel

    @classmethod
    async def _create_channel_ticket(
        cls, ticket_category: ChannelTicketCategory, channel_name: str, owner: hikari.User
    ) -> hikari.GuildTextChannel | None:
        """Create a channel-based ticket with appropriate permissions."""
        if cls._guild_id is None or cls._everyone_overwrites is None:
            logger.error("Ticket system not properly initialized")
            return None

        try:
            client = cls._get_client()

            # Permission overwrites for the ticket channel
            permissions = [
                cls._everyone_overwrites,
                # User permissions
                hikari.PermissionOverwrite(
                    id=owner.id,
                    type=hikari.PermissionOverwriteType.MEMBER,
                    allow=(
                        hikari.Permissions.READ_MESSAGE_HISTORY | hikari.Permissions.SEND_MESSAGES
                    ),
                ),
                # Staff permissions
                hikari.PermissionOverwrite(
                    id=ticket_category.staff_role,
                    type=hikari.PermissionOverwriteType.ROLE,
                    allow=(
                        hikari.Permissions.READ_MESSAGE_HISTORY | hikari.Permissions.SEND_MESSAGES
                    ),
                ),
            ]

            return await client.rest.create_guild_text_channel(
                cls._guild_id,
                channel_name,
                category=ticket_category.category_id,
                permission_overwrites=permissions,
            )
        except hikari.ForbiddenError:
            logger.error("Bot doesn't have permission to create channels")
            return None
        except hikari.BadRequestError as e:
            logger.error(f"Invalid request when creating channel: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create channel ticket: {e}")
            return None

    @classmethod
    async def _create_thread_ticket(
        cls, ticket_category: ThreadTicketCategory, channel_name: str, owner: hikari.User
    ) -> hikari.GuildThreadChannel | None:
        """Create a thread-based ticket and add the owner to it."""
        from helper import ChannelHelper

        try:
            client = cls._get_client()

            # Get parent channel for the thread
            thread_channel = await ChannelHelper.fetch_channel(
                ticket_category.channel_id, hikari.PermissibleGuildChannel
            )

            if not thread_channel:
                logger.error(f"Failed to fetch parent channel {ticket_category.channel_id}")
                return None

            # Create thread and add owner
            channel = await client.rest.create_thread(
                thread_channel,
                hikari.ChannelType.GUILD_PRIVATE_THREAD,
                channel_name,
            )
            await client.rest.add_thread_member(channel, owner)

            return channel
        except hikari.ForbiddenError:
            logger.error("Bot doesn't have permission to create threads")
            return None
        except hikari.BadRequestError as e:
            logger.error(f"Invalid request when creating thread: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create thread ticket: {e}")
            return None

    @classmethod
    async def _register_ticket_in_database(
        cls, channel: hikari.TextableGuildChannel, owner: hikari.User, ticket_category: CategoryType
    ) -> None:
        """Register the ticket in the database for tracking."""
        try:
            await TicketChannelService.create_or_update_ticket_channel(
                TicketChannelSchema(
                    id=channel.id, owner_id=owner.id, category=ticket_category.category_name
                )
            )
            logger.debug(
                f"Created ticket {channel.id} for user {owner.id} "
                f"in category {ticket_category.category_name}"
            )
        except Exception as e:
            logger.error(f"Failed to register ticket in database: {e}")

    @classmethod
    async def close_ticket_channel(cls, channel: hikari.TextableGuildChannel | int) -> None:
        """Close and delete a ticket channel, generating transcript if configured."""
        from helper import ChannelHelper

        # Ensure we have a channel object
        if isinstance(channel, int):
            channel_obj = await ChannelHelper.fetch_channel(channel, hikari.TextableGuildChannel)
            if not channel_obj:
                logger.error(f"Failed to fetch channel {channel} for closing")
                return
            channel = channel_obj

        try:
            # Generate and upload transcript if enabled
            if cls._transcript:
                if transcript_path := await cls._generate_transcript(channel):
                    await cls._upload_transcript(channel, transcript_path)

            # Delete channel and remove from database
            await channel.delete()
            await TicketChannelService.delete_ticket_channel(channel.id)
            logger.debug(f"Ticket channel {channel.id} closed and deleted")

        except hikari.ForbiddenError:
            logger.error(f"Bot doesn't have permission to delete channel {channel.id}")
        except hikari.NotFoundError:
            logger.warning(f"Channel {channel.id} not found, may have been already deleted")
            # Still try to clean up database
            await TicketChannelService.delete_ticket_channel(channel.id)
        except Exception as e:
            logger.error(f"Failed to close ticket channel {channel.id}: {e}")

    @classmethod
    async def _generate_transcript(cls, channel: hikari.TextableGuildChannel) -> Path | None:
        """Generate a transcript of the ticket channel."""
        if cls._transcript is None:
            return None

        # Get ticket information
        ticket_info = await TicketChannelService.get_ticket_channel(channel.id)
        if ticket_info is None:
            logger.debug(f"No ticket info found for channel {channel.id}")
            return None

        # Get ticket owner
        from helper import UserHelper

        ticket_owner = await UserHelper.fetch_user(ticket_info.owner_id)
        if ticket_owner is None:
            logger.debug(f"Could not fetch owner {ticket_info.owner_id}")
            return None

        # Format file name
        file_name = cls._transcript.file_name.format(
            ticket_category=ticket_info.category.lower().replace(" ", "_"),
            ticket_owner_discord_username=ticket_owner.username,
            ticket_owner_discord_user_id=ticket_owner.id,
            ticket_channel_id=channel.id,
        )

        # Generate transcript based on format setting
        return await (
            cls._generate_text_transcript(channel, file_name)
            if cls._transcript_file_format == TicketTranscriptFormat.TEXT
            else cls._generate_html_transcript(channel, file_name)
        )

    @classmethod
    async def _generate_text_transcript(
        cls, channel: hikari.TextableGuildChannel, file_name: str
    ) -> Path | None:
        """Generate a plain text transcript of the channel."""
        file_path = Path("temp/transcript/text") / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            messages = []
            async for message in channel.fetch_history():
                timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                author = message.author.username if message.author else "Unknown User"
                content = message.content or "[No text content]"
                messages.append(f"{author} ({timestamp}): {content}")

            # Write messages in reverse chronological order (oldest first)
            with open(file_path, "w", encoding="utf-8") as file:
                for message in reversed(messages):
                    file.write(f"{message}\n")

            return file_path
        except Exception as e:
            logger.error(f"Failed to generate text transcript: {e}")
            return None

    @classmethod
    async def _generate_html_transcript(
        cls, channel: hikari.TextableGuildChannel, file_name: str
    ) -> Path | None:
        """Generate an HTML transcript using chat_exporter."""
        file_path = Path("temp/transcript/html") / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            export = await chat_exporter.export(channel)
            if export is None:
                logger.error(f"Failed to export channel {channel.id} to HTML")
                return None

            with open(file_path, "w", encoding="utf-8") as file:
                file.write(export)
            return file_path
        except Exception as e:
            logger.error(f"Failed to generate HTML transcript: {e}")
            return None

    @classmethod
    async def _upload_transcript(
        cls, channel: hikari.TextableGuildChannel | int, file_path: Path
    ) -> None:
        """Upload a transcript to the configured destination (Discord or GitHub)."""
        from helper import ChannelHelper, UserHelper

        try:
            # Ensure we have a channel object
            channel_obj = (
                channel
                if isinstance(channel, hikari.TextableGuildChannel)
                else (await ChannelHelper.fetch_channel(channel, hikari.TextableGuildChannel))
            )
            if not channel_obj:
                logger.error(f"Failed to fetch channel {channel}")
                return

            # Get ticket info and owner
            ticket_info = await TicketChannelService.get_ticket_channel(channel_obj.id)
            if not ticket_info:
                logger.error(f"No ticket info found for channel {channel_obj.id}")
                return

            ticket_owner = await UserHelper.fetch_user(ticket_info.owner_id)
            if not ticket_owner:
                logger.error(f"Could not fetch owner {ticket_info.owner_id}")
                return

            # Check if log channel exists
            if not cls._log_channel:
                logger.error("Log channel not configured, cannot upload transcript")
                return

            # Common parameters for message formatting
            common_params = {
                "ticket_channel_id": channel_obj.id,
                "ticket_channel_name": channel_obj.name,
                "ticket_category": ticket_info.category,
                "ticket_owner_discord_username": ticket_owner.username,
                "ticket_owner_discord_user_id": ticket_owner.id,
                "ticket_owner_discord_user_mention": ticket_owner.mention,
            }

            # Handle different upload methods
            if cls._transcript_upload_method == TicketTranscriptUploadMethod.GITHUB:
                await cls._upload_transcript_to_github(file_path, common_params, ticket_info)
            else:
                await cls._upload_transcript_to_discord(file_path, common_params)

        except Exception as e:
            logger.error(f"Failed to upload transcript: {e}")
        finally:
            # Clean up file regardless of success or failure
            if file_path.exists():
                os.remove(file_path)

    @classmethod
    async def _upload_transcript_to_discord(cls, file_path: Path, params: dict) -> None:
        """Upload transcript directly to Discord channel."""
        if not cls._log_channel:
            return

        await MessageHelper(MessageKeys.systems.TICKET_LOG_TRANSCRIPT, **params).send_to_channel(
            cls._log_channel, attachment=file_path
        )

    @classmethod
    async def _upload_transcript_to_github(
        cls, file_path: Path, params: dict, ticket_info: TicketChannelSchema
    ) -> None:
        """Upload transcript to GitHub repository."""
        if (
            not cls._transcript_github_repo
            or not cls._transcript_github_repo_branch
            or not cls._log_channel
        ):
            logger.error("GitHub repository or log channel not properly configured")
            await cls._upload_transcript_to_discord(file_path, params)
            return

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Create upload path
            upload_path = file_path.relative_to(Path("temp")).as_posix()

            # Upload to GitHub
            response = cls._transcript_github_repo.create_file(
                path=upload_path,
                message=f"Ticket transcript for {ticket_info.category} - {ticket_info.id}",
                branch=cls._transcript_github_repo_branch,
                content=content,
            )

            # Get file URL - try GitHub Pages first, fall back to raw URL
            file_url = response["content"].html_url
            if cls._transcript_github_repo.has_pages:
                try:
                    repo_full_name = cls._transcript_github_repo.full_name
                    owner, repo_name = repo_full_name.split("/")
                    pages_url = f"https://{owner}.github.io/{repo_name}"
                    file_url = f"{pages_url}/{upload_path}"
                except Exception:
                    pass  # Fall back to the standard URL

            # Send log message with URL
            await MessageHelper(
                MessageKeys.systems.TICKET_LOG_TRANSCRIPT,
                **params,
                ticket_transcript_url=file_url,
            ).send_to_channel(cls._log_channel)

        except GithubException:
            # Fall back to Discord upload on GitHub error
            await cls._upload_transcript_to_discord(file_path, params)
