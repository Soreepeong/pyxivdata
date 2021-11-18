import ctypes

from pyxivdata.escaped_string import SeString
from pyxivdata.network.common import IpcStructure, PositionVector, uint8_to_float_rot
from pyxivdata.network.enums import ActionType, ChatType


class IpcRequestMove(ctypes.LittleEndianStructure, IpcStructure, opcode_field="RequestMove"):
    _fields_ = (
        ("rotation", ctypes.c_float),
        ("animation_type", ctypes.c_uint8),
        ("animation_state", ctypes.c_uint8),
        ("client_animation_type", ctypes.c_uint8),
        ("head_rotation_uint8", ctypes.c_uint8),
        ("position_vector", PositionVector),
        ("unknown_0x00c", ctypes.c_uint8 * 4),
    )

    rotation: float
    animation_type: int
    animation_state: int
    client_animation_type: int
    head_rotation_uint8: int
    position_vector: PositionVector
    unknown_0x00c: bytearray

    @property
    def head_rotation(self):
        return uint8_to_float_rot(self.head_rotation_uint8)


class IpcRequestMoveInstance(ctypes.LittleEndianStructure, IpcStructure, opcode_field="RequestMoveInstance"):
    _fields_ = (
        ("rotation", ctypes.c_float),
        ("interpolate_rotation", ctypes.c_float),
        ("flags", ctypes.c_uint32),
        ("position_vector", PositionVector),
        ("interpolate_position_vector", PositionVector),
        ("padding_0x024", ctypes.c_uint8 * 4),
    )

    rotation: float
    interpolate_rotation: float
    flags: int
    position_vector: PositionVector
    interpolate_position_vector: PositionVector
    padding_0x024: bytearray


class IpcRequestAction(ctypes.LittleEndianStructure, IpcStructure, opcode_field="RequestAction"):
    _fields_ = (
        ("padding_0x000", ctypes.c_uint8 * 1),
        ("_action_type", ctypes.c_uint8),
        ("padding_0x003", ctypes.c_uint8 * 2),
        ("action_id", ctypes.c_uint32),
        ("sequence", ctypes.c_uint16),
        ("padding_0x00c", ctypes.c_uint8),
        ("target_id", ctypes.c_uint64),
        ("item_source_slot", ctypes.c_uint16),
        ("item_source_container", ctypes.c_uint16),
        ("unknown_0x01c", ctypes.c_uint8 * 4),
    )

    padding_0x000: bytearray
    _action_type: int
    padding_0x003: bytearray
    action_id: int
    sequence: int
    padding_0x00c: bytearray
    target_id: int
    item_source_slot: int
    item_source_container: int
    unknown_0x01c: bytearray

    @property
    def action_type(self):
        return ActionType(self._action_type)


class IpcRequestActionFromCoordinates(ctypes.LittleEndianStructure, IpcStructure,
                                      opcode_field="RequestActionFromCoordinates"):
    _fields_ = (
        ("padding_0x000", ctypes.c_uint8 * 1),
        ("_action_type", ctypes.c_uint8),
        ("padding_0x003", ctypes.c_uint8 * 2),
        ("action_id", ctypes.c_uint32),
        ("sequence", ctypes.c_uint16),
        ("padding_0x00c", ctypes.c_uint8 * 6),
        ("position_vector", PositionVector),
        ("unknown_0x01c", ctypes.c_uint8 * 4),
    )

    padding_0x000: bytearray
    _action_type: int
    padding_0x003: bytearray
    action_id: int
    sequence: int
    padding_0x00c: bytearray
    position_vector: PositionVector
    unknown_0x01c: bytearray

    @property
    def action_type(self):
        return ActionType(self._action_type)


class IpcRequestEmote(ctypes.LittleEndianStructure, IpcStructure, opcode_field="RequestEmote"):
    _fields_ = (
        ("actor_id", ctypes.c_uint64),
        ("event_id", ctypes.c_uint32),
        ("emote_id", ctypes.c_uint16),
        # TODO: shouldn't there be something that indicates whether to leave emote messages?
        #   ex. `/hug` vs `/hug motion`
    )

    actor_id: int
    event_id: int
    emote_id: int


class IpcRequestTell(ctypes.LittleEndianStructure, IpcStructure, opcode_field="RequestTell"):
    _fields_ = (
        ("content_id", ctypes.c_uint64),
        ("world_id", ctypes.c_uint16),
        ("unknown_0x00a", ctypes.c_uint8 * 6),
        ("world_id_2", ctypes.c_uint16),
        ("unknown_0x012", ctypes.c_uint8 * 1),
        ("_target_name", ctypes.c_char * 32),
        ("_message", ctypes.c_char * 1029),
    )

    content_id: int
    world_id: int
    unknown_0x00a: bytearray
    world_id_2: int
    unknown_0x012: bytearray
    _target_name: bytearray
    _message: bytearray

    @property
    def target_name(self) -> str:
        return self._target_name.decode("utf-8")

    @property
    def message(self) -> SeString:
        return SeString(self._message.rstrip(b'\0'))


class IpcRequestChat(ctypes.LittleEndianStructure, IpcStructure, opcode_field="RequestChat"):
    _fields_ = (
        ("padding_0x000", ctypes.c_uint8 * 4),
        ("source_id", ctypes.c_uint32),
        ("position_vector", PositionVector),
        ("rotation", ctypes.c_float),
        ("_chat_type", ctypes.c_uint16),
        ("_message", ctypes.c_char * 1012),
    )

    padding_0x000: bytearray
    source_id: int
    position_vector: PositionVector
    rotation: float
    _chat_type: int
    _message: bytearray

    @property
    def chat_type(self) -> ChatType:
        return ChatType(self._chat_type)

    @property
    def message(self) -> SeString:
        return SeString(self._message.rstrip(b'\0'))


class IpcRequestChatParty(ctypes.LittleEndianStructure, IpcStructure, opcode_field="RequestChatParty"):
    _fields_ = (
        ("party_id", ctypes.c_uint64),
        ("_message", ctypes.c_char * 1024),
    )

    party_id: int
    _message: bytearray

    @property
    def message(self) -> SeString:
        return SeString(self._message.rstrip(b'\0'))
