import enum


class ActorControlType(enum.IntEnum):
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

    Nothing = 0
    Miss = 1
    FullResist = 2
    Damage = 3
    Heal = 4
    BlockedDamage = 5
    ParriedDamage = 6
    Invulnerable = 7
    NoEffectText = 8
    Unknown_9 = 9
    MpLoss = 10
    MpGain = 11
    TpLoss = 12
    TpGain = 13
    GpGain = 14
    ApplyStatusEffectTarget = 15
    ApplyStatusEffectSource = 16  # effect entry on target but buff applies to source, like storm's eye
    StatusNoEffect = 20  # shifted one up from 5.18
    StartActionCombo = 27  # shifted one up from 5.18
    ComboSucceed = 28  # shifted one up from 5.18, on retail this is not seen anymore, still working though.
    Knockback = 33
    Mount = 40  # shifted one down from 5.18
    VFX = 59  # links to VFX sheet


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
    A = 1
    B = 2
    C = 3
    D = 4
    One = 5
    Two = 6
    Three = 7
    Four = 8


class ChatType(enum.IntEnum):
    LogKindError = 1
    ServerDebug = 2
    ServerUrgent = 3
    ServerNotice = 4
    Unused4 = 5
    Unused5 = 6
    Unused6 = 7
    Unused7 = 8
    Unused8 = 9
    Unused9 = 10
    Say = 11
    Shout = 12
    Tell = 13
    TellReceive = 14
    Party = 15
    Alliance = 16
    LS1 = 17
    LS2 = 18
    LS3 = 19
    LS4 = 20
    LS5 = 21
    LS6 = 22
    LS7 = 23
    LS8 = 24
    FreeCompany = 25
    Unused25 = 26
    Unused26 = 27
    NoviceNetwork = 28
    CustomEmote = 29
    StandardEmote = 30
    Yell = 31
    Unknown31 = 32
    PartyUnk2 = 33
    Unused33 = 34
    Unused34 = 35
    Unused35 = 36
    Unused36 = 37
    Unused37 = 38
    Unused38 = 39
    Unused39 = 40
    Unused40 = 41
    BattleDamage = 42
    BattleFailed = 43
    BattleActions = 44
    BattleItems = 45
    BattleHealing = 46
    BattleBeneficial = 47
    BattleDetrimental = 48
    BattleUnk48 = 49
    BattleUnk49 = 50
    Unused50 = 51
    Unused51 = 52
    Unused52 = 53
    Unused53 = 54
    Unused54 = 55
    Unused55 = 56
    Echo = 57
    SystemMessage = 58
    SystemErrorMessage = 59
    BattleSystem = 60
    GatheringSystem = 61
    NPCMessage = 62
    LootMessage = 63
    Unused63 = 64
    CharProgress = 65
    Loot = 66
    Crafting = 67
    Gathering = 68
    NPCAnnouncement = 69
    FCAnnouncement = 70
    FCLogin = 71
    RetainerSale = 72
    PartySearch = 73
    PCSign = 74
    DiceRoll = 75
    NoviceNetworkNotice = 76
    Unknown76 = 77
    Unused77 = 78
    Unused78 = 79
    Unused79 = 80
    GMTell = 81
    GMSay = 82
    GMShout = 83
    GMYell = 84
    GMParty = 85
    GMFreeCompany = 86
    GMLS1 = 87
    GMLS2 = 88
    GMLS3 = 89
    GMLS4 = 90
    GMLS5 = 91
    GMLS6 = 92
    GMLS7 = 93
    GMLS8 = 94
    GMNoviceNetwork = 95
    Unused95 = 96
    Unused96 = 97
    Unused97 = 98
    Unused98 = 99
    Unused99 = 100
    Unused100 = 101
