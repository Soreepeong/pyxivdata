from pyxivdata.common import GameLanguage
from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.resource.excel.reader import ExcelReader
from pyxivdata.resource.excel.structures import ExhDepth
from pyxivdata.sqpack.reader import SqpackReader


def __main__():
    with SqpackReader(
            r"C:\Program Files (x86)\SquareEnix\FINAL FANTASY XIV - A Realm Reborn\game\sqpack\ffxiv\0a0000.win32.index"
            # r"C:\Program Files (x86)\FINAL FANTASY XIV - KOREA\game\sqpack\ffxiv\0a0000.win32.index"
    ) as sqpack:
        files = sqpack["exd/root.exl"].decode("utf-8").splitlines()[1:]
        for i, name in enumerate(files):
            name, *_ = name.split(",")
            reader = ExcelReader(sqpack, name)
            if reader.header.depth != ExhDepth.Level2:
                continue
            for language in reader.languages:
                # if language != GameLanguage.English: continue
                print(f"[{i:>{len(str(len(files)))}}/{len(files)}] {name}: {language}...")
                reader.set_language(language)
                try:
                    for row_id, row in reader:
                        for col in row:
                            if isinstance(col, SqEscapedString) and col.escaped:
                                esc = SqEscapedString(parsed=col.parsed, components=col.components).escaped
                                if esc != col.escaped:
                                    breakpoint()
                                    print(SqEscapedString(parsed=col.parsed, components=col.components).escaped)
                                # print(str(col))
                except KeyError:
                    pass


if __name__ == "__main__":
    exit(__main__())
