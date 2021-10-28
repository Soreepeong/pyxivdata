import ctypes
import typing

from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.network.common import PositionVector, IpcStructure, uint8_to_float_rot, uint16_to_float, \
    uint16_to_float_rot
from pyxivdata.network.enums import EffectType, EffectDisplayType, ActorControlType, WaymarkType, ActionType, ChatType
from pyxivdata.network.server_ipc.common import ActionEffect, StatusEffect, StatusEffectEntryModificationInfo, \
    ActionEffectTarget
from pyxivdata.network.server_ipc.opcodes import ServerIpcOpcodes


class IpcEffectStub(ctypes.LittleEndianStructure):
    _pack_ = 2
    _fields_ = (
        ("animation_target_id", ctypes.c_uint32),
        ("unknown_0x004", ctypes.c_uint8 * 4),
        ("action_id", ctypes.c_uint32),
        ("global_sequence_id", ctypes.c_uint32),
        ("animation_lock_duration", ctypes.c_float),
        ("some_target_id", ctypes.c_uint32),
        ("source_sequence_id", ctypes.c_uint16),
        ("rotation_uint16", ctypes.c_uint16),
        ("animation_id", ctypes.c_uint16),
        ("animation_variation", ctypes.c_uint8),
        ("_effect_display_type", ctypes.c_uint8),
        ("unknown_0x020", ctypes.c_uint8 * 1),
        ("effect_count", ctypes.c_uint8),
        ("padding_0x022", ctypes.c_uint8 * 8),
    )

    animation_target_id: int
    unknown_0x004: bytearray
    action_id: int
    global_sequence_id: int
    animation_lock_duration: float
    some_target_id: int
    source_sequence_id: int
    rotation_uint16: int
    animation_id: int
    animation_variation: int
    _effect_display_type: int
    unknown_0x01e: bytearray
    effect_count: int
    padding_0x020: bytearray
    effects: typing.Sequence[typing.Sequence[ActionEffect]]
    padding_var_1: bytearray
    target_ids: typing.Sequence[ActionEffectTarget]
    padding_var_2: bytearray

    @property
    def rotation(self):
        return uint16_to_float_rot(self.rotation_uint16)

    @property
    def effect_display_type(self) -> EffectDisplayType:
        return EffectDisplayType(self._effect_display_type)

    @property
    def valid_known_effects_per_target(self) -> typing.Dict[int, typing.List[ActionEffect]]:
        return {
            target.actor_id: [
                effect
                for effect in effects
                if effect.known_effect_type not in (EffectType.Nothing, None)
            ] for target, effects in zip(self.target_ids[:self.effect_count], self.effects[:self.effect_count])
        }


class IpcEffect01(IpcEffectStub, IpcStructure, opcode_field="Effect01"):
    _fields_ = (
        ("effects", ActionEffect * 8 * 1),
        ("padding_var_1", ctypes.c_uint8 * 6),
        ("target_ids", ActionEffectTarget * 1),
        ("padding_var_2", ctypes.c_uint8 * 4)
    )


class IpcEffect08(IpcEffectStub, IpcStructure, opcode_field="Effect08"):
    _fields_ = (
        ("effects", ActionEffect * 8 * 8),
        ("padding_var_1", ctypes.c_uint8 * 6),
        ("target_ids", ActionEffectTarget * 8),
        ("padding_var_2", ctypes.c_uint8 * 12),
    )


class IpcEffect16(IpcEffectStub, IpcStructure, opcode_field="Effect16"):
    _fields_ = (
        ("effects", ActionEffect * 8 * 16),
        ("padding_var_1", ctypes.c_uint8 * 6),
        ("target_ids", ActionEffectTarget * 16),
        ("padding_var_2", ctypes.c_uint8 * 12),
    )


class IpcEffect24(IpcEffectStub, IpcStructure, opcode_field="Effect24"):
    _fields_ = (
        ("effects", ActionEffect * 8 * 24),
        ("padding_var_1", ctypes.c_uint8 * 6),
        ("target_ids", ActionEffectTarget * 24),
        ("padding_var_2", ctypes.c_uint8 * 12),
    )


class IpcEffect32(IpcEffectStub, IpcStructure, opcode_field="Effect32"):
    _fields_ = (
        ("effects", ActionEffect * 8 * 32),
        ("padding_var_1", ctypes.c_uint8 * 6),
        ("target_ids", ActionEffectTarget * 32),
        ("padding_var_2", ctypes.c_uint8 * 12),
    )


class IpcEffectResult(ctypes.LittleEndianStructure, IpcStructure, opcode_field="EffectResult"):
    _fields_ = (
        ("global_sequence_id", ctypes.c_uint32),
        ("actor_id", ctypes.c_uint32),
        ("hp", ctypes.c_uint32),
        ("max_hp", ctypes.c_uint32),
        ("mp", ctypes.c_uint16),
        ("unknown_0x012", ctypes.c_uint8 * 1),
        ("class_or_job", ctypes.c_uint8),
        ("shield_percentage", ctypes.c_uint8),
        ("entry_count", ctypes.c_uint8),
        ("unknown_0x016", ctypes.c_uint8 * 2),
        ("entries", StatusEffectEntryModificationInfo * 4),
    )
    global_sequence_id: int
    actor_id: int
    hp: int
    max_hp: int
    mp: int
    unknown_0x012: bytearray
    class_or_job: int
    shield_percentage: int
    entry_count: int
    unknown_0x016: bytearray
    entries: typing.Sequence[StatusEffectEntryModificationInfo]


