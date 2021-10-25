import dataclasses
import os
import pathlib
import typing

from pyxivdata.common import GameInstallationRegion


@dataclasses.dataclass
class GameInstallation:
    region: GameInstallationRegion
    root_path: pathlib.Path
    version: str

    @classmethod
    def from_root_path(cls, path: typing.Union[str, os.PathLike]):
        path = pathlib.Path(path)
        while True:
            try:
                with open(path / "game" / "ffxivgame.ver", "r") as fp:
                    game_version = fp.read()
                    break
            except FileNotFoundError:
                pass
            if path.parent == path:
                raise FileNotFoundError
            path = path.parent

        if (path / "boot" / "ffxivboot64.exe").exists():
            region = GameInstallationRegion.Japan
        elif (path / "sdologinentry.dll").exists():
            region = GameInstallationRegion.MainlandChina
        elif (path / "boot" / "FFXIV_Boot.exe").exists():
            region = GameInstallationRegion.SouthKorea
        else:
            region = GameInstallationRegion.Unknown

        return GameInstallation(
            region=region,
            root_path=path,
            version=game_version,
        )

    @property
    def game_path(self) -> pathlib.Path:
        return self.root_path / "game"


class GameLocator:
    _game_installations: typing.List[GameInstallation]

    def __init__(self):
        if os.name == "nt":
            from pyxivdata.installation.game_locator_implementation.win32 import find_game_installations
            self._game_installations = find_game_installations()
        else:
            raise NotImplementedError

    def __len__(self):
        return len(self._game_installations)

    def __getitem__(self, item: typing.Union[int, GameInstallationRegion]) -> GameInstallation:
        if isinstance(item, int):
            return self._game_installations[item]

        elif isinstance(item, GameInstallationRegion):
            for x in self._game_installations:
                if x.region == item:
                    return x
            raise KeyError(f"Specified game region \"{item}\" not found.")

        else:
            raise TypeError

    def __iter__(self):
        return iter(self._game_installations)

    def __str__(self):
        return f"GameLocator({self._game_installations})"
