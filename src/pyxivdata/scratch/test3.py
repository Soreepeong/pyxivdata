import dataclasses
import typing

from pyxivdata.common import GameLanguage
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.excel.rowdef import ActionRow


@dataclasses.dataclass
class Action:
    name: str
    potency: int
    charges: int = 1
    cooldown: int = 0  # use GCD
    animation_lock: int = 600
    cast: int = 0
    cooldown_groups: typing.Set[int] = dataclasses.field(default_factory=set)
    gauge_required: int = 0
    gauge_delta: int = 0
    buff_required: typing.Set[int] = dataclasses.field(default_factory=set)
    buff_nonexist: typing.Set[int] = dataclasses.field(default_factory=set)
    buff_given: typing.Set[int] = dataclasses.field(default_factory=set)
    buff_taken: typing.Set[int] = dataclasses.field(default_factory=set)


@dataclasses.dataclass
class Status:
    name: str
    duration: int
    max_stacks: int = 0
    damage_up: int = 0


def __main__():
    with GameResourceReader(default_language=[GameLanguage.English]) as game:
        # class_job_category = {
        #     x.row_id
        #     for x in game.excels["ClassJobCategory"]
        #     if x[30] or x[31]  # ROG, NIN
        # }
        # actions: typing.Dict[int, ActionRow] = {
        #     x.row_id: x
        #     for x in game.excels["Action"]
        #     if (x.class_job_category in class_job_category
        #         and x.is_player_action
        #         and not x.is_pvp
        #         and (x.targets_self or x.targets_hostile))
        # }
        action_ids = {2240, 2241, 2242, 2245, 2246, 2247, 2248, 2254, 2255, 2258, 2259, 2260, 2261, 2263, 2264, 3563,
                      3566, 7401, 7402, 7403, 7541, 7542, 7546, 7548, 7549, 7863, 16488, 16489, 16493, 25774, 25777,
                      25778, 25876, 16492,
                      2267,  # Raiton
                      18881,  # TCJ Suiton
                      }
        actions: typing.Dict[int, Action] = {}
        for action_id in action_ids:
            action: ActionRow = game.excels["Action"][action_id]
            actions[action_id] = Action(
                name=str(action.name),
                potency=0,
                charges=action.max_charges,
                cooldown=action.recast_100ms * 100,
                animation_lock=600,
                cooldown_groups={x for x in (action.cooldown_group, action.additional_cooldown_group) if x != 0},
                gauge_required=action.primary_cost_value if action.primary_cost_type == 27 else 0,
                gauge_delta=-action.primary_cost_value if action.primary_cost_type == 27 else 0,
                buff_required={y for x, y in ((action.primary_cost_type, action.primary_cost_value),
                                              (action.secondary_cost_type, action.secondary_cost_value))
                               if x in (32, 35)},
                buff_nonexist={1186, *{y for x, y in ((action.primary_cost_type, action.primary_cost_value),
                                                      (action.secondary_cost_type, action.secondary_cost_value))
                                       if x == 46}},
                buff_taken={y for x, y in ((action.primary_cost_type, action.primary_cost_value),
                                           (action.secondary_cost_type, action.secondary_cost_value))
                            if x in (35,)},
            )
        del actions[25778]  # Fleeting Raiju
        del actions[25876]  # Huraijin
        del actions[7863]  # Leg Sweep
        del actions[2241]  # Shade Shift
        del actions[2245]  # Hide
        del actions[2246]  # Assassinate
        del actions[2247]  # Throwing Dagger
        del actions[2254]  # Death Blossom
        del actions[2259], actions[2260], actions[2261], actions[2263]  # Ten, Ninjutsu, Chi, Jin
        del actions[16488]  # Hakke Mujinsatsu
        del actions[7401]  # Hellfrog Medium
        del actions[3563]  # Armor Crush
        del actions[7541]  # Second Wind
        del actions[7542]  # Bloodbath
        del actions[7546]  # True North
        del actions[7548]  # Arm's Length
        del actions[7549]  # Feint

        actions[2240] = dataclasses.replace(actions[2240], potency=200, gauge_delta=5)  # Spinning Edge
        actions[-103] = dataclasses.replace(actions[2240], name="Spinning Edge(Bunshin)", potency=360, gauge_delta=10)

        actions[2242] = dataclasses.replace(actions[2242], potency=300, gauge_delta=5)  # Gust Slash
        actions[-104] = dataclasses.replace(actions[2242], name="Gust Slash(Bunshin)", potency=460, gauge_delta=10)

        actions[2248].gauge_delta = 40  # Mug

        actions[2258].potency = 400
        actions[2258].buff_given.add(64)  # Trick Attack

        actions[2255] = dataclasses.replace(actions[2255], potency=400, gauge_delta=15)  # Aeolian Edge
        actions[-105] = dataclasses.replace(actions[2255], name="Aeolian Edge(Bunshin)", potency=560, gauge_delta=20)

        actions[2264].buff_given.add(497)  # Kassatsu

        actions[3566].potency = 150 * 3  # Dream Within A Dream

        actions[7402].potency = 400  # Bhavacakra
        actions[-101] = dataclasses.replace(actions[7402], name="Bhavacakra(Meisui)", potency=500)

        actions[16489].buff_required.add(507)  # Meisui
        actions[16489].buff_taken.add(507)
        actions[16489].buff_given.add(2689)
        actions[16489].gauge_delta = 50

        actions[16492].buff_required.add(497)  # Hyosho Ranryu
        actions[16492].buff_taken.add(497)

        actions[2267].buff_nonexist.add(497)
        actions[2267].cast = 500  # Raiton

        actions[18881].name = "TCJ F+R+S"  # TCJ Fuma+Raiton+Suiton
        actions[18881].cast = 2000

        actions[-102] = dataclasses.replace(actions[25777], name="Forked Raiju(Bunshin)", potency=720, gauge_delta=10)

        actions[25774].gauge_delta = 10  # Phantom Kamaitachi

        actions[25777].gauge_delta = 5  # Forked Raiju

        statuses = {
            64: Status("Vulnerability Up", 15, damage_up=5),
            2689: Status("Meisui", 30),
            507: Status("Suiton", 20),
            497: Status("Kassatsu", 15, damage_up=30),
            2723: Status("Phantom Kamaitachi Ready", 45),
            2690: Status("Raiju Ready", 30, max_stacks=3),
        }
        pass


if __name__ == "__main__":
    exit(__main__())
