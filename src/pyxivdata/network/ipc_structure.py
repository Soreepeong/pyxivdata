import ctypes
import typing

from pyxivdata.common import AlmostStructureBase


class GameIpcDataCommonStatusEffect(ctypes.LittleEndianStructure):
    _fields_ = (
        ("effect_id", ctypes.c_uint16),
        ("param", ctypes.c_uint16),
        ("duration", ctypes.c_float),
        ("source_actor_id", ctypes.c_uint32),
    )

    effect_id: int
    param: int
    duration: float
    source_actor_id: int


class GameIpcDataCommonActionEffect(ctypes.LittleEndianStructure):
    _fields_ = (
        ("effect_type", ctypes.c_uint8),
        ("param0", ctypes.c_uint8),
        ("param1", ctypes.c_uint8),
        ("param2", ctypes.c_uint8),
        ("extended_value_highest_byte", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("value", ctypes.c_uint16),
    )

    effect_type: int
    param0: int
    param1: int
    param2: int
    extended_value_highest_byte: int
    flags: int
    value: int


class GameIpcDataCommonPositionVector(ctypes.LittleEndianStructure):
    _fields_ = (
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
    )

    x: float
    y: float
    z: float


class GameIpcDataCommonStatusEffectEntryModificationInfo(ctypes.LittleEndianStructure):
    _fields_ = (
        ("index", ctypes.c_uint8),
        ("unknown_3", ctypes.c_uint8),  # "unknown1"
        ("effect_id", ctypes.c_uint16),
        ("param", ctypes.c_uint16),  # "unknown2"
        ("unknown_4", ctypes.c_uint16),  # "unknown3"
        ("duration", ctypes.c_float),
        ("source_actor_id", ctypes.c_uint32)
    )

    index: int
    effect_id: int
    param: int
    duration: float
    source_actor_id: int


class GameIpcDataIpcOnPlayerSpawn(AlmostStructureBase):
    @property
    def name(self) -> str:
        begin_offset = self._offset + 0x0230
        return self._data[begin_offset:self._data.find(0, begin_offset)].decode("utf-8")

    @property
    def owner_id(self) -> int:
        return self._uint32_at(0x0054)

    @property
    def max_hp(self) -> int:
        return self._uint32_at(0x005c)

    @property
    def hp(self) -> int:
        return self._uint32_at(0x0060)

    @property
    def max_mp(self) -> int:
        return self._uint16_at(0x006a)

    @property
    def mp(self) -> int:
        return self._uint16_at(0x006c)

    @property
    def bnpcname_id(self) -> int:
        return self._uint32_at(0x0044)

    @property
    def job(self) -> int:
        return self._data[self._offset + 0x0082]

    @property
    def level(self) -> int:
        return self._data[self._offset + 0x0081]

    @property
    def status_effects(self) -> typing.List[GameIpcDataCommonStatusEffect]:
        offset = self._offset + 0x0094
        return [
            GameIpcDataCommonStatusEffect.from_buffer(
                self._data, offset + i * ctypes.sizeof(GameIpcDataCommonStatusEffect)
            ) for i in range(30)
        ]

    @property
    def position_vector(self) -> GameIpcDataCommonPositionVector:
        return GameIpcDataCommonPositionVector.from_buffer(self._offset + 0x01fc)


class GameIpcDataIpcModelEquip(AlmostStructureBase):
    @property
    def job(self) -> int:
        return self._data[self._offset + 0x0011]

    @property
    def level(self) -> int:
        return self._data[self._offset + 0x0012]


class GameIpcDataIpcActionEffect(AlmostStructureBase):
    SLOTS_PER_EFFECT_COUNT: typing.ClassVar[typing.Sequence[int]] = (
        8,  # Missed AoE results in 8-slot response.
        1, 8, 8, 8, 8, 8, 8, 8,
        16, 16, 16, 16, 16, 16, 16, 16,
        24, 24, 24, 24, 24, 24, 24, 24,
        32, 32, 32, 32, 32, 32, 32, 32,
    )

    @property
    def action_id(self) -> int:
        return self._uint32_at(0x0008)

    @property
    def global_sequence_id(self):
        return self._uint32_at(0x000c)

    @property
    def animation_lock_duration(self) -> float:
        return self._float_at(0x0010)

    @property
    def effect_count(self) -> int:
        return self._data[self._offset + 0x0021]

    @property
    def action_effects(self) -> typing.List[typing.List[GameIpcDataCommonActionEffect]]:
        offset = self._offset + 0x002a
        try:
            effect_slot_count = GameIpcDataIpcActionEffect.SLOTS_PER_EFFECT_COUNT[self.effect_count]
        except KeyError:
            raise RuntimeError(f"effect_count above {self.effect_count} is unsupported")
        return [
            [
                GameIpcDataCommonActionEffect.from_buffer(
                    self._data, offset + ctypes.sizeof(GameIpcDataCommonActionEffect) * (i * 8 + j)
                ) for j in range(8)
            ] for i in range(effect_slot_count)
        ]

    @property
    def targets(self) -> typing.List[int]:
        try:
            effect_slot_count = GameIpcDataIpcActionEffect.SLOTS_PER_EFFECT_COUNT[self.effect_count]
        except KeyError:
            raise RuntimeError(f"effect_count above {self.effect_count} is unsupported")
        offset = 0x002a + ctypes.sizeof(GameIpcDataCommonActionEffect) * 8 * effect_slot_count + 6
        return [self._uint32_at(offset + 2 * 4 * i) for i in range(effect_slot_count)]


class GameIpcDataIpcUpdateHpMpTp(AlmostStructureBase):
    @property
    def hp(self):
        return self._uint32_at(0x0000)

    @property
    def mp(self):
        return self._uint16_at(0x0004)


class GameIpcDataIpcActorStats(AlmostStructureBase):
    @property
    def max_hp(self) -> int:
        return self._uint32_at(0x0018)

    @property
    def max_mp(self) -> int:
        return self._uint32_at(0x001c)

    @property
    def attack_power(self) -> int:
        return self._uint32_at(0x0034)

    @property
    def critical_hit(self) -> int:
        return self._uint32_at(0x0048)

    @property
    def magic_attack_potency(self) -> int:
        return self._uint32_at(0x004c)

    @property
    def magic_heal_potency(self) -> int:
        return self._uint32_at(0x0050)

    @property
    def skill_speed(self) -> int:
        return self._uint32_at(0x005c)

    @property
    def spell_speed(self) -> int:
        return self._uint32_at(0x0060)


class GameIpcDataIpcActorControl(AlmostStructureBase):
    CATEGORY_JOB_CHANGE = 0x0005
    CATEGORY_DEATH = 0x0006
    CATEGORY_CANCEL_CAST = 0x000f
    CATEGORY_EFFECT_OVER_TIME = 0x0017

    @property
    def category(self) -> int:
        return self._uint16_at(0x0000)

    @property
    def padding1(self) -> int:  # not actually a padding
        return self._uint16_at(0x0002)

    @property
    def param1(self) -> int:
        return self._uint32_at(0x0004)

    @property
    def param2(self) -> int:
        return self._uint32_at(0x0008)

    @property
    def param3(self) -> int:
        return self._uint32_at(0x000c)

    @property
    def param4(self) -> int:
        return self._uint32_at(0x0010)

    @property
    def padding2(self) -> int:
        return self._uint32_at(0x0014)


class GameIpcDataIpcActionEffectResult(AlmostStructureBase):
    @property
    def global_sequence_id(self):
        return self._uint32_at(0x0000)

    @property
    def actor_id(self):  # don't use?
        return self._uint32_at(0x0004)

    @property
    def hp(self):
        return self._uint32_at(0x0008)

    @property
    def max_hp(self):
        return self._uint32_at(0x000c)

    @property
    def mp(self):
        return self._uint16_at(0x0010)

    @property
    def job(self):
        return self._data[self._offset + 0x0013]

    @property
    def shield_percentage(self):
        return self._data[self._offset + 0x0014]

    @property
    def entry_count(self):
        return self._data[self._offset + 0x0015]

    @property
    def entries(self) -> typing.List[GameIpcDataCommonStatusEffectEntryModificationInfo]:
        offset = self._offset + 0x0018
        return [
            GameIpcDataCommonStatusEffectEntryModificationInfo.from_buffer(
                self._data, offset + ctypes.sizeof(GameIpcDataCommonStatusEffectEntryModificationInfo) * i
            ) for i in range(self.entry_count)
        ]


class GameIpcDataIpcStatusEffectList(AlmostStructureBase):
    _info_offset: int
    _has_more_effect_list: bool

    @classmethod
    def from_buffer(cls, data: typing.Union[bytearray], offset: int = 0,
                    is_type_2: bool = False, is_boss: bool = False):
        self = cls()
        self._data = data
        self._offset = offset
        self._info_offset = 4 if is_type_2 else (30 * ctypes.sizeof(GameIpcDataCommonStatusEffect) if is_boss else 0)
        self._has_more_effect_list = is_boss
        return self

    @property
    def job(self):
        return self._data[self._offset + self._info_offset + 0x0000]

    @property
    def effective_level(self):
        return self._data[self._offset + self._info_offset + 0x0001]

    @property
    def level(self):
        return self._data[self._offset + self._info_offset + 0x0002]

    @property
    def synced_level(self):
        return self._data[self._offset + self._info_offset + 0x0003]

    @property
    def hp(self):
        return self._uint32_at(self._info_offset + 0x0004)

    @property
    def max_hp(self):
        return self._uint32_at(self._info_offset + 0x0008)

    @property
    def mp(self):
        return self._uint16_at(self._info_offset + 0x000c)

    @property
    def max_mp(self):
        return self._uint16_at(self._info_offset + 0x000e)

    @property
    def shield_percentage(self):
        return self._data[self._offset + self._info_offset + 0x0010]

    @property
    def status_effects(self) -> typing.List[GameIpcDataCommonStatusEffect]:
        offset = self._offset + self._info_offset + 0x0014
        result = [
            GameIpcDataCommonStatusEffect.from_buffer(
                self._data, offset + i * ctypes.sizeof(GameIpcDataCommonStatusEffect)
            ) for i in range(30)
        ]
        if self._has_more_effect_list:
            offset = self._offset
            result += [
                GameIpcDataCommonStatusEffect.from_buffer(
                    self._data, offset + i * ctypes.sizeof(GameIpcDataCommonStatusEffect)
                ) for i in range(30)
            ]
        return result
