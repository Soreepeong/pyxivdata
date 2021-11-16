from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.resource.excel.reader import ExcelReader
from pyxivdata.resource.excel.structures import ExhDepth
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.font.reader import FontReader


def __main__():
    with GameResourceReader() as game:
        print(game.get_status(2625))
        print(game.excels[209][4][1])
        print(game.get_action_name(4))
        print(game.get_status_effect_name(4))
        print(game.get_status_effect_description(4))
        print(game.get_bnpc_name(10254, plural=True))
        print(game.get_eobj_name(2000010, plural=True))
        print(game.get_companion_name(12, plural=True))
        print(game.get_world_name(2078))
        axis18 = FontReader(game["common/font/AXIS_18.fdt"])
        print(axis18["A"].char, axis18["V"].char, axis18["\uFFFE"].char, axis18["A", "V"])
        files = game["exd/root.exl"].decode("utf-8").splitlines()[1:]
        for i, name in enumerate(files):
            name, *_ = name.split(",")
            reader = ExcelReader(game, name)
            if reader.header.depth != ExhDepth.Level2:
                continue
            for language in reader.languages:
                print(f"[{i:>{len(str(len(files)))}}/{len(files)}] {name}: {language}...")
                reader.set_default_languages(language)
                try:
                    for row_id, row in reader:
                        for col in row:
                            if isinstance(col, SqEscapedString) and col.escaped:
                                print(col.parsed)
                except KeyError:
                    pass


if __name__ == "__main__":
    exit(__main__())
