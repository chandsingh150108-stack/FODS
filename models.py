"""Domain models for 3D factory and warehouse bin packing.

Defines the core data structures and physics/containment logic:
- Orientation: Spatial 3D dimensions of an item.
- Item: Physical object to be packed with geometric and safety attributes.
- Container: Warehouse bin with volume, weight capacity, and placement constraints.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional


def approximately_equal(a: float, b: float, tolerance: float = 0.001) -> bool:
    """Check whether two floating point numbers are equal within a small tolerance."""
    return abs(a - b) < tolerance


def boxes_overlap(
    x1: float,
    y1: float,
    z1: float,
    length1: float,
    width1: float,
    height1: float,
    x2: float,
    y2: float,
    z2: float,
    length2: float,
    width2: float,
    height2: float,
) -> bool:
    """Check whether two 3D axis-aligned bounding boxes overlap."""
    if x1 + length1 <= x2 or x2 + length2 <= x1:
        return False
    if y1 + width1 <= y2 or y2 + width2 <= y1:
        return False
    if z1 + height1 <= z2 or z2 + height2 <= z1:
        return False
    return True


@dataclass(frozen=True)
class Orientation:
    """Represents a specific 3D orientation (length, width, height) of an item."""

    length: float
    width: float
    height: float

    def matches(self, other_length: float, other_width: float, other_height: float) -> bool:
        """Check if this orientation matches given dimensions within tolerance."""
        return (
            approximately_equal(self.length, other_length)
            and approximately_equal(self.width, other_width)
            and approximately_equal(self.height, other_height)
        )


@dataclass
class Item:
    """Represents a factory or warehouse item to be placed inside a container."""

    id: int
    name: str
    length: float
    width: float
    height: float
    weight: float
    shape: str  # 'cuboid', 'cube', 'cylinder', 'sphere', 'wedge', 'pyramid', 'capsule', 'hexagonal_prism', 'torus', 'flat'
    fragile: bool
    stackable: bool
    rotatable: bool

    # Calculated physical attributes
    volume: float = 0.0

    # Packing state
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    packed_length: float = 0.0
    packed_width: float = 0.0
    packed_height: float = 0.0
    container_id: int = -1
    packed: bool = False

    SUPPORTED_SHAPES = (
        "cuboid",
        "cube",
        "cylinder",
        "sphere",
        "wedge",
        "pyramid",
        "capsule",
        "hexagonal_prism",
        "torus",
        "flat",
    )

    def __post_init__(self) -> None:
        if self.volume <= 0.0:
            self.volume = self.calculate_volume()

    def calculate_volume(self) -> float:
        """Calculate item volume based on geometric shape."""
        l, w, h = max(0.001, self.length), max(0.001, self.width), max(0.001, self.height)
        s = (self.shape or "cuboid").lower().strip()

        if s == "cylinder":
            # Circular / elliptical cylinder: pi * (l/2) * (w/2) * h
            return math.pi * (l / 2.0) * (w / 2.0) * h
        elif s == "sphere":
            # Ellipsoid / sphere: 4/3 * pi * (l/2) * (w/2) * (h/2)
            return (4.0 / 3.0) * math.pi * (l / 2.0) * (w / 2.0) * (h / 2.0)
        elif s in ("wedge", "triangular_prism"):
            # Right triangular prism: 1/2 * l * w * h
            return 0.5 * l * w * h
        elif s == "pyramid":
            # 4-sided pyramid: 1/3 * base_area * h
            return (1.0 / 3.0) * l * w * h
        elif s == "hexagonal_prism":
            # Regular hexagonal prism inscribed in l x w: area ~ 3*sqrt(3)/8 * l * w
            return (3.0 * math.sqrt(3.0) / 8.0) * l * w * h
        elif s == "capsule":
            # Cylinder with 2 hemispherical end caps
            r_cap = min(l, w, h) / 2.0
            cyl_h = max(0.0, h - 2.0 * r_cap)
            cyl_vol = math.pi * (l / 2.0) * (w / 2.0) * cyl_h
            sph_vol = (4.0 / 3.0) * math.pi * (r_cap ** 3)
            return cyl_vol + sph_vol
        elif s == "torus":
            # Torus with major radius R and tube radius r
            r_tube = h / 2.0
            r_major = max(0.001, (min(l, w) / 2.0) - r_tube)
            return 2.0 * (math.pi ** 2) * r_major * (r_tube ** 2)
        # Default for cuboid, cube, flat
        return l * w * h

    def generate_orientations(self) -> List[Orientation]:
        """Generate all unique valid 3D orientations for this item."""
        if not self.rotatable:
            return [Orientation(self.length, self.width, self.height)]

        possible = [
            (self.length, self.width, self.height),
            (self.length, self.height, self.width),
            (self.width, self.length, self.height),
            (self.width, self.height, self.length),
            (self.height, self.length, self.width),
            (self.height, self.width, self.length),
        ]

        unique_orientations: List[Orientation] = []
        for l, w, h in possible:
            if not any(o.matches(l, w, h) for o in unique_orientations):
                unique_orientations.append(Orientation(l, w, h))

        return unique_orientations

    def reset_placement(self) -> None:
        """Reset item packing status and coordinates."""
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.packed_length = 0.0
        self.packed_width = 0.0
        self.packed_height = 0.0
        self.container_id = -1
        self.packed = False


@dataclass
class Container:
    """Represents a container with physical bounds, weight limit, and placed items."""

    id: int
    length: float
    width: float
    height: float
    maximum_weight: float

    used_weight: float = 0.0
    used_volume: float = 0.0
    packed_items: List[Item] = field(default_factory=list)

    @property
    def total_volume(self) -> float:
        """Total volume capacity of the container."""
        return self.length * self.width * self.height

    @property
    def remaining_volume(self) -> float:
        """Unused volume inside the container."""
        return self.total_volume - self.used_volume

    @property
    def remaining_weight(self) -> float:
        """Remaining weight capacity of the container."""
        return self.maximum_weight - self.used_weight

    @property
    def utilization_percentage(self) -> float:
        """Percentage of container volume utilized."""
        if self.total_volume <= 0:
            return 0.0
        return (self.used_volume / self.total_volume) * 100.0

    def fits_boundaries(
        self, x: float, y: float, z: float, length: float, width: float, height: float
    ) -> bool:
        """Check whether the bounding box fits within the container physical walls."""
        if x < 0 or y < 0 or z < 0:
            return False
        if x + length > self.length:
            return False
        if y + width > self.width:
            return False
        if z + height > self.height:
            return False
        return True

    def can_accommodate_weight(self, weight: float) -> bool:
        """Check if adding the given weight exceeds the container maximum weight."""
        return (self.used_weight + weight) <= self.maximum_weight

    def collision_exists(
        self, x: float, y: float, z: float, length: float, width: float, height: float
    ) -> bool:
        """Check if proposed box collides with any already packed item in this container."""
        for existing in self.packed_items:
            if boxes_overlap(
                x,
                y,
                z,
                length,
                width,
                height,
                existing.x,
                existing.y,
                existing.z,
                existing.packed_length,
                existing.packed_width,
                existing.packed_height,
            ):
                return True
        return False

    def support_is_valid(
        self,
        item: Item,
        x: float,
        y: float,
        z: float,
        length: float,
        width: float,
        height: float,
    ) -> bool:
        """Check whether the item has a valid, safe physical foundation."""
        # Condition 1: Object resting directly on container floor
        if approximately_equal(z, 0):
            return True

        # Condition 2: Resting on top of one or more existing items
        for support in self.packed_items:
            support_top = support.z + support.packed_height
            if not approximately_equal(support_top, z):
                continue

            # Fragile items cannot support other items
            if support.fragile:
                continue

            # Non-stackable items cannot support other items
            if not support.stackable:
                continue

            # Heavier items cannot be placed on lighter items
            if item.weight > support.weight:
                continue

            # Calculate 2D contact footprint in XY plane
            overlap_x = max(
                0.0,
                min(x + length, support.x + support.packed_length) - max(x, support.x),
            )
            overlap_y = max(
                0.0,
                min(y + width, support.y + support.packed_width) - max(y, support.y),
            )

            overlap_area = overlap_x * overlap_y
            item_area = length * width

            # Require minimum 50% footprint support for stability
            if item_area > 0 and (overlap_area / item_area) >= 0.50:
                return True

        return False

    def can_place(
        self,
        item: Item,
        x: float,
        y: float,
        z: float,
        length: float,
        width: float,
        height: float,
    ) -> bool:
        """Validate all safety and space constraints for placing an item at (x, y, z)."""
        # Constraint 1: Inside container boundaries
        if not self.fits_boundaries(x, y, z, length, width, height):
            return False

        # Constraint 2: Maximum weight capacity
        if not self.can_accommodate_weight(item.weight):
            return False

        # Constraint 3: No overlap / collision with existing items
        if self.collision_exists(x, y, z, length, width, height):
            return False

        # Constraint 4: Structural support & stacking safety
        if not self.support_is_valid(item, x, y, z, length, width, height):
            return False

        return True

    def place_item(
        self,
        item: Item,
        x: float,
        y: float,
        z: float,
        length: float,
        width: float,
        height: float,
    ) -> None:
        """Place an item into the container and update container metrics."""
        item.x = x
        item.y = y
        item.z = z
        item.packed_length = length
        item.packed_width = width
        item.packed_height = height
        item.container_id = self.id
        item.packed = True

        self.packed_items.append(item)
        self.used_weight += item.weight
        self.used_volume += length * width * height

    def reset(self) -> None:
        """Reset container state and clear all packed items."""
        self.used_weight = 0.0
        self.used_volume = 0.0
        self.packed_items.clear()

