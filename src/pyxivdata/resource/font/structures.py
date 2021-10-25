import ctypes
import struct
import typing

import unicodedata


class FdtHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("signature", ctypes.c_char * 8),
        ("font_table_header_offset", ctypes.c_uint32),
        ("kerning_table_header_offset", ctypes.c_uint32),
        ("padding_0x010", ctypes.c_uint8 * 0x10)
    )

    SIGNATURE = b"fcsv0100"

    signature: bytearray
    font_table_header_offset: int
    kerning_table_header_offset: int
    padding_0x010: bytearray


class FontTableHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("signature", ctypes.c_char * 4),
        ("font_table_entry_count", ctypes.c_uint32),
        ("kerning_table_entry_count", ctypes.c_uint32),
        ("padding_0x00c", ctypes.c_uint8 * 4),
        ("texture_width", ctypes.c_uint16),
        ("texture_height", ctypes.c_uint16),
        ("points", ctypes.c_float),
        ("line_height", ctypes.c_uint32),
        ("ascent", ctypes.c_uint32),
    )

    SIGNATURE: typing.ClassVar[bytes] = b"fthd"

    signature: bytearray
    font_table_entry_count: int
    kerning_table_entry_count: int
    padding_0x00c: bytearray
    texture_width: int
    texture_height: int
    points: float
    line_height: int
    ascent: int


def _utf8int_to_str(n: int):
    if (n & 0xFFFFFF80) == 0:
        return chr(n & 0x7F)
    elif (n & 0xFFFFE0C0) == 0xC080:
        return chr(
            (((n >> 0x08) & 0x1F) << 6) |
            (((n >> 0x00) & 0x3F) << 0)
        )
    elif (n & 0xFFF0C0C0) == 0xE08080:
        return chr(
            (((n >> 0x10) & 0x0F) << 12) |
            (((n >> 0x08) & 0x3F) << 6) |
            (((n >> 0x00) & 0x3F) << 0)
        )
    elif (n & 0xF8C0C0C0) == 0xF0808080:
        return chr(
            (((n >> 0x18) & 0x07) << 18) |
            (((n >> 0x10) & 0x3F) << 12) |
            (((n >> 0x08) & 0x3F) << 6) |
            (((n >> 0x00) & 0x3F) << 0)
        )
    else:
        return "\uFFFF"  # Guaranteed non-unicode


def _str_to_utf8_sjis(new_char: str):
    if len(new_char) != 1:
        raise ValueError
    u8_bytes = f"\0\0\0{new_char}".encode("utf-8")[-4:]

    sjis_bytes = new_char.encode("shift_jis", errors="ignore")
    if not sjis_bytes:
        # Shift_JIS does not have an exactly matching character, so find a near match.
        sjis_bytes = unicodedata.normalize("NFKD", new_char).encode("shift_jis", errors="ignore")
        if not sjis_bytes:
            # No near match could be found.
            sjis_bytes = b" "
        elif len(sjis_bytes.decode("shift_jis")) == 2:
            # Cannot accurately represent in 1 character, so drop it (ex. composed roman numbers)
            sjis_bytes = b" "
    if len(sjis_bytes) < 2:
        sjis_bytes = b"\0" * (2 - len(sjis_bytes)) + sjis_bytes

    return struct.unpack(">IH", bytes(u8_bytes + sjis_bytes))


class FontTableEntry(ctypes.LittleEndianStructure):
    _fields_ = (
        ("char_utf8", ctypes.c_uint32),
        ("char_sjis", ctypes.c_uint16),
        ("texture_index", ctypes.c_uint16),
        ("texture_offset_x", ctypes.c_uint16),
        ("texture_offset_y", ctypes.c_uint16),
        ("bounding_width", ctypes.c_uint8),
        ("bounding_height", ctypes.c_uint8),
        ("next_offset_x", ctypes.c_int8),
        ("current_offset_y", ctypes.c_int8),
    )

    char_utf8: int
    char_sjis: int
    texture_index: int
    texture_offset_x: int
    texture_offset_y: int
    bounding_width: int
    bounding_height: int
    next_offset_x: int
    current_offset_y: int

    @property
    def char(self) -> str:
        return _utf8int_to_str(self.char_utf8)

    @char.setter
    def char(self, new_char: str):
        self.char_utf8, self.char_sjis = _str_to_utf8_sjis(new_char)


class KerningTableHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("signature", ctypes.c_char * 4),
        ("count", ctypes.c_uint32),
        ("padding_0x008", ctypes.c_uint8 * 8)
    )

    SIGNATURE: typing.ClassVar[bytes] = b"knhd"

    signature: bytearray
    count: int
    padding_0x008: bytearray


class KerningTableEntry(ctypes.LittleEndianStructure):
    _fields_ = (
        ("left_utf8", ctypes.c_uint32),
        ("right_utf8", ctypes.c_uint32),
        ("left_sjis", ctypes.c_uint16),
        ("right_sjis", ctypes.c_uint16),
        ("right_offset", ctypes.c_int32),
    )

    left_utf8: int
    right_utf8: int
    left_sjis: int
    right_sjis: int
    right_offset: int

    @property
    def left(self) -> str:
        return _utf8int_to_str(self.left_utf8)

    @left.setter
    def left(self, new_char: str):
        self.left_utf8, self.left_sjis = _str_to_utf8_sjis(new_char)

    @property
    def right(self) -> str:
        return _utf8int_to_str(self.right_utf8)

    @right.setter
    def right(self, new_char: str):
        self.right_utf8, self.right_sjis = _str_to_utf8_sjis(new_char)
