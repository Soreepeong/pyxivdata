import ctypes

from pyxivdata.network.enums import EffectType


class StatusEffect(ctypes.LittleEndianStructure):
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


class ActionEffect(ctypes.LittleEndianStructure):
    _fields_ = (
        ("_effect_type", ctypes.c_uint8),
        ("param0", ctypes.c_uint8),
        ("param1", ctypes.c_uint8),
        ("param2", ctypes.c_uint8),
        ("_extended_value_highest_byte", ctypes.c_uint8),
        ("flags", ctypes.c_uint8),
        ("_raw_value", ctypes.c_uint16),
    )

    _effect_type: int
    param0: int
    param1: int
    param2: int
    _extended_value_highest_byte: int
    flags: int
    _raw_value: int

    @property
    def effect_type(self) -> EffectType:
        return EffectType(self._effect_type)

    @property
    def absorbed(self) -> bool:
        return bool(self.flags & 0x04)

    @property
    def use_extended_value_byte(self) -> bool:
        return bool(self.flags & 0x40)

    @property
    def effect_on_source(self) -> bool:
        return bool(self.flags & 0x80)

    @property
    def reflected(self) -> bool:
        return bool(self.flags & 0xa0)

    @property
    def critical_hit(self):
        if self._effect_type == EffectType.Damage:
            return bool(self.param0 & 0x01)
        if self._effect_type == EffectType.Heal:
            return bool(self.param1 & 0x01)
        return False

    @property
    def direct_hit(self):
        if self._effect_type == EffectType.Damage:
            return bool(self.param0 & 0x02)
        return False

    @property
    def value(self) -> int:
        if self.use_extended_value_byte:
            return self._extended_value_highest_byte << 16 | self._raw_value
        return self._raw_value


class ActionEffectTarget(ctypes.LittleEndianStructure):
    _fields_ = (
        ("actor_id", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
    )

    actor_id: int
    flags: int


class StatusEffectEntryModificationInfo(ctypes.LittleEndianStructure):
    _fields_ = (
        ("index", ctypes.c_uint8),
        ("unknown_0x001", ctypes.c_uint8 * 1),
        ("effect_id", ctypes.c_uint16),
        ("param", ctypes.c_uint16),
        ("unknown_0x006", ctypes.c_uint8 * 2),
        ("duration", ctypes.c_float),
        ("source_actor_id", ctypes.c_uint32)
    )

    index: int
    unknown_0x001: bytes
    effect_id: int
    param: int
    unknown_0x006: bytes
    duration: float
    source_actor_id: int