class IpcPlayerGauge(ctypes.LittleEndianStructure, IpcStructure, opcode_field="PlayerGauge"):
    _fields_ = (
        ("class_or_job", ctypes.c_uint8),
        ("data", ctypes.c_uint8 * 15),
    )

    class_or_job: int
    data: bytearray


class IpcPlayerParams(ctypes.LittleEndianStructure, IpcStructure, opcode_field="PlayerParams"):
    # order comes from baseparam order column
    _fields_ = (
        ("strength", ctypes.c_uint32),
        ("dexterity", ctypes.c_uint32),
        ("vitality", ctypes.c_uint32),
        ("intelligence", ctypes.c_uint32),
        ("mind", ctypes.c_uint32),
        ("piety", ctypes.c_uint32),
        ("hp", ctypes.c_uint32),
        ("mp", ctypes.c_uint32),
        ("tp", ctypes.c_uint32),
        ("gp", ctypes.c_uint32),
        ("cp", ctypes.c_uint32),
        ("delay", ctypes.c_uint32),
        ("tenacity", ctypes.c_uint32),
        ("attack_power", ctypes.c_uint32),
        ("defense", ctypes.c_uint32),
        ("direct_hit_rate", ctypes.c_uint32),
        ("evasion", ctypes.c_uint32),
        ("magic_defense", ctypes.c_uint32),
        ("critical_hit", ctypes.c_uint32),
        ("attack_magic_potency", ctypes.c_uint32),
        ("healing_magic_potency", ctypes.c_uint32),
        ("elemental_bonus", ctypes.c_uint32),
        ("determination", ctypes.c_uint32),
        ("skill_speed", ctypes.c_uint32),
        ("spell_speed", ctypes.c_uint32),
        ("haste", ctypes.c_uint32),
        ("craftsmanship", ctypes.c_uint32),
        ("control", ctypes.c_uint32),
        ("gathering", ctypes.c_uint32),
        ("perception", ctypes.c_uint32),
    )

    strength: int
    dexterity: int
    vitality: int
    intelligence: int
    mind: int
    piety: int
    hp: int
    mp: int
    tp: int
    gp: int
    cp: int
    delay: int
    tenacity: int
    attack_power: int
    defense: int
    direct_hit_rate: int
    evasion: int
    magic_defense: int
    critical_hit: int
    attack_magic_potency: int
    healing_magic_potency: int
    elemental_bonus: int
    determination: int
    skill_speed: int
    spell_speed: int
    haste: int
    craftsmanship: int
    control: int
    gathering: int
    perception: int


class IpcChat(ctypes.LittleEndianStructure, IpcStructure, opcode_field="Chat"):
    _fields_ = (
        ("content_id", ctypes.c_uint64),
        ("character_id", ctypes.c_uint32),
        ("world_id", ctypes.c_uint16),
        ("_chat_type", ctypes.c_uint16),
        ("_name", ctypes.c_char * 32),
        ("_message", ctypes.c_char * 1012),
    )

    content_id: int
    character_id: int
    world_id: int
    _chat_type: int
    _name: bytearray
    _message: bytearray

    @property
    def chat_type(self) -> ChatType:
        return ChatType(self._chat_type)

    @property
    def name(self) -> str:
        return self._name.decode("utf-8")

    @property
    def message(self) -> SqEscapedString:
        return SqEscapedString(self._message.rstrip(b'\0'))


