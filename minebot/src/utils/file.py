import os
from functools import lru_cache
from logging import Logger
from pathlib import Path
from typing import Final

import hikari

from debug import get_logger

# Constants
LOCALIZATION_PATH: Final[Path] = Path("configuration/localization").resolve()
logger: Logger = get_logger(__name__)


@lru_cache(maxsize=2)
def fetch_files_with_extension(folder_path: Path, file_extension: str) -> dict[str, Path]:
    """
    Get a dictionary of file names and their corresponding paths from a folder.

    This function scans a specified folder and creates a dictionary where the keys are
    file names (without extension) and the values are the complete file paths for files
    matching the specified extension.

    Args:
        folder_path (Path): The path to the folder to scan.
        file_extension (str): The file extension to filter for (without the dot).

    Returns:
        dict[str, Path]: A dictionary mapping file names (without extension) to their full Path objects.
            For example: {'file1': Path('/path/to/file1.txt'), 'file2': Path('/path/to/file2.txt')}

    Raises:
        FileNotFoundError: If the folder path does not exist or is not a directory.
        ValueError: If the file extension is empty or invalid.

    Example:
        >>> folder = Path('/path/to/folder')
        >>> files = get_file_names_and_paths(folder, 'txt')
        >>> print(files)
        ... {'document': PosixPath('/path/to/folder/document.txt')}
    """
    logger.debug(f"Scanning folder: {folder_path} for files with extension: .{file_extension}")

    if not folder_path.exists() or not folder_path.is_dir():
        error_msg = f"The folder path '{folder_path}' does not exist or is not a directory."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if not file_extension or not file_extension.strip():
        error_msg = "The file extension provided is empty or invalid."
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        file_paths_dict: dict[str, Path] = {
            file_path.stem: file_path
            for file_path in folder_path.iterdir()
            if file_path.suffix == f".{file_extension}"
        }
        logger.debug(
            f"Found {len(file_paths_dict)} files with extension '.{file_extension}' in {folder_path}"
        )
        return file_paths_dict
    except Exception as e:
        logger.error(f"An error occurred while scanning folder '{folder_path}': {e}")
        raise


@lru_cache(maxsize=1)
def fetch_available_locales() -> list[hikari.Locale]:
    """
    Retrieves the list of supported locales based on available localization files.

    The function looks for localization files in the 'configuration/localization' directory
    and matches their base names (without extensions) against hikari.Locale values.
    Results are cached for performance.

    Returns:
        list[hikari.Locale]: A list of hikari.Locale objects representing the supported locales.

    Raises:
        FileNotFoundError: If the localization directory doesn't exist or is not a directory.

    Example:
        >>> get_supported_locales()
        ... [<Locale.EN_US: 'en-US'>, <Locale.TR: 'tr'>]
    """

    logger.debug(f"Fetching supported locales from {LOCALIZATION_PATH}")

    if not LOCALIZATION_PATH.exists() or not LOCALIZATION_PATH.is_dir():
        error_msg: str = f"{LOCALIZATION_PATH} does not exist or is not a directory."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        # Get all filenames and extract base names without extensions
        file_names: list[str] = os.listdir(LOCALIZATION_PATH)
        base_names: set[str] = {Path(file_name).stem for file_name in file_names}

        # Match base names with hikari.Locale values
        supported_locales: list[hikari.Locale] = []
        locale_value_map: dict[str, hikari.Locale] = {
            locale.value: locale for locale in hikari.Locale
        }

        for locale_name in base_names:
            if locale_name in locale_value_map:
                supported_locales.append(locale_value_map[locale_name])

        logger.debug(f"Found {len(supported_locales)} supported locales: {supported_locales}")
        return supported_locales

    except Exception as e:
        logger.error(f"Error while getting supported locales: {e}")
        raise
