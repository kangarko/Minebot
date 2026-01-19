import json
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, ClassVar, Final

from model import LogStyle


class ColoredFormatter(logging.Formatter):
    """Custom formatter for colored log output with improved readability."""

    # Cache format strings to avoid rebuilding them for each log record
    _FORMATS: ClassVar[dict[str, str]] = {}

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a logging record into a styled string based on its log level.

        This method customizes the log message format by applying specific styles
        (e.g., colors) to different parts of the log message, such as the log level,
        logger name, timestamp, and message content. The styles are cached for each
        log level to improve performance.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log message as a string.
        """
        # Get cached format for this level if available
        if record.levelname not in self._FORMATS:
            # Get styling
            level_color = LogStyle[record.levelname].value
            reset = LogStyle.RESET.value
            timestamp_color = LogStyle.TIMESTAMP.value
            name_color = LogStyle.NAME.value
            bracket = LogStyle.BRACKET.value
            arrow = LogStyle.ARROW.value

            # Create cached format string for this level
            self._FORMATS[record.levelname] = (
                f"{bracket}[{level_color}{record.levelname:4}{reset}{bracket}] "
                f"{bracket}[{name_color}%(name)-8s{bracket}] "
                f"{bracket}[{timestamp_color}%(asctime)s{bracket}] "
                f"{arrow}→ "
                f"{level_color}%(message)s{reset}"
            )

        # Set format for this record
        self._style._fmt = self._FORMATS[record.levelname]

        # Apply standard formatting
        return super().format(record)


# Configuration constants
DEFAULT_CONFIG_PATH: Final[Path] = Path("configuration/debug.json")
FALLBACK_CONFIG: Final[dict[str, Any]] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": f"{ColoredFormatter.__module__}.{ColoredFormatter.__name__}",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "standard": {
            "format": "[%(levelname)4s] [%(name)-8s] [%(asctime)s] → %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "colored",
            "stream": "ext://sys.stdout",
        },
        # Add file handler for production environment
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": "logs/minebot.log",
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "minebot": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
        "hikari": {"level": "INFO", "handlers": ["console", "file"], "propagate": False},
    },
    "root": {
        "level": "WARNING",
        "handlers": ["console", "file"],
    },
}


def setup_logging(config_path: Path | None = None) -> bool:
    """
    Configures the logging system for the application.

    This function sets up logging based on a configuration file provided via
    `config_path`. If no path is provided, a default configuration path is used.
    It ensures that the necessary directories for log files exist and falls back
    to a basic logging configuration in case of errors.

    Args:
        config_path (Path | None): The path to the logging configuration file.
            If not provided, a default path is used.

    Returns:
        bool: True if logging was successfully configured, False otherwise.

    Exceptions Handled:
        - json.JSONDecodeError, ValueError: Raised when the configuration file
          contains invalid JSON or formatting issues.
        - PermissionError, OSError: Raised when there are issues accessing the
          configuration file or creating necessary directories.
        - Exception: Catches all other unexpected errors.

    Notes:
        - If the configuration file is invalid or inaccessible, the function
          falls back to a basic logging configuration and logs the error.
        - The function ensures that a "logs" directory exists for file-based
          logging handlers.
    """
    try:
        config_path = config_path or DEFAULT_CONFIG_PATH

        # Ensure logs directory exists for file handlers
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        if config_path.exists():
            with config_path.open("rt", encoding="utf-8") as f:
                config: dict[str, Any] = json.load(f)
        else:
            config = FALLBACK_CONFIG

        logging.config.dictConfig(config)
        return True

    except (json.JSONDecodeError, ValueError) as e:
        # Handle specific formatting errors in the config file
        _setup_emergency_logging()
        logging.error(f"Invalid logging configuration format: {e}. Using basic configuration.")
        return False
    except (PermissionError, OSError) as e:
        # Handle file access errors
        _setup_emergency_logging()
        logging.error(
            f"Could not access logging configuration file: {e}. Using basic configuration."
        )
        return False
    except Exception as e:
        # Catch all remaining exceptions
        _setup_emergency_logging()
        logging.error(f"Failed to configure logging: {e}. Using basic configuration.")
        return False


def _setup_emergency_logging() -> None:
    """
    Configures emergency logging settings for the application.

    This function sets up basic logging with the INFO level, a standard log
    message format, and outputs log messages to the standard output stream.
    It is intended to provide a fallback logging mechanism in case other
    logging configurations fail or are unavailable.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger instance with a specified name, prefixed by 'minebot.'.

    Args:
        name (str): The name to append to the 'minebot.' prefix for the logger.

    Returns:
        logging.Logger: A logger instance with the specified name.
    """
    return logging.getLogger(f"minebot.{name}")
