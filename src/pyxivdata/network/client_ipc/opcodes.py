import dataclasses
import typing


@dataclasses.dataclass
class ClientIpcOpcodes:
    """
    Define opcodes for IPC.
    Practically an enum, thus using CamelCase.

    See: https://github.com/SapphireServer/Sapphire/blob/master/src/common/Network/PacketDef/Zone/ClientZoneDef.h
    """

    RequestMove: typing.Optional[int] = None
    RequestMoveInstance: typing.Optional[int] = None
    RequestAction: typing.Optional[int] = 0x02dc
    RequestActionFromCoordinates: typing.Optional[int] = 0x0152
    RequestEmote: typing.Optional[int] = None
    RequestTell: typing.Optional[int] = None
    RequestChat: typing.Optional[int] = None
