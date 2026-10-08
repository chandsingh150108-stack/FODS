"""Packing engine for 3D factory and warehouse bin packing.

Contains the algorithmic strategies:
- In-place Selection Sort (Volume descending, Weight descending tie-breaker)
- Extreme Point / Corner Candidate Position Generation
- Lexicographical Position Comparison (Lower Z, Smaller Y, Smaller X, Lower Height)
- Greedy Best-Fit Multi-Container Allocation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from models import Container, Item, approximately_equal


@dataclass
class Placement:
    """Represents a placement solution for an item inside a container."""

    x: float
    y: float
    z: float
    length: float
    width: float
    height: float


class CandidatePositionGenerator:
    """Generates candidate 3D corner coordinates where items can be placed."""

    @staticmethod
    def _is_duplicate(
        candidates: List[Tuple[float, float, float]],
        x: float,
        y: float,
        z: float,
    ) -> bool:
        """Check if candidate coordinates already exist within tolerance."""
        for cx, cy, cz in candidates:
            if (
                approximately_equal(cx, x)
                and approximately_equal(cy, y)
                and approximately_equal(cz, z)
            ):
                return True
        return False

    @classmethod
    def generate(cls, container: Container) -> List[Tuple[float, float, float]]:
        """Generate candidate positions from the container origin and packed items' faces."""
        candidates: List[Tuple[float, float, float]] = []

        # Always evaluate the container floor origin first
        candidates.append((0.0, 0.0, 0.0))

        # Generate adjacent corner candidates from all already-placed items
        for existing in container.packed_items:
            # 1. Right side
            rx = existing.x + existing.packed_length
            ry = existing.y
            rz = existing.z
            if not cls._is_duplicate(candidates, rx, ry, rz):
                candidates.append((rx, ry, rz))

            # 2. Front side
            fx = existing.x
            fy = existing.y + existing.packed_width
            fz = existing.z
            if not cls._is_duplicate(candidates, fx, fy, fz):
                candidates.append((fx, fy, fz))

            # 3. Top face
            tx = existing.x
            ty = existing.y
            tz = existing.z + existing.packed_height
            if not cls._is_duplicate(candidates, tx, ty, tz):
                candidates.append((tx, ty, tz))

        return candidates


class PositionComparator:
    """Compares candidate positions to pick the optimal location."""

    @staticmethod
    def is_better(
        x: float,
        y: float,
        z: float,
        height: float,
        best: Optional[Placement],
    ) -> bool:
        """Evaluate if the new candidate position is preferable to the current best.

        Priority order:
        1. Lower Z (keeps heavy items grounded and lowers center of gravity)
        2. Smaller Y (compact along width/depth)
        3. Smaller X (compact along length)
        4. Smaller Height (minimizes upward protrusion)
        """
        if best is None:
            return True

        if z < best.z:
            return True
        if z > best.z:
            return False

        if y < best.y:
            return True
        if y > best.y:
            return False

        if x < best.x:
            return True
        if x > best.x:
            return False

        if height < best.height:
            return True

        return False


class PackingEngine:
    """Orchestrates sorting, candidate evaluation, constraint checking, and Best-Fit packing."""

    def __init__(self) -> None:
        self.candidate_generator = CandidatePositionGenerator()
        self.comparator = PositionComparator()

    def sort_items(self, items: List[Item]) -> None:
        """Sort items in-place using Selection Sort.

        Priority:
        1. Volume (descending - largest objects packed first)
        2. Weight (descending - heavier objects prioritized on tie)
        """
        count = len(items)
        for i in range(count - 1):
            best_position = i
            for j in range(i + 1, count):
                current = items[j]
                best = items[best_position]

                if current.volume > best.volume:
                    best_position = j
                elif approximately_equal(current.volume, best.volume):
                    if current.weight > best.weight:
                        best_position = j

            if best_position != i:
                items[i], items[best_position] = items[best_position], items[i]

    def find_best_position(self, container: Container, item: Item) -> Optional[Placement]:
        """Find the optimal legal placement for an item in a given container."""
        orientations = item.generate_orientations()
        candidates = self.candidate_generator.generate(container)

        best_placement: Optional[Placement] = None

        for orientation in orientations:
            for x, y, z in candidates:
                if container.can_place(
                    item, x, y, z, orientation.length, orientation.width, orientation.height
                ):
                    if self.comparator.is_better(x, y, z, orientation.height, best_placement):
                        best_placement = Placement(
                            x=x,
                            y=y,
                            z=z,
                            length=orientation.length,
                            width=orientation.width,
                            height=orientation.height,
                        )

        return best_placement

    def pack(
        self,
        containers: List[Container],
        items: List[Item],
        verbose: bool = True,
    ) -> List[Item]:
        """Pack all items into containers using the Best-Fit strategy."""
        if verbose:
            print()
            print("=" * 70)
            print("PACKING ALGORITHM STARTED")
            print("=" * 70)
            print()

        # Reset container & item state
        for container in containers:
            container.reset()
        for item in items:
            item.reset_placement()
            item.volume = item.calculate_volume()

        # Sort items: largest and heaviest first
        self.sort_items(items)

        # Place each item
        for item in items:
            best_container: Optional[Container] = None
            best_placement: Optional[Placement] = None
            best_remaining_volume = float("inf")

            # Evaluate each container to find the best fit
            for container in containers:
                placement = self.find_best_position(container, item)
                if placement is not None:
                    # Remaining volume after hypothetically packing this item
                    remaining_vol = (
                        container.total_volume
                        - container.used_volume
                        - item.volume
                    )

                    if best_container is None or remaining_vol < best_remaining_volume:
                        best_container = container
                        best_placement = placement
                        best_remaining_volume = remaining_vol

            if best_container is not None and best_placement is not None:
                best_container.place_item(
                    item,
                    best_placement.x,
                    best_placement.y,
                    best_placement.z,
                    best_placement.length,
                    best_placement.width,
                    best_placement.height,
                )
                if verbose:
                    print(
                        f"[PACKED] {item.name} -> Container {best_container.id} | "
                        f"Position: ({round(best_placement.x, 2)}, "
                        f"{round(best_placement.y, 2)}, {round(best_placement.z, 2)})"
                    )
            else:
                if verbose:
                    print(f"[NOT PACKED] {item.name} -> No safe position found.")

        return items

