from pyxivdata.common import GameLanguage, GameInstallationRegion
from pyxivdata.escaped_string import SePayloadUnknown
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.excel.reader import ExdRow
from pyxivdata.resource.excel.structures import ExhDepth, ExhColumnDataType

LAST_I = 0
LAST_ROW_ID = 0


def __main__():
    with open("Z:/test.txt", "w") as fp:
        for language, installation_region in (
                # (GameLanguage.Japanese, GameInstallationRegion.Japan),
                (GameLanguage.English, GameInstallationRegion.Japan),
                (GameLanguage.German, GameInstallationRegion.Japan),
                (GameLanguage.French, GameInstallationRegion.Japan),
                (GameLanguage.ChineseSimplified, GameInstallationRegion.MainlandChina),
                (GameLanguage.Korean, GameInstallationRegion.SouthKorea),
        ):
            with GameResourceReader(installation=installation_region, default_language=[language]) as game:
                files = game["exd/root.exl"].data.decode("utf-8").splitlines()[1:]
                for i, name in enumerate(game.excels.names):
                    if i < LAST_I:
                        continue

                    name, *_ = name.split(",")
                    reader = game.excels[name]
                    if reader.header.depth != ExhDepth.Level2:
                        continue

                    print(f"\r[{i:>{len(str(len(files)))}}/{len(files)}] {language}: {name}...", end="")
                    try:
                        row: ExdRow
                        for row in reader:
                            if i == LAST_I and row.row_id < LAST_ROW_ID:
                                continue
                            for col_id, col in enumerate(row.columns):
                                if col.type != ExhColumnDataType.String:
                                    continue
                                val = row[col_id]
                                for x in val:
                                    if isinstance(x, SePayloadUnknown) and int(x.type) not in (0x1b, 0x1c):
                                        fp.write(
                                            f"{name}({i})[{row.row_id}:{col_id}] = {repr(val)}\n"
                                        )
                                        print(f"{name}({i})[{row.row_id}:{col_id}] = {repr(val)}\n")
                    except KeyError:
                        pass


if __name__ == "__main__":
    exit(__main__())