"""Resource management for Heroes HD."""
from dataclasses import dataclass, field
from config import RESOURCES, STARTING_GOLD, STARTING_WOOD, STARTING_ORE


@dataclass
class Resources:
    """Holds all resource quantities for a player."""
    gold: int = STARTING_GOLD
    wood: int = STARTING_WOOD
    ore: int = STARTING_ORE
    mercury: int = 0
    sulfur: int = 0
    crystal: int = 0
    gems: int = 0

    def as_dict(self) -> dict[str, int]:
        return {r: getattr(self, r) for r in RESOURCES}

    def can_afford(self, cost: dict[str, int]) -> bool:
        return all(getattr(self, res, 0) >= amt for res, amt in cost.items())

    def spend(self, cost: dict[str, int]) -> bool:
        if not self.can_afford(cost):
            return False
        for res, amt in cost.items():
            setattr(self, res, getattr(self, res) - amt)
        return True

    def add(self, income: dict[str, int]):
        for res, amt in income.items():
            if hasattr(self, res):
                setattr(self, res, getattr(self, res) + amt)

    def __add__(self, other: "Resources") -> "Resources":
        return Resources(**{r: getattr(self, r) + getattr(other, r) for r in RESOURCES})

    def __iadd__(self, other: "Resources") -> "Resources":
        for r in RESOURCES:
            setattr(self, r, getattr(self, r) + getattr(other, r))
        return self

    def copy(self) -> "Resources":
        return Resources(**{r: getattr(self, r) for r in RESOURCES})
