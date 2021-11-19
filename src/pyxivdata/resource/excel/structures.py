import ctypes
import enum
import typing


class ExhColumnDataType(enum.IntEnum):
    SeString = 0x0
    Bool = 0x1
    Int8 = 0x2
    UInt8 = 0x3
    Int16 = 0x4
    UInt16 = 0x5
    Int32 = 0x6
    UInt32 = 0x7
    Float32 = 0x9
    Int64 = 0xA
    UInt64 = 0xB

    # 0 is read like data & 1, 1 is like data & 2, 2 = data & 4, etc...
    PackedBool0 = 0x19
    PackedBool1 = 0x1A
    PackedBool2 = 0x1B
    PackedBool3 = 0x1C
    PackedBool4 = 0x1D
    PackedBool5 = 0x1E
    PackedBool6 = 0x1F
    PackedBool7 = 0x20

    @property
    def is_bool(self):
        return self in (ExhColumnDataType.Bool, ExhColumnDataType.PackedBool0, ExhColumnDataType.PackedBool1,
                        ExhColumnDataType.PackedBool2, ExhColumnDataType.PackedBool3, ExhColumnDataType.PackedBool4,
                        ExhColumnDataType.PackedBool5, ExhColumnDataType.PackedBool6, ExhColumnDataType.PackedBool7)

    @property
    def is_int(self):
        return self in (ExhColumnDataType.Int8, ExhColumnDataType.UInt8, ExhColumnDataType.Int16,
                        ExhColumnDataType.UInt16, ExhColumnDataType.Int32, ExhColumnDataType.UInt32,
                        ExhColumnDataType.Int64, ExhColumnDataType.UInt64)

    @property
    def is_float(self):
        return self == ExhColumnDataType.Float32

    @property
    def is_string(self):
        return self == ExhColumnDataType.SeString


class ExhDepth(enum.IntEnum):
    Level2 = 1
    Level3 = 2


class ExhColumnDefinition(ctypes.BigEndianStructure):
    _fields_ = (
        ("_type", ctypes.c_uint16),
        ("offset", ctypes.c_uint16),
    )

    _type: int
    offset: int

    @property
    def type(self) -> ExhColumnDataType:
        return ExhColumnDataType(self._type)

    @type.setter
    def type(self, value: ExhColumnDataType):
        self._type = value.value


class ExhPageDefinition(ctypes.BigEndianStructure):
    _fields_ = (
        ("start_id", ctypes.c_uint32),
        ("row_count_with_skip", ctypes.c_uint32),
    )

    start_id: int
    row_count_with_skip: int


class ExdHeader(ctypes.BigEndianStructure):
    _fields_ = (
        ("signature", ctypes.c_uint32),
        ("version", ctypes.c_uint16),
        ("padding_0x006", ctypes.c_uint16),
        ("index_size", ctypes.c_uint32),
        ("data_size", ctypes.c_uint32),
        ("padding_0x010", ctypes.c_uint8 * 0x10),
    )

    SIGNATURE: typing.ClassVar[bytes] = b"EXDF"

    index_size: int
    data_size: int


class ExdRowLocator(ctypes.BigEndianStructure):
    _fields_ = (
        ("row_id", ctypes.c_uint32),
        ("offset", ctypes.c_uint32)
    )

    row_id: int
    offset: int


class ExdRowHeader(ctypes.BigEndianStructure):
    _pack_ = 2
    _fields_ = (
        ("data_size", ctypes.c_uint32),
        ("sub_row_count", ctypes.c_uint16)
    )

    data_size: int
    sub_row_count: int


class ExhHeader(ctypes.BigEndianStructure):
    _fields_ = (
        ("signature", ctypes.c_char * 4),
        ("version", ctypes.c_uint16),
        ("fixed_data_size", ctypes.c_uint16),
        ("column_count", ctypes.c_uint16),
        ("page_count", ctypes.c_uint16),
        ("language_count", ctypes.c_uint16),
        ("unknown", ctypes.c_uint16),
        ("padding_0x010", ctypes.c_uint8 * 1),
        ("_depth", ctypes.c_uint8),
        ("padding_0x012", ctypes.c_uint8 * 2),
        ("row_count_without_skip", ctypes.c_uint32),
        ("padding_0x018", ctypes.c_uint8 * 6),
    )

    SIGNATURE: typing.ClassVar[bytes] = b"EXHF"

    signature: bytearray
    version: int
    fixed_data_size: int
    column_count: int
    page_count: int
    language_count: int
    unknown: int
    padding_0x010: bytes
    _depth: int
    padding_0x012: bytes
    row_count_without_skip: int
    padding_0x018: bytes

    @property
    def depth(self) -> ExhDepth:
        return ExhDepth(self._depth)

    @depth.setter
    def depth(self, value: ExhDepth):
        self._depth = value.value
