"""Zone class."""

from dataclasses import dataclass


@dataclass
class ZoneTouch3Zone:
    """A class for holding Zone information."""

    id: int
    name: str
    position: int

    def __str__(self):
        """Return a string representation of a zone."""
        return f"""
        Group ID:\t{self.id}
        Group Name:\t{self.name}`
        Group Position:\t{self.position}
        """
