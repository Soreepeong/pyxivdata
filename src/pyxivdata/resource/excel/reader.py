import abc
import ctypes
import functools
import typing
from bisect import bisect_left

from pyxivdata.common import GameLanguage
from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.resource.excel.structures import ExhHeader, ExhColumnDefinition, ExhPageDefinition, ExdHeader, \
    ExdRowLocator, ExdRowHeader, ExhColumnDataType, ExhDepth

if typing.TYPE_CHECKING:
    from pyxivdata.sqpack.reader import SqpackReader
    from pyxivdata.installation.resource_reader import GameResourceReader

PossibleColumnType = typing.Union[SqEscapedString, bool, int, float]


def transform_column(col: ExhColumnDefinition, fixed_data: bytearray, variable_data: bytearray
                     ) -> PossibleColumnType:
    if col.type == ExhColumnDataType.String:
        string_offset = int.from_bytes(fixed_data[col.offset:col.offset + 4], "big", signed=False)
        return SqEscapedString(variable_data[string_offset:variable_data.index(0, string_offset)])
    elif col.type == ExhColumnDataType.Bool:
        return not not fixed_data[col.offset]
    elif col.type == ExhColumnDataType.Int8:
        return int.from_bytes(fixed_data[col.offset:col.offset + 1], "big", signed=True)
    elif col.type == ExhColumnDataType.UInt8:
        return fixed_data[col.offset]
    elif col.type == ExhColumnDataType.Int16:
        return int.from_bytes(fixed_data[col.offset:col.offset + 2], "big", signed=True)
    elif col.type == ExhColumnDataType.UInt16:
        return int.from_bytes(fixed_data[col.offset:col.offset + 2], "big", signed=True)
    elif col.type == ExhColumnDataType.Int32:
        return int.from_bytes(fixed_data[col.offset:col.offset + 4], "big", signed=True)
    elif col.type == ExhColumnDataType.UInt32:
        return int.from_bytes(fixed_data[col.offset:col.offset + 4], "big", signed=True)
    elif col.type == ExhColumnDataType.Float32:
        return int.from_bytes(fixed_data[col.offset:col.offset + 4], "big", signed=True)
    elif col.type == ExhColumnDataType.Int64:
        return int.from_bytes(fixed_data[col.offset:col.offset + 8], "big", signed=True)
    elif col.type == ExhColumnDataType.UInt64:
        return int.from_bytes(fixed_data[col.offset:col.offset + 8], "big", signed=True)
    elif ExhColumnDataType.PackedBool0 <= col.type <= ExhColumnDataType.PackedBool7:
        return bool(fixed_data[col.offset] & (1 << (col.type - ExhColumnDataType.PackedBool0)))
    raise AssertionError


