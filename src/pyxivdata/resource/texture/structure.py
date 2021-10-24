import ctypes
import enum


class TextureCompressionType(enum.IntEnum):
    Unknown = 0

    # https://github.com/goaaats/ffxiv-explorer-fork/blob/develop/src/main/java/com/fragmenterworks/ffxivextract/models/Texture_File.java

    # Grayscale
    L8_1 = 0x1130  # 1 byte (L8) per pixel
    L8_2 = 0x1131  # same with above

    # Full color with alpha channel
    RGBA4444 = 0x1440  # 2 bytes (LE binary[16]: aaaaBBBBggggRRRR) per pixel
    RGBA5551 = 0x1441  # 2 bytes (LE binary[16]: aBBBBBgggggRRRRR) per pixel
    RGBA_1 = 0x1450  # 4 bytes (LE binary[32]: aaaaaaaaBBBBBBBBggggggggRRRRRRRR) per pixel
    RGBA_2 = 0x1451  # same with above
    RGBAF = 0x2460  # 8 bytes (LE half[4]: rgba)
    #                 ^ TODO: check if it's rgba or abgr

    # https://en.wikipedia.org/wiki/S3_Texture_Compression
    DXT1 = 0x3420
    DXT3 = 0x3430
    DXT5 = 0x3431


class TextureHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("unknown_0x000", ctypes.c_uint16),
        ("header_size", ctypes.c_uint16),
        ("_compression_type", ctypes.c_uint32),
        ("width", ctypes.c_uint16),
        ("height", ctypes.c_uint16),
        ("depth", ctypes.c_uint16),
        ("mipmap_count", ctypes.c_uint16),
        ("unknown_0x010", ctypes.c_uint8 * 0x0C),
    )

    unknown_0x000: int
    header_size: int
    _compression_type: int
    width: int
    height: int
    depth: int
    mipmap_count: int
    unknown_0x010: bytearray

    @property
    def compression_type(self) -> TextureCompressionType:
        return TextureCompressionType(self._compression_type)

    @compression_type.setter
    def compression_type(self, value: TextureCompressionType):
        self._compression_type = value.value
