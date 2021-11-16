import functools
import importlib
import os
import pathlib
import typing

from pyxivdata.common import SqPathSpec, GameLanguage, GameInstallationRegion
from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.installation.game_locator import GameInstallation, GameLocator
from pyxivdata.resource.excel.rowdef import KNOWN_ROW_TYPES
from pyxivdata.resource.excel.rowdef.status import StatusRow
from pyxivdata.resource.excel.reader import ExcelReader, ExdRow
from pyxivdata.sqpack.reader import SqpackReader

SQPACK_CATEGORY_MAP = {
    "common": "000000",
    "bgcommon": "010000",
    "bg": "020000",
    "cut": "030000",
    "chara": "040000",
    "shader": "050000",
    "ui": "060000",
    "sound": "070000",
    "vfx": "080000",
    "exd": "0a0000",
    "game_script": "0b0000",
    "music": "0c0000",
}
EXPAC_DEPENDENT_SQPACKS = ("music", "bg", "cut")


class GameResourceReader:
    _default_languages: typing.List[GameLanguage] = [GameLanguage.Undefined]

    def __init__(self,
                 installation: typing.Union[GameInstallationRegion, GameInstallation, str, os.PathLike, None] = None,
                 default_language: typing.Union[GameLanguage, typing.Sequence[GameLanguage], None] = None):
        if installation is None:
            try:
                installation = GameLocator()[0]
            except KeyError:
                raise FileNotFoundError("Game installation not found")

        elif isinstance(installation, GameInstallationRegion):
            try:
                installation = GameLocator()[installation]
            except KeyError:
                raise FileNotFoundError("Game installation not found")

        elif isinstance(installation, GameInstallation):
            installation = installation

        elif isinstance(installation, (str, os.PathLike)):
            installation = GameInstallation.from_root_path(installation)

        else:
            raise TypeError

        self._game_path = installation.game_path
        self._readers: typing.Dict[pathlib.Path, SqpackReader] = {}
        self._open_all_attempted = False
        self._excel_readers: typing.Dict[str, ExcelReader] = {}

        if default_language is None:
            self._default_languages = list(self.excels["Action"].languages)
        elif isinstance(default_language, GameLanguage):
            self._default_languages = [default_language]
        else:
            self._default_languages = list(default_language)

    def __getitem__(self, item: typing.Union[SqPathSpec, str, bytes, os.PathLike]):
        item = SqPathSpec(item)
        if item.has_full_path():
            path_components = item.full_path.split("/")
            category = path_components[0]
            sqpack = SQPACK_CATEGORY_MAP[category]
            if sqpack in EXPAC_DEPENDENT_SQPACKS:
                expac = path_components[1]
            else:
                expac = "ffxiv"
            index_path = self._game_path / "sqpack" / expac / f"{sqpack}.win32.index"
            if index_path not in self._readers:
                self._readers[index_path] = SqpackReader(index_path)
            return self._readers[index_path][item]

        if not self._open_all_attempted:
            self._open_all_attempted = True
            for expac_path in (self._game_path / "sqpack").iterdir():
                if not expac_path.is_dir():
                    continue
                for path in expac_path.iterdir():
                    if not path.is_file():
                        continue
                    if not path.name.lower().endswith(".win32.index"):
                        continue
                    self._readers[path] = SqpackReader(path)

        for reader in self._readers:
            reader: SqpackReader
            try:
                return reader[item]
            except KeyError:
                continue

        raise KeyError(f"{item} not found in any sqpack file")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> typing.NoReturn:
        for f in self._readers.values():
            f.close()
        self._readers.clear()
        self._excel_readers.clear()

    def set_default_language(self, *language: GameLanguage) -> typing.NoReturn:
        self._default_languages = list(language)
        self.get_excel_row.cache_clear()
        for r in self._excel_readers.values():
            r.set_default_languages(*self._default_languages)

    @functools.cached_property
    def excels(self):
        name_to_id = dict(x.split(",", 1) for x in self["exd/root.exl"].decode("utf-8").splitlines()[1:])
        name_to_id = {x: int(y) for x, y in name_to_id.items()}
        id_to_name = {y: x for x, y in name_to_id.items() if y != -1}

        outer_self = self

        class _Impl:
            def __getitem__(self, item: typing.Union[str, int]):
                if isinstance(item, int):
                    item = id_to_name[item]
                elif not isinstance(item, str):
                    raise TypeError
                item = item.lower()
                if item not in outer_self._excel_readers:
                    outer_self._excel_readers[item] = ExcelReader(outer_self, item, outer_self._default_languages,
                                                                  KNOWN_ROW_TYPES.get(item, ExdRow))
                return outer_self._excel_readers[item]

            @property
            def name_to_id(self) -> typing.Dict[str, int]:
                return name_to_id

            @property
            def id_to_name(self) -> typing.Dict[int, str]:
                return id_to_name

            @property
            def names(self) -> typing.List[str]:
                return sorted(name_to_id.keys())

            @property
            def ids(self) -> typing.List[str]:
                return sorted(id_to_name.keys())

        return _Impl()

    @functools.cache
    def get_excel_row(
            self, excel_name: str, row_id: int, language: typing.Optional[GameLanguage] = None,
            row_type: typing.Type[ExdRow] = None
    ) -> typing.Optional[ExdRow]:
        reader = self.excels[excel_name]
        if GameLanguage.Undefined in reader.languages:
            language = GameLanguage.Undefined
        try:
            if language is not None:
                return reader[language, row_id]
            else:
                for language in self._default_languages:
                    if language in reader.languages:
                        try:
                            return reader[language, row_id]
                        except KeyError:
                            pass
        except KeyError:
            pass
        return None

    def get_status(self, status_effect_id: int, language: typing.Optional[GameLanguage] = None) -> StatusRow:
        return self.get_excel_row("Status", status_effect_id, language, StatusRow)

    def get_excel_string(self, excel_name: str, row_id: int, column_index: int,
                         language: typing.Optional[GameLanguage] = None,
                         fallback_format: typing.Optional[str] = None,
                         plural_column_index: typing.Optional[int] = None) -> SqEscapedString:
        res = self.get_excel_row(excel_name, row_id, language)
        if res is None:
            if fallback_format is None:
                raise
            return SqEscapedString(parsed=fallback_format.format(row_id), components=[])
        if plural_column_index is None or res[plural_column_index].escaped == b"":
            return res[column_index]
        return res[plural_column_index]

    def get_action_name(self, action_id: int, language: typing.Optional[GameLanguage] = None,
                        fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("Action", action_id, 0, language, fallback_format)

    def get_action_description(self, action_id: int, language: typing.Optional[GameLanguage] = None,
                               fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("ActionTransient", action_id, 0, language, fallback_format)

    def get_status_effect_name(self, status_effect_id: int, language: typing.Optional[GameLanguage] = None,
                               fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("Status", status_effect_id, 0, language, fallback_format)

    def get_status_effect_description(self, status_effect_id: int, language: typing.Optional[GameLanguage] = None,
                                      fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("Status", status_effect_id, 1, language, fallback_format)

    def get_bnpc_name(self, index: int, language: typing.Optional[GameLanguage] = None, plural: bool = False,
                      fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("BNpcName", index, 0, language, fallback_format, 2 if plural else None)

    def get_eobj_name(self, index: int, language: typing.Optional[GameLanguage] = None, plural: bool = False,
                      fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("EObjName", index, 0, language, fallback_format, 2 if plural else None)

    def get_companion_name(self, index: int, language: typing.Optional[GameLanguage] = None, plural: bool = False,
                           fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("Companion", index, 0, language, fallback_format, 2 if plural else None)

    def get_world_name(self, index: int, fallback_format: typing.Optional[str] = None) -> SqEscapedString:
        return self.get_excel_string("World", index, 0, GameLanguage.Undefined, fallback_format)

    def get_territory_name(self, territory_id: int, language: typing.Optional[GameLanguage] = None,
                           title_form: bool = True, fallback_format: typing.Optional[str] = None
                           ) -> SqEscapedString:
        territory = self.get_excel_row("TerritoryType", territory_id, GameLanguage.Undefined)
        if territory is None:
            if fallback_format is None:
                raise KeyError
            return SqEscapedString(parsed=fallback_format.format(territory_id), components=())
        placename_index = territory[5]
        return self.get_excel_string("PlaceName", placename_index, 0, language, fallback_format, 0 if title_form else 2)
