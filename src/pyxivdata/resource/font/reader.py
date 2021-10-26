import ctypes
import functools
import typing
from bisect import bisect_left

from pyxivdata.common import CorruptDataException
from pyxivdata.resource.font.structures import FdtHeader, FontTableHeader, KerningTableHeader, FontTableEntry, \
    KerningTableEntry


class FontReader:
    _font_table_entries: typing.Union[ctypes.Array[FontTableEntry], typing.Sequence[FontTableEntry]]
    _kerning_table_entries: typing.Union[ctypes.Array[KerningTableEntry], typing.Sequence[KerningTableEntry]]

    def __init__(self, data: bytearray, custom_fallback_characters: typing.Optional[str] = None):
        header = FdtHeader.from_buffer(data, 0)
        if header.signature != FdtHeader.SIGNATURE:
            raise CorruptDataException("Bad signature")

        self._font_table_header = FontTableHeader.from_buffer(data, header.font_table_header_offset)
        if self._font_table_header.signature != FontTableHeader.SIGNATURE:
            raise CorruptDataException("Bad font table signature")

        self._kerning_table_header = KerningTableHeader.from_buffer(data, header.kerning_table_header_offset)
        if self._kerning_table_header.signature != KerningTableHeader.SIGNATURE:
            raise CorruptDataException("Bad kerning table signature")

        if self._kerning_table_header.count != self._font_table_header.kerning_table_entry_count:
            raise CorruptDataException(
                "Kerning table entry count specified in kerning table header and font table header are different")

        self._font_table_entries = (
            (FontTableEntry * self._font_table_header.font_table_entry_count).from_buffer(
                data, header.font_table_header_offset + ctypes.sizeof(self._font_table_header)))
        self._kerning_table_entries = (
            (KerningTableEntry * self._font_table_header.kerning_table_entry_count).from_buffer(
                data, header.kerning_table_header_offset + ctypes.sizeof(self._kerning_table_header)))

        for char in (custom_fallback_characters or "＝= !") + self._font_table_entries[0].char:
            i = bisect_left(self._font_table_entries, char, key=lambda x: x.char)
            if i == len(self._font_table_entries) or self._font_table_entries[i].char != char:
                continue
            self._fallback_glyph_entry = self._font_table_entries[i]
            break
        else:
            raise CorruptDataException("No glyph found")

    def __getitem__(self, item: typing.Union[str, typing.Tuple[str, str]]) -> typing.Union[FontTableEntry, int]:
        if isinstance(item, str):
            return self.glyph(item, False)
        elif isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) and isinstance(item[1], str):
            return self.kerning_distance(item[0], item[1], False)
        else:
            raise TypeError

    def __len__(self):
        return len(self._font_table_entries)

    def glyph(self, char: str, raise_on_not_found: bool = True) -> FontTableEntry:
        i = bisect_left(self._font_table_entries, char, key=lambda x: x.char)
        if i == len(self._font_table_entries) or self._font_table_entries[i].char != char:
            if raise_on_not_found:
                raise KeyError
            return self._fallback_glyph_entry

        return self._font_table_entries[i]

    def kerning_distance(self, left: str, right: str, raise_on_not_found: bool = True) -> int:
        i = bisect_left(self._kerning_table_entries, (left, right), key=lambda x: (x.left, x.right))
        if (i == len(self._kerning_table_entries)
                or self._kerning_table_entries[i].left != left
                or self._kerning_table_entries[i].right != right):
            if raise_on_not_found:
                raise KeyError
            return 0

        return self._kerning_table_entries[i].right_offset

    @functools.cached_property
    def kerning_table(self) -> typing.Dict[typing.Tuple[str, str], int]:
        return {
            (x.left, x.right): x.right_offset
            for x in self._kerning_table_entries
        }
