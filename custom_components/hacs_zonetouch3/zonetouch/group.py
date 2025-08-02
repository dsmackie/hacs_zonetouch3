"""Group file."""

from dataclasses import dataclass
from enum import Enum
import struct
from typing import Self


class GroupPowerStatus(Enum):
    """Group Power Status."""

    NO_ZONE = -1
    ON = 1
    OFF = 0
    TURBO = 2


@dataclass
class ZoneTouch3Group:
    """ZoneTouch3 Group class."""

    id: int
    name: str
    position: int
    status: GroupPowerStatus
    is_support_turbo: bool
    is_spill_on: bool

    @classmethod
    def parse_group_names(cls, data: bytes, count: int, length: int) -> dict[int, str]:
        """Parse group names."""
        group_names: dict[int, str] = {}
        name_len: int = struct.unpack_from(">B", data)[0]
        for x in range(count):
            (groupIndex, name) = struct.unpack_from(
                f">B{name_len}s", data, (length * x) + 2
            )
            name = name.decode("utf-8").rstrip("\x00").strip()
            group_names[groupIndex] = name
        return group_names

    @classmethod
    def parse_group_control(
        cls, data: bytes, count: int, length: int
    ) -> dict[int, Self]:
        """Parse groups."""
        groups: dict[int, Self] = {}
        data_len = 8
        for idx in range(count):
            index: int = struct.unpack_from(">B", data, (data_len * idx) + 0)[0]
            position = struct.unpack_from(">B", data, (data_len * idx) + 1)[0]
            sign = struct.unpack_from(">B", data, (data_len * idx) + 6)[0]

            groupIndex = index & 0x3F
            powerStatus = GroupPowerStatus(index >> 6)
            is_support_turbo = (sign & 0x80) != 0
            is_spill_on = (sign & 0x02) != 0

            groups[groupIndex] = cls(
                groupIndex,
                "",
                position,
                powerStatus,
                is_support_turbo,
                is_spill_on,
            )

        return groups
