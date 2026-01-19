from logging import Logger
from pathlib import Path
from typing import Final

import hikari

from core import GlobalState
from debug import debugger
from helper.command import CommandHelper
from model import CommandsKeys
from utils import fetch_available_locales, fetch_files_with_extension

# Set up logging
logger: Logger = debugger.get_logger(__name__)


class WikiHelper:
    # Store both file paths and content in a single structure
    # Format: {locale: {filename: (path, content)}}
    _data: dict[str, dict[str, tuple[Path, str | None]]] = {}
    MAX_CONTENT_LENGTH: Final[int] = 4000
    GUILD_LANGUAGE: hikari.Locale | None = None

    @classmethod
    def _get_guild_locale(cls) -> hikari.Locale:
        """Get and cache the guild locale if not already cached."""
        if cls.GUILD_LANGUAGE is None:
            logger.debug("Caching guild locale")
            cls.GUILD_LANGUAGE = GlobalState.guild.get_locale()
        else:
            logger.debug("Using cached guild locale")
        return cls.GUILD_LANGUAGE

    @classmethod
    def load_wiki_data(cls) -> None:
        """Load wiki data from markdown files for all available locales."""
        system_data: CommandHelper = CommandHelper(CommandsKeys.WIKI)

        if not system_data.command_enabled:
            return

        wiki_data_path = Path("configuration/wiki")
        cls._data.clear()  # Clear existing data before reloading

        for locale in fetch_available_locales():
            locale_str = str(locale)
            locale_path: Path = wiki_data_path / locale_str

            try:
                files_dict: dict[str, Path] = fetch_files_with_extension(
                    locale_path.resolve(), "md"
                )

                valid_files: dict[str, tuple[Path, str | None]] = {}

                # Process files and cache their content
                for name, path in files_dict.items():
                    try:
                        content: str = path.read_text(encoding="utf-8")
                        if len(content) <= cls.MAX_CONTENT_LENGTH:
                            valid_files[name] = (path, content)
                        else:
                            logger.warning(f"Wiki file too large: {path} ({len(content)} bytes)")
                    except (UnicodeDecodeError, IOError) as e:
                        logger.warning(f"Error reading wiki file {path}: {e}")

                if valid_files:  # Only add if there are valid files
                    cls._data[locale_str] = valid_files

            except FileNotFoundError:
                logger.info(f"No wiki files found for locale: {locale_str}")

    @classmethod
    def get_wiki_files(cls, locale: str) -> dict[str, Path] | None:
        """Get all wiki files for a specific locale, falling back to guild locale if needed."""
        # Try with requested locale first
        if locale in cls._data and cls._data[locale]:
            return {name: path_content[0] for name, path_content in cls._data[locale].items()}

        # Fall back to guild locale if user locale has no wiki files
        guild_locale = str(cls._get_guild_locale())
        if guild_locale in cls._data and cls._data[guild_locale]:
            logger.info(
                f"Falling back to guild locale {guild_locale} for wiki files (requested: {locale})"
            )
            return {name: path_content[0] for name, path_content in cls._data[guild_locale].items()}

        return None

    @classmethod
    def get_wiki_file_content(cls, locale: str, file_name: str) -> str | None:
        """Get the content of a specific wiki file, falling back to guild locale if needed."""
        # Try with requested locale first
        if locale in cls._data and file_name in cls._data.get(locale, {}):
            return cls._data[locale][file_name][1]

        # Fall back to guild locale if content not found in user locale
        guild_locale = str(cls._get_guild_locale())
        if guild_locale in cls._data and file_name in cls._data.get(guild_locale, {}):
            logger.info(
                f"Falling back to guild locale {guild_locale} for wiki content {file_name} (requested: {locale})"
            )
            return cls._data[guild_locale][file_name][1]

        return None
