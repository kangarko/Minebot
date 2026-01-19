from __future__ import annotations

import json
import logging
import sys
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any, Final, cast

import hikari
import lightbulb
from pydantic import ValidationError

from core import GlobalState
from debug import get_logger
from model import BotSettings, LocalizationData, config, message

logger: logging.Logger = get_logger(__name__)

SettingsType = (
    config.SecretKeys
    | config.DatabaseKeys
    | config.BotKeys
    | config.EventsKeys
    | config.CommandsKeys
    | config.SystemsKeys
    | config.WebSocketKeys
)
LocalizationType = (
    message.GeneralMessageKeys
    | message.CommandMessageKeys
    | message.ErrorMessageKeys
    | message.EventMessageKeys
    | message.ModalKeys
    | message.MenuKeys
    | message.TimeUnitKeys
)

DEFAULT_CONFIG_PATH: Final[Path] = Path("configuration/settings.json").resolve()
DEFAULT_LOCALIZATION_PATH: Final[Path] = Path("configuration/localization").resolve()


class Settings:
    """Settings manager with caching and validation."""

    _instance: Settings | None = None
    _data: BotSettings | None = None
    _config_path: Path = DEFAULT_CONFIG_PATH

    def __new__(cls) -> Settings:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config_path: Path | None = None) -> None:
        """
        Initializes the JSON wrapper with an optional configuration file path.
        If a configuration path is provided, it sets the internal `_config_path`
        to the given path. Then, it loads the configuration data.

        Args:
            config_path (Path | None): Optional path to the configuration file.
                                       If not provided, the default path is used.
        Returns:
            None
        """

        if config_path:
            cls._config_path = config_path
        cls.load()

    @classmethod
    def load(cls) -> None:
        """
        Load the settings from the JSON configuration file.

        This method attempts to read and parse the JSON file specified by the `_config_path` attribute.
        It validates the settings and initializes the `_data` attribute with the parsed configuration.

        Raises:
            FileNotFoundError: If the configuration file does not exist at the specified path.
            json.JSONDecodeError: If the configuration file contains invalid JSON.
            ValidationError: If the parsed settings do not meet the required validation criteria.
            Exception: For any other unexpected errors during the loading process.

        Logs:
            - Critical errors for missing files, invalid JSON, validation issues, or unexpected errors.
            - Informational message upon successful loading of settings.

        Exits:
            The application will terminate with a non-zero exit code if any critical error occurs.
        """

        try:
            if not cls._config_path.exists():
                raise FileNotFoundError(f"Settings file not found at {cls._config_path}")

            with cls._config_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
                cls._data = BotSettings(**data)
                cls._validate_required_settings()
                logger.info("Settings loaded successfully")

        except FileNotFoundError as e:
            logger.critical(f"Configuration error: {e}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON in settings file: {e}")
            sys.exit(1)
        except ValidationError as e:
            logger.critical("Invalid settings configuration:")
            for error in e.errors():
                field_path: str = " -> ".join(str(loc) for loc in error["loc"])
                logger.critical(f"• {field_path}: {error['msg']}")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"Unexpected error loading settings: {e}")
            sys.exit(1)

    @classmethod
    def _validate_required_settings(cls) -> None:
        """
        Validates that all required settings are properly loaded and accessible.
        This method checks if the settings data has been loaded and ensures that
        all settings defined in the `SettingsType` enumeration can be accessed
        without errors. If the settings data is not loaded, a `RuntimeError` is raised.
        If any required setting is missing or inaccessible, a `ValueError` is raised
        with details about the missing setting.

        Raises:
            RuntimeError: If the settings data has not been loaded.
            ValueError: If a required setting is missing or cannot be accessed.
        """

        if cls._data is None:
            raise RuntimeError("Settings not loaded")

        # Validate all enum values can be accessed
        from enum import Enum

        for enum_type in SettingsType.__args__:
            if issubclass(enum_type, Enum):
                for setting in enum_type:
                    try:
                        cls.get(setting)
                    except AttributeError as e:
                        logger.critical(f"Missing required setting: {setting.value}")
                        raise ValueError(f"Missing required setting: {setting.value}") from e

    @classmethod
    @lru_cache(maxsize=128)
    def get(cls, key: SettingsType, default: Any = None) -> Any:
        """
        Retrieve a value from the settings data using a dot-separated key.

        Args:
            key (SettingsType): A dot-separated key representing the path to the desired value.
            default (Optional[T], optional): A default value to return if the key is not found. Defaults to None.

        Returns:
            Any: The value associated with the specified key, or the default value if the key is not found.

        Raises:
            ValueError: If the settings data has not been loaded.
            AttributeError: If the key is not found and no default is specified (default=NO_DEFAULT).
        """

        if cls._data is None:
            raise ValueError("Settings not loaded")

        try:
            parts: Sequence[str] = key.value.split(".")
            value: Any = cls._data

            for part in parts:
                value = getattr(value, part)

            return cast(Any, value)
        except AttributeError:
            # Always return default without raising, even if default is None
            return default