class AbstractExdReader(abc.ABC):
    def __init__(self, data: bytearray, reader: 'ExcelReader', supported_depth: ExhDepth):
        if reader.header.depth != supported_depth:
            raise RuntimeError

        self._reader = reader
        self._data = data
        self._header = ExdHeader.from_buffer(data, 0)
        self._locators = (ExdRowLocator * (self._header.index_size // ctypes.sizeof(ExdRowLocator))
                          ).from_buffer(data, ctypes.sizeof(self._header))
        self._fixed_size = self._reader.header.fixed_data_size

    def get_ids(self) -> typing.List[int]:
        return [x.row_id for x in self._locators]

    def __getitem__(self, item: int) -> typing.Union[typing.List[PossibleColumnType],
                                                     typing.List[typing.List[PossibleColumnType]]]:
        i = bisect_left(self._locators, item, key=lambda x: x.row_id)
        if i == len(self._locators):
            raise KeyError

        locator = self._locators[i]
        if locator.row_id != item:
            raise KeyError

        return self._read_row(locator)

    def __iter__(self):
        def generator():
            for row in self._locators:
                yield row.row_id, self._read_row(row)

        return iter(generator())

    def _read_row(self, locator: ExdRowLocator) -> typing.Union[typing.List[PossibleColumnType],
                                                                typing.List[typing.List[PossibleColumnType]]]:
        raise NotImplementedError


class ExdReaderForDepth2(AbstractExdReader):
    def __init__(self, data: bytearray, reader: 'ExcelReader'):
        super().__init__(data, reader, ExhDepth.Level2)

    def __getitem__(self, item: int) -> typing.List[PossibleColumnType]:
        return super().__getitem__(item)

    def _read_row(self, locator: ExdRowLocator) -> typing.List[PossibleColumnType]:
        header = ExdRowHeader.from_buffer(self._data, locator.offset)
        data = self._data[locator.offset + ctypes.sizeof(header):][:header.data_size]
        return [transform_column(col, data[:self._fixed_size], data[self._fixed_size:])
                for col in self._reader.columns]


class ExdReaderForDepth3(AbstractExdReader):
    def __init__(self, data: bytearray, reader: 'ExcelReader'):
        super().__init__(data, reader, ExhDepth.Level3)

    def __getitem__(self, item: int) -> typing.List[typing.List[PossibleColumnType]]:
        return super().__getitem__(item)

    def _read_row(self, locator: ExdRowLocator) -> typing.List[typing.List[PossibleColumnType]]:
        header = ExdRowHeader.from_buffer(self._data, locator.offset)
        data = self._data[locator.offset + ctypes.sizeof(header):][:header.data_size]
        variable_data = data[header.sub_row_count * (2 + self._fixed_size):]
        rows = []
        for i in range(header.sub_row_count):
            fixed_data = data[i * (2 + self._fixed_size) + 2:][:self._fixed_size]
            rows.append([transform_column(col, fixed_data, variable_data)
                         for col in self._reader.columns])
        return rows


class ExcelReader:
    LANG_SUFFIX = {
        GameLanguage.Undefined: "",
        GameLanguage.Japanese: "_ja",
        GameLanguage.English: "_en",
        GameLanguage.German: "_de",
        GameLanguage.French: "_fr",
        GameLanguage.ChineseSimplified: "_chs",
        GameLanguage.ChineseTraditional: "_cht",
        GameLanguage.Korean: "_ko",
    }

    _columns: typing.Union[ctypes.Array[ExhColumnDefinition], typing.Sequence[ExhColumnDefinition]]
    _pages: typing.Union[ctypes.Array[ExhPageDefinition], typing.Sequence[ExhPageDefinition]]
    _default_languages: typing.List[GameLanguage] = [GameLanguage.Undefined]

    def __init__(self, reader: typing.Union['SqpackReader', 'GameResourceReader'], name: str,
                 default_language: typing.Union[GameLanguage, typing.Sequence[GameLanguage], None] = None):
        self._reader = reader
        self._name = name

        data = reader[f"exd/{name}.exh"]
        self._header = ExhHeader.from_buffer(data, 0)

        offset = ctypes.sizeof(self._header)
        self._columns = (ExhColumnDefinition * self._header.column_count).from_buffer(data, offset)

        offset += ctypes.sizeof(self._columns)
        self._pages = (ExhPageDefinition * self._header.page_count).from_buffer(data, offset)

        offset += ctypes.sizeof(self._pages)
        # noinspection PyTypeChecker
        self._languages: typing.Tuple[GameLanguage] = tuple(
            GameLanguage(int.from_bytes(data[offset + i * 2:offset + i * 2 + 2], "little"))
            for i in range(self._header.language_count)
        )

        if default_language is None:
            self._default_languages = list(GameLanguage)
        elif isinstance(default_language, GameLanguage):
            self._default_languages = [default_language]
        else:
            self._default_languages = list(default_language)

        self._exd: typing.Dict[typing.Tuple[int, GameLanguage], AbstractExdReader] = {}

    def set_default_languages(self, *language: GameLanguage) -> typing.NoReturn:
        self._default_languages = list(language)

    def _get_page(self, page: ExhPageDefinition, language: GameLanguage
                  ) -> AbstractExdReader:
        exd_key = page.start_id, language
        if exd_key not in self._exd:
            path = f"exd/{self._name}_{page.start_id}{ExcelReader.LANG_SUFFIX[language]}.exd"
            if self._header.depth == ExhDepth.Level2:
                self._exd[exd_key] = ExdReaderForDepth2(self._reader[path], self)
            elif self._header.depth == ExhDepth.Level3:
                self._exd[exd_key] = ExdReaderForDepth3(self._reader[path], self)
        return self._exd[exd_key]

    @property
    def languages(self) -> typing.Tuple[GameLanguage]:
        return self._languages

    @functools.cached_property
    def ids(self) -> typing.List[int]:
        ids = set()
        for page in self._pages:
            for language in self.languages:
                try:
                    ids.update(self._get_page(page, language).get_ids())
                except KeyError:
                    pass
        return sorted(ids)

    def __iter__(self):
        def generator():
            for page in self._pages:
                for language in self._default_languages:
                    try:
                        yield from self._get_page(page, language)
                        break
                    except KeyError:
                        continue
                else:
                    raise KeyError("No matching row found among the selected languages.")

        return iter(generator())

    def __getitem__(
            self,
            item: typing.Union[int, typing.Tuple[typing.Union[GameLanguage, typing.Sequence[GameLanguage]], int]]
    ) -> typing.Union[typing.List[PossibleColumnType], typing.List[typing.List[PossibleColumnType]]]:
        if isinstance(item, int):
            item = self._default_languages, item
        languages, row_id = item
        if isinstance(languages, GameLanguage):
            languages = [languages]

        i = bisect_left(self._pages, row_id + 1, key=lambda x: x.start_id + x.row_count_with_skip)
        if i == len(self._pages):
            raise KeyError

        page = self._pages[i]
        if not (page.start_id <= row_id < page.start_id + page.row_count_with_skip):
            raise KeyError

        if GameLanguage.Undefined in self.languages:
            languages = [GameLanguage.Undefined]

        for language in languages:
            try:
                return self._get_page(page, language)[row_id]
            except KeyError:
                continue
        else:
            raise KeyError

    @property
    def columns(self) -> typing.Tuple[ExhColumnDefinition]:
        return tuple(self._columns)

    @property
    def header(self) -> ExhHeader:
        return self._header
