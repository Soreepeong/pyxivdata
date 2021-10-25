import abc
import ctypes
import enum
import typing


class ScdHeaderEndiannessFlag(enum.IntEnum):
    LittleEndian = 0
    BigEndian = 1


class SoundEntryFormat(enum.IntEnum):
    WaveFormatPcm = 0x01
    Ogg = 0x06
    WaveFormatAdpcm = 0x0C
    Empty = 0xFFFFFFFF


class ScdHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("sedb_signature", ctypes.c_char * 4),
        ("sscf_signature", ctypes.c_char * 4),
        ("sedb_version", ctypes.c_uint32),
        ("_endianness", ctypes.c_uint8),
        ("sscf_version", ctypes.c_uint8),
        ("header_size", ctypes.c_uint16),
        ("size", ctypes.c_uint32),
        ("padding_0x014", ctypes.c_uint8 * 0x01c),
    )

    SEDB_SIGNATURE = b"SEDB"
    SSCF_SIGNATURE = b"SSCF"

    sedb_signature: bytearray
    sscf_signature: bytearray
    sedb_version: int
    _endianness: int
    sscf_version: int
    header_size: int
    size: int
    padding_0x014: bytearray

    @property
    def endianness(self) -> ScdHeaderEndiannessFlag:
        return ScdHeaderEndiannessFlag(self._endianness)

    @endianness.setter
    def endianness(self, value: ScdHeaderEndiannessFlag):
        self._endianness = value.value


class ScdDataOffsets(ctypes.LittleEndianStructure):
    _fields_ = (
        ("table_1_and_4_entry_count", ctypes.c_uint16),
        ("table_2_entry_count", ctypes.c_uint16),
        ("sound_entry_count", ctypes.c_uint16),
        ("unknown_0x006", ctypes.c_uint8 * 2),
        ("table_2_offset", ctypes.c_uint32),
        ("sound_entry_offset", ctypes.c_uint32),
        ("table_4_offset", ctypes.c_uint32),
        ("padding_0x014", ctypes.c_uint8 * 4),
        ("table5_offset", ctypes.c_uint32),
        ("unknown_0x01C", ctypes.c_uint8 * 4),
    )

    table_1_and_4_entry_count: int
    table_2_entry_count: int
    sound_entry_count: int
    unknown_0x006: bytearray
    table_2_offset: int
    sound_entry_offset: int
    table_4_offset: int
    padding_0x014: bytearray
    table5_offset: int
    unknown_0x01C: bytearray


class ScdDataSoundEntryHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("stream_size", ctypes.c_uint32),
        ("channel_count", ctypes.c_uint32),
        ("sampling_rate", ctypes.c_uint32),
        ("_format", ctypes.c_uint32),
        ("loop_start_seek_offset", ctypes.c_uint32),
        ("loop_end_seek_offset", ctypes.c_uint32),
        ("stream_offset", ctypes.c_uint32),
        ("aux_chunk_count", ctypes.c_uint32),
        ("unknown_0x02e", ctypes.c_uint8 * 4),
    )

    stream_size: int
    channel_count: int
    sampling_rate: int
    _format: int
    loop_start_seek_offset: int
    loop_end_seek_offset: int
    stream_offset: int
    aux_chunk_count: int
    unknown_0x02e: bytearray

    @property
    def format(self) -> SoundEntryFormat:
        return SoundEntryFormat(self._format)

    @format.setter
    def format(self, value: ScdHeaderEndiannessFlag):
        self._format = value.value


class ScdDataAuxChunkHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("name", ctypes.c_char * 4),
        ("size", ctypes.c_uint32)
    )

    NAME_MARK = b"MARK"

    name: bytearray
    size: int


class ScdDataAuxMarkHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("loop_start_sample_block_index", ctypes.c_uint32),
        ("loop_end_sample_block_index", ctypes.c_uint32),
        ("count", ctypes.c_uint32),
    )

    loop_start_sample_block_index: int
    loop_end_sample_block_index: int
    count: int


class ScdDataOggHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("version", ctypes.c_uint8),
        ("header_size", ctypes.c_uint8),
        ("encode_byte", ctypes.c_uint8),
        ("padding_0x003", ctypes.c_uint8 * 1),
        ("unknown_0x004", ctypes.c_uint8 * 4),
        ("unknown_0x008", ctypes.c_uint8 * 4),
        ("unknown_0x00c", ctypes.c_uint8 * 4),
        ("seek_table_size", ctypes.c_uint32),
        ("vorbis_header_size", ctypes.c_uint32),
        ("unknown_0x018", ctypes.c_uint8 * 4),
        ("padding_0x01c", ctypes.c_uint8 * 4),
    )

    version: int
    header_size: int
    encode_byte: int
    padding_0x003: bytearray
    unknown_0x004: bytearray
    unknown_0x008: bytearray
    unknown_0x00c: bytearray
    seek_table_size: int
    vorbis_header_size: int
    unknown_0x018: bytearray
    padding_0x01c: bytearray


class AdpcmOffset(ctypes.LittleEndianStructure):
    _pack_ = 2
    _fields_ = (
        ("coef_1", ctypes.c_int16),
        ("coef_2", ctypes.c_int16),
    )

    coef_1: int
    coef_2: int


class WaveFormat(ctypes.LittleEndianStructure):
    _fields_ = (
        ("format_tag", ctypes.c_uint16),
        ("num_channels", ctypes.c_uint16),
        ("samples_per_sec", ctypes.c_uint32),
        ("avg_bytes_per_sec", ctypes.c_uint32),
        ("block_size_align", ctypes.c_uint16),
        ("bits_per_sample", ctypes.c_uint16),
    )

    format_tag: int
    num_channels: int
    samples_per_sec: int
    avg_bytes_per_sec: int
    block_size_align: int
    bits_per_sample: int


class WaveFormatEx(WaveFormat):
    _pack_ = 2
    _fields_ = (
        ("cb_size", ctypes.c_uint16),
    )

    cb_size: int


class AdpcmWaveFormat(WaveFormatEx):
    _fields_ = (
        ("samples_per_block", ctypes.c_uint16),
        ("num_coef", ctypes.c_uint16),
    )

    samples_per_block: int
    num_coef: int

    def get_coefficients(self, buf: typing.Union[bytearray, memoryview]
                         ) -> typing.Union[ctypes.Array[AdpcmOffset], typing.Sequence[AdpcmOffset]]:
        return (AdpcmOffset * self.num_coef).from_buffer(buf, ctypes.sizeof(self))