class Localization:
    """Localization manager with caching and validation."""

    _instance: Localization | None = None
    _data: dict[str, LocalizationData] | None = None
    _localization_path: Path = DEFAULT_LOCALIZATION_PATH
    _guild_locale: hikari.Locale = hikari.Locale.EN_US
    _fetched_locales_once: bool = False

    def __new__(cls) -> Localization:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, localization_path: Path | None = None) -> None:
        """
        Initializes the localization manager with an optional localization folder path.
        If a localization path is provided, it sets the internal `_localization_path`
        to the given path. Then, it loads the localization data.

        Args:
            localization_path (Path | None): Optional path to the localization folder.
                                              If not provided, the default path is used.
        Returns:
            None
        """

        if localization_path:
            cls._localization_path = localization_path
        cls.load()

    @classmethod
    def load(cls) -> None:
        """
        Load localization data from JSON files in the localization directory.

        This method reads all JSON files in the specified localization directory,
        validates them against the LocalizationData model, and stores them in
        the _data dictionary keyed by locale.

        The method performs the following steps:
        1. Check if the localization directory exists
        2. Find all JSON files in the directory
        3. For each file, attempt to:
           - Parse the JSON content
           - Match the filename to a hikari.Locale
           - Validate against the LocalizationData model
           - Store in the _data dictionary

        Raises:
            FileNotFoundError: If the localization directory does not exist.
            ValueError: If a localization file does not match a valid locale.
            json.JSONDecodeError: If a localization file contains invalid JSON.
            ValidationError: If a localization file fails validation against the model.

        Logs:
            - Critical errors for missing directory, invalid JSON, validation issues.
            - Warning for files that don't match a valid locale.
            - Info for successful loading of localization files.
        """
        try:
            if not cls._localization_path.exists() or not cls._localization_path.is_dir():
                error_msg = f"Localization directory not found at {cls._localization_path}"
                logger.critical(error_msg)
                raise FileNotFoundError(error_msg)

            # Initialize empty dictionary for localization data
            cls._data = {}

            # Get all JSON files in the localization directory
            json_files = list(cls._localization_path.glob("*.json"))
            if not json_files:
                logger.warning(f"No localization files found in {cls._localization_path}")
                return

            # Map locale values to enum objects for faster lookup
            locale_map = {locale.value: locale for locale in hikari.Locale}

            # Process each localization file
            for json_file in json_files:
                locale_name = json_file.stem

                # Check if filename matches a valid locale
                if locale_name not in locale_map:
                    logger.warning(f"Skipping file {json_file.name}: Not a valid locale identifier")
                    continue

                locale = locale_map[locale_name]

                try:
                    # Read and parse the JSON file
                    with json_file.open("r", encoding="utf-8") as file:
                        data = json.load(file)

                        # Add locale to the data for validation
                        data["locale"] = locale_name

                        # Validate and create model instance
                        loader = LocalizationData(**data)

                        # Store in the data dictionary
                        cls._data[locale] = loader
                        logger.debug(f"Loaded localization for {locale_name}")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in localization file {json_file.name}: {e}")
                except ValidationError as e:
                    logger.error(f"Validation error in localization file {json_file.name}:")
                    for error in e.errors():
                        field_path = " -> ".join(str(loc) for loc in error["loc"])
                        logger.error(f"• {field_path}: {error['msg']}")
                except Exception as e:
                    logger.error(f"Error loading localization file {json_file.name}: {e}")

            loaded_locales = list(cls._data.keys())
            if loaded_locales:
                logger.info(
                    f"Successfully loaded {len(loaded_locales)} localizations: {loaded_locales}"
                )
            else:
                logger.warning("No valid localization files were loaded")

        except Exception as e:
            logger.critical(f"Unexpected error loading localizations: {e}")
            cls._data = None
            sys.exit(1)

    @classmethod
    def serialize(cls) -> lightbulb.DictLocalizationProvider:
        """
        Creates and returns a dictionary-based localization provider for commands and messages.

        This method processes command labels, descriptions, and options for all supported locales
        and organizes the data in a structure suitable for lightbulb's localization system.

        The localization structure follows these patterns:
        - For commands: "extensions.{command_name}.label/description"
        - For options: "extensions.{command_name}.options.{option_name}.label/description"

        Returns:
            lightbulb.DictLocalizationProvider: A localization provider containing all processed
            translations organized by locale.
        """
        if cls._data is None:
            logger.info("Localization data not loaded, loading now")
            cls.load()

        if not cls._data:
            logger.warning("No localization data available, returning empty provider")
            return lightbulb.DictLocalizationProvider({})

        # Initialize the localization data dictionary with valid locales
        localization_data: dict[hikari.Locale, dict[str, str]] = {}

        # First, collect all available locales
        for locale_str, loader in cls._data.items():
            try:
                locale = hikari.Locale(locale_str)
                localization_data[locale] = {}
            except (ValueError, KeyError):
                logger.warning(f"Skipping invalid locale: {locale_str}")
                continue

        # Process commands directly from the loaded data structure
        for locale, locale_data in cls._data.items():
            try:
                hikari_locale = hikari.Locale(locale)

                # Access commands through the commands attribute
                if not hasattr(locale_data, "commands"):
                    logger.warning(f"No commands found in locale data for {locale}")
                    continue

                commands_data = locale_data.commands

                # Process each command in the commands section
                for command_name, command_data in vars(commands_data).items():
                    # Skip non-command attributes
                    if not hasattr(command_data, "command"):
                        continue

                    # Process command label and description
                    cmd = command_data.command
                    localization_data[hikari_locale].update(
                        {
                            f"extensions.{command_name}.label": cmd.label,
                            f"extensions.{command_name}.description": cmd.description,
                        }
                    )

                    # Process command options if they exist
                    if hasattr(cmd, "options"):
                        for option_name, option_data in vars(cmd.options).items():
                            if hasattr(option_data, "label") and hasattr(
                                option_data, "description"
                            ):
                                localization_data[hikari_locale].update(
                                    {
                                        f"extensions.{command_name}.options.{option_name}.label": option_data.label,
                                        f"extensions.{command_name}.options.{option_name}.description": option_data.description,
                                    }
                                )

            except Exception as e:
                logger.warning(f"Error processing localization for locale {locale}: {e}")

        logger.info(f"Serialized localization data for {len(localization_data)} locales")
        return lightbulb.DictLocalizationProvider(localization_data)

    @classmethod
    def _get_guild_locale(cls) -> hikari.Locale:
        """Get and cache the guild locale if not already cached."""
        try:
            if not cls._fetched_locales_once:
                cls._guild_locale = GlobalState.guild.get_locale()
                cls._fetched_locales_once = True
            return cls._guild_locale
        except ValueError:
            cls._fetched_locales_once = False
            return hikari.Locale.EN_US

    @classmethod
    @lru_cache(maxsize=128)
    def get(
        cls,
        key: LocalizationType,
        locale: str | hikari.Locale | None = None,
        default: Any = "Unknown",
    ) -> Any:
        """
        Retrieve a specific localization value for a given locale and key.

        Args:
            key (LocalizationType): The key representing the localization value to retrieve.
            locale (str | hikari.Locale | "all"): The locale identifier (e.g., "en-US") or "all" to get
                                                  values for all locales. Defaults to guild language.
            default (Any): The default value to return if the key is not found. Defaults to "Unknown".

        Returns:
            Any | dict[str, Any]: The localized value for the specified key, or a dictionary mapping
                                 locales to values if locale="all", or the default value if not found.
        """
        # Load data if needed
        if cls._data is None:
            logger.debug("Localization data not loaded, attempting to load now.")
            cls.load()
            if cls._data is None:
                return default

        # Special case: return values for all locales
        if locale == "all" and cls._data:
            all_values = {}
            for loc, data in cls._data.items():
                try:
                    value = data
                    for part in key.value.split("."):
                        value = getattr(value, part)
                    all_values[loc] = value
                except AttributeError:
                    all_values[loc] = default
            return all_values

        # Resolve locale
        locale_key = locale
        if locale_key is None:
            locale_key = cls._get_guild_locale()
        if isinstance(locale_key, hikari.Locale):
            locale_key = locale_key.value

        # Get localization data
        localization_data = cls._data.get(locale_key)
        if not localization_data:
            logger.warning(f"Localization data for locale '{locale_key}' not found.")
            return default

        # Navigate through the object hierarchy
        try:
            value = localization_data
            for part in key.value.split("."):
                value = getattr(value, part)
            return value
        except AttributeError:
            logger.error(f"Key '{key.value}' not found in locale '{locale_key}'.")
            return default
