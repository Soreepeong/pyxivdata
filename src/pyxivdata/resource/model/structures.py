import ctypes
import typing


class ModelHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("version", ctypes.c_uint32),
        ("stack_memory_size", ctypes.c_uint32),
        ("runtime_memory_size", ctypes.c_uint32),
        ("vertex_declaration_count", ctypes.c_uint16),
        ("material_count", ctypes.c_uint16),

        ("vertex_data_offset", ctypes.c_uint32 * 3),
        ("index_data_offset", ctypes.c_uint32 * 3),
        ("vertex_buffer_size", ctypes.c_uint32 * 3),
        ("index_buffer_size", ctypes.c_uint32 * 3),

        ("lod_count", ctypes.c_uint8),
        ("enable_index_buffer_streaming", ctypes.c_bool),
        ("enable_edge_geometry", ctypes.c_bool),
        ("padding", ctypes.c_uint8),
    )

    version: int
    stack_memory_size: int
    runtime_memory_size: int
    vertex_declaration_count: int
    material_count: int

    vertex_data_offset: typing.List[int]
    index_data_offset: typing.List[int]
    vertex_buffer_size: typing.List[int]
    index_buffer_size: typing.List[int]

    lod_count: int
    enable_index_buffer_streaming: bool
    enable_edge_geometry: bool
    padding: int
