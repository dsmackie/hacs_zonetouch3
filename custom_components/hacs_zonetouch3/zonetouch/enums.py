"""ZoneTouch3 Enum Constants."""

from enum import Enum


class Protocol(Enum):
    """Protocol header bytes."""

    PROTOCOL_HEAD_S = 0x55
    PROTOCOL_HEAD_E = 0xAA


class Address(Enum):
    """Address of source and destinations."""

    ADDRESS_MAIN_BOARD = 0x80
    ADDRESS_CONSOLE = 0x90
    ADDRESS_REMOTE = 0xB0


class Response(Enum):
    """Received command type."""

    RESPONSE_GROUP_CONTROL = 0x21
    RESPONSE_GROUP_NAME = 0x43
    RESPONSE_FAVOURITE = 0x31
    RESPONSE_PROGRAM = 0x35
    RESPONSE_PREFERENCE = 0x45
    RESPONSE_ZONE_INFO = 0x53
    RESPONSE_GROUPING = 0x55
    RESPONSE_SPILL = 0x57
    RESPONSE_SERVICE = 0x59
    RESPONSE_PASSWORD = 0x47
    RESPONSE_NOTIFICATION = 0x2D
    RESPONSE_SENSOR = 0x2B
    RESPONSE_PARAMETERS = 0x51


class MessageType(Enum):
    """Received message type."""

    MESSAGE_TYPE_EXPAND = 0x1F
    MESSAGE_TYPE_SUBCOMMAND = 0xC0


class Command(Enum):
    """Subcommand commands."""

    COMMAND_GROUP_CONTROL = 0xC020
    COMMAND_GROUP_STATUS = 0xC021
    COMMAND_GROUP_NAME = 0xC042
    COMMAND_SPILL = 0xC057
    COMMAND_FAVOURITE = 0xC030
    COMMAND_PROGRAM = 0xC034
    COMMAND_EXPAND = 0x1F


class ExData(Enum):
    """Extended message data."""

    EX_DATA_FULL_STATE = 0xFFF0
    EX_DATA_OWNER_NAME = 0xFF3A
    EX_DATA_PROGRAM_ADD = 0xFF2A
    EX_DATA_PROGRAM_DEL = 0xFF2B


class ServiceDueStatus(Enum):
    """Service Due status."""

    UNKNOWN = -1
    NO = 0
    HALF_YEAR = 1
    ONE_YEAR = 2
    TWO_YEARS = 3


class GroupPowerStatus(Enum):
    """Group Power Status."""

    NO_ZONE = -1
    ON = 1
    OFF = 0
    TURBO = 2
