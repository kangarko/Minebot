from logging import Logger

import lightbulb
from pydantic import PositiveInt

from debug import get_logger
from model import EventsKeys
from model.schemas import BasicEvent
from settings import Settings

logger: Logger = get_logger(__name__)


class EventHelper:
    def __init__(self, event: EventsKeys) -> None:
        """
        Initialize an event helper.

        Args:
            event (EventsKeys): The event key identifier.

        Attributes:
            event_name (LiteralString): The lowercase name of the event.
            event_enabled (bool): Whether the event is enabled.
            event_log_enabled (bool): Whether logging is enabled for the event.
            event_log_channel (PositiveInt | None): The channel ID for logging.
        """
        self.event_name: str = event.name.lower()

        try:
            event_info: BasicEvent = Settings.get(event)

            # Check if event_info is None and handle it
            if event_info is None:
                self._set_defaults()
                return

            # Basic event properties
            self.event_enabled: bool = True

            # Handle logging configuration
            self._configure_logging(event_info)

            # Log initialization
            self._log_initialization()

        except Exception as e:
            logger.error(f"[Event: {self.event_name}] Initialization FAILED: {str(e)}")
            raise ValueError(f"Failed to initialize event {event.name}: {str(e)}") from e

    def _set_defaults(self) -> None:
        """
        Set default values for event properties.

        This method is called when the event configuration is not found,
        setting all properties to safe default values.
        """
        self.event_enabled = False
        self.event_log_enabled = False
        self.event_log_channel = None

        logger.debug(
            f"[Event: {self.event_name}] Initialized with defaults - Enabled: {self.event_enabled}, "
            f"Logging: {self.event_log_enabled}"
        )

    def _log_initialization(self) -> None:
        """
        Log basic event initialization details.

        Outputs debug information about the event's configuration
        to help with troubleshooting.
        """
        logger.debug(
            f"[Event: {self.event_name}] Initialized - Enabled: {self.event_enabled}, "
            f"Logging: {self.event_log_enabled}, Channel: {self.event_log_channel}"
        )

    def _configure_logging(self, event_info: BasicEvent) -> None:
        """
        Configure logging properties if available.

        Args:
            event_info (BasicEvent): The event configuration containing logging settings.
        """
        # Default values
        self.event_log_enabled = False
        self.event_log_channel = None

        if hasattr(event_info, "log") and event_info.log is not None:
            self.event_log_enabled = bool(event_info.log)
            self.event_log_channel: PositiveInt | None = event_info.log
            logger.debug(
                f"[Event: {self.event_name}] Logging configured - Enabled: {self.event_log_enabled}, "
                f"Channel: {self.event_log_channel}"
            )

    def get_loader(self) -> lightbulb.Loader:
        """
        Get the lightbulb event loader for the event helper.

        Returns:
            lightbulb.Loader: A loader instance that uses the event_enabled status as a condition.
        """
        logger.info(
            f"[Event: {self.event_name}] Creating event loader "
            f"(Status: {'ENABLED' if self.event_enabled else 'DISABLED'})"
        )
        return lightbulb.Loader(lambda: self.event_enabled)

    def has_logging_enabled(self) -> bool:
        """
        Check if logging is enabled for the event.

        Returns:
            bool: True if logging is enabled, False otherwise.
        """
        return self.event_log_enabled

    def get_log_channel_id(self) -> PositiveInt | None:
        """
        Get the ID of the channel where event logs should be sent.

        Returns:
            PositiveInt | None: The channel ID if logging is enabled, None otherwise.
        """
        return self.event_log_channel if self.event_log_enabled else None
