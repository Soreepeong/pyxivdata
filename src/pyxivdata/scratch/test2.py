import csv
import typing

from pyxivdata.common import GameLanguage
from pyxivdata.escaped_string import SeString
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.excel.rowdef import ActionRow, StatusRow, ActionTransientRow


def __main__():
    for lang in [GameLanguage.Japanese]:
        with GameResourceReader(default_language=[lang]) as game, \
                open(fr"Z:\test_{lang.name}.csv", "w", newline="", encoding="utf-8-sig") as fp:
            writer = csv.writer(fp)

            action_transients: typing.Dict[int, ActionTransientRow] = dict(game.excels["ActionTransient"])
            for x in action_transients.values():
                new = bytes(SeString(str(x.description), *x.description))
                if bytes(x.description) != new:
                    raise AssertionError
                print(repr(x.description))

            actions: typing.Dict[int, ActionRow] = dict(game.excels["Action"])
            statuses: typing.Dict[int, StatusRow] = dict(game.excels["Status"])
            status_by_name = {str(v.name): k for k, v in statuses.items() if str(v.name) != ''}

            for action_id, action in actions.items():
                if action.status_gain_self:
                    status = statuses[action.status_gain_self]
                elif str(action.name) in status_by_name:
                    status = statuses[status_by_name[str(action.name)]]
                else:
                    continue

                action_transient = action_transients[action_id]
                writer.writerow([action, status, repr(action_transient.description), repr(status.description)])
                effects = repr(action_transient.description).split("追加効果")
                for effect_string in effects:
                    is_over_time = "一定時間" in effect_string
                    potency = None
                    if "威力：" in effect_string:
                        effect_string.split("威力：")[1]
                    pass


if __name__ == "__main__":
    exit(__main__())
