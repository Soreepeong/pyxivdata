import ctypes
import enum
import typing


class ConnectionType(enum.IntEnum):
    Zone = 1
    Chat = 2


class GameMessageBundleHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("signature", ctypes.c_char * 16),
        ("timestamp", ctypes.c_uint64),
        ("size", ctypes.c_uint32),
        ("_connection_type", ctypes.c_uint16),
        ("message_count", ctypes.c_uint16),
        ("is_big_endian", ctypes.c_bool),
        ("is_deflated", ctypes.c_bool),
        ("unknown_0x022", ctypes.c_uint8 * 6)
    )

    SIGNATURE_1: typing.ClassVar[bytes] = b"\x52\x52\xa0\x41\xff\x5d\x46\xe2\x7f\x2a\x64\x4d\x7b\x99\xc4\x75"
    SIGNATURE_2: typing.ClassVar[bytes] = b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    signature: bytearray
    timestamp: int
    size: int
    _connection_type: int
    message_count: int
    is_big_endian: bool
    is_deflated: bool
    unknown_0x022: bytearray

    @property
    def connection_type(self) -> ConnectionType:
        return ConnectionType(self._connection_type)

    @connection_type.setter
    def connection_type(self, value: ConnectionType):
        self._connection_type = value.value


class GameMessageHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("size", ctypes.c_uint32),
        ("actor_id", ctypes.c_uint32),
        ("login_actor_id", ctypes.c_uint32),
        ("type", ctypes.c_uint16),
        ("unknown_0x00e", ctypes.c_uint8 * 2),
    )

    TYPE_IPC = 3
    TYPE_CLIENT_KEEP_ALIVE = 7
    TYPE_SERVER_KEEP_ALIVE = 8

    size: int
    actor_id: int
    login_actor_id: int
    type: int
    unknown_0x00e: bytes


class GameIpcMessageDataHeader(ctypes.LittleEndianStructure):
    _fields_ = (
        ("type1", ctypes.c_uint16),
        ("type2", ctypes.c_uint16),
        ("unknown_0x004", ctypes.c_uint8 * 2),
        ("server_id", ctypes.c_uint16),
        ("timestamp", ctypes.c_uint32),
        ("unknown_0x014", ctypes.c_uint8 * 4)
    )

    type1: int
    type2: int
    unknown_0x004: bytes
    server_id: int
    timestamp: int
    unknown_0x014: int
