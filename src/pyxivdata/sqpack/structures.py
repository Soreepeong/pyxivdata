import ctypes
import enum
import os
import typing

from pyxivdata.common import SqPathSpec


class SqpackType(enum.IntEnum):
    Database = 0
    Data = 1
    Index = 2


class SqpackHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("signature", ctypes.c_char * 12),  # SqPack\0\0\0\0\0\0
        ("header_size", ctypes.c_uint32),
        ("unknown_0x010", ctypes.c_uint32),
        ("_sqpack_type", ctypes.c_uint32),  # 0: sqdb, 1: data, 2: index
        ("yyyymmdd", ctypes.c_uint32),
        ("time", ctypes.c_uint32),
        ("unknown_0x020", ctypes.c_uint32),
        ("padding_0x024", ctypes.c_uint8 * (0x3c0 - 0x024)),
        ("sha1", ctypes.c_uint8 * 20),
        ("padding_0x3d4", ctypes.c_uint8 * 0x02c),
    )

    SIGNATURE: typing.ClassVar[bytes] = b"SqPack\0\0\0\0\0\0"

    signature: bytearray
    header_size: int
    unknown_0x010: int
    _sqpack_type: int
    yyyymmdd: int
    time: int
    unknown_0x020: int
    padding_0x024: bytearray
    sha1: bytearray
    padding_0x3d4: bytearray

    @property
    def sqpack_type(self) -> SqpackType:
        return SqpackType(self._sqpack_type)

    @sqpack_type.setter
    def sqpack_type(self, val: SqpackType):
        self._sqpack_type = val.value


class SqIndexSegmentDescriptor(ctypes.LittleEndianStructure):
    _fields_ = (
        ("count", ctypes.c_uint32),
        ("offset", ctypes.c_uint32),
        ("size", ctypes.c_uint32),
        ("sha1", ctypes.c_uint8 * 20),
        ("padding_0x020", ctypes.c_uint8 * 0x028),
    )

    count: int
    offset: int
    size: int
    sha1: bytearray
    padding_0x020: bytearray


class SqIndexType(enum.IntEnum):
    Index = 0
    Index2 = 2


class SqIndexHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("header_size", ctypes.c_uint32),
        ("hash_locator_segment", SqIndexSegmentDescriptor),
        ("padding_0x04c", ctypes.c_uint8 * 4),
        ("text_locator_segment", SqIndexSegmentDescriptor),
        ("unknown_segment_3", SqIndexSegmentDescriptor),
        ("path_hash_locator_segment", SqIndexSegmentDescriptor),
        ("padding_0x128", ctypes.c_uint8 * 4),
        ("_index_type", ctypes.c_uint32),
        ("padding_0x130", ctypes.c_uint8 * (0x3c0 - 0x130)),
        ("sha1", ctypes.c_uint8 * 20),
        ("padding_0x3d4", ctypes.c_uint8 * 0x02c),
    )

    header_size: int
    hash_locator_segment: SqIndexSegmentDescriptor
    padding_0x04c: bytearray
    text_locator_segment: SqIndexSegmentDescriptor
    unknown_segment_3: SqIndexSegmentDescriptor
    path_hash_locator_segment: SqIndexSegmentDescriptor
    padding_0x128: bytearray
    _index_type: int
    padding_0x130: bytearray
    sha1: bytearray
    padding_0x3d4: bytearray

    @property
    def index_type(self) -> SqIndexType:
        return SqIndexType(self._index_type)

    @index_type.setter
    def index_type(self, val: SqIndexType):
        self._index_type = val.value


class SqIndexDataLocator(ctypes.c_uint32):
    @property
    def synonym(self) -> bool:
        return bool(self.value & 0x1)

    @synonym.setter
    def synonym(self, value: bool):
        self.value = (self.value & ~1) | (1 if value else 0)

    @property
    def index(self) -> int:
        return (self.value & 0xF) >> 1

    @index.setter
    def index(self, value: int):
        if value not in range(8):
            raise ValueError("Data file index must be in range of [0, 8).")
        self.value = (self.value & ~0x0F) | (value << 1)

    @property
    def offset(self) -> int:
        return (self.value & 0xFFFFFFF0) << 3

    @offset.setter
    def offset(self, value: int):
        if value & 0x7F:
            raise ValueError("Offset must be a multiple of 128.")
        value >>= 3
        if value not in range(1 << 32):
            raise ValueError("Offset cannot be larger than 1 << 35.")
        self.value = (self.value & 0xF) | value


class SqIndexPairHashLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("name_hash", ctypes.c_uint32),
        ("path_hash", ctypes.c_uint32),
        ("locator", SqIndexDataLocator),
        ("padding_0x00c", ctypes.c_uint8 * 4),
    )

    name_hash: int
    path_hash: int
    locator: SqIndexDataLocator
    padding_0x00c: int

    def set_path(self, path: typing.Union[str, bytes, os.PathLike, SqPathSpec]):
        path = SqPathSpec(path)
        self.name_hash = path.name_hash
        self.path_hash = path.path_hash

    def path_spec(self) -> SqPathSpec:
        return SqPathSpec(path_hash=self.path_hash, name_hash=self.name_hash)

    def __lt__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash < other.path_hash
        return self.path_hash < other.path_hash

    def __gt__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash > other.path_hash
        return self.path_hash > other.path_hash

    def __le__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash <= other.path_hash
        return self.path_hash <= other.path_hash

    def __ge__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash >= other.path_hash
        return self.path_hash >= other.path_hash

    def __eq__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash == other.path_hash and self.name_hash == other.name_hash

    def __ne__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash != other.path_hash or self.name_hash != other.name_hash


class SqIndexFullHashLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("full_path_hash", ctypes.c_uint32),
        ("locator", SqIndexDataLocator),
    )

    full_path_hash: int
    locator: SqIndexDataLocator

    def set_path(self, path: typing.Union[str, bytes, os.PathLike, SqPathSpec]):
        self.full_path_hash = SqPathSpec(path).full_path_hash

    def path_spec(self) -> SqPathSpec:
        return SqPathSpec(path_hash=self.path_hash, name_hash=self.name_hash)

    def __lt__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash < other.path_hash
        return self.path_hash < other.path_hash

    def __gt__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash > other.path_hash
        return self.path_hash > other.path_hash

    def __le__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash <= other.path_hash
        return self.path_hash <= other.path_hash

    def __ge__(self, other: 'SqIndexPairHashLocator'):
        if self.path_hash == other.path_hash:
            return self.name_hash >= other.path_hash
        return self.path_hash >= other.path_hash

    def __eq__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash == other.path_hash and self.name_hash == other.name_hash

    def __ne__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash != other.path_hash or self.name_hash != other.name_hash


class SqIndexPathHashLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("path_hash", ctypes.c_uint32),
        ("pair_hash_locator_offset", ctypes.c_uint32),
        ("pair_hash_locator_size", ctypes.c_uint32),
        ("padding_0x00c", ctypes.c_uint8 * 4),
    )

    path_hash: int
    pair_hash_locator_offset: int
    pair_hash_locator_size: int
    padding_0x00c: bytearray

    def __lt__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash < other.path_hash

    def __gt__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash > other.path_hash

    def __le__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash <= other.path_hash

    def __ge__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash >= other.path_hash

    def __eq__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash == other.path_hash

    def __ne__(self, other: 'SqIndexPairHashLocator'):
        return self.path_hash != other.path_hash


class SqIndexPairHashWithTextLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("name_hash", ctypes.c_uint32),
        ("path_hash", ctypes.c_uint32),
        ("locator", SqIndexDataLocator),
        ("conflict_index", ctypes.c_uint32),
        ("_full_path", ctypes.c_char * 0xf0),
    )

    SENTINEL = 0xFFFFFFFF

    name_hash: int
    path_hash: int
    locator: SqIndexDataLocator
    conflict_index: int
    _full_path: bytearray

    @property
    def full_path(self):
        return self._full_path.decode("utf-8")

    @full_path.setter
    def full_path(self, value: str):
        self._full_path = bytearray(value.encode("utf-8"))

    @property
    def path_spec(self):
        return SqPathSpec(self.full_path)


class SqIndexFullHashWithTextLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("full_path_hash", ctypes.c_uint32),
        ("unused_hash", ctypes.c_uint32),
        ("locator", SqIndexDataLocator),
        ("conflict_index", ctypes.c_uint32),
        ("_full_path", ctypes.c_char * 0xf0),
    )

    SENTINEL = 0xFFFFFFFF

    full_path_hash: int
    unused_hash: int
    locator: SqIndexDataLocator
    conflict_index: int
    _full_path: bytearray

    @property
    def full_path(self):
        return self._full_path.decode("utf-8")

    @full_path.setter
    def full_path(self, value: str):
        self._full_path = bytearray(value.encode("utf-8"))


class SqDataHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("header_size", ctypes.c_uint32),
        ("padding_0x004", ctypes.c_uint8 * 4),
        ("unknown_1", ctypes.c_uint32),
        ("_data_size", ctypes.c_uint32),
        ("span_index", ctypes.c_uint32),
        ("padding_0x014", ctypes.c_uint8 * 4),
        ("max_file_size", ctypes.c_uint64),
        ("data_sha1", ctypes.c_uint8 * 20),
        ("padding_0x034", ctypes.c_uint8 * (0x3c0 - 0x034)),
        ("sha1", ctypes.c_uint8 * 20),
        ("padding_0x03d4", ctypes.c_uint8 * 0x02c)
    )
    
    header_size: int
    padding_0x004: bytearray
    unknown_1: int
    _data_size: int
    span_index: int
    padding_0x014: bytearray
    max_file_size: int
    data_sha1: bytearray
    padding_0x034: bytearray
    sha1: bytearray
    padding_0x3d4: bytearray

    @property
    def data_size(self) -> int:
        return self._data_size << 7

    @data_size.setter
    def data_size(self, value: int):
        if value & 0x7F:
            raise ValueError("Data size must be a multiple of 128.")
        value >>= 3
        if value not in range(1 << 32):
            raise ValueError("Data size cannot be larger than 1 << 35.")
        self._data_size = (self._data_size & 0xF) | value


class SqDataFileEntryType(enum.IntEnum):
    Empty = 1
    Binary = 2
    Model = 3
    Texture = 4


class SqDataFileEntryHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("header_size", ctypes.c_uint32),
        ("_type", ctypes.c_uint32),
        ("decompressed_size", ctypes.c_uint32),
        ("unknown_1", ctypes.c_uint32),
        ("aligned_unit_allocation_count", ctypes.c_uint32),
        ("block_count_or_version", ctypes.c_uint32),
    )

    header_size: int
    _type: int
    decompressed_size: int
    unknown_1: int
    aligned_unit_allocation_count: int
    block_count_or_version: int

    @property
    def type(self) -> SqDataFileEntryType:
        return SqDataFileEntryType(self._type)

    @type.setter
    def type(self, value: SqDataFileEntryType):
        self._type = value.value

    @property
    def allocation_size(self) -> int:
        return 0x7F + (self.aligned_unit_allocation_count << 7)

    @allocation_size.setter
    def allocation_size(self, value: int):
        self.aligned_unit_allocation_count = (value + 0x7F) >> 7


class SqDataBlockHeaderLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("offset", ctypes.c_uint32),
        ("block_size", ctypes.c_uint16),
        ("decompressed_data_size", ctypes.c_uint16),
    )

    offset: int
    block_size: int
    decompressed_data_size: int


class SqDataBlockHeader(ctypes.LittleEndianStructure):
    COMPRESSED_SIZE_NOT_COMPRESSED: typing.ClassVar[int] = 32000
    
    _fields_ = (
        ("header_size", ctypes.c_uint32),
        ("version", ctypes.c_uint32),
        ("compressed_size", ctypes.c_uint32),
        ("decompressed_size", ctypes.c_uint32),
    )

    header_size: int
    version: int
    compressed_size: int
    decompressed_size: int

    def is_compressed(self):
        return self.compressed_size != SqDataBlockHeader.COMPRESSED_SIZE_NOT_COMPRESSED
    
    def set_compressed(self):
        self.compressed_size = SqDataBlockHeader.COMPRESSED_SIZE_NOT_COMPRESSED


class SqDataTextureBlockHeaderLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("first_block_offset", ctypes.c_uint32),
        ("total_size", ctypes.c_uint32),
        ("decompressed_size", ctypes.c_uint32),
        ("first_sub_block_index", ctypes.c_uint32),
        ("sub_block_count", ctypes.c_uint32),
    )
    
    first_block_offset: int
    total_size: int
    decompressed_size: int
    first_sub_block_index: int
    sub_block_count: int


class SqDataModelBlockLocatorChunkInfo32(ctypes.LittleEndianStructure):
    _fields_ = (
        ("stack", ctypes.c_uint32),
        ("runtime", ctypes.c_uint32),
        ("vertex", ctypes.c_uint32 * 3),
        ("edge_geometry_vertex", ctypes.c_uint32 * 3),
        ("index", ctypes.c_uint32 * 3),
    )

    stack: int
    runtime: int
    vertex: typing.List[int]
    edge_geometry_vertex: typing.List[int]
    index: typing.List[int]

    def __getitem__(self, item: int) -> int:
        if item == 0:
            return self.stack
        elif item == 1:
            return self.runtime
        elif item == 2:
            return self.vertex[0]
        elif item == 3:
            return self.edge_geometry_vertex[0]
        elif item == 4:
            return self.index[0]
        elif item == 5:
            return self.vertex[1]
        elif item == 6:
            return self.edge_geometry_vertex[1]
        elif item == 7:
            return self.index[1]
        elif item == 8:
            return self.vertex[2]
        elif item == 9:
            return self.edge_geometry_vertex[2]
        elif item == 10:
            return self.index[2]
        else:
            raise KeyError

    def __len__(self):
        return 11


class SqDataModelBlockLocatorChunkInfo16(ctypes.LittleEndianStructure):
    _fields_ = (
        ("stack", ctypes.c_uint16),
        ("runtime", ctypes.c_uint16),
        ("vertex", ctypes.c_uint16 * 3),
        ("edge_geometry_vertex", ctypes.c_uint16 * 3),
        ("index", ctypes.c_uint16 * 3),
    )

    stack: int
    runtime: int
    vertex: typing.List[int]
    edge_geometry_vertex: typing.List[int]
    index: typing.List[int]

    def __getitem__(self, item: int) -> int:
        if item == 0:
            return self.stack
        elif item == 1:
            return self.runtime
        elif item == 2:
            return self.vertex[0]
        elif item == 3:
            return self.edge_geometry_vertex[0]
        elif item == 4:
            return self.index[0]
        elif item == 5:
            return self.vertex[1]
        elif item == 6:
            return self.edge_geometry_vertex[1]
        elif item == 7:
            return self.index[1]
        elif item == 8:
            return self.vertex[2]
        elif item == 9:
            return self.edge_geometry_vertex[2]
        elif item == 10:
            return self.index[2]
        else:
            raise KeyError

    def __len__(self):
        return 11


class SqDataModelBlockLocator(ctypes.LittleEndianStructure):
    _fields_ = (
        ("aligned_decompressed_sizes", SqDataModelBlockLocatorChunkInfo32),
        ("chunk_sizes", SqDataModelBlockLocatorChunkInfo32),
        ("first_block_offsets", SqDataModelBlockLocatorChunkInfo32),
        ("first_block_indices", SqDataModelBlockLocatorChunkInfo16),
        ("block_count", SqDataModelBlockLocatorChunkInfo16),
        ("vertex_declaration_count", ctypes.c_uint16),
        ("material_count", ctypes.c_uint16),
        ("lod_count", ctypes.c_uint8),
        ("enable_index_buffer_streaming", ctypes.c_bool),
        ("enable_edge_geometry", ctypes.c_bool),
        ("padding", ctypes.c_uint8),
    )

    aligned_decompressed_sizes: SqDataModelBlockLocatorChunkInfo32
    chunk_sizes: SqDataModelBlockLocatorChunkInfo32
    first_block_offsets: SqDataModelBlockLocatorChunkInfo32
    first_block_indices: SqDataModelBlockLocatorChunkInfo16
    block_count: SqDataModelBlockLocatorChunkInfo16
    vertex_declaration_count: int
    material_count: int
    lod_count: int
    enable_index_buffer_streaming: int
    enable_edge_geometry: int
    padding: int
