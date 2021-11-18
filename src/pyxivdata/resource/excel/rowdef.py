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
    class_or_job: int = 12
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
    recast_100ms: int = 38
    cooldown_group: int = 39
    additional_cooldown_group: int = 40
    max_charges: int = 41
    attack_type: AttackType = 42
    aspect: int = 43
    action_proc_status: int = 44
    status_gain_self: int = 46
    class_or_job_category: int = 48
    affects_position: int = 51
    omen: int = 52
    is_pvp: bool = 53
    is_player_action: bool = 65


class ActionCategoryRow(ExdRow):
    name: SeString = 0


class ActionTransientRow(ExdRow):
    description: SeString = 0


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
