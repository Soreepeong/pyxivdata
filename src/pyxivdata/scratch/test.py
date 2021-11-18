from pyxivdata.common import GameLanguage
from pyxivdata.escaped_string import SePayloadUnknown
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.excel.reader import ExcelReader, ExdRow
from pyxivdata.resource.excel.structures import ExhDepth, ExhColumnDataType
from pyxivdata.resource.font.reader import FontReader


LAST_I = 24
LAST_ROW_ID = 17


def __main__():
    langlist = [GameLanguage.English, GameLanguage.ChineseSimplified, GameLanguage.Korean]
    with GameResourceReader(default_language=langlist) as game:
        # print(game["chara/monster/m0489/animation/a0001/bt_common/loop_sp/"][0])
        # print(game.get_status(2625))
        # print(game.excels[209][4][1])
        # print(game.get_action_name(4))
        # print(game.get_status_effect_name(4))
        # print(game.get_status_effect_description(4))
        # print(game.get_bnpc_name(10254, plural=True))
        # print(game.get_eobj_name(2000010, plural=True))
        # print(game.get_companion_name(12, plural=True))
        # print(game.get_world_name(2078))
        # axis18 = FontReader(game["common/font/AXIS_18.fdt"].data)
        # print(axis18["A"].char, axis18["V"].char, axis18["\uFFFE"].char, axis18["A", "V"])
        files = game["exd/root.exl"].data.decode("utf-8").splitlines()[1:]
        for i, name in enumerate(files):
            if i < LAST_I:
                continue

            name, *_ = name.split(",")
            reader = ExcelReader(game, name, default_language=langlist)
            if reader.header.depth != ExhDepth.Level2:
                continue

            print(f"[{i:>{len(str(len(files)))}}/{len(files)}] {name}...")
            try:
                for row_id, row in reader:
                    if i == LAST_I and row_id < LAST_ROW_ID:
                        continue
                    row: ExdRow
                    for col_id, col in enumerate(row.columns):
                        if col.type != ExhColumnDataType.String:
                            continue
                        val = row[col_id]
                        if len(val):
                            print(i, row_id, repr(val))
                            if any(type(x) is SePayloadUnknown for x in val):
                                exit(0)
            except KeyError:
                pass


if __name__ == "__main__":
    exit(__main__())
