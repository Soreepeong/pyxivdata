import ctypes
import io
import typing
import zlib

from pyxivdata.resource.model.structures import ModelHeader
from pyxivdata.sqpack.structures import SqDataFileEntryHeader, SqDataFileEntryType, SqDataBlockHeaderLocator, \
    SqDataBlockHeader, SqDataTextureBlockHeaderLocator, SqDataModelBlockLocator
from pyxivdata.resource.texture.structure import TextureHeader


def decode_entry(fp: typing.Union[typing.BinaryIO, io.RawIOBase], offset: int,
                 read_size: typing.Optional[int] = None) -> bytearray:
    fp.seek(offset)
    if read_size is None:
        fp.readinto(header := SqDataFileEntryHeader())
        read_size = header.allocation_size + 0xFF
    data = bytearray(read_size)
    fp.readinto(data)
    header = SqDataFileEntryHeader.from_buffer_copy(data, 0)
    if header.type == SqDataFileEntryType.Empty:
        return bytearray()
    elif header.type == SqDataFileEntryType.Binary:
        return decode_binary_entry(header, data)
    elif header.type == SqDataFileEntryType.Model:
        return decode_model_entry(header, data)
    elif header.type == SqDataFileEntryType.Texture:
        return decode_texture_entry(header, data)
    else:
        raise AssertionError


def decode_binary_entry(header: SqDataFileEntryHeader, data: bytearray) -> bytearray:
    locators = (SqDataBlockHeaderLocator * header.block_count_or_version).from_buffer(data, ctypes.sizeof(header))
    result: typing.List[typing.Optional[bytes]] = [None] * len(locators)
    for i, locator in enumerate(locators):
        offset = header.header_size + locator.offset
        block_header = SqDataBlockHeader.from_buffer(data, offset)
        if block_header.is_compressed():
            compressed = data[offset + block_header.header_size:
                              offset + block_header.header_size + block_header.compressed_size]
            if len(compressed) != block_header.compressed_size:
                raise ValueError("Incomplete data")
            result[i] = zlib.decompress(compressed, wbits=-zlib.MAX_WBITS, bufsize=block_header.decompressed_size)
        else:
            result[i] = data[offset + block_header.header_size:][:block_header.decompressed_size]

    return bytearray().join(result)


def decode_model_entry(header: SqDataFileEntryHeader, data: bytearray) -> bytearray:
    locator = SqDataModelBlockLocator.from_buffer(data, ctypes.sizeof(header))
    read_offset = ctypes.sizeof(header) + ctypes.sizeof(locator)
    block_sizes = [
        int.from_bytes(data[read_offset + i * 2:][:2], "little", signed=False)
        for i in range(locator.first_block_indices.index[2] + locator.block_count.index[2])
    ]

    model_header = ModelHeader()
    model_header.version = header.block_count_or_version
    model_header.vertex_declaration_count = locator.vertex_declaration_count
    model_header.material_count = locator.material_count
    model_header.lod_count = locator.lod_count
    model_header.enable_index_buffer_streaming = locator.enable_index_buffer_streaming
    model_header.enable_edge_geometry = locator.enable_edge_geometry
    model_header.padding = locator.padding

    blocks = []
    result_size = ctypes.sizeof(model_header)
    for i in range(len(locator.block_count)):
        if not locator.block_count[i]:
            continue

        from_result_size = result_size
        offset = header.header_size + locator.first_block_offsets[i]
        for block_index in range(locator.first_block_indices[i],
                                 locator.first_block_indices[i] + locator.block_count[i]):
            block_header = SqDataBlockHeader.from_buffer(data, offset)
            if block_header.is_compressed():
                d = zlib.decompress(data[offset + block_header.header_size:][:block_header.compressed_size],
                                    wbits=-zlib.MAX_WBITS, bufsize=block_header.decompressed_size)
            else:
                d = data[offset + block_header.header_size:][:block_header.decompressed_size]
            blocks.append(d)
            result_size += len(d)
            offset += block_sizes[block_index]
        if i == 0:
            model_header.stack_memory_size = result_size - from_result_size
        elif i == 1:
            model_header.runtime_memory_size = result_size - from_result_size
        elif i in (2, 5, 8):
            model_header.vertex_buffer_size[(i - 2) // 3] = result_size - from_result_size
            model_header.vertex_data_offset[(i - 2) // 3] = from_result_size
        elif i in (4, 7, 10):
            model_header.index_buffer_size[(i - 4) // 3] = result_size - from_result_size
            model_header.index_data_offset[(i - 4) // 3] = from_result_size

    # noinspection PyTypeChecker
    return bytearray(model_header) + bytearray().join(blocks)


def decode_texture_entry(header: SqDataFileEntryHeader, data: bytearray) -> bytearray:
    read_offset = ctypes.sizeof(header)
    locators = (SqDataTextureBlockHeaderLocator * header.block_count_or_version
                ).from_buffer(data, read_offset)

    read_offset += ctypes.sizeof(locators)
    sub_block_sizes = [
        int.from_bytes(data[read_offset + i * 2:][:2], "little", signed=False)
        for i in range(sum(locator.sub_block_count for locator in locators))
    ]

    read_offset = header.header_size
    texture_header = TextureHeader.from_buffer(data, read_offset)

    read_offset += ctypes.sizeof(texture_header)
    mipmap_offsets = [
        int.from_bytes(data[read_offset + i * 4:][:4], "little", signed=False)
        for i in range(texture_header.mipmap_count)
    ]

    result = bytearray(header.decompressed_size)
    result[0:texture_header.header_size] = data[header.header_size:header.header_size + texture_header.header_size]
    for mipmap_offset, locator in zip(mipmap_offsets, locators):
        offset = header.header_size + locator.first_block_offset
        for sub_block_size in sub_block_sizes[locator.first_sub_block_index:][:locator.sub_block_count]:
            block_header = SqDataBlockHeader.from_buffer(data, offset)
            if block_header.is_compressed():
                d = zlib.decompress(data[offset + block_header.header_size:][:block_header.compressed_size],
                                    wbits=-zlib.MAX_WBITS, bufsize=block_header.decompressed_size)
            else:
                d = data[offset + block_header.header_size:][:block_header.decompressed_size]
            result[mipmap_offset:mipmap_offset + len(d)] = d
            offset += sub_block_size
            mipmap_offset += len(d)

    return result
