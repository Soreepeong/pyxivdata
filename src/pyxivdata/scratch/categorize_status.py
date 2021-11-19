import re

from pyxivdata.common import GameLanguage
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.excel.rowdef import StatusRow


def __main__():
    damage_types = ("physical and magic", "physical", "magic")
    damage_type_pattern = "(|" + "|".join(f" {x}" for x in damage_types) + ")"

    aspects = ("unaspected", "water", "fire", "ice", "wind", "earth", "lightning")
    aspect_pattern = "(|" + "|".join(f" {x}" for x in aspects) + ")"

    damage_over_time_pattern = re.compile(
        fr"(?:(?:causing|sustaining){aspect_pattern} damage|bleeding hp) over time",
        re.IGNORECASE)
    heal_over_time_pattern = re.compile(r"regenerating hp over time", re.IGNORECASE)

    keywords = (
        "damage over time",

        "hp recovery via healing (magic|actions)"
        
        "attack magic potency",
        "healing magic potency",

        "(?:(physical and magic|physical|magic) )?(defense|damage dealt|damage taken)",

        "defense and magic defense"

        "critical hit rate",
        "direct hit rate",
        "evasion rate",

        "strength",
        "vitality",
        "dexterity",
        "intelligence",
        "mind",
        "parry",

        "blunt resistance",
        "slashing resistance",
        "piercing resistance",
    )
    pre_modifiers = (
        "increasing",
        "decreasing",
        "reducing",
    )
    post_modifiers = (
        "increased",
        "decreased",
        "reduced",
    )
    simple_verb = re.compile(r"is|are")
    with GameResourceReader(default_language=[GameLanguage.English]) as res:
        for row in res.excels['Status']:
            row: StatusRow
            if not row.icon:
                continue
            if damage_over_time_pattern.match(row.description.parsed):
                print(f"{row.name}: DoT")
            if heal_over_time_pattern.match(row.description.parsed):
                print(f"{row.name}: HoT")

    return 0


if __name__ == "__main__":
    exit(__main__())
