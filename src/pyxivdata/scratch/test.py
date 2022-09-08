import contextlib
import dataclasses
import enum
import json
import pathlib
import sqlite3
import typing

from pyxivdata.common import GameLanguage, GameInstallationRegion
from pyxivdata.installation.resource_reader import GameResourceReader
from pyxivdata.resource.excel.reader import ExdRow
from pyxivdata.resource.excel.structures import ExhDepth


class ConverterType(enum.Enum):
    # https://github.com/xivapi/SaintCoinach/tree/36e9d613f4bcc45b173959eed3f7b5549fd6f540/SaintCoinach/Ex/Relational/ValueConverters
    Color = "color"
    ComplexLink = "complexlink"
    Generic = "generic"
    Icon = "icon"
    Multiref = "multiref"  # polymorphic association
    Quad = "quad"
    Link = "link"
    Tomestone = "tomestone"


@dataclasses.dataclass
class Converter:
    _type_map: typing.ClassVar[typing.Dict[ConverterType, typing.Type['Converter']]] = {}

    type: ConverterType

    def __init_subclass__(cls, **kwargs):
        t = kwargs.pop("type", None)
        if t is not None:
            cls._type_map[t] = cls

    @classmethod
    def from_dict(cls, d: dict):
        t = ConverterType(d["type"])
        if cls is Converter:
            return cls._type_map[t].from_dict(d)
        else:
            return cls(t)


@dataclasses.dataclass
class ColorConverter(Converter, type=ConverterType.Color):
    pass


@dataclasses.dataclass
class ComplexLinkConverterLinkWhen:
    key: str
    value: int

    @classmethod
    def from_dict(cls, d: typing.Optional[dict]):
        if d is None:
            return None
        return cls(d["key"], d["value"])


@dataclasses.dataclass
class ComplexLinkConverterLink:
    when: typing.Optional[ComplexLinkConverterLinkWhen] = None
    sheet: typing.Optional[str] = None
    sheets: typing.Optional[typing.List[str]] = None

    @classmethod
    def from_dict(cls, d: typing.Optional[dict]):
        if d is None:
            return None
        return cls(ComplexLinkConverterLinkWhen.from_dict(d.get("when", None)), d.get("sheet", None),
                   d.get("sheets", None))


@dataclasses.dataclass
class ComplexLinkConverter(Converter, type=ConverterType.ComplexLink):
    links: typing.List[ComplexLinkConverterLink]

    @classmethod
    def from_dict(cls, d: typing.Optional[dict]):
        if d is None:
            return None
        return cls(ConverterType(d["type"]), [ComplexLinkConverterLink.from_dict(x) for x in d["links"]])


@dataclasses.dataclass
class GenericConverter(Converter, type=ConverterType.Generic):
    # converts to sheet itself from id?
    pass


@dataclasses.dataclass
class IconConverter(Converter, type=ConverterType.Icon):
    pass


@dataclasses.dataclass
class MultirefConverter(Converter, type=ConverterType.Multiref):
    targets: typing.List[str]

    @classmethod
    def from_dict(cls, d: typing.Optional[dict]):
        if d is None:
            return None
        return cls(ConverterType(d["type"]), d["targets"])


@dataclasses.dataclass
class QuadConverter(Converter, type=ConverterType.Quad):
    pass


@dataclasses.dataclass
class SheetLinkConverter(Converter, type=ConverterType.Link):
    target: str

    @classmethod
    def from_dict(cls, d: typing.Optional[dict]):
        if d is None:
            return None
        return cls(ConverterType(d["type"]), d["target"])


@dataclasses.dataclass
class TomestoneOrItemReferenceConverter(Converter, type=ConverterType.Tomestone):
    pass


class ColumnDefinitionType(enum.Enum):
    Column = "column"
    Repeat = "repeat"
    Group = "group"


