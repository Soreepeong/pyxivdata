import dataclasses
import typing


@dataclasses.dataclass
class ServerIpcOpcodes:
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

    PlayerGauge: typing.Optional[int] = 0x01c1
    # PlayerSetup: typing.Optional[int] = 0x01d5
    PlayerParams: typing.Optional[int] = 0x0295

    Chat: typing.Optional[int] = None
    ChatParty: typing.Optional[int] = None
    # ServerNoticeShort: typing.Optional[int] = None
    # ServerNotice: typing.Optional[int] = None

    PartyList: typing.Optional[int] = None

    ActorCast: typing.Optional[int] = 0x015d
    ActorControl: typing.Optional[int] = 0x00b0
    ActorControlSelf: typing.Optional[int] = 0x02b6
    ActorControlTarget: typing.Optional[int] = 0x03c5
    ActorDespawn: typing.Optional[int] = None
    ActorModelEquip: typing.Optional[int] = 0x03a2
    ActorMove: typing.Optional[int] = 0x00f8
    # ActorOwner: typing.Optional[int] = None
    ActorSetPos: typing.Optional[int] = 0x0299
    ActorSpawn: typing.Optional[int] = 0x01d8
    ActorSpawnNpc: typing.Optional[int] = 0x00d2
    ActorSpawnNpc2: typing.Optional[int] = 0x018a
    ActorStats: typing.Optional[int] = 0x01a7
    ActorStatusEffectList: typing.Optional[int] = 0x0074
    ActorStatusEffectList2: typing.Optional[int] = 0x02aa
    ActorStatusEffectListBoss: typing.Optional[int] = 0x0223

    # TODO: How are these two different? One is incoming and one is outgoing?
    AggroList: typing.Optional[int] = None
    AggroRank: typing.Optional[int] = None

    InitZone: typing.Optional[int] = None

    PlaceWaymark: typing.Optional[int] = 0x0371
    PlacePresetWaymark: typing.Optional[int] = 0x026d

    # ObjectSpawn: typing.Optional[int] = None
    # ObjectDespawn: typing.Optional[int] = None
