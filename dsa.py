"""Explicit Data Structures & Algorithms (DSA) Implementation.

Contains strictly from-scratch algorithmic routines without relying on
built-in Python DSA utilities (.sort(), sorted(), min(), max(), sum(), any(), all()).

Routines:
- custom_sort: In-place Selection Sort / Dual-key sorting O(N^2)
- custom_min: Iterative linear-scan minimum O(N)
- custom_max: Iterative linear-scan maximum O(N)
- custom_sum: Iterative accumulation summation O(N)
- custom_any: Short-circuit linear existential scan O(N)
- custom_all: Short-circuit linear universal scan O(N)
- linear_search: Linear predicate scan O(N)
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, List, Optional, TypeVar

T = TypeVar("T")


def custom_sort(
    arr: List[T],
    key: Optional[Callable[[T], Any]] = None,
    reverse: bool = False,
) -> List[T]:
    """In-place Selection Sort algorithm written explicitly from scratch.
    
    Time Complexity: O(N^2) comparisons, O(N) swaps.
    Space Complexity: O(1) auxiliary space (in-place).
    
    Args:
        arr: The list of elements to sort in-place.
        key: Optional extraction function to compute comparison keys.
        reverse: If True, sort in descending order; otherwise ascending.
        
    Returns:
        The same list reference, sorted in-place.
    """
    n = len(arr)
    for i in range(n - 1):
        target_idx = i
        for j in range(i + 1, n):
            val_j = key(arr[j]) if key is not None else arr[j]
            val_target = key(arr[target_idx]) if key is not None else arr[target_idx]

            if reverse:
                # Descending order: look for larger values
                if val_j > val_target:
                    target_idx = j
            else:
                # Ascending order: look for smaller values
                if val_j < val_target:
                    target_idx = j

        # Swap elements if target index changed
        if target_idx != i:
            arr[i], arr[target_idx] = arr[target_idx], arr[i]

    return arr


def custom_min(*args: Any) -> Any:
    """Explicit minimum computation via single-pass linear scan.
    
    Time Complexity: O(N)
    Space Complexity: O(1)
    
    Accepts either multiple scalar arguments (e.g. custom_min(a, b, c))
    or a single iterable sequence (e.g. custom_min([1, 2, 3])).
    """
    if len(args) == 0:
        raise ValueError("custom_min expected at least 1 argument, got 0")
    
    if len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], (str, bytes)):
        elements = args[0]
    else:
        elements = args

    smallest = None
    is_first = True
    for val in elements:
        if is_first:
            smallest = val
            is_first = False
        elif val < smallest:
            smallest = val

    if is_first:
        raise ValueError("custom_min arg is an empty sequence")
    return smallest


def custom_max(*args: Any) -> Any:
    """Explicit maximum computation via single-pass linear scan.
    
    Time Complexity: O(N)
    Space Complexity: O(1)
    
    Accepts either multiple scalar arguments (e.g. custom_max(a, b, c))
    or a single iterable sequence (e.g. custom_max([1, 2, 3])).
    """
    if len(args) == 0:
        raise ValueError("custom_max expected at least 1 argument, got 0")
    
    if len(args) == 1 and hasattr(args[0], "__iter__") and not isinstance(args[0], (str, bytes)):
        elements = args[0]
    else:
        elements = args

    largest = None
    is_first = True
    for val in elements:
        if is_first:
            largest = val
            is_first = False
        elif val > largest:
            largest = val

    if is_first:
        raise ValueError("custom_max arg is an empty sequence")
    return largest


def custom_sum(iterable: Iterable[Any], start: float = 0.0) -> float:
    """Explicit accumulation summation without built-in sum().
    
    Time Complexity: O(N)
    Space Complexity: O(1)
    """
    accumulator = start
    for item in iterable:
        accumulator += item
    return accumulator


def custom_any(iterable: Iterable[Any]) -> bool:
    """Explicit short-circuit existential scan without built-in any().
    
    Time Complexity: O(N) worst case, O(1) best case.
    Space Complexity: O(1)
    """
    for item in iterable:
        if item:
            return True
    return False


def custom_all(iterable: Iterable[Any]) -> bool:
    """Explicit short-circuit universal scan without built-in all().
    
    Time Complexity: O(N) worst case, O(1) best case.
    Space Complexity: O(1)
    """
    for item in iterable:
        if not item:
            return False
    return True


def linear_search(items: Iterable[T], predicate: Callable[[T], bool]) -> Optional[T]:
    """Explicit linear scan search without built-in filtering helpers.
    
    Time Complexity: O(N)
    Space Complexity: O(1)
    """
    for elem in items:
        if predicate(elem):
            return elem
    return None
