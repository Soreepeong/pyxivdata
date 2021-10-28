import enum


class ActorControlType(enum.IntEnum):
    Aggro = 0x0004
    ClassJobChange = 0x0005
    Death = 0x0006
    CastInterrupt = 0x000f
    AddStatusEffect = 0x0016  # ? param1=buff_index(uint8), param2=buff_id(uint16), param3=buff_extra(uint16)
    EffectOverTime = 0x0017
    Unknown_0x0022 = 0x0022  # CombatIndicationShow, NetworkTargetIcon?
    Tether = 0x0023  # param3: tether with actor id
    ToggleTargetEnabled = 0x0036  # ToggleNameHidden, NetworkNameToggle; uses "param1", probably as boolean
    MarkTarget = 0x1f6


class EffectDisplayType(enum.IntEnum):
    HideActionName = 0
    ShowActionName = 1
    ShowItemName = 2


class ActionType(enum.IntEnum):
    Normal = 0x01
    ItemAction = 0x02
    Mount = 0x0D


class EffectType(enum.IntEnum):
    # https://github.com/SapphireServer/Sapphire/blob/fee9ed6b0593ee2d324a66195b6163b10faf8237/src/common/Common.h#L626-L657

    Nothing = 0x00
    Miss = 0x01
    FullResist = 0x02
    Damage = 0x03
    Heal = 0x04
    BlockedDamage = 0x05
    ParriedDamage = 0x06
    Invulnerable = 0x07
    NoEffectText = 0x08
    Unknown_0x09 = 0x09
    MpLoss = 0x0a
    MpGain = 0x0b
    TpLoss = 0x0c
    TpGain = 0x0d
    GpGain = 0x0e
    ApplyStatusEffectTarget = 0x0f
    ApplyStatusEffectSource = 0x10  # effect entry on target but buff applies to source, like storm's eye
    StatusNoEffect = 0x14  # shifted one up from 5.18
    StartActionCombo = 0x1b  # shifted one up from 5.18
    ComboSucceed = 0x1c  # shifted one up from 5.18, on retail this is not seen anymore, still working though.
    Knockback = 0x21
    Mount = 0x28  # shifted one down from 5.18
    Unknown_0x34 = 0x34
    VFX = 0x3b  # links to VFX sheet
    Unknown_0x3c = 0x3c
    Unknown_0x42 = 0x42


class TargetMarkerType(enum.IntEnum):
    Attack1 = 1
    Attack2 = 2
    Attack3 = 3
    Attack4 = 4
    Attack5 = 5
    Bind1 = 6
    Bind2 = 7
    Bind3 = 8
    Ignore1 = 9
    Ignore2 = 10
    Square = 11
    Circle = 12
    Cross = 13
    Triangle = 14


class WaymarkType(enum.IntEnum):
    A = 0
    B = 1
    C = 2
    D = 3
    One = 4
    Two = 5
    Three = 6
    Four = 7


class ChatType(enum.IntEnum):
    LogKindError = 0
    ServerDebug = 1
    ServerUrgent = 2
    ServerNotice = 3
    Unused4 = 4
    Unused5 = 5
    Unused6 = 6
    Unused7 = 7
    Unused8 = 8
    Unused9 = 9
    Say = 10
    Shout = 11
    Tell = 12
    TellReceive = 13
    Party = 14
    Alliance = 15
    LS1 = 16
    LS2 = 17
    LS3 = 18
    LS4 = 19
    LS5 = 20
    LS6 = 21
    LS7 = 22
    LS8 = 23
    FreeCompany = 24
    Unused25 = 25
    Unused26 = 26
    NoviceNetwork = 27
    CustomEmote = 28
    StandardEmote = 29
    Yell = 30
    Unknown31 = 31
    PartyUnk2 = 32
    Unused33 = 33
    Unused34 = 34
    Unused35 = 35
    Unused36 = 36
    Unused37 = 37
    Unused38 = 38
    Unused39 = 39
    Unused40 = 40
    BattleDamage = 41
    BattleFailed = 42
    BattleActions = 43
    BattleItems = 44
    BattleHealing = 45
    BattleBeneficial = 46
    BattleDetrimental = 47
    BattleUnk48 = 48
    BattleUnk49 = 49
    Unused50 = 50
    Unused51 = 51
    Unused52 = 52
    Unused53 = 53
    Unused54 = 54
    Unused55 = 55
    Echo = 56
    SystemMessage = 57
    SystemErrorMessage = 58
    BattleSystem = 59
    GatheringSystem = 60
    NPCMessage = 61
    LootMessage = 62
    Unused63 = 63
    CharProgress = 64
    Loot = 65
    Crafting = 66
    Gathering = 67
    NPCAnnouncement = 68
    FCAnnouncement = 69
    FCLogin = 70
    RetainerSale = 71
    PartySearch = 72
    PCSign = 73
    DiceRoll = 74
    NoviceNetworkNotice = 75
    Unknown76 = 76
    Unused77 = 77
    Unused78 = 78
    Unused79 = 79
    GMTell = 80
    GMSay = 81
    GMShout = 82
    GMYell = 83
    GMParty = 84
    GMFreeCompany = 85
    GMLS1 = 86
    GMLS2 = 87
    GMLS3 = 88
    GMLS4 = 89
    GMLS5 = 90
    GMLS6 = 91
    GMLS7 = 92
    GMLS8 = 93
    GMNoviceNetwork = 94
    Unused95 = 95
    Unused96 = 96
    Unused97 = 97
    Unused98 = 98
    Unused99 = 99
    Unused100 = 100