@dataclasses.dataclass
class ColumnDefinition:
    index: int = 0
    name: typing.Optional[str] = None
    converter: typing.Optional[Converter] = None
    type: ColumnDefinitionType = ColumnDefinitionType.Column
    count: typing.Optional[int] = None
    definition: typing.Optional['ColumnDefinition'] = None  # for repeat
    members: typing.Optional[typing.List['ColumnDefinition']] = None  # for group

    @classmethod
    def from_dict(cls, d: typing.Optional[dict]):
        if d is None:
            return None
        res = ColumnDefinition(
            index=d.get("index", 0),
            name=d.get("name", None),
            type=ColumnDefinitionType(d.get("type", ColumnDefinitionType.Column)),
            count=d.get("count", None),
        )
        t = d.get("definition", None)
        if t is not None:
            res.definition = ColumnDefinition.from_dict(t)
        t = d.get("members", None)
        if t is not None:
            res.members = [ColumnDefinition.from_dict(x) for x in t]
        t = d.get("converter", None)
        if t is not None:
            res.converter = Converter.from_dict(t)
        return res

    @property
    def flat_names(self):
        cntr = self.index

        def next_cntr():
            nonlocal cntr
            cntr += 1
            return cntr - 1

        if self.type == ColumnDefinitionType.Column:
            return {next_cntr(): (self.name, (), ())}
        elif self.type == ColumnDefinitionType.Repeat:
            return {next_cntr(): (n, tuple((i, *indexer)), tuple((self.count, *counts)))
                    for i in range(self.count)
                    for n, indexer, counts in self.definition.flat_names.values()}
        elif self.type == ColumnDefinitionType.Group:
            return {next_cntr(): (n, tuple((i, *indexer)), tuple((len(self.members), *counts)))
                    for i, member in enumerate(self.members)
                    for n, indexer, counts in member.flat_names.values()}
        else:
            raise AssertionError


@dataclasses.dataclass
class Sheet:
    sheet: str
    definitions: typing.List[ColumnDefinition]
    default_column: typing.Optional[str] = None
    is_generic_reference_target: typing.Optional[bool] = False

    @classmethod
    def from_dict(cls, d: typing.Optional[dict]):
        if d is None:
            return None
        return cls(d["sheet"], [ColumnDefinition.from_dict(x) for x in d["definitions"]],
                   d.get("defaultColumn", None), d.get("isGenericReferenceTarget", None))

    def column_names(self):
        res = {}
        for x in self.definitions:
            res.update(x.flat_names)
        return res

    def flat_column_names(self):
        res = {}
        for x in self.definitions:
            res.update(x.flat_names)
        return res


def parse_sc_ex_def():
    p = pathlib.Path(r"Z:\GitWorks\SaintCoinach\SaintCoinach\Definitions")
    res = {}
    for d in p.iterdir():
        if d.suffix != ".json":
            continue
        with d.open("r", encoding="utf-8-sig") as fp:
            sheet = Sheet.from_dict(json.load(fp))
        res[sheet.sheet] = sheet
    return res