class IpcChatParty(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ChatParty"):
    _fields_ = (
        ("party_id", ctypes.c_uint64),
        ("content_id", ctypes.c_uint64),
        ("character_id", ctypes.c_uint32),
        ("world_id", ctypes.c_uint8),
        ("unknown_0x015", ctypes.c_uint8 * 2),
        ("_name", ctypes.c_char * 32),
        ("_message", ctypes.c_char * 1025),
    )

    party_id: int
    content_id: int
    character_id: int
    world_id: int
    unknown_0x015: bytearray
    _name: bytearray
    _message: bytearray

    @property
    def name(self) -> str:
        return self._name.decode("utf-8")

    @property
    def message(self) -> SqEscapedString:
        return SqEscapedString(self._message.rstrip(b'\0'))


class IpcChatTell(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ChatTell"):
    _fields_ = (
        ("content_id", ctypes.c_uint64),
        ("world_id", ctypes.c_uint8),
        ("unknown_0x009", ctypes.c_uint8),
        ("unknown_0x00a", ctypes.c_uint8),
        ("_name", ctypes.c_char * 32),
        ("_message", ctypes.c_char * 1029),
    )

    content_id: int
    world_id: int
    unknown_0x009: int
    unknown_0x00a: int
    _name: bytearray
    _message: bytearray

    @property
    def name(self) -> str:
        return self._name.decode("utf-8")

    @property
    def message(self) -> SqEscapedString:
        return SqEscapedString(self._message.rstrip(b'\0'))


class IpcPartyList(ctypes.LittleEndianStructure, IpcStructure, opcode_field="PartyList"):
    class Member(ctypes.LittleEndianStructure):
        _fields_ = (
            ("_name", ctypes.c_char * 32),
            ("content_id", ctypes.c_uint64),
            ("character_id", ctypes.c_uint32),
            ("some_actor_id_1", ctypes.c_uint32),
            ("some_actor_id_2", ctypes.c_uint32),
            ("hp", ctypes.c_uint32),
            ("max_hp", ctypes.c_uint32),
            ("mp", ctypes.c_uint16),
            ("max_mp", ctypes.c_uint16),
            ("unknown_0x040", ctypes.c_uint8 * 2),
            ("zone_id", ctypes.c_uint16),
            ("gpose_selectable", ctypes.c_bool),
            ("class_or_job", ctypes.c_uint8),
            ("unknown_0x046", ctypes.c_uint8 * 1),
            ("level", ctypes.c_uint8),
            ("unknown_0x048", ctypes.c_uint8 * 368),
        )

        # TODO: find coordinates

        _name: bytearray
        content_id: int
        character_id: int
        some_actor_id_1: int
        some_actor_id_2: int
        hp: int
        max_hp: int
        mp: int
        max_mp: int
        unknown_0x040: bytearray
        zone_id: int
        gpose_selectable: bool
        class_or_job: int
        unknown_0x046: bytearray
        level: int
        unknown_0x048: bytearray

        @property
        def name(self) -> str:
            return self._name.decode("utf-8")

    _fields_ = (
        ("members", Member * 8),
        ("content_id_1", ctypes.c_uint64),
        ("party_id", ctypes.c_uint64),
        ("leader_index", ctypes.c_uint8),
        ("party_size", ctypes.c_uint8),
        ("padding_var_1", ctypes.c_uint8 * 6)
    )

    members: typing.Sequence[Member]
    content_id_1: int
    party_id: int
    leader_index: int
    party_size: int
    padding_var_1: bytearray


class IpcPartyModify(ctypes.LittleEndianStructure, IpcStructure, opcode_field="PartyModify"):
    _fields_ = (
        ("leader_content_id", ctypes.c_uint64),
        ("member_content_id", ctypes.c_uint64),
        ("unknown_0x010", ctypes.c_uint8),
        ("unknown_0x011", ctypes.c_uint8),
        ("type", ctypes.c_uint16),
        ("party_size", ctypes.c_uint8),
        ("_leader_name", ctypes.c_char * 32),
        ("_member_name", ctypes.c_char * 32),
        ("padding_0x050", ctypes.c_uint8 * 3),
    )

    leader_content_id: int
    member_content_id: int
    unknown_0x010: int
    unknown_0x011: int
    type: int
    party_size: int
    _leader_name: bytearray
    _member_name: bytearray
    padding_0x050: bytearray

    @property
    def leader_name(self) -> str:
        return self._leader_name.decode("utf-8")

    @property
    def member_name(self) -> str:
        return self._member_name.decode("utf-8")


class IpcAllianceList(ctypes.LittleEndianStructure, IpcStructure, opcode_field="AllianceList"):
    class Member(ctypes.LittleEndianStructure):
        _fields_ = (
            ("_name", ctypes.c_char * 32),
            ("character_id", ctypes.c_uint32),
            ("hp", ctypes.c_uint32),
            ("max_hp", ctypes.c_uint32),
            ("home_world_id", ctypes.c_uint16),
            ("class_or_job", ctypes.c_uint8),
            ("level", ctypes.c_uint8),
            ("unknown_0x030", ctypes.c_uint8),
            ("unknown_0x031", ctypes.c_uint8),
            ("unknown_0x032", ctypes.c_uint8),
            ("unknown_0x033", ctypes.c_uint8),
        )

        # TODO: find coordinates

        _name: bytearray
        character_id: int
        hp: int
        max_hp: int
        home_world_id: int
        class_or_job: int
        level: int
        unknown_0x030: int
        unknown_0x031: int
        unknown_0x032: int
        unknown_0x033: int

        @property
        def name(self) -> str:
            return self._name.decode("utf-8")

    _fields_ = (
        ("members", Member * 16),
        ("padding_var_1", ctypes.c_uint8 * 4)
    )

    members: typing.Sequence[Member]
    padding_var_1: bytearray


class IpcActorCast(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorCast"):
    _fields_ = (
        ("action_id", ctypes.c_uint16),
        ("_action_type", ctypes.c_uint8),
        ("unknown_0x003", ctypes.c_uint8),
        ("effective_verb_id", ctypes.c_uint32),
        ("cast_time", ctypes.c_float),
        ("target_id", ctypes.c_uint32),
        ("rotation_uint16", ctypes.c_uint16),
        ("flag", ctypes.c_uint16),
        ("unknown_0x014", ctypes.c_uint8 * 4),
        ("x_uint16", ctypes.c_uint16),
        ("y_uint16", ctypes.c_uint16),
        ("z_uint16", ctypes.c_uint16),
        ("unknown_0x01e", ctypes.c_uint8 * 2),
    )

    action_id: int
    _action_type: int
    unknown_0x003: int
    effective_action_id: int
    cast_time: float
    target_id: int
    rotation_uint16: int
    flag: int
    unknown_0x014: bytearray
    x_uint16: int
    y_uint16: int
    z_uint16: int
    unknown_0x01e: bytearray

    @property
    def action_type(self):
        return ActionType(self._action_type)

    @property
    def interruptible(self) -> bool:
        return bool(self.flag & 1)

    @property
    def rotation(self):
        return uint16_to_float_rot(self.rotation_uint16)

    @property
    def x(self):
        return uint16_to_float(self.x_uint16)

    @property
    def y(self):
        return uint16_to_float(self.x_uint16)

    @property
    def z(self):
        return uint16_to_float(self.x_uint16)

    @property
    def position_vector(self):
        return PositionVector(self.x, self.y, self.z)


class IpcActorControlStub(ctypes.LittleEndianStructure, IpcStructure):
    _fields_ = (
        ("type", ctypes.c_uint16),
        ("padding_0x002", ctypes.c_uint8 * 2),
        ("param1", ctypes.c_uint32),
        ("param2", ctypes.c_uint32),
        ("param3", ctypes.c_uint32),
        ("param4", ctypes.c_uint32),
    )

    type: int
    padding_0x002: bytearray
    param1: int
    param2: int
    param3: int
    param4: int

    @property
    def known_type(self) -> typing.Optional[ActorControlType]:
        try:
            return ActorControlType(self.type)
        except ValueError:
            return None


class IpcActorControl(IpcActorControlStub, IpcStructure, opcode_field="ActorControl"):
    _fields_ = (
        ("padding_0x018", ctypes.c_uint8 * 4),
    )

    padding_0x018: bytearray


class IpcActorControlSelf(IpcActorControlStub, IpcStructure, opcode_field="ActorControlSelf"):
    _fields_ = (
        ("param5", ctypes.c_uint32),
        ("param6", ctypes.c_uint32),
        ("padding_0x028", ctypes.c_uint8 * 4),
    )

    param5: int
    param6: int
    padding_0x028: bytearray


class IpcActorControlTarget(IpcActorControlStub, IpcStructure, opcode_field="ActorControlTarget"):
    _fields_ = (
        ("param5", ctypes.c_uint32),
        ("target_id", ctypes.c_uint32),
        ("padding_0x028", ctypes.c_uint8 * 4),
    )

    param5: int
    target_id: int
    padding_0x028: bytearray


class IpcActorDespawn(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorDespawn"):
    _fields_ = (
        ("spawn_id", ctypes.c_uint8),
        ("unknown_0x001", ctypes.c_uint8),
        ("unknown_0x002", ctypes.c_uint16),
        ("actor_id", ctypes.c_uint32),
    )

    spawn_id: int
    unknown_0x001: int
    unknown_0x002: int
    actor_id: int


class IpcActorModelEquip(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorModelEquip"):
    _fields_ = (
        ("main_weapon", ctypes.c_uint64),
        ("sub_weapon", ctypes.c_uint64),
        ("unknown_0x010", ctypes.c_uint8),
        ("class_or_job", ctypes.c_uint8),
        ("level", ctypes.c_uint8),
        ("unknown_0x013", ctypes.c_uint8),
        ("models", ctypes.c_uint32 * 10),
        ("padding_0x064", ctypes.c_uint8 * 4),
    )

    main_weapon: int
    sub_weapon: int
    unknown_0x010: bytearray
    class_or_job: int
    level: int
    unknown_0x013: bytearray
    models: typing.Sequence[int]
    padding_0x064: bytearray


class IpcActorMove(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorMove"):
    _fields_ = (
        ("head_rotation_uint8", ctypes.c_uint8),
        ("rotation_uint8", ctypes.c_uint8),
        ("animation_type", ctypes.c_uint8),
        ("animation_state", ctypes.c_uint8),
        ("animation_speed", ctypes.c_uint8),
        ("rotation_unknown_uint8", ctypes.c_uint8),
        ("x_uint16", ctypes.c_uint16),
        ("y_uint16", ctypes.c_uint16),
        ("z_uint16", ctypes.c_uint16),
        ("unknown_0x00c", ctypes.c_uint8 * 4),
    )

    head_rotation_uint8: int
    rotation_uint8: int
    animation_type: int
    animation_state: int
    animation_speed: int
    rotation_unknown_uint8: int
    x_uint16: int
    y_uint16: int
    z_uint16: int
    unknown_0x00c: bytearray

    @property
    def head_rotation(self):
        return uint8_to_float_rot(self.head_rotation_uint8)

    @property
    def rotation(self):
        return uint8_to_float_rot(self.rotation_uint8)

    @property
    def rotation_unknown(self):
        return uint8_to_float_rot(self.rotation_unknown_uint8)

    @property
    def x(self):
        return uint16_to_float(self.x_uint16)

    @property
    def y(self):
        return uint16_to_float(self.y_uint16)

    @property
    def z(self):
        return uint16_to_float(self.z_uint16)

    @property
    def position_vector(self):
        return PositionVector(self.x, self.y, self.z)


class IpcActorSetPos(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorSetPos"):
    _fields_ = (
        ("rotation_uint16", ctypes.c_uint16),
        ("wait_for_load", ctypes.c_bool),
        ("unknown_0x003", ctypes.c_uint8 * 5),
        ("position_vector", PositionVector),
        ("unknown_0x00c", ctypes.c_uint8 * 4),
    )

    rotation_uint16: int
    wait_for_load: bool
    unknown_0x003: bytearray
    position_vector: PositionVector
    unknown_0x00c: bytearray

    @property
    def rotation(self):
        return uint8_to_float_rot(self.rotation_uint16)


class IpcActorSpawn(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorSpawn"):
    _fields_ = (
        ("title_id", ctypes.c_uint16),
        ("unknown_0x002", ctypes.c_uint16),
        ("current_world_id", ctypes.c_uint16),
        ("home_world_id", ctypes.c_uint16),

        ("gm_rank", ctypes.c_uint8),
        ("unknown_0x011", ctypes.c_uint8),
        ("unknown_0x012", ctypes.c_uint8),
        ("online_status", ctypes.c_uint8),
        ("pose", ctypes.c_uint8),
        ("unknown_0x015", ctypes.c_uint8),
        ("unknown_0x016", ctypes.c_uint16),
        ("target_id", ctypes.c_uint64),

        ("unknown_0x020", ctypes.c_uint64),
        ("main_weapon_model", ctypes.c_uint64),

        ("sub_weapon_model", ctypes.c_uint64),
        ("craft_tool_model", ctypes.c_uint64),

        ("unknown_0x040", ctypes.c_uint32),
        ("unknown_0x044", ctypes.c_uint32),
        ("bnpc_base", ctypes.c_uint32),
        ("bnpc_name", ctypes.c_uint32),

        ("unknown_0x050", ctypes.c_uint64),
        ("director_id", ctypes.c_uint32),
        ("owner_id", ctypes.c_uint32),

        ("some_actor_id", ctypes.c_uint32),
        ("max_hp", ctypes.c_uint32),
        ("hp", ctypes.c_uint32),
        ("display_flags", ctypes.c_uint32),

        ("fate_id", ctypes.c_uint16),
        ("mp", ctypes.c_uint16),
        ("max_mp", ctypes.c_uint16),
        ("unknown_0x076", ctypes.c_uint16),
        ("model_chara", ctypes.c_uint16),
        ("rotation_uint16", ctypes.c_uint16),
        ("active_minion", ctypes.c_uint16),
        ("unknown_0x07e", ctypes.c_uint8),
        ("unknown_0x07f", ctypes.c_uint8),

        ("spawn_id", ctypes.c_uint8),
        ("state", ctypes.c_uint8),
        ("persistent_emote", ctypes.c_uint8),
        ("model_type", ctypes.c_uint8),
        ("model_subtype", ctypes.c_uint8),
        ("voice", ctypes.c_uint8),
        ("unknown_0x086", ctypes.c_uint16),
        ("npc_type", ctypes.c_uint8),
        ("level", ctypes.c_uint8),
        ("class_or_job", ctypes.c_uint8),
        ("unknown_0x08b", ctypes.c_uint8),
        ("unknown_0x08c", ctypes.c_uint8),
        ("current_mount", ctypes.c_uint8),
        ("chocobo_barding_head", ctypes.c_uint8),
        ("chocobo_barding_body", ctypes.c_uint8),

        ("chocobo_barding_feet", ctypes.c_uint8),
        ("chocobo_color", ctypes.c_uint8),
        ("unknown_0x092", ctypes.c_uint8),
        ("duty_specific_level", ctypes.c_uint8),
        ("unknown_0x094", ctypes.c_uint8),
        ("unknown_0x095", ctypes.c_uint8),
        ("element_data", ctypes.c_uint8 * 6),
        ("status_effects", StatusEffect * 30),
        ("position_vector", PositionVector),
        ("models", ctypes.c_uint32 * 10),
        ("_name", ctypes.c_char * 32),
        ("look", ctypes.c_uint8 * 26),
        ("_fc_tag", ctypes.c_char * 6),
        ("unknown_var_1", ctypes.c_uint32),
    )

    title_id: int
    unknown_0x002: bytearray
    current_world_id: int
    home_world_id: int
    gm_rank: int
    unknown_0x011: bytearray
    online_status: int
    pose: int
    unknown_0x015: bytearray
    target_id: int
    unknown_0x020: bytearray
    main_weapon_model: int
    sub_weapon_model: int
    craft_tool_model: int
    unknown_0x040: bytearray
    bnpc_base: int
    bnpc_name: int
    unknown_0x050: bytearray
    director_id: int
    owner_id: int
    unknown_0x060: bytearray
    max_hp: int
    hp: int
    display_flags: int
    fate_id: int
    mp: int
    max_mp: int
    unknown_0x076: bytearray
    model_chara: int
    rotation_uint16: int
    active_minion: int
    spawn_id: int
    state: int
    persistent_emote: int
    model_type: int
    model_subtype: int
    voice: int
    unknown_0x084: bytearray
    npc_type: int
    level: int
    class_or_job: int
    unknown_0x089: bytearray
    current_mount: int
    chocobo_barding_head: int
    chocobo_barding_body: int
    chocobo_barding_feet: int
    chocobo_color: int
    scale: int
    element_data: int
    status_effects: typing.Sequence[StatusEffect]
    position_vector: PositionVector
    models: typing.Sequence[int]
    name: bytearray
    look: typing.Sequence[int]
    fc_tag: bytearray
    unknown_var_1: bytearray

    @property
    def rotation(self):
        return uint16_to_float_rot(self.rotation_uint16)

    @property
    def name(self) -> str:
        return self._name.rstrip(b'\0').decode("utf-8")

    @property
    def fc_tag(self) -> str:
        return self._fc_tag.rstrip(b'\0').decode("utf-8")


class IpcActorSpawnNpc(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorSpawnNpc"):
    _fields_ = (
        ("gimmick_id", ctypes.c_uint32),
        ("unknown_0x004", ctypes.c_uint16),
        ("gm_rank", ctypes.c_uint8),
        ("unknown_0x007", ctypes.c_uint8),

        ("aggression_mode", ctypes.c_uint8),
        ("online_status", ctypes.c_uint8),
        ("unknown_0x010", ctypes.c_uint8),
        ("pose", ctypes.c_uint8),
        ("unknown_0x015", ctypes.c_uint32),  # 0x1400
        ("target_id", ctypes.c_uint64),

        ("unknown_0x020", ctypes.c_uint64),
        ("main_weapon_model", ctypes.c_uint64),

        ("sub_weapon_model", ctypes.c_uint64),
        ("craft_tool_model", ctypes.c_uint64),

        # 火剣のメリオール(0x4000a0d4)
        # 法剣のロヴロ(0x4000a0d0)
        # G.M.(0x40009d66)
        # T.A.(0x4000a0d4)
        ("unknown_0x040", ctypes.c_uint32),
        ("unknown_0x044", ctypes.c_uint32),
        ("bnpc_base", ctypes.c_uint32),
        ("bnpc_name", ctypes.c_uint32),

        # 火剣のメリオール(0x85e9cc)
        # ザトゥノル・カンパ(0x84df7b, 0x84df75, 0x84df7c, 0x84df79, 0x84df7d)
        # ウォータースプライト(0x84df6a)
        # ザトゥノル・クリフモ(0x84df9b, 0x84df9f, 0x84df9d, 0x84df9e)
        ("unknown_0x050", ctypes.c_uint64),
        ("director_id", ctypes.c_uint32),
        ("owner_id", ctypes.c_uint32),

        ("some_actor_id", ctypes.c_uint32),
        ("max_hp", ctypes.c_uint32),
        ("hp", ctypes.c_uint32),
        ("display_flags", ctypes.c_uint32),

        ("fate_id", ctypes.c_uint16),
        ("mp", ctypes.c_uint16),
        ("max_mp", ctypes.c_uint16),
        ("unknown_0x076", ctypes.c_uint16),
        ("model_chara", ctypes.c_uint16),
        ("rotation_uint16", ctypes.c_uint16),
        ("active_minion", ctypes.c_uint16),
        ("unknown_0x07e", ctypes.c_uint8),
        ("unknown_0x07f", ctypes.c_uint8),

        ("spawn_id", ctypes.c_uint8),
        ("state", ctypes.c_uint8),
        ("persistent_emote", ctypes.c_uint8),
        ("model_type", ctypes.c_uint8),
        ("model_subtype", ctypes.c_uint8),
        ("voice", ctypes.c_uint8),
        ("unknown_0x086", ctypes.c_uint16),
        ("npc_type", ctypes.c_uint8),
        ("level", ctypes.c_uint8),
        ("class_or_job", ctypes.c_uint8),
        ("unknown_0x08b", ctypes.c_uint8),
        ("unknown_0x08c", ctypes.c_uint8),
        ("current_mount", ctypes.c_uint8),
        ("chocobo_barding_head", ctypes.c_uint8),
        ("chocobo_barding_body", ctypes.c_uint8),

        ("chocobo_barding_feet", ctypes.c_uint8),
        ("chocobo_color", ctypes.c_uint8),
        ("unknown_0x092", ctypes.c_uint8),
        ("duty_specific_level", ctypes.c_uint8),
        ("unknown_0x094", ctypes.c_uint8),
        ("unknown_0x095", ctypes.c_uint8),
        ("element_data", ctypes.c_uint8 * 6),
        ("status_effects", StatusEffect * 30),
        ("position_vector", PositionVector),
        ("models", ctypes.c_uint32 * 10),
        ("_name", ctypes.c_char * 32),
        ("look", ctypes.c_uint8 * 26),
        ("_fc_tag", ctypes.c_char * 6),
        ("unknown_var_1", ctypes.c_uint8 * 4),
    )

    gimmick_id: int
    unknown_0x004: bytearray
    gm_rank: int
    unknown_0x007: bytearray
    aggression_mode: int
    online_status: int
    unknown_0x010: bytearray
    pose: int
    unknown_0x015: bytearray
    target_id: int
    unknown_0x020: bytearray
    main_weapon_model: int
    sub_weapon_model: int
    craft_tool_model: int
    unknown_0x040: bytearray
    bnpc_base: int
    bnpc_name: int
    unknown_0x050: bytearray
    director_id: int
    owner_id: int
    some_actor_id: bytearray
    max_hp: int
    hp: int
    display_flags: int
    fate_id: int
    mp: int
    max_mp: int
    unknown_0x076: bytearray
    model_chara: int
    rotation_uint16: int
    active_minion: int
    spawn_id: int
    state: int
    persistent_emote: int
    model_type: int
    model_subtype: int
    voice: int
    unknown_0x084: bytearray
    npc_type: int
    level: int
    class_or_job: int
    unknown_0x089: bytearray
    current_mount: int
    chocobo_barding_head: int
    chocobo_barding_body: int
    chocobo_barding_feet: int
    chocobo_color: int
    scale: int
    element_data: int
    status_effects: typing.Sequence[StatusEffect]
    position_vector: PositionVector
    models: typing.Sequence[int]
    _name: bytearray
    look: typing.Sequence[int]
    _fc_tag: bytearray
    unknown_var_1: bytearray

    @property
    def rotation(self):
        return uint16_to_float_rot(self.rotation_uint16)

    @property
    def name(self) -> str:
        return self._name.rstrip(b'\0').decode("utf-8")

    @property
    def fc_tag(self) -> str:
        return self._fc_tag.rstrip(b'\0').decode("utf-8")


class IpcActorSpawnNpc2(IpcActorSpawnNpc, opcode_field="ActorSpawnNpc2"):
    pass


class IpcActorStats(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorStats"):
    _fields_ = (
        ("hp", ctypes.c_uint32),
        ("mp", ctypes.c_uint16),
        ("tp", ctypes.c_uint16),
    )

    hp: int
    mp: int
    tp: int


class IpcActorStatusEffectList(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorStatusEffectList"):
    _fields_ = (
        ("class_or_job", ctypes.c_uint8),
        ("level1", ctypes.c_uint8),
        ("level", ctypes.c_uint16),
        ("hp", ctypes.c_uint32),
        ("max_hp", ctypes.c_uint32),
        ("mp", ctypes.c_uint16),
        ("max_mp", ctypes.c_uint16),
        ("shield_percentage", ctypes.c_uint8),
        ("unknown_0x011", ctypes.c_uint8 * 3),
        ("effects", StatusEffect * 30),
        ("unknown_var_1", ctypes.c_uint8 * 4),
    )

    class_or_job: int
    level1: int
    level: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    shield_percentage: int
    unknown_0x011: bytearray
    effects: typing.Sequence[StatusEffect]
    unknown_var_1: bytearray


class IpcActorStatusEffectList2(ctypes.LittleEndianStructure, IpcStructure, opcode_field="ActorStatusEffectList2"):
    _fields_ = (
        ("unknown_0x000", ctypes.c_uint32),
        ("class_or_job", ctypes.c_uint8),
        ("level1", ctypes.c_uint8),
        ("level", ctypes.c_uint16),
        ("hp", ctypes.c_uint32),
        ("max_hp", ctypes.c_uint32),
        ("mp", ctypes.c_uint16),
        ("max_mp", ctypes.c_uint16),
        ("shield_percentage", ctypes.c_uint8),
        ("unknown_0x015", ctypes.c_uint8 * 3),
        ("effects", StatusEffect * 30),
    )

    unknown_0x000: int
    class_or_job: int
    level1: int
    level: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    shield_percentage: int
    unknown_0x015: bytearray
    effects: typing.Sequence[StatusEffect]


class IpcActorStatusEffectListBoss(ctypes.LittleEndianStructure, IpcStructure,
                                   opcode_field="ActorStatusEffectListBoss"):
    _fields_ = (
        ("effects_2", StatusEffect * 30),
        ("class_or_job", ctypes.c_uint8),
        ("level1", ctypes.c_uint8),
        ("level", ctypes.c_uint16),
        ("hp", ctypes.c_uint32),
        ("max_hp", ctypes.c_uint32),
        ("mp", ctypes.c_uint16),
        ("max_mp", ctypes.c_uint16),
        ("shield_percentage", ctypes.c_uint8),
        ("unknown_var_1", ctypes.c_uint8 * 3),
        ("effects_1", StatusEffect * 30),
        ("unknown_var_2", ctypes.c_uint8 * 4),
    )

    effects_2: typing.Sequence[StatusEffect]
    class_or_job: int
    level1: int
    level: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    shield_percentage: int
    unknown_var_1: bytearray
    effects_1: typing.Sequence[StatusEffect]
    unknown_var_2: bytearray

    @property
    def effects(self) -> typing.List[StatusEffect]:
        return [*self.effects_1, *self.effects_2]


class IpcAggroList(ctypes.LittleEndianStructure, IpcStructure, opcode_field="AggroList"):
    class Entry(ctypes.LittleEndianStructure):
        _fields_ = (
            ("actor_id", ctypes.c_uint32),
            ("enmity_percent", ctypes.c_uint8),
            ("unknown_0x005", ctypes.c_uint8 * 3)
        )

        actor_id: int
        enmity_percent: int
        unknown_0x005: bytearray

    _fields_ = (
        ("entry_count", ctypes.c_uint8),
        ("unknown_0x001", ctypes.c_uint8 * 3),
        ("entries", Entry * 32),
        ("padding_0x104", ctypes.c_uint32),
    )

    entry_count: int
    unknown_0x001: bytearray
    entries: typing.Sequence[Entry]
    padding_0x104: bytearray


class IpcAggroRank(ctypes.LittleEndianStructure, IpcStructure, opcode_field="AggroRank"):
    class Entry(ctypes.LittleEndianStructure):
        _fields_ = (
            ("actor_id", ctypes.c_uint32),
            ("enmity", ctypes.c_uint32),
        )

        actor_id: int
        enmity: int

    _fields_ = (
        ("entry_count", ctypes.c_uint8),
        ("unknown_0x001", ctypes.c_uint8 * 3),
        ("entries", Entry * 32),
        ("padding_0x104", ctypes.c_uint32),
    )

    entry_count: int
    unknown_0x001: bytearray
    entries: typing.Sequence[Entry]
    padding_0x104: bytearray


class IpcInitZone(ctypes.LittleEndianStructure, IpcStructure, opcode_field="InitZone"):
    _fields_ = (
        ("server_id", ctypes.c_uint16),
        ("zone_id", ctypes.c_uint16),
        ("unknown_0x004", ctypes.c_uint8 * 2),
        ("content_finder_condition_id", ctypes.c_uint16),
        ("unknown_0x008", ctypes.c_uint8 * 8),
        ("weather_id", ctypes.c_uint8),
        ("flags1", ctypes.c_uint8),
        ("flags2", ctypes.c_uint8),
        ("unknown_0x013", ctypes.c_uint8 * 5),
        ("festival_id", ctypes.c_uint16),
        ("additional_festival_id", ctypes.c_uint16),
        ("unknown_0x024", ctypes.c_uint8 * 40),
        ("position_vector", PositionVector),
        ("unknown_0x050", ctypes.c_uint8 * 16),
    )

    server_id: int
    zone_id: int
    unknown_0x004: bytearray
    content_finder_condition_id: int
    unknown_0x008: bytearray
    weather_id: int
    flags1: int
    flags2: int
    unknown_0x013: bytearray
    festival_id: int
    additional_festival_id: int
    unknown_0x024: bytearray
    position_vector: PositionVector
    unknown_0x050: bytearray


class IpcDirectorUpdate(ctypes.LittleEndianStructure, IpcStructure, opcode_field="DirectorUpdate"):
    _fields_ = (
        ("director_id", ctypes.c_uint32),
        ("sequence", ctypes.c_uint8),
        ("branch", ctypes.c_uint8),
        ("data", ctypes.c_uint8 * 10),
        ("unknown_0x010", ctypes.c_uint16),
        ("unknown_0x012", ctypes.c_uint16),
        ("unknown_0x014", ctypes.c_uint16),
        ("unknown_0x016", ctypes.c_uint16),
    )

    director_id: int
    sequence: int
    branch: int
    data: bytearray
    unknown_0x010: int
    unknown_0x012: int
    unknown_0x014: int
    unknown_0x016: int


class IpcPlaceWaymark(ctypes.LittleEndianStructure, IpcStructure, opcode_field="PlaceWaymark"):
    _fields_ = (
        ("_waymark_type", ctypes.c_uint8),
        ("visible", ctypes.c_bool),
        ("padding_0x002", ctypes.c_uint8 * 2),
        ("x_int32", ctypes.c_int32),
        ("y_int32", ctypes.c_int32),
        ("z_int32", ctypes.c_int32),
    )

    _waymark_type: int
    visible: bool
    padding_0x002: bytearray
    x_int32: int
    y_int32: int
    z_int32: int

    @property
    def waymark_type(self):
        return WaymarkType(self._waymark_type)

    @property
    def x(self) -> float:
        return self.x_int32 / 1000

    @property
    def y(self) -> float:
        return self.y_int32 / 1000

    @property
    def z(self) -> float:
        return self.z_int32 / 1000

    @property
    def position_vector(self):
        return PositionVector(self.x, self.y, self.z)


class IpcPlacePresetWaymark(ctypes.LittleEndianStructure, IpcStructure, opcode_field="PlacePresetWaymark"):
    _fields_ = (
        ("waymark_flags", ctypes.c_uint8),
        ("x_int32", ctypes.c_int32 * 8),
        ("y_int32", ctypes.c_int32 * 8),
        ("z_int32", ctypes.c_int32 * 8),
    )

    waymark_flags: int
    x_int32: typing.Sequence[int]
    y_int32: typing.Sequence[int]
    z_int32: typing.Sequence[int]

    @property
    def x(self) -> typing.List[float]:
        return [i / 1000 for i in self.x_int32]

    @property
    def y(self) -> typing.List[float]:
        return [i / 1000 for i in self.y_int32]

    @property
    def z(self) -> typing.List[float]:
        return [i / 1000 for i in self.z_int32]

    @property
    def position_vectors(self) -> typing.List[PositionVector]:
        return [PositionVector(x, y, z) for x, y, z in zip(self.x, self.y, self.z)]

    @property
    def visible_position_vectors(self) -> typing.Dict[WaymarkType, PositionVector]:
        return {
            waymark_type: position_vector
            for waymark_type, position_vector in zip(WaymarkType, self.position_vectors)
            if self.is_visible(waymark_type)
        }

    def is_visible(self, waymark_type: WaymarkType) -> bool:
        return bool(self.waymark_flags & (1 << waymark_type))
