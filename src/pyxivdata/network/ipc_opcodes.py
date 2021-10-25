import dataclasses
import typing


@dataclasses.dataclass
class GameIpcOpcodes:
    """
    Define opcodes for IPC.
    Practically an enum, so CamelCase is being used.

    See: https://github.com/SapphireServer/Sapphire/blob/master/src/common/Network/PacketDef/Zone/ServerZoneDef.h
    """

    Effect01: typing.Optional[int] = 0x03ca
    Effect08: typing.Optional[int] = 0x03c4
    Effect16: typing.Optional[int] = 0x00fa
    Effect24: typing.Optional[int] = 0x0339
    Effect32: typing.Optional[int] = 0x023c
    EffectResult: typing.Optional[int] = 0x0387
    ActorCast: typing.Optional[int] = 0x015d
    ActorControl: typing.Optional[int] = 0x00b0
    ActorControlSelf: typing.Optional[int] = 0x02b6
    ActorControlTarget: typing.Optional[int] = 0x03c5
    UpdateHpMpTp: typing.Optional[int] = 0x01a7
    PlayerSetup: typing.Optional[int] = 0x01d5
    PlayerSpawn: typing.Optional[int] = 0x01d8
    NpcSpawn: typing.Optional[int] = 0x00d2
    ModelEquip: typing.Optional[int] = 0x03a2
    PlayerStats: typing.Optional[int] = 0x0295
    StatusEffectList: typing.Optional[int] = 0x0074
    StatusEffectList2: typing.Optional[int] = 0x02aa
    StatusEffectListBoss: typing.Optional[int] = 0x0223