def __main__():
    s = parse_sc_ex_def()

    db: sqlite3.Connection
    cursor: sqlite3.Cursor
    with contextlib.closing(sqlite3.connect("Z:/ex2.db")) as db:
        for language, installation_region in (
                # (GameLanguage.Japanese, GameInstallationRegion.Japan),
                (GameLanguage.English, GameInstallationRegion.Japan),
                # (GameLanguage.German, GameInstallationRegion.Japan),
                # (GameLanguage.French, GameInstallationRegion.Japan),
                # (GameLanguage.ChineseSimplified, GameInstallationRegion.MainlandChina),
                # (GameLanguage.Korean, GameInstallationRegion.SouthKorea),
        ):
            with GameResourceReader(installation=installation_region, default_language=[language]) as game:
                files = game["exd/root.exl"].data.decode("utf-8").splitlines()[1:]
                for i, name in enumerate(game.excels.names):
                    print(f"\r[{i:>{len(str(len(files)))}}/{len(files)}] {language}: {name}...", end="")

                    name, *_ = name.split(",")
                    reader = game.excels[name]

                    is_language_neutral = GameLanguage.Undefined in reader.languages

                    row_header = {}

                    if '/' in name:
                        row_header["path"] = "TEXT DEFAULT ''"
                        table_name, table_path = name.split('/', 1)
                        table_name = f"kv_{table_name}"
                    else:
                        table_name = name
                        table_path = None

                    if reader.header.depth == ExhDepth.Level3:
                        row_header.update({"row_id": "INTEGER", "subrow_id": "INT"})
                    else:
                        row_header.update({"row_id": "INTEGER"})

                    if is_language_neutral:
                        reader.set_default_languages(GameLanguage.Undefined)
                    else:
                        row_header["lang_id"] = "INTEGER"

                    unique_set = set(row_header.keys())
                    if len(unique_set) == 1:
                        row_header["row_id"] = "INTEGER PRIMARY KEY AUTOINCREMENT"

                    col_names = {i: f"col_{i}" for i in range(len(reader.columns))}
                    if len(col_names) > 2000:
                        print("Skip")
                        continue
                    try:
                        col_names.update({i: (
                                f"{col_name.replace('}', '').replace('{', '').replace(']', '').replace('[', '_')}" +
                                "".join(f"_{j}" for j in path)
                        ) for i, (col_name, path, *_) in s[name].flat_column_names().items()})
                    except KeyError:
                        pass

                    def remap_cols(r):
                        if language == GameLanguage.ChineseSimplified and name == 'FATE':
                            return [*r[30:36], *r[6:30], *r[0:6], *r[36:]]
                        else:
                            return r

                    for col_index, col_name, col in zip(col_names.keys(), col_names.values(), reader.columns):
                        if col.type.is_bool:
                            row_header[col_name] = "BOOLEAN DEFAULT FALSE"
                        elif col.type.is_int:
                            row_header[col_name] = "INTEGER DEFAULT 0"
                        elif col.type.is_float:
                            row_header[col_name] = "REAL DEFAULT 0"
                        elif col.type.is_string:
                            row_header[col_name] = "TEXT DEFAULT ''"

                    with contextlib.closing(db.cursor()) as cursor:
                        cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS {table_name} (
                                {', '.join(f'"{k}" {v}' for k, v in row_header.items())},
                                UNIQUE ({', '.join(unique_set)})
                            )
                        """)
                        row: ExdRow
                        if reader.header.depth == ExhDepth.Level3:
                            cursor.executemany(f"""
                                INSERT OR REPLACE INTO {table_name} (
                                    {', '.join(f'"{k}"' for k in row_header.keys())}
                                ) VALUES (
                                    {', '.join('?' for _ in row_header.keys())}
                                )
                            """, [
                                [
                                    *([] if table_path is None else [table_path]),
                                    row.row_id,
                                    row.sub_row_id,
                                    *([] if is_language_neutral else [language.value]),
                                    *(
                                        col_value.xml_repr if col_info.type.is_string else col_value
                                        for col_info, col_value in zip(row.columns, remap_cols(row))
                                    )
                                ]
                                for rows in reader
                                for row in rows
                            ])
                        else:
                            cursor.executemany(f"""
                                INSERT OR REPLACE INTO {table_name} (
                                    {', '.join(f'"{k}"' for k in row_header.keys())}
                                ) VALUES (
                                    {', '.join('?' for _ in row_header.keys())}
                                )
                            """, [
                                [
                                    *([] if table_path is None else [table_path]),
                                    row.row_id,
                                    *([] if is_language_neutral else [language.value]),
                                    *(
                                        col_value.xml_repr if col_info.type.is_string else col_value
                                        for col_info, col_value in zip(row.columns, remap_cols(row))
                                    )
                                ]
                                for row in reader
                            ])
                        db.commit()


if __name__ == "__main__":
    exit(__main__())
