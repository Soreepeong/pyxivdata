import enum

from pyxivdata.escaped_string import SeString
from pyxivdata.resource.excel.reader import ExdRow


# See:
# https://github.com/xivapi/SaintCoinach/tree/master/SaintCoinach/Definitions/
# https://github.com/xivapi/ffxiv-datamining/tree/master/csv/

class ActionRow(ExdRow):
    class AttackType(enum.IntEnum):
        Neutral = -1  # ?
        Undefined = 0
        Slashing = 1
        Piercing = 2
        Blunt = 3
        Shot = 4  # there probably exists a better word for this
        Magic = 5
        Breath = 6
        Sound = 7
        LimitBreak = 8

    name: SeString = 0
    icon: int = 2
    action_category_id: int = 3
    class_job: int = 12
    is_role_action: bool = 13
    range: int = 14
    targets_self: bool = 15
    targets_party: bool = 16
    targets_friendly: bool = 17
    targets_hostile: bool = 18
    targets_area: bool = 21
    targets_dead: bool = 25
    cast_type: int = 27
    effect_range: int = 28
    x_axis_modifier: int = 29
    primary_cost_type: int = 31
    primary_cost_value: int = 32
    secondary_cost_type: int = 33
    secondary_cost_value: int = 34
    action_combo: int = 35
    preserves_combo: bool = 36
    cast_100ms: int = 37
    recast_100ms: int = 39
    cooldown_group: int = 40
    additional_cooldown_group: int = 41
    max_charges: int = 42
    attack_type: AttackType = 43
    aspect: int = 44
    action_proc_status: int = 45
    status_gain_self: int = 47
    class_job_category: int = 49
    affects_position: int = 52
    omen: int = 53
    is_pvp: bool = 55
    is_player_action: bool = 67


class ActionCategoryRow(ExdRow):
    name: SeString = 0


class ActionTransientRow(ExdRow):
    description: SeString = 0


class CompletionRow(ExdRow):
    group_id: int = 0
    key: int = 1
    lookup_table: SeString = 2
    text: SeString = 3
    group_title: SeString = 4


class MainCommand(ExdRow):
    icon_id: int = 0
    category: int = 1
    main_command_category_id: int = 2
    sort_id: int = 3
    name: SeString = 4
    description: SeString = 5


class MapRow(ExdRow):
    map_condition_id: int = 0
    priority_category_ui: int = 1
    priority_ui: int = 2
    map_index: int = 3
    hierarchy: int = 4
    map_marker_range: int = 5
    id: SeString = 6
    size_factor: int = 7
    offset_x: int = 8
    offset_y: int = 9
    placename_region_id: int = 10
    placename_id: int = 11
    placename_sub_id: int = 12
    discovery_index: int = 13
    discovery_flag: int = 14
    territory_type_id: int = 15
    discovery_array_byte: bool = 16
    is_event: bool = 17


class StatusRow(ExdRow):
    class StatusCategory(enum.IntEnum):
        Undefined = 0
        Beneficial = 1
        Detrimental = 2

    name: SeString = 0
    description: SeString = 1
    icon_id: int = 2
    max_stacks: int = 3
    category: StatusCategory = 5
    lock_movement: bool = 8
    lock_action: bool = 10
    lock_control: bool = 11
    transfiguration: bool = 12
    can_dispel: bool = 14
    inflicted_by_actor: bool = 15
    is_permanent: bool = 16
    party_list_priority: int = 17
    amount: int = 21
    log: int = 24
    is_fc_buff: bool = 25
    invisibility: bool = 26
