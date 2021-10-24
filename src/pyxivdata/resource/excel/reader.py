import abc
import ctypes
import typing
from bisect import bisect_left

from pyxivdata.common import GameLanguage
from pyxivdata.escaped_string import SqEscapedString
from pyxivdata.resource.excel.structures import ExhHeader, ExhColumnDefinition, ExhPageDefinition, ExdHeader, ExdRowLocator, \
    ExdRowHeader, ExhColumnDataType, ExhDepth
from pyxivdata.sqpack.reader import SqpackReader


def transform_column(col: ExhColumnDefinition, fixed_data: bytearray, variable_data: bytearray):
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
        self._locators = [
            ExdRowLocator.from_buffer(data, ctypes.sizeof(self._header) + i)
            for i in range(0, self._header.index_size, ctypes.sizeof(ExdRowLocator))
        ]
        self._fixed_size = self._reader.header.fixed_data_size

    def get_ids(self) -> typing.List[int]:
        return [x.row_id for x in self._locators]

    def __getitem__(self, item: int):
        i = bisect_left(self._locators, item, key=lambda x: x.row_id)
        if i == len(self._locators):
            return KeyError

        locator = self._locators[i]
        if locator.row_id != item:
            raise KeyError

        return self._read_row(locator)

    def __iter__(self):
        def generator():
            for row in self._locators:
                yield row.row_id, self._read_row(row)

        return iter(generator())

    def _read_row(self, locator: ExdRowLocator):
        raise NotImplementedError


class ExdReaderForDepth2(AbstractExdReader):
    def __init__(self, data: bytearray, reader: 'ExcelReader'):
        super().__init__(data, reader, ExhDepth.Level2)

    def _read_row(self, locator: ExdRowLocator):
        header = ExdRowHeader.from_buffer(self._data, locator.offset)
        data = self._data[locator.offset + ctypes.sizeof(header):][:header.data_size]
        return [transform_column(col, data[:self._fixed_size], data[self._fixed_size:])
                for col in self._reader.columns]


class ExdReaderForDepth3(AbstractExdReader):
    def __init__(self, data: bytearray, reader: 'ExcelReader'):
        super().__init__(data, reader, ExhDepth.Level3)

    def _read_row(self, locator: ExdRowLocator):
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

    def __init__(self, reader: 'SqpackReader', name: str,
                 default_language: typing.Union[GameLanguage, typing.Sequence[GameLanguage], None] = None):
        self._reader = reader
        self._name = name

        data = reader[f"exd/{name}.exh"]
        self._header = ExhHeader.from_buffer(data, 0)

        offset = ctypes.sizeof(self._header)
        self._columns = tuple(
            ExhColumnDefinition.from_buffer(data, offset + ctypes.sizeof(ExhColumnDefinition) * i)
            for i in range(self._header.column_count)
        )

        offset += len(self._columns) * ctypes.sizeof(ExhColumnDefinition)
        self._pages = tuple(
            ExhPageDefinition.from_buffer(data, offset + ctypes.sizeof(ExhPageDefinition) * i)
            for i in range(self._header.page_count)
        )

        offset += len(self._pages) * ctypes.sizeof(ExhPageDefinition)
        self._languages = tuple(
            GameLanguage(int.from_bytes(data[offset + i * 2:offset + i * 2 + 2], "little"))
            for i in range(self._header.language_count)
        )

        if default_language is None:
            default_language = list(GameLanguage)
        elif isinstance(default_language, GameLanguage):
            default_language = [default_language]
        for language in default_language:
            if language in self._languages:
                self._language = language
                break
        else:
            raise ValueError("Unsupported language")
        self._exd: typing.Dict[typing.Tuple[int, GameLanguage], AbstractExdReader] = {}

    def set_language(self, language: GameLanguage):
        if language not in self._languages:
            raise ValueError("Unsupported language")
        self._language = language

    def _get_page(self, page: ExhPageDefinition, language: GameLanguage):
        exd_key = page.start_id, language
        if exd_key not in self._exd:
            path = f"exd/{self._name}_{page.start_id}{ExcelReader.LANG_SUFFIX[language]}.exd"
            if self._header.depth == ExhDepth.Level2:
                self._exd[exd_key] = ExdReaderForDepth2(self._reader[path], self)
            elif self._header.depth == ExhDepth.Level3:
                self._exd[exd_key] = ExdReaderForDepth3(self._reader[path], self)
        return self._exd[exd_key]

    @property
    def languages(self):
        return self._languages

    def get_ids(self):
        ids = []
        for page in self._pages:
            ids.extend(self._get_page(page, self._language).get_ids())
        return ids

    def __iter__(self):
        def generator():
            for page in self._pages:
                yield from self._get_page(page, self._language)

        return iter(generator())

    def __getitem__(self, item: typing.Union[int, typing.Tuple[GameLanguage, int]]):
        if isinstance(item, int):
            item = self._language, item
        language, row_id = item

        i = bisect_left(self._pages, row_id + 1, key=lambda x: x.start_id + x.row_count_with_skip)
        if i == len(self._pages):
            raise KeyError

        page = self._pages[i]
        if not (page.start_id <= row_id < page.start_id + page.row_count_with_skip):
            raise KeyError

        return self._get_page(page, language)[row_id]

    @property
    def columns(self):
        return self._columns

    @property
    def header(self):
        return self._header
