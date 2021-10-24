from pyxivdata.common import GameLanguage
from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.resource.excel.reader import ExcelReader
from pyxivdata.resource.excel.structures import ExhDepth
from pyxivdata.sqpack.game_reader import GameReader


def __main__():
    with GameReader(
            r"C:\Program Files (x86)\SquareEnix\FINAL FANTASY XIV - A Realm Reborn\game",
            # r"C:\Program Files (x86)\FINAL FANTASY XIV - KOREA\game",
            default_language=[
                GameLanguage.English,
                GameLanguage.ChineseSimplified,
                GameLanguage.Korean,
            ]
    ) as game:
        print(game.excels[209][4][1])
        print(game.get_action_name(4))
        print(game.get_status_effect_name(4))
        print(game.get_status_effect_description(4))
        print(game.get_bnpc_name(10254, plural=True))
        print(game.get_eobj_name(2000010, plural=True))
        print(game.get_companion_name(12, plural=True))
        print(game.get_world_name(2078))
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
