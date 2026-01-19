"""
Timed collection types for items that expire after specified durations.

This module provides specialized container types that automatically manage the
lifetime of their elements. The primary class is TimedSet, which functions like
a standard set but automatically removes elements after they've been present for
a configurable duration.
"""

import heapq
import threading
import time
from logging import Logger
from typing import Any, Generic, Hashable, Iterable, Iterator, Mapping, TypeVar

from debug import get_logger

logger: Logger = get_logger(__name__)

# Type variable to support any hashable type
T = TypeVar("T", bound=Hashable)
K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class TimedSet(Generic[T]):
    """
    A set-like container where items automatically expire after a specified duration.

    TimedSet maintains items for a configurable period of time after which they are
    automatically removed. This is useful for tracking recently seen items, implementing
    time-based caches, or managing temporary data that should automatically expire.

    The implementation is thread-safe and offers both eager (background thread) and
    lazy (on-access) expiration mechanisms.

    Attributes:
        expiration_time (float): Duration in seconds that items remain valid
        item_type (type): Type constraint for items added to the set
        lazy_expiration (bool): Whether expiration checks happen only upon access

    Examples:
        >>> # Create a set where strings expire after 60 seconds
        >>> recent_users = TimedSet[str](60)
        >>> recent_users.add("user123")
        >>> "user123" in recent_users  # True until 60 seconds pass
        True

        >>> # Create a set of integers with lazy expiration
        >>> recent_ids = TimedSet[int](300, item_type=int, lazy_expiration=True)
        >>> recent_ids.add([101, 102, 103])
        >>> len(recent_ids)  # 3 until items expire
        3
    """

    def __init__(
        self, expiration_time: float, item_type: type[T] = str, lazy_expiration: bool = False
    ) -> None:
        """
        Initialize a TimedSet with a specified expiration time and type constraint.

        Args:
            expiration_time: Time in seconds after which items expire
            item_type: Type of items that can be stored (default: str)
            lazy_expiration: If True, only check for expired items on access;
                            if False, run a background thread to remove expired items

        Raises:
            ValueError: If expiration_time is not positive
        """
        if expiration_time <= 0:
            raise ValueError("Expiration time must be positive")

        self.expiration_time: float = expiration_time
        self.item_type: type[T] = item_type
        self.lazy_expiration: bool = lazy_expiration

        # Core data structures
        self._items: dict[T, float] = {}  # Maps items to their insertion timestamps
        self._expiration_heap: list[tuple[float, int, T]] = []  # (expiry_time, sequence, item)
        self._sequence_counter: int = 0  # For stable ordering in the heap
        self._expired_items_count: int = 0  # Count expired items to trigger cleanup

        # Thread synchronization
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._condition = None if lazy_expiration else threading.Condition(self._lock)

        # Configuration with adaptive thresholds
        self._cleanup_threshold: int = 1000  # Base threshold for queue cleanup
        self._cleanup_ratio: float = 2.0  # Rebuild when queue > items * ratio
        self._heap_size_limit: int = 100000  # Maximum heap size before forced cleanup
        self._adaptive_cleanup_factor: float = 0.1  # Percentage of items to trigger cleanup

        # Start background worker if not in lazy mode
        self._worker_thread = None
        if not lazy_expiration:
            self._worker_thread = threading.Thread(
                target=self._expire_items_periodically,
                daemon=True,
                name=f"TimedSet-Expiration-{id(self)}",
            )
            self._worker_thread.start()

        logger.debug(
            f"TimedSet initialized: expiration={expiration_time}s, "
            f"type={item_type.__name__}, lazy={lazy_expiration}"
        )

    def _expire_items_periodically(self) -> None:
        """Worker thread function that periodically checks and removes expired items."""
        check_interval = min(
            self.expiration_time / 10, 1.0
        )  # More frequent checks for responsiveness

        while not self._shutdown_event.is_set():
            # Remove expired items
            self._remove_expired_items()

            # Sleep with condition variable to allow waking up for state changes
            if self._condition is not None:
                with self._condition:
                    # Use wait_for to handle spurious wakeups and ensure timeout
                    self._condition.wait_for(
                        lambda: self._shutdown_event.is_set(), timeout=check_interval
                    )
            else:
                # Fallback to simple sleep if condition is None
                time.sleep(check_interval)

    def _remove_expired_items(self) -> None:
        """Remove all expired items from the set."""
        with self._lock:
            if not self._expiration_heap:
                return

            current_time = time.monotonic()
            removed_count = 0

            # Process heap while the earliest item is expired
            while self._expiration_heap and self._expiration_heap[0][0] <= current_time:
                expiry_time, _, item = heapq.heappop(self._expiration_heap)

                # Only remove if this is the current entry for the item
                if item in self._items and self._items[item] <= current_time - self.expiration_time:
                    del self._items[item]
                    removed_count += 1

                self._expired_items_count += 1

            # Rebuild heap if we've accumulated too many expired entries
            if (
                self._expired_items_count > self._cleanup_threshold
                and len(self._expiration_heap) > len(self._items) * self._cleanup_ratio
            ):
                self._rebuild_expiration_heap()

            if removed_count > 0:
                logger.debug(f"TimedSet: removed {removed_count} expired items")

    def _rebuild_expiration_heap(self) -> None:
        """Rebuild the expiration heap to remove stale entries."""
        current_time = time.monotonic()
        heap_size = len(self._expiration_heap)
        items_size = len(self._items)

        # Calculate adaptive threshold based on current size
        adaptive_threshold = max(
            self._cleanup_threshold,
            min(int(items_size * self._adaptive_cleanup_factor), self._heap_size_limit // 10),
        )

        # Early return if we don't need a rebuild yet
        if (
            self._expired_items_count <= adaptive_threshold
            and heap_size <= items_size * self._cleanup_ratio
        ):
            return

        start_time = time.monotonic()

        # For small heaps, or when heap is much larger than items, rebuild from scratch
        if heap_size < 1000 or heap_size > items_size * 3 or heap_size > self._heap_size_limit:
            # Create a fresh heap with only current items
            # Preallocate array with estimated capacity for better performance
            valid_entries = []
            valid_entries_append = valid_entries.append  # Local reference for faster calls

            for item, timestamp in self._items.items():
                expiry_time = timestamp + self.expiration_time
                if expiry_time > current_time:  # Only include non-expired items
                    self._sequence_counter += 1
                    valid_entries_append((expiry_time, self._sequence_counter, item))

            # Replace the heap with our new clean version
            self._expiration_heap = valid_entries
            heapq.heapify(self._expiration_heap)
        else:
            # For larger heaps, filter in-place using a more efficient approach
            valid_items = frozenset(self._items.keys())  # Faster lookups with frozenset

            # Filter the heap in-place with a two-pointer approach
            i, write_idx = 0, 0
            while i < len(self._expiration_heap):
                entry = self._expiration_heap[i]
                _, _, item = entry
                if item in valid_items:
                    if i != write_idx:
                        self._expiration_heap[write_idx] = entry
                    write_idx += 1
                i += 1

            # Truncate the heap to the correct size
            if write_idx < len(self._expiration_heap):
                self._expiration_heap = self._expiration_heap[:write_idx]

            # Restore heap property
            heapq.heapify(self._expiration_heap)

        self._expired_items_count = 0

        # Log performance metrics for large heaps
        rebuild_time = time.monotonic() - start_time
        if heap_size > 10000:
            logger.debug(
                f"TimedSet: rebuilt expiration heap with {len(self._expiration_heap)} items "
                f"in {rebuild_time:.4f}s (was {heap_size})"
            )
        else:
            logger.debug(
                f"TimedSet: rebuilt expiration heap with {len(self._expiration_heap)} items"
            )

    def _check_expiration_if_lazy(self) -> None:
        """Check for expired items when in lazy expiration mode."""
        if self.lazy_expiration:
            self._remove_expired_items()

    def add(self, item_or_items: T | Iterable[T]) -> None:
        """
        Add an item or multiple items to the set with current timestamp.

        Items will be automatically removed after expiration_time. If an item
        already exists in the set, its expiration timer is reset.

        Args:
            item_or_items: A single item or an iterable of items to add

        Raises:
            TypeError: If the item(s) are not of the expected type
        """
        # Convert single item to list for uniform processing
        if isinstance(item_or_items, self.item_type):
            items = [item_or_items]
        elif isinstance(item_or_items, Iterable):
            items = list(item_or_items)
        else:
            raise TypeError(
                f"Expected {self.item_type.__name__} or iterable of {self.item_type.__name__}, "
                f"got {type(item_or_items).__name__}"
            )

        with self._lock:
            current_time = time.monotonic()
            batch_size = len(items)

            # Pre-allocate heap entries for batch insertion
            new_heap_entries = []

            for item in items:
                if not isinstance(item, self.item_type):
                    raise TypeError(
                        f"Expected {self.item_type.__name__}, got {type(item).__name__}"
                    )

                # Add/update item with current timestamp
                self._items[item] = current_time

                # Prepare heap entry
                self._sequence_counter += 1
                expiry_time = current_time + self.expiration_time
                new_heap_entries.append((expiry_time, self._sequence_counter, item))

            # Batch add to heap
            if batch_size == 1:
                heapq.heappush(self._expiration_heap, new_heap_entries[0])
            elif batch_size <= 10:
                # For small batches, individual pushes are efficient enough
                for entry in new_heap_entries:
                    heapq.heappush(self._expiration_heap, entry)
            else:
                # For larger batches, extend and re-heapify
                self._expiration_heap.extend(new_heap_entries)
                heapq.heapify(self._expiration_heap)

            # Signal the condition variable to optimize expiration checks
            if self._condition is not None:
                self._condition.notify()

            if batch_size == 1:
                logger.debug(
                    f"TimedSet: added item '{items[0]}', expires in {self.expiration_time}s"
                )
            else:
                logger.debug(f"TimedSet: added {batch_size} items")

    def remove(self, item_or_items: T | Iterable[T]) -> int:
        """
        Remove an item or multiple items from the set.

        Items are immediately removed regardless of their expiration time.

        Args:
            item_or_items: A single item or an iterable of items to remove

        Returns:
            int: Number of items that were successfully removed

        Raises:
            TypeError: If the item(s) are not of the expected type
        """
        # Handle single item case
        if isinstance(item_or_items, self.item_type):
            items = [item_or_items]
        elif isinstance(item_or_items, Iterable):
            items = list(item_or_items)
        else:
            raise TypeError(
                f"Expected {self.item_type.__name__} or iterable of {self.item_type.__name__}, "
                f"got {type(item_or_items).__name__}"
            )

        with self._lock:
            removed_count = 0
            items_to_remove = set()

            for item in items:
                if item in self._items:
                    del self._items[item]
                    items_to_remove.add(item)
                    removed_count += 1

            # Mark for cleanup if enough items were removed to justify the cost
            if removed_count > min(100, len(self._items) // 10):
                self._rebuild_expiration_heap()
            # Signal the condition variable to wake up the worker thread
            elif self._condition is not None:
                self._condition.notify()

            if removed_count > 0:
                if len(items) == 1:
                    logger.debug(f"TimedSet: removed item '{items[0]}'")
                else:
                    logger.debug(f"TimedSet: removed {removed_count} of {len(items)} items")

            return removed_count

    def clear(self) -> None:
        """Remove all items from the set immediately."""
        with self._lock:
            item_count = len(self._items)
            self._items.clear()
            self._expiration_heap.clear()
            self._expired_items_count = 0
            self._sequence_counter = 0
            logger.debug(f"TimedSet: cleared {item_count} items")

    def contains(self, item: T) -> bool:
        """
        Check if an item is currently in the set.

        In lazy expiration mode, this will trigger an expiration check.

        Args:
            item: The item to check for

        Returns:
            bool: True if the item is in the set and not expired
        """
        with self._lock:
            self._check_expiration_if_lazy()
            return item in self._items

    def time_remaining(self, item: T) -> float | None:
        """
        Get the time remaining before an item expires.

        Args:
            item: The item to check

        Returns:
            float | None: Seconds remaining until expiration, or None if item not found
        """
        with self._lock:
            if item in self._items:
                current_time = time.monotonic()
                elapsed = current_time - self._items[item]
                remaining = max(0.0, self.expiration_time - elapsed)
                return remaining
            return None

    def extend(self, item: T, extra_time: float) -> bool:
        """
        Extend the expiration time of an item.

        Args:
            item: The item whose expiration to extend
            extra_time: Additional seconds to add to the item's lifetime

        Returns:
            bool: True if the item was found and extended, False otherwise
        """
        if extra_time <= 0:
            return False

        with self._lock:
            if item not in self._items:
                return False

            # Calculate new expiry based on current time (reset timer + extra)
            current_time = time.monotonic()
            new_expiry = current_time + self.expiration_time + extra_time

            # Update the item's timestamp
            self._items[item] = current_time

            # Add a new expiry entry
            self._sequence_counter += 1
            heapq.heappush(self._expiration_heap, (new_expiry, self._sequence_counter, item))

            # Check if we need to clean the heap
            if self._expired_items_count > self._cleanup_threshold:
                self._rebuild_expiration_heap()

            logger.debug(f"TimedSet: extended item '{item}' expiration by {extra_time}s")
            return True

    def items_with_expiry(self) -> dict[T, float]:
        """
        Return all items with their expiration times.

        Returns:
            dict[T, float]: Dictionary mapping items to their expiration timestamps
        """
        with self._lock:
            self._check_expiration_if_lazy()
            return {
                item: timestamp + self.expiration_time for item, timestamp in self._items.items()
            }

    def __contains__(self, item: T) -> bool:
        """Support for 'in' operator to check if an item is in the set."""
        return self.contains(item)

    def __len__(self) -> int:
        """Return the number of non-expired items in the set."""
        with self._lock:
            self._check_expiration_if_lazy()
            return len(self._items)

    def __str__(self) -> str:
        """Return a string representation showing items and their remaining times."""
        with self._lock:
            items_with_remaining = {
                item: round(self.time_remaining(item) or 0, 1) for item in self._items
            }
            return f"TimedSet({items_with_remaining})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the TimedSet."""
        with self._lock:
            return (
                f"TimedSet(expiration_time={self.expiration_time}, "
                f"item_type={self.item_type.__name__}, "
                f"lazy_expiration={self.lazy_expiration}, "
                f"items={len(self._items)})"
            )

    def __iter__(self) -> Iterator[T]:
        """Return an iterator over non-expired items in the set."""
        with self._lock:
            self._check_expiration_if_lazy()
            # Create a safe copy for iteration to avoid concurrent modification issues
            return iter(list(self._items.keys()))

    def shutdown(self) -> None:
        """
        Shut down the worker thread gracefully.

        This should be called before application exit to ensure clean shutdown.
        """
        if hasattr(self, "_shutdown_event") and self._shutdown_event is not None:
            self._shutdown_event.set()

            if (
                hasattr(self, "_worker_thread")
                and self._worker_thread is not None
                and self._worker_thread.is_alive()
            ):
                self._worker_thread.join(timeout=2.0)
                if self._worker_thread.is_alive():
                    logger.warning("TimedSet: Worker thread did not terminate within timeout")
                else:
                    logger.debug("TimedSet: Worker thread shut down successfully")

    def __del__(self) -> None:
        """Ensure cleanup on garbage collection."""
        try:
            self.shutdown()
        except Exception:
            # Avoid exceptions during garbage collection
            pass


class TimedDict(Generic[K, V]):
    """
    A dict-like container where key-value pairs automatically expire after a specified duration.

    TimedDict maintains entries for a configurable period of time after which they are
    automatically removed. This is useful for tracking time-sensitive data, implementing
    time-based caches, or managing temporary data that should automatically expire.

    The implementation is thread-safe and offers both eager (background thread) and
    lazy (on-access) expiration mechanisms.

    Attributes:
        expiration_time (float): Duration in seconds that entries remain valid
        key_type (type): Type constraint for keys added to the dictionary
        lazy_expiration (bool): Whether expiration checks happen only upon access

    Examples:
        >>> # Create a dict where entries expire after 60 seconds
        >>> user_sessions = TimedDict[str, dict](60)
        >>> user_sessions["user123"] = {"login_time": "2025-04-29T12:00:00"}
        >>> "user123" in user_sessions  # True until 60 seconds pass
        True

        >>> # Create a dict with lazy expiration
        >>> temp_cache = TimedDict[int, str](300, key_type=int, lazy_expiration=True)
        >>> temp_cache[101] = "cached_data"
        >>> len(temp_cache)  # 1 until entry expires
        1
    """

    def __init__(
        self, expiration_time: float, key_type: type[K] = str, lazy_expiration: bool = False
    ) -> None:
        """
        Initialize a TimedDict with a specified expiration time and key type constraint.

        Args:
            expiration_time: Time in seconds after which entries expire
            key_type: Type of keys that can be stored (default: str)
            lazy_expiration: If True, only check for expired entries on access;
                            if False, run a background thread to remove expired entries

        Raises:
            ValueError: If expiration_time is not positive
        """
        if expiration_time <= 0:
            raise ValueError("Expiration time must be positive")

        self.expiration_time: float = expiration_time
        self.key_type: type[K] = key_type
        self.lazy_expiration: bool = lazy_expiration

        # Core data structures
        self._entries: dict[K, tuple[V, float]] = {}  # Maps keys to (value, insertion timestamp)
        self._expiration_heap: list[tuple[float, int, K]] = []  # (expiry_time, sequence, key)
        self._sequence_counter: int = 0  # For stable ordering in the heap
        self._expired_entries_count: int = 0  # Count expired entries to trigger cleanup

        # Thread synchronization
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        self._condition = None if lazy_expiration else threading.Condition(self._lock)

        # Configuration with adaptive thresholds
        self._cleanup_threshold: int = 1000  # Base threshold for queue cleanup
        self._cleanup_ratio: float = 2.0  # Rebuild when queue > entries * ratio
        self._heap_size_limit: int = 100000  # Maximum heap size before forced cleanup
        self._adaptive_cleanup_factor: float = 0.1  # Percentage of entries to trigger cleanup

        # Start background worker if not in lazy mode
        self._worker_thread = None
        if not lazy_expiration:
            self._worker_thread = threading.Thread(
                target=self._expire_entries_periodically,
                daemon=True,
                name=f"TimedDict-Expiration-{id(self)}",
            )
            self._worker_thread.start()

        logger.debug(
            f"TimedDict initialized: expiration={expiration_time}s, "
            f"key_type={key_type.__name__}, lazy={lazy_expiration}"
        )

    def _expire_entries_periodically(self) -> None:
        """Worker thread function that periodically checks and removes expired entries."""
        check_interval = min(
            self.expiration_time / 10, 1.0
        )  # More frequent checks for responsiveness

        while not self._shutdown_event.is_set():
            # Remove expired entries
            self._remove_expired_entries()

            # Sleep with condition variable to allow waking up for state changes
            if self._condition is not None:
                with self._condition:
                    # Use wait_for to handle spurious wakeups and ensure timeout
                    self._condition.wait_for(
                        lambda: self._shutdown_event.is_set(), timeout=check_interval
                    )
            else:
                # Fallback to simple sleep if condition is None
                time.sleep(check_interval)

    def _remove_expired_entries(self) -> None:
        """Remove all expired entries from the dictionary."""
        with self._lock:
            if not self._expiration_heap:
                return

            current_time = time.monotonic()
            removed_count = 0

            # Process heap while the earliest entry is expired
            while self._expiration_heap and self._expiration_heap[0][0] <= current_time:
                expiry_time, _, key = heapq.heappop(self._expiration_heap)

                # Only remove if this is the current entry for the key
                if (
                    key in self._entries
                    and self._entries[key][1] <= current_time - self.expiration_time
                ):
                    del self._entries[key]
                    removed_count += 1

                self._expired_entries_count += 1

            # Rebuild heap if we've accumulated too many expired entries
            if (
                self._expired_entries_count > self._cleanup_threshold
                and len(self._expiration_heap) > len(self._entries) * self._cleanup_ratio
            ):
                self._rebuild_expiration_heap()

            if removed_count > 0:
                logger.debug(f"TimedDict: removed {removed_count} expired entries")

    def _rebuild_expiration_heap(self) -> None:
        """Rebuild the expiration heap to remove stale entries."""
        current_time = time.monotonic()
        heap_size = len(self._expiration_heap)
        entries_size = len(self._entries)

        # Calculate adaptive threshold based on current size
        adaptive_threshold = max(
            self._cleanup_threshold,
            min(int(entries_size * self._adaptive_cleanup_factor), self._heap_size_limit // 10),
        )

        # Early return if we don't need a rebuild yet
        if (
            self._expired_entries_count <= adaptive_threshold
            and heap_size <= entries_size * self._cleanup_ratio
        ):
            return

        start_time = time.monotonic()

        # For small heaps, or when heap is much larger than entries, rebuild from scratch
        if heap_size < 1000 or heap_size > entries_size * 3 or heap_size > self._heap_size_limit:
            # Create a fresh heap with only current entries
            valid_entries = []
            valid_entries_append = valid_entries.append  # Local reference for faster calls

            for key, (_, timestamp) in self._entries.items():
                expiry_time = timestamp + self.expiration_time
                if expiry_time > current_time:  # Only include non-expired entries
                    self._sequence_counter += 1
                    valid_entries_append((expiry_time, self._sequence_counter, key))

            # Replace the heap with our new clean version
            self._expiration_heap = valid_entries
            heapq.heapify(self._expiration_heap)
        else:
            # For larger heaps, filter in-place using a more efficient approach
            valid_keys = frozenset(self._entries.keys())  # Faster lookups with frozenset

            # Filter the heap in-place with a two-pointer approach
            i, write_idx = 0, 0
            while i < len(self._expiration_heap):
                entry = self._expiration_heap[i]
                _, _, key = entry
                if key in valid_keys:
                    if i != write_idx:
                        self._expiration_heap[write_idx] = entry
                    write_idx += 1
                i += 1

            # Truncate the heap to the correct size
            if write_idx < len(self._expiration_heap):
                self._expiration_heap = self._expiration_heap[:write_idx]

            # Restore heap property
            heapq.heapify(self._expiration_heap)

        self._expired_entries_count = 0

        # Log performance metrics for large heaps
        rebuild_time = time.monotonic() - start_time
        if heap_size > 10000:
            logger.debug(
                f"TimedDict: rebuilt expiration heap with {len(self._expiration_heap)} entries "
                f"in {rebuild_time:.4f}s (was {heap_size})"
            )
        else:
            logger.debug(
                f"TimedDict: rebuilt expiration heap with {len(self._expiration_heap)} entries"
            )

    def _check_expiration_if_lazy(self) -> None:
        """Check for expired entries when in lazy expiration mode."""
        if self.lazy_expiration:
            self._remove_expired_entries()

    def __setitem__(self, key: K, value: V) -> None:
        """
        Set a key-value pair in the dictionary with current timestamp.

        The entry will be automatically removed after expiration_time.
        If the key already exists, its value is updated and expiration timer is reset.

        Args:
            key: The key to set
            value: The value to associate with the key

        Raises:
            TypeError: If the key is not of the expected type
        """
        if not isinstance(key, self.key_type):
            raise TypeError(
                f"Expected key of type {self.key_type.__name__}, got {type(key).__name__}"
            )

        with self._lock:
            current_time = time.monotonic()

            # Add/update entry with current timestamp
            self._entries[key] = (value, current_time)

            # Add to expiration heap
            self._sequence_counter += 1
            expiry_time = current_time + self.expiration_time
            heapq.heappush(self._expiration_heap, (expiry_time, self._sequence_counter, key))

            # Signal the condition variable to optimize expiration checks
            if self._condition is not None:
                self._condition.notify()

            logger.debug(f"TimedDict: set key '{key}', expires in {self.expiration_time}s")

    def __getitem__(self, key: K) -> V:
        """
        Get the value associated with the key.

        In lazy expiration mode, this will trigger an expiration check.

        Args:
            key: The key to retrieve the value for

        Returns:
            The value associated with the key

        Raises:
            KeyError: If the key doesn't exist or has expired
        """
        with self._lock:
            self._check_expiration_if_lazy()
            if key in self._entries:
                return self._entries[key][0]
            raise KeyError(key)

    def get(self, key: K, default: V | None = None) -> V | None:
        """
        Get the value for key if it exists, otherwise return default.

        Args:
            key: The key to retrieve
            default: Value to return if key doesn't exist or has expired

        Returns:
            The value associated with key or default
        """
        with self._lock:
            self._check_expiration_if_lazy()
            if key in self._entries:
                return self._entries[key][0]
            return default

    def pop(self, key: K, default: Any = ...) -> V:
        """
        Remove key and return its value, or default if key doesn't exist.

        Args:
            key: The key to remove
            default: Value to return if key doesn't exist

        Returns:
            The value associated with the key or default

        Raises:
            KeyError: If key doesn't exist and no default is provided
        """
        with self._lock:
            self._check_expiration_if_lazy()
            if key in self._entries:
                value, _ = self._entries.pop(key)
                logger.debug(f"TimedDict: popped key '{key}'")
                return value
            if default is ...:
                raise KeyError(key)
            return default

    def time_remaining(self, key: K) -> float | None:
        """
        Get the time remaining before an entry expires.

        Args:
            key: The key to check

        Returns:
            float | None: Seconds remaining until expiration, or None if key not found
        """
        with self._lock:
            if key in self._entries:
                current_time = time.monotonic()
                _, timestamp = self._entries[key]
                elapsed = current_time - timestamp
                remaining = max(0.0, self.expiration_time - elapsed)
                return remaining
            return None

    def extend(self, key: K, extra_time: float) -> bool:
        """
        Extend the expiration time of an entry.

        Args:
            key: The key whose expiration to extend
            extra_time: Additional seconds to add to the entry's lifetime

        Returns:
            bool: True if the entry was found and extended, False otherwise
        """
        if extra_time <= 0:
            return False

        with self._lock:
            if key not in self._entries:
                return False

            # Get current value
            value, _ = self._entries[key]

            # Update with new timestamp
            current_time = time.monotonic()
            self._entries[key] = (value, current_time)

            # Add a new expiry entry
            new_expiry = current_time + self.expiration_time + extra_time
            self._sequence_counter += 1
            heapq.heappush(self._expiration_heap, (new_expiry, self._sequence_counter, key))

            # Check if we need to clean the heap
            if self._expired_entries_count > self._cleanup_threshold:
                self._rebuild_expiration_heap()

            logger.debug(f"TimedDict: extended key '{key}' expiration by {extra_time}s")
            return True

    def clear(self) -> None:
        """Remove all entries from the dictionary immediately."""
        with self._lock:
            entry_count = len(self._entries)
            self._entries.clear()
            self._expiration_heap.clear()
            self._expired_entries_count = 0
            self._sequence_counter = 0
            logger.debug(f"TimedDict: cleared {entry_count} entries")

    def contains(self, key: K) -> bool:
        """
        Check if a key is currently in the dictionary.

        In lazy expiration mode, this will trigger an expiration check.

        Args:
            key: The key to check for

        Returns:
            bool: True if the key is in the dictionary and not expired
        """
        with self._lock:
            self._check_expiration_if_lazy()
            return key in self._entries

    def __contains__(self, key: K) -> bool:
        """Support for 'in' operator to check if a key is in the dictionary."""
        return self.contains(key)

    def __delitem__(self, key: K) -> None:
        """Remove an entry from the dictionary."""
        with self._lock:
            if key in self._entries:
                del self._entries[key]
                logger.debug(f"TimedDict: deleted key '{key}'")
            else:
                raise KeyError(key)

    def __len__(self) -> int:
        """Return the number of non-expired entries in the dictionary."""
        with self._lock:
            self._check_expiration_if_lazy()
            return len(self._entries)

    def __iter__(self) -> Iterator[K]:
        """Return an iterator over non-expired keys in the dictionary."""
        with self._lock:
            self._check_expiration_if_lazy()
            # Create a safe copy for iteration to avoid concurrent modification issues
            return iter(list(self._entries.keys()))

    def keys(self) -> list[K]:
        """
        Return a list of all keys in the dictionary.

        Returns:
            list[K]: List of non-expired keys
        """
        with self._lock:
            self._check_expiration_if_lazy()
            return list(self._entries.keys())

    def values(self) -> list[V]:
        """
        Return a list of all values in the dictionary.

        Returns:
            list[V]: List of values associated with non-expired keys
        """
        with self._lock:
            self._check_expiration_if_lazy()
            return [value for value, _ in self._entries.values()]

    def items(self) -> list[tuple[K, V]]:
        """
        Return a list of all key-value pairs in the dictionary.

        Returns:
            list[tuple[K, V]]: List of (key, value) pairs for non-expired entries
        """
        with self._lock:
            self._check_expiration_if_lazy()
            return [(k, v) for k, (v, _) in self._entries.items()]

    def items_with_expiry(self) -> dict[K, tuple[V, float]]:
        """
        Return all entries with their expiration times.

        Returns:
            Dict[K, Tuple[V, float]]: Dictionary mapping keys to (value, expiration timestamp) tuples
        """
        with self._lock:
            self._check_expiration_if_lazy()
            return {
                key: (value, timestamp + self.expiration_time)
                for key, (value, timestamp) in self._entries.items()
            }

    def update(self, mapping: Mapping[K, V] | None = None, **kwargs: V) -> None:
        """
        Update the dictionary with key/value pairs from mapping or keyword arguments.

        Args:
            mapping: A mapping object with keys and values
            **kwargs: Key/value pairs to update the dictionary with

        Raises:
            TypeError: If any key is not of the expected type
        """
        with self._lock:
            current_time = time.monotonic()
            new_heap_entries = []

            # Process the mapping argument
            if mapping:
                for key, value in mapping.items():
                    if not isinstance(key, self.key_type):
                        raise TypeError(
                            f"Expected key of type {self.key_type.__name__}, got {type(key).__name__}"
                        )

                    # Add/update entry
                    self._entries[key] = (value, current_time)

                    # Prepare heap entry
                    self._sequence_counter += 1
                    expiry_time = current_time + self.expiration_time
                    new_heap_entries.append((expiry_time, self._sequence_counter, key))

            # Process keyword arguments
            for key, value in kwargs.items():
                if not isinstance(key, self.key_type):
                    raise TypeError(
                        f"Expected key of type {self.key_type.__name__}, got {type(key).__name__}"
                    )

                # Add/update entry
                self._entries[key] = (value, current_time)

                # Prepare heap entry
                self._sequence_counter += 1
                expiry_time = current_time + self.expiration_time
                new_heap_entries.append((expiry_time, self._sequence_counter, key))

            # Add all entries to the heap efficiently
            if len(new_heap_entries) <= 10:
                for entry in new_heap_entries:
                    heapq.heappush(self._expiration_heap, entry)
            elif new_heap_entries:
                self._expiration_heap.extend(new_heap_entries)
                heapq.heapify(self._expiration_heap)

            if new_heap_entries:
                logger.debug(f"TimedDict: updated {len(new_heap_entries)} entries")

    def __str__(self) -> str:
        """Return a string representation of the dictionary."""
        with self._lock:
            self._check_expiration_if_lazy()
            entries_str = ", ".join(
                f"{key!r}: {value!r} ({round(self.time_remaining(key) or 0, 1)}s)"
                for key, (value, _) in self._entries.items()
            )
            return f"TimedDict({{{entries_str}}})"

    def __repr__(self) -> str:
        """Return a detailed string representation of the TimedDict."""
        with self._lock:
            return (
                f"TimedDict(expiration_time={self.expiration_time}, "
                f"key_type={self.key_type.__name__}, "
                f"lazy_expiration={self.lazy_expiration}, "
                f"entries={len(self._entries)})"
            )

    def shutdown(self) -> None:
        """
        Shut down the worker thread gracefully.

        This should be called before application exit to ensure clean shutdown.
        """
        if hasattr(self, "_shutdown_event") and self._shutdown_event is not None:
            self._shutdown_event.set()

            if (
                hasattr(self, "_worker_thread")
                and self._worker_thread is not None
                and self._worker_thread.is_alive()
            ):
                self._worker_thread.join(timeout=2.0)
                if self._worker_thread.is_alive():
                    logger.warning("TimedDict: Worker thread did not terminate within timeout")
                else:
                    logger.debug("TimedDict: Worker thread shut down successfully")

    def __del__(self) -> None:
        """Ensure cleanup on garbage collection."""
        try:
            self.shutdown()
        except Exception:
            # Avoid exceptions during garbage collection
            pass
