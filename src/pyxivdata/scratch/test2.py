from pyxivdata.common import SqPathSpec, GameLanguage, GameInstallationRegion
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.sound.structures import ScdHeader, ScdDataOffsets


def __main__():
    with GameResourceReader(installation=GameInstallationRegion.SouthKorea, default_language=GameLanguage.Korean) as game:
        print(game.get_excel_string("LogMessage", 409, 4).xml_repr)
    pass


if __name__ == "__main__":
    exit(__main__())
