import datetime
import re
from functools import lru_cache
from logging import Logger

import hikari

from debug import get_logger
from model import TimeUnitKeys
from model.schemas import TimeUnitsLocalization
from settings import Localization

logger: Logger = get_logger(__name__)


class TimeHelper:
    """
    Utility class for handling time conversions with localization support.

    This class provides methods to convert between various time units,
    parse time strings, and format time values with appropriate localization.
    It supports multiple locales and automatically handles unit name variations.

    Attributes:
        units: Dictionary mapping unit names to their localized strings and second values
        sorted_units: Pre-sorted units by duration for efficient processing
        abbr_to_unit: Mapping of all localized unit names/abbreviations to canonical unit names
    """

    def __init__(self, locale: str | hikari.Locale | None = None) -> None:
        """
        Initialize the TimeHelper with the specified locale.

        Args:
            locale: The locale to use for time unit names and formats
        """
        logger.debug(f"Initializing TimeHelper with locale: {locale}")

        # Store units directly in the dictionary with their localized names
        self.units: dict[str, tuple[TimeUnitsLocalization.BasicUnit, int]] = {
            "year": (Localization.get(TimeUnitKeys.YEAR, locale=locale), 31536000),
            "month": (Localization.get(TimeUnitKeys.MONTH, locale=locale), 2592000),
            "week": (Localization.get(TimeUnitKeys.WEEK, locale=locale), 604800),
            "day": (Localization.get(TimeUnitKeys.DAY, locale=locale), 86400),
            "hour": (Localization.get(TimeUnitKeys.HOUR, locale=locale), 3600),
            "minute": (Localization.get(TimeUnitKeys.MINUTE, locale=locale), 60),
            "second": (Localization.get(TimeUnitKeys.SECOND, locale=locale), 1),
        }

        # Pre-sort units by seconds (descending) for faster from_timedelta processing
        self.sorted_units: list[tuple[str, tuple[TimeUnitsLocalization.BasicUnit, int]]] = sorted(
            self.units.items(), key=lambda x: x[1][1], reverse=True
        )
        logger.debug(f"Sorted {len(self.sorted_units)} time units for efficient processing")

        # Create a mapping of localized abbreviations to unit names with a single iteration
        self.abbr_to_unit: dict[str, str] = {}
        for unit_name, (unit_info, _) in self.units.items():
            # Add all forms from singular and plural lists to the mapping
            for form in unit_info.singular + unit_info.plural:  # type: ignore
                self.abbr_to_unit[form.lower()] = unit_name

            # Also add the unit name itself as a mapping
            self.abbr_to_unit[unit_name.lower()] = unit_name

        logger.debug(f"Created abbreviation mapping with {len(self.abbr_to_unit)} entries")

        # Compile regex pattern for parsing time strings
        self._time_pattern = re.compile(r"(\d+)\s*([a-zA-Z]+)")

    @lru_cache(maxsize=128)
    def to_timedelta(self, value: int | float, unit: str) -> datetime.timedelta:
        """
        Convert a value and unit to a timedelta object.

        Args:
            value: The numeric value
            unit: The unit name (year, month, week, day, hour, minute, second)

        Returns:
            A timedelta object representing the specified time

        Raises:
            ValueError: If the unit is not recognized

        Examples:
            >>> helper = TimeHelper()
            >>> helper.to_timedelta(2, "days")
            datetime.timedelta(days=2)
            >>> helper.to_timedelta(1.5, "hours")
            datetime.timedelta(seconds=5400)
        """
        unit = unit.lower()
        logger.debug(f"Converting {value} {unit} to timedelta")

        try:
            _, seconds_per_unit = self.units[unit]
            result = datetime.timedelta(seconds=value * seconds_per_unit)
            logger.debug(f"Converted to {result}")
            return result
        except KeyError:
            logger.error(f"Unknown time unit requested: {unit}")
            raise ValueError(f"Unknown time unit: {unit}")

    def from_timedelta(
        self, delta: datetime.timedelta, max_units: int = 2, include_seconds: bool = True
    ) -> str:
        """
        Convert a timedelta to a formatted string with appropriate units.

        Args:
            delta: The timedelta object to format
            max_units: Maximum number of units to include in the result (default: 2)
            include_seconds: Whether to include seconds in the result (default: True)

        Returns:
            A formatted string representation of the timedelta

        Examples:
            >>> helper = TimeHelper()
            >>> helper.from_timedelta(datetime.timedelta(days=1, hours=2, minutes=30))
            '1 day 2 hours'
            >>> helper.from_timedelta(datetime.timedelta(seconds=70), max_units=2)
            '1 minute 10 seconds'
        """
        logger.debug(
            f"Converting timedelta {delta} to string (max_units={max_units}, include_seconds={include_seconds})"
        )

        seconds = delta.total_seconds()
        is_negative = seconds < 0
        total_seconds = abs(int(seconds))

        if total_seconds == 0:
            unit_info, _ = self.units["second"]
            return f"0 {unit_info.plural[0]}"

        parts = []
        # Use pre-sorted units list instead of sorting on each call
        for unit_name, (unit_info, seconds_per_unit) in self.sorted_units:
            # Skip seconds if not including them
            if not include_seconds and unit_name == "second":
                continue

            # Calculate value for this unit
            value = total_seconds // seconds_per_unit
            if value > 0:
                # Format the unit name based on value
                formatted_unit = unit_info.singular[0] if value == 1 else unit_info.plural[0]
                parts.append(f"{value} {formatted_unit}")
                total_seconds %= seconds_per_unit

                # Stop if we've reached the maximum number of units
                if len(parts) >= max_units:
                    break

        # Join parts with space separator
        result = " ".join(parts)
        if is_negative:
            result = f"-{result}"

        logger.debug(f"Formatted timedelta as: '{result}'")
        return result

    def format_time_remaining(self, seconds: int | float) -> str:
        """
        Format a number of seconds as a human-readable time remaining string.

        Args:
            seconds: The number of seconds

        Returns:
            A formatted string representation of the time

        Examples:
            >>> helper = TimeHelper()
            >>> helper.format_time_remaining(3665)
            '1 hour 1 minute'
            >>> helper.format_time_remaining(86465)
            '1 day 5 seconds'
        """
        logger.debug(f"Formatting {seconds} seconds as human-readable time")
        result = self.from_timedelta(datetime.timedelta(seconds=seconds))
        logger.debug(f"Formatted time: {result}")
        return result

    def parse_time_string(self, time_string: str) -> datetime.timedelta:
        """
        Parse a time string into a timedelta object.

        Handles various formats like "1d 2h 30m" or "1 day 2 hours 3 minutes",
        using localized unit names and abbreviations.

        Args:
            time_string: A string containing time values with unit indicators
                         (using localized abbreviations)

        Returns:
            A timedelta object representing the total time

        Examples:
            >>> helper = TimeHelper()
            >>> helper.parse_time_string("1d 12h 30m")
            datetime.timedelta(days=1, seconds=45000)
            >>> helper.parse_time_string("1 day 2 hours 3 minutes")
            datetime.timedelta(days=1, seconds=7380)
            >>> helper.parse_time_string("")
            datetime.timedelta(0)
        """
        logger.debug(f"Parsing time string: '{time_string}'")

        if not time_string:
            logger.debug("Empty time string, returning zero timedelta")
            return datetime.timedelta(0)

        # Use the compiled regex pattern to find all number+unit pairs
        matches = self._time_pattern.findall(time_string.lower())

        if not matches:
            logger.warning(f"No valid time patterns found in string: '{time_string}'")
            return datetime.timedelta(0)

        total_seconds = 0

        for value_str, unit_text in matches:
            try:
                value = int(value_str)
                unit_name = self.abbr_to_unit.get(unit_text)

                if unit_name:
                    _, seconds_per_unit = self.units[unit_name]
                    unit_seconds = value * seconds_per_unit
                    logger.debug(
                        f"Parsed {value} {unit_text} as {value} {unit_name} = {unit_seconds} seconds"
                    )
                    total_seconds += unit_seconds
                else:
                    logger.warning(f"Unknown unit abbreviation: '{unit_text}'")
            except (ValueError, KeyError) as e:
                logger.error(f"Error parsing time component '{value_str} {unit_text}': {str(e)}")
                continue

        result = datetime.timedelta(seconds=total_seconds)
        logger.debug(f"Parsed time string as {result} ({total_seconds} seconds)")
        return result
