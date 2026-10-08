"""Pre-defined factory scenarios and scenario definitions.

Provides:
- Scenario: Data container combining containers, items, metadata.
- ScenarioRepository: Factory methods creating the 4 standard factory test conditions
  and custom scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from models import Container, Item


@dataclass
class Scenario:
    """Represents a packing scenario including containers, items, and metadata."""

    name: str
    description: str
    containers: List[Container]
    items: List[Item]


class ScenarioRepository:
    """Factory for standard benchmarks and custom factory scenarios."""

    @staticmethod
    def get_test_condition_one() -> Scenario:
        """Test Condition 1: Basic factory components with varied sizes, weights, shapes."""
        containers = [
            Container(id=1, length=12.0, width=10.0, height=10.0, maximum_weight=120.0),
        ]

        items = [
            Item(
                id=1,
                name="Industrial Motor",
                length=5.0,
                width=4.0,
                height=3.0,
                weight=20.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=2,
                name="Control Box",
                length=4.0,
                width=3.0,
                height=2.0,
                weight=10.0,
                shape="cuboid",
                fragile=True,
                stackable=False,
                rotatable=True,
            ),
            Item(
                id=3,
                name="Metal Pump",
                length=4.0,
                width=4.0,
                height=3.0,
                weight=18.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=4,
                name="Sensor Package",
                length=3.0,
                width=2.0,
                height=2.0,
                weight=5.0,
                shape="flat",
                fragile=True,
                stackable=False,
                rotatable=True,
            ),
            Item(
                id=5,
                name="Steel Block",
                length=3.0,
                width=3.0,
                height=3.0,
                weight=22.0,
                shape="cube",
                fragile=False,
                stackable=True,
                rotatable=False,
            ),
        ]

        return Scenario(
            name="TEST CONDITION 1 - BASIC FACTORY PACKING",
            description="Basic factory components with different sizes, weights and shapes.",
            containers=containers,
            items=items,
        )

    @staticmethod
    def get_test_condition_two() -> Scenario:
        """Test Condition 2: Safety, fragility, and stacking stability."""
        containers = [
            Container(id=1, length=10.0, width=10.0, height=12.0, maximum_weight=150.0),
        ]

        items = [
            Item(
                id=1,
                name="Heavy Gear",
                length=5.0,
                width=5.0,
                height=3.0,
                weight=40.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=2,
                name="Steel Motor",
                length=4.0,
                width=4.0,
                height=3.0,
                weight=30.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=3,
                name="Glass Sensor",
                length=3.0,
                width=3.0,
                height=2.0,
                weight=5.0,
                shape="cuboid",
                fragile=True,
                stackable=False,
                rotatable=False,
            ),
            Item(
                id=4,
                name="Electronic Board",
                length=4.0,
                width=2.0,
                height=1.0,
                weight=4.0,
                shape="flat",
                fragile=True,
                stackable=False,
                rotatable=True,
            ),
            Item(
                id=5,
                name="Pipe Assembly",
                length=3.0,
                width=3.0,
                height=5.0,
                weight=12.0,
                shape="cylinder",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
        ]

        return Scenario(
            name="TEST CONDITION 2 - SAFETY AND FRAGILITY",
            description="Demonstrates heavy items, fragile items, stackability and safe stacking.",
            containers=containers,
            items=items,
        )

    @staticmethod
    def get_test_condition_three() -> Scenario:
        """Test Condition 3: Multiple containers and Best-Fit selection."""
        containers = [
            Container(id=1, length=8.0, width=8.0, height=8.0, maximum_weight=70.0),
            Container(id=2, length=12.0, width=10.0, height=10.0, maximum_weight=120.0),
            Container(id=3, length=7.0, width=7.0, height=12.0, maximum_weight=80.0),
        ]

        items = [
            Item(
                id=1,
                name="Large Motor",
                length=6.0,
                width=5.0,
                height=4.0,
                weight=30.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=2,
                name="Pump",
                length=5.0,
                width=4.0,
                height=3.0,
                weight=20.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=3,
                name="Control Panel",
                length=4.0,
                width=3.0,
                height=2.0,
                weight=8.0,
                shape="flat",
                fragile=True,
                stackable=False,
                rotatable=True,
            ),
            Item(
                id=4,
                name="Metal Cylinder",
                length=3.0,
                width=3.0,
                height=5.0,
                weight=15.0,
                shape="cylinder",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=5,
                name="Gear Box",
                length=3.0,
                width=3.0,
                height=3.0,
                weight=12.0,
                shape="cube",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=6,
                name="Sensor",
                length=2.0,
                width=2.0,
                height=2.0,
                weight=3.0,
                shape="cube",
                fragile=True,
                stackable=False,
                rotatable=False,
            ),
            Item(
                id=7,
                name="Small Motor",
                length=3.0,
                width=3.0,
                height=3.0,
                weight=10.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=8,
                name="Electronics Box",
                length=3.0,
                width=2.0,
                height=2.0,
                weight=5.0,
                shape="cuboid",
                fragile=True,
                stackable=False,
                rotatable=True,
            ),
        ]

        return Scenario(
            name="TEST CONDITION 3 - MULTIPLE CONTAINERS",
            description="Demonstrates Best-Fit container selection and space utilization.",
            containers=containers,
            items=items,
        )

    @staticmethod
    def get_test_condition_four() -> Scenario:
        """Test Condition 4: Large production batch with multiple containers."""
        containers = [
            Container(id=1, length=12.0, width=10.0, height=10.0, maximum_weight=150.0),
            Container(id=2, length=12.0, width=10.0, height=10.0, maximum_weight=150.0),
            Container(id=3, length=10.0, width=10.0, height=12.0, maximum_weight=140.0),
        ]

        items = [
            Item(
                id=1,
                name="Hydraulic Motor",
                length=5.0,
                width=4.0,
                height=3.0,
                weight=25.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=2,
                name="Industrial Pump",
                length=5.0,
                width=4.0,
                height=3.0,
                weight=23.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=3,
                name="Steel Housing",
                length=4.0,
                width=4.0,
                height=4.0,
                weight=28.0,
                shape="cube",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=4,
                name="Gear Assembly",
                length=4.0,
                width=3.0,
                height=3.0,
                weight=18.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=5,
                name="Pressure Cylinder",
                length=3.0,
                width=3.0,
                height=5.0,
                weight=15.0,
                shape="cylinder",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=6,
                name="Pipe Assembly",
                length=2.5,
                width=2.5,
                height=5.0,
                weight=10.0,
                shape="cylinder",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=7,
                name="PLC Controller",
                length=3.0,
                width=2.0,
                height=2.0,
                weight=5.0,
                shape="cuboid",
                fragile=True,
                stackable=False,
                rotatable=True,
            ),
            Item(
                id=8,
                name="Control Board",
                length=4.0,
                width=2.0,
                height=1.0,
                weight=3.0,
                shape="flat",
                fragile=True,
                stackable=False,
                rotatable=True,
            ),
            Item(
                id=9,
                name="Temperature Sensor",
                length=2.0,
                width=2.0,
                height=2.0,
                weight=2.0,
                shape="cube",
                fragile=True,
                stackable=False,
                rotatable=False,
            ),
            Item(
                id=10,
                name="Bearing Box",
                length=3.0,
                width=3.0,
                height=2.0,
                weight=7.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=11,
                name="Valve Assembly",
                length=3.0,
                width=3.0,
                height=3.0,
                weight=8.0,
                shape="cuboid",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
            Item(
                id=12,
                name="Small Gear",
                length=2.0,
                width=2.0,
                height=2.0,
                weight=4.0,
                shape="cube",
                fragile=False,
                stackable=True,
                rotatable=True,
            ),
        ]

        return Scenario(
            name="TEST CONDITION 4 - FACTORY PRODUCTION BATCH",
            description="Large mixed factory batch demonstrating sorting, multiple containers, safety and space utilization.",
            containers=containers,
            items=items,
        )

    @staticmethod
    def create_custom_scenario(
        containers: List[Container],
        items: List[Item],
    ) -> Scenario:
        """Create a custom user-defined scenario."""
        return Scenario(
            name="CUSTOM FACTORY INPUT",
            description="User-defined factory items packed using the constraint-based 3D bin packing algorithm.",
            containers=containers,
            items=items,
        )

