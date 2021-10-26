import ctypes
import math
import typing


class PositionVector(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = (
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
    )

    x: float
    y: float
    z: float


class IpcStructure:
    OPCODE_FIELD: typing.ClassVar[str] = None

    def __init_subclass__(cls, opcode_field: typing.Optional[str] = None, **kwargs):
        cls.OPCODE_FIELD = opcode_field


def float_to_uint16(val: float) -> int:
    return 0x8000 + int(max(-1000., min(1000., val)) * 32.767)


def uint16_to_float(val: int) -> float:
    return (val - 0x8000) / 32.767


def float_to_uint16_rot(val: float) -> int:
    return int(0x8000 * (max(-math.pi, min(math.pi, val)) + math.pi) / math.pi)


def uint16_to_float_rot(val: int) -> float:
    return (val - 0x8000) / 0x8000 * math.pi


def float_to_uint8_rot(val: float) -> int:
    return int(0x80 * (max(-math.pi, min(math.pi, val)) + math.pi) / math.pi)


def uint8_to_float_rot(val: int) -> float:
    return (val - 0x80) / 0x80 * math.pi
