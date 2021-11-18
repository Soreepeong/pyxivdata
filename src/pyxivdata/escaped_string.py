import ctypes
import enum
import functools
import html
import typing

if typing.TYPE_CHECKING:
    from pyxivdata.resource.excel.rowdef import ExdRow, CompletionRow, MapRow
    from pyxivdata.resource.excel.reader import ExcelReader

SHEET_READER = typing.Callable[[typing.Union[int, str]], 'ExcelReader']


class SeExpressionType(enum.IntEnum):
    # https://github.com/xivapi/SaintCoinach/blob/36e9d613f4bcc45b173959eed3f7b5549fd6f540/SaintCoinach/Text/DecodeExpressionType.cs

    # Predefined parameters
    Xd0 = 0xd0
    Xd1 = 0xd1
    Xd2 = 0xd2
    Xd3 = 0xd3
    Xd4 = 0xd4
    Xd5 = 0xd5
    Xd6 = 0xd6
    Xd7 = 0xd7
    Xd8 = 0xd8
    Xd9 = 0xd9
    Xda = 0xda
    Hour = 0xdb  # 0 ~ 23
    Xdc = 0xdc
    Weekday = 0xdd  # 1(sunday) ~ 7(saturday)
    Xde = 0xde
    Xdf = 0xdf

    # Binary expressions
    GreaterThanOrEqualTo = 0xe0
    GreaterThan = 0xe1
    LessThanOrEqualTo = 0xe2
    LessThan = 0xe3
    Equal = 0xe4
    NotEqual = 0xe5
    # Xe6 = 0xe6
    # Xe7 = 0xe7

    # Unary expressions
    IntegerParameter = 0xe8
    PlayerParameter = 0xe9
    StringParameter = 0xea
    ObjectParameter = 0xeb

    # Alone - what is this?
    Xec = 0xec
    # Xed = 0xed
    # Xee = 0xee
    # Xef = 0xef

    SeString = 0xff  # Followed by length (including length) and data


class SePayloadType(enum.IntEnum):
    Empty = 0x00
    ResetTime = 0x06
    Time = 0x07
    If = 0x08
    Switch = 0x09
    ActorFullName = 0x0a  # probably
    IfEquals = 0x0c
    IfEndsWithJongseong = 0x0d  # 은/는(eun/neun), 이/가(i/ga), or 을/를(Eul/Reul)
    IfEndsWithJongseongExceptRieul = 0x0e  # 로/으로(Ro/Euro)
    IfPlayer = 0x0f  # "You are"/"Someone Else is"
    NewLine = 0x10
    BitmapFontIcon = 0x12
    ColorFill = 0x13
    ColorBorder = 0x14
    DialoguePageSeparator = 0x17  # probably
    Italics = 0x1a
    Indent = 0x1d
    Icon2 = 0x1e
    Hyphen = 0x1f
    Value = 0x20
    Format = 0x22
    TwoDigitValue = 0x24  # f"{:02}"
    SheetReference = 0x28
    Highlight = 0x29
    Link = 0x2b
    Split = 0x2c
    Placeholder = 0x2e
    SheetReferenceJa = 0x30
    SheetReferenceEn = 0x31
    SheetReferenceDe = 0x32
    SheetReferenceFr = 0x33
    InstanceContent = 0x40
    UiColorFill = 0x48
    UiColorBorder = 0x49
    ZeroPaddedValue = 0x50
    OrdinalValue = 0x51  # "1st", "2nd", "3rd", ...

    X19 = 0x19  # Part of name?
    X1b = 0x1b  # Used in QuickChatTransient
    X1c = 0x1c  # Used in QuickChatTransient

    X16 = 0x16
    X26 = 0x26
    X2d = 0x2d
    X2f = 0x2f
    X60 = 0x60
    X61 = 0x61

    def __str__(self):
        return f"{self.name}({self.value:02x})"


class SeExpression:
    _buffer: typing.Optional[bytes] = None
    _sheet_reader: typing.Optional[SHEET_READER] = None

    def __init__(self, sheet_reader: typing.Optional[SHEET_READER] = None):
        self._sheet_reader = sheet_reader

    def __bytes__(self):
        return self._buffer

    def __int__(self):
        raise TypeError

    @classmethod
    def from_value(cls, value: typing.Union[int, str, 'SeExpression']):
        if isinstance(value, SeExpression):
            return value
        elif isinstance(value, int):
            return SeExpressionUint32(value)
        elif isinstance(value, str):
            return SeExpressionSeString(SeString(value))
        elif isinstance(value, SeString):
            return SeExpressionSeString(value)
        raise TypeError(f"Value {value} of type {type(value)} is not implicitly convertible to a SeExpression.")

    @staticmethod
    def from_buffer_copy(data: typing.Union[bytes, bytearray, memoryview], offset: int = 0,
                         sheet_reader: typing.Optional[SHEET_READER] = None):
        begin = offset
        marker = data[offset]
        offset += 1
        if marker < 0xD0:
            value = marker - 1
            self = SeExpressionUint32(value)

        elif 0xD0 <= marker <= 0xDF:
            self = SeExpressionPredefinedParameter(SeExpressionType(marker), sheet_reader)

        elif 0xE0 <= marker <= 0xE5:
            operand1 = SeExpression.from_buffer_copy(data, offset, sheet_reader)
            offset += len(bytes(operand1))
            operand2 = SeExpression.from_buffer_copy(data, offset, sheet_reader)
            offset += len(bytes(operand2))
            self = SeExpressionBinary(SeExpressionType(marker), operand1, operand2, sheet_reader)

        elif 0xE8 <= marker <= 0xEB:
            operand = SeExpression.from_buffer_copy(data, offset, sheet_reader)
            offset += len(bytes(operand))
            self = SeExpressionUnary(SeExpressionType(marker), operand, sheet_reader)

        elif 0xEC <= marker <= 0xEC:
            self = SeExpressionPredefinedParameter(SeExpressionType(marker), sheet_reader)  # TODO: what is this?

        elif 0xF0 <= marker <= 0xFE:
            marker = (marker + 1) & 0xF
            res = 0
            for i in reversed(range(4)):
                res <<= 8
                if marker & (1 << i):
                    res |= data[offset]
                    offset += 1

            value = res

            self = SeExpressionUint32(value)

        elif marker == SeExpressionType.SeString:
            se_string_len = SeExpression.from_buffer_copy(data, offset, sheet_reader)
            offset += len(bytes(se_string_len))
            se_string = SeString(data[offset:offset + se_string_len], sheet_reader=sheet_reader)
            offset += len(bytes(se_string))
            self = SeExpressionSeString(se_string, sheet_reader)

        else:
            raise ValueError(f"Marker 0x{marker:02x} is not a valid SeUint32.")
        self._buffer = data[begin:offset]
        return self


class SeExpressionSeString(SeExpression):
    def __init__(self, data: 'SeString', sheet_reader: typing.Optional[SHEET_READER] = None):
        super().__init__(sheet_reader)
        self._data = data

    def __bytes__(self):
        if self._buffer is not None:
            return self._buffer

        self._buffer = bytes((SeExpressionType.SeString,)) + bytes(self._data)
        return self._buffer

    def __repr__(self):
        return repr(self._data)


class SeExpressionPredefinedParameter(SeExpression):
    def __init__(self, expression_type: SeExpressionType, sheet_reader: typing.Optional[SHEET_READER] = None):
        super().__init__(sheet_reader)
        self._type = expression_type

    @property
    def type(self):
        return self._type

    def __bytes__(self):
        if self._buffer is not None:
            return self._buffer

        self._buffer = bytes((self._type.value,))
        return self._buffer

    def __repr__(self):
        return f"({self._type.name})"


class SeExpressionPlayerParameters(enum.IntEnum):
    # https://github.com/xivapi/SaintCoinach/blob/36e9d613f4bcc45b173959eed3f7b5549fd6f540/SaintCoinach/Text/Parameters/PlayerParameters.cs
    ActiveClassOrJobIndex = 68
    LevelIndex1 = 69
    LevelIndex2 = 72
    GamePadTypeIndex = 75
    RegionIndex = 77


class SeExpressionUnary(SeExpression):
    def __init__(self, expression_type: SeExpressionType, operand: SeExpression,
                 sheet_reader: typing.Optional[SHEET_READER] = None):
        super().__init__(sheet_reader)
        self._type = expression_type
        self._operand = operand

    @property
    def type(self):
        return self._type

    @property
    def operand(self):
        return self._operand

    def __bytes__(self):
        if self._buffer is not None:
            return self._buffer

        self._buffer = bytes((self._type.value,)) + bytes(self._operand)
        return self._buffer

    def __repr__(self):
        if self._type == SeExpressionType.PlayerParameter:
            try:
                return SeExpressionPlayerParameters(int(self._operand)).name
            except (TypeError, ValueError):
                pass
        return f"({self._type.name}={self._operand})"


class SeExpressionBinary(SeExpression):
    def __init__(self, expression_type: SeExpressionType, operand1: SeExpression, operand2: SeExpression,
                 sheet_reader: typing.Optional[SHEET_READER] = None):
        super().__init__(sheet_reader)
        self._type = expression_type
        self._operand1 = operand1
        self._operand2 = operand2

    @property
    def type(self):
        return self._type

    def __bytes__(self):
        if self._buffer is not None:
            return self._buffer

        self._buffer = bytes((self._type.value,)) + bytes(self._operand1) + bytes(self._operand2)
        return self._buffer

    def __repr__(self):
        if self._type == SeExpressionType.GreaterThanOrEqualTo:
            op = ">="
        elif self._type == SeExpressionType.GreaterThan:
            op = ">"
        elif self._type == SeExpressionType.LessThanOrEqualTo:
            op = "<="
        elif self._type == SeExpressionType.LessThan:
            op = "<"
        elif self._type == SeExpressionType.Equal:
            op = "=="
        elif self._type == SeExpressionType.NotEqual:
            op = "!="
        else:
            op = self._type.name
        return f"({self._operand1}) {op} ({self._operand2})"


class SeExpressionUint32(int, SeExpression):
    def __new__(cls, data: int):
        return super(SeExpressionUint32, cls).__new__(cls, int(data))

    def __bytes__(self):
        if self._buffer is not None:
            return self._buffer

        if self < 0xCF:
            self._buffer = bytes((self + 1,))
        else:
            res = bytearray()
            res.append(0)
            for i in reversed(range(4)):
                b = (self >> (8 * i)) & 0xFF
                if b:
                    res.append(b)
                    res[0] |= 1 << i
            res[0] = (res[0] | 0xF0) - 1
            self._buffer = bytes(res)
        return self._buffer


class SePayload:
    _implemented_payload_types: typing.ClassVar[typing.Dict[SePayloadType, typing.Type['SePayload']]] = {}

    PAYLOAD_TYPE: typing.ClassVar[typing.Optional[SePayloadType]] = None
    MIN_EXPRESSION_COUNT: typing.ClassVar[typing.Optional[int]] = None
    MAX_EXPRESSION_COUNT: typing.ClassVar[typing.Optional[int]] = None

    _buffer: bytes
    _sheet_reader: typing.Optional[SHEET_READER]

    def __init_subclass__(cls,
                          payload_type: typing.Optional[SePayloadType] = None,
                          count: typing.Tuple[typing.Optional[int], typing.Optional[int]] = (None, None),
                          **kwargs):
        cls.PAYLOAD_TYPE = payload_type
        cls.MIN_EXPRESSION_COUNT, cls.MAX_EXPRESSION_COUNT = count
        if payload_type is not None:
            cls._implemented_payload_types[payload_type] = cls

    @classmethod
    def _validate_expression_count_or_throw(cls, count):
        if cls.MIN_EXPRESSION_COUNT is not None and count < cls.MIN_EXPRESSION_COUNT:
            raise ValueError(f"{cls.__name__}: Too few expressions({count} < {cls.MIN_EXPRESSION_COUNT})")
        if cls.MAX_EXPRESSION_COUNT is not None and count > cls.MAX_EXPRESSION_COUNT:
            raise ValueError(f"{cls.__name__}: Too many expressions({count} > {cls.MAX_EXPRESSION_COUNT})")

    @classmethod
    def from_bytes(cls, data: typing.Union[bytearray, bytes, memoryview],
                   payload_type: typing.Optional[typing.Union[int, SePayloadType]] = None,
                   sheet_reader: typing.Optional[SHEET_READER] = None):
        if payload_type is None:
            payload_type = cls.type
        try:
            payload_type = SePayloadType(payload_type)
        except ValueError:
            pass
        t = cls._implemented_payload_types.get(payload_type, None)
        if t is None:
            self = SePayloadUnknown(data, sheet_reader=sheet_reader)
            self._payload_type = payload_type
        else:
            self = t(data, sheet_reader=sheet_reader)
        return self

    @classmethod
    def from_values(cls, *values: typing.Union[int, str, SeExpression],
                    payload_type: typing.Optional[typing.Union[int, SePayloadType]] = None):
        cls._validate_expression_count_or_throw(len(values))
        return SePayload.from_bytes(b"".join(bytes(SeExpression.from_value(v)) for v in values), payload_type)

    def __new__(cls, data: typing.Union[bytearray, bytes, memoryview] = b"",
                sheet_reader: typing.Optional[SHEET_READER] = None):
        self = super().__new__(cls)
        self._buffer = bytes(data)
        self._sheet_reader = sheet_reader
        return self

    def set_sheet_reader(self, reader: SHEET_READER):
        self._sheet_reader = reader

    @functools.cached_property
    def expressions(self):
        offset = 0
        res = []
        while offset < len(self._buffer):
            res.append(SeExpression.from_buffer_copy(self._buffer, offset))
            offset += len(bytes(res[-1]))
        self._validate_expression_count_or_throw(len(res))
        return tuple(res)

    @property
    def _repr_expression_names(self):
        return "param",

    @property
    def type(self) -> int:
        return self.PAYLOAD_TYPE

    def __bytes__(self):
        return self._buffer

    def _repr_extra(self) -> typing.Optional[str]:
        return None

    def __repr__(self):
        type_name = self.type
        if isinstance(type_name, SePayloadType):
            type_name = type_name.value
        else:
            type_name = f"X{type_name:02x}"
        if not self.expressions:
            return f"<SePayload type=\"{type_name}\" />"

        extra = self._repr_extra()
        if extra is not None:
            res = [f"<SePayload type=\"{type_name}\" representation=\"{html.escape(str(extra))}\">"]
        else:
            res = [f"<SePayload type=\"{type_name}\">"]
        names = self._repr_expression_names
        if (len(self.expressions) == self.MIN_EXPRESSION_COUNT
                and self.MIN_EXPRESSION_COUNT == self.MAX_EXPRESSION_COUNT):
            for name, v in zip(names, self.expressions):
                res.append(f"""<{name}>{repr(v)}</{name}>""")
        else:
            for i, v in enumerate(self.expressions):
                if i < len(names) - 1:
                    res.append(f"""<{names[i]}>{repr(v)}</{names[i]}>""")
                else:
                    res.append(f"""<{names[-1]} index="{2 + i - len(names)}">{repr(v)}</{names[-1]}>""")
        res.append(f"</SePayload>")
        return "".join(res)


class SePayloadUnknown(SePayload):
    _payload_type: SePayloadType

    @property
    def type(self):
        return self._payload_type


class SePayloadNewLine(SePayload, payload_type=SePayloadType.NewLine, count=(0, 0)):
    pass


class SePayloadHyphen(SePayload, payload_type=SePayloadType.Hyphen, count=(0, 0)):
    pass


class SePayloadIndent(SePayload, payload_type=SePayloadType.Indent, count=(0, 0)):
    pass


class SePayloadUiColorBorder(SePayload, payload_type=SePayloadType.UiColorBorder, count=(1, 1)):
    pass


class SePayloadUiColorFill(SePayload, payload_type=SePayloadType.UiColorFill, count=(1, 1)):
    pass


class SePayloadHighlight(SePayload, payload_type=SePayloadType.Highlight, count=(1, 1)):
    pass


class SePayloadTwoDigitValue(SePayload, payload_type=SePayloadType.TwoDigitValue, count=(1, 1)):
    pass


class SePayloadValue(SePayload, payload_type=SePayloadType.Value, count=(1, 1)):
    pass


class SePayloadZeroPaddedValue(SePayload, payload_type=SePayloadType.ZeroPaddedValue, count=(2, 2)):
    @property
    def value(self):
        return self.expressions[0]

    @property
    def pad(self):
        return self.expressions[1]

    @property
    def _repr_expression_names(self):
        return "value", "pad"


class SePayloadTime(SePayload, payload_type=SePayloadType.Time, count=(1, 1)):
    pass


class SePayloadItalics(SePayload, payload_type=SePayloadType.Italics, count=(1, 1)):
    pass


class SePayloadFormat(SePayload, payload_type=SePayloadType.Format, count=(2, 2)):
    @property
    def value(self):
        return self.expressions[0]

    @property
    def format(self):
        return self.expressions[1]

    @property
    def _repr_expression_names(self):
        return "value", "format"


class SePayloadSheetReference(SePayload, payload_type=SePayloadType.SheetReference, count=(2, None)):
    @property
    def sheet_name(self):
        return self.expressions[0]

    @property
    def row_id(self):
        return self.expressions[1]

    @property
    def column_id(self):
        try:
            return self.expressions[2]
        except IndexError:
            return None

    @property
    def parameters(self):
        return self.expressions[3:]

    @property
    def _repr_expression_names(self):
        return "sheet", "row", "column", "parameter"


class SePayloadSheetLanguageReference(SePayload, count=(3, None)):
    @property
    def sheet_name(self):
        return self.expressions[0]

    @property
    def row_id(self):
        return self.expressions[1]

    @property
    def attribute(self):
        return self.expressions[2]

    @property
    def column_id(self):
        try:
            return self.expressions[3]
        except IndexError:
            return None

    @property
    def parameters(self):
        return self.expressions[4:]

    @property
    def _repr_expression_names(self):
        return "sheet", "row", "attribute", "column", "parameter"


class SePayloadSheetLanguageReferenceJa(SePayloadSheetLanguageReference, payload_type=SePayloadType.SheetReferenceJa):
    pass


class SePayloadSheetLanguageReferenceEn(SePayloadSheetLanguageReference, payload_type=SePayloadType.SheetReferenceEn):
    pass


class SePayloadSheetLanguageReferenceDe(SePayloadSheetLanguageReference, payload_type=SePayloadType.SheetReferenceDe):
    pass


class SePayloadSheetLanguageReferenceFr(SePayloadSheetLanguageReference, payload_type=SePayloadType.SheetReferenceFr):
    pass


class SePayloadLink(SePayload, payload_type=SePayloadType.Link, count=(1, 1)):
    pass


class SePayloadIf(SePayload, payload_type=SePayloadType.If, count=(1, None)):
    @property
    def condition(self):
        return self.expressions[0]

    @property
    def true_value(self) -> typing.Optional[SeExpression]:
        try:
            return self.expressions[1]
        except IndexError:
            return None

    @property
    def false_value(self) -> typing.Optional[SeExpression]:
        try:
            return self.expressions[2]
        except IndexError:
            return None

    @property
    def misc_values(self):
        return self.expressions[3:]

    @property
    def _repr_expression_names(self):
        return "condition", "true", "false", "misc"


class SePayloadIfEquals(SePayload, payload_type=SePayloadType.IfEquals, count=(2, None)):
    @property
    def left(self):
        return self.expressions[0]

    @property
    def right(self):
        return self.expressions[1]

    @property
    def true_value(self) -> typing.Optional[SeExpression]:
        try:
            return self.expressions[2]
        except IndexError:
            return None

    @property
    def false_value(self) -> typing.Optional[SeExpression]:
        try:
            return self.expressions[3]
        except IndexError:
            return None

    @property
    def misc_values(self):
        return self.expressions[4:]

    @property
    def _repr_expression_names(self):
        return "left", "right", "true", "false", "misc"


class SePayloadSwitch(SePayload, payload_type=SePayloadType.Switch, count=(1, None)):
    @property
    def condition(self):
        return self.expressions[0]

    @property
    def cases(self):
        return {i: x for i, x in enumerate(self.expressions[1:], 1)}

    @property
    def _repr_expression_names(self):
        return "condition", "case"


class SePayloadIfPlayer(SePayload, payload_type=SePayloadType.IfPlayer, count=(3, 3)):
    @property
    def actor_id(self):
        return self.expressions[0]

    @property
    def player_value(self):
        return self.expressions[1]

    @property
    def someone_else_value(self):
        return self.expressions[2]

    @property
    def _repr_expression_names(self):
        return "actor_id", "player", "someone_else"


class SePayloadBitmapFontIcon(SePayload, payload_type=SePayloadType.BitmapFontIcon, count=(1, 1)):
    pass


class SePayloadIcon2(SePayload, payload_type=SePayloadType.Icon2, count=(1, 1)):
    pass


class SePayloadPlaceholder(SePayload, payload_type=SePayloadType.Placeholder, count=(2, None)):
    def __new__(cls, data: typing.Union[bytearray, bytes, memoryview] = b"",
                sheet_reader: typing.Optional[SHEET_READER] = None):
        if cls is SePayloadPlaceholder:
            if SeExpression.from_buffer_copy(data, 0) == 0xc8:
                return SePayloadPlaceholderComplex(data, sheet_reader)
            else:
                return SePayloadPlaceholderCompletion(data, sheet_reader)
        return super().__new__(cls, data, sheet_reader)

    @property
    def type(self):
        return SePayloadType.Placeholder

    @property
    def group_id(self):
        return self.expressions[0] + 1

    @property
    def _repr_expression_names(self):
        return "group_id", "param"


class SePayloadPlaceholderCompletion(SePayloadPlaceholder, count=(2, 2)):
    @property
    def row_id(self):
        return self.expressions[1]

    @property
    def completion(self):
        if self._sheet_reader is None:
            return None
        reader: 'ExcelReader' = self._sheet_reader("Completion")
        row: typing.Union['CompletionRow', 'ExdRow']
        try:
            return reader[self.row_id].text
        except KeyError:
            pass
        for row in reader:
            if row.group_id == self.group_id:
                break
        else:
            return None
        reader = self._sheet_reader(str(row.lookup_table).split("[", 1)[0])
        try:
            row = reader[self.row_id]
            if hasattr(row, 'name'):
                return row.name
            return row[0]
        except KeyError:
            return None

    @property
    def _repr_expression_names(self):
        return "group_id", "row_id"

    def _repr_extra(self):
        return self.completion


class SePayloadPlaceholderComplex(SePayloadPlaceholder, count=(3, None)):
    _complex_type_map: typing.ClassVar[typing.Dict[int, typing.Type['SePayloadPlaceholderComplex']]] = {}

    COMPLEX_TYPE: typing.ClassVar[typing.Optional[int]] = None

    def __init_subclass__(cls, complex_type: typing.Optional[int] = None, **kwargs):
        if complex_type is not None:
            cls.COMPLEX_TYPE = complex_type
            cls._complex_type_map[complex_type] = cls

    def __new__(cls, data: typing.Union[bytearray, bytes, memoryview] = b"",
                sheet_reader: typing.Optional[SHEET_READER] = None):
        if cls is SePayloadPlaceholderComplex:
            subinfo_type = SeExpression.from_buffer_copy(data, len(bytes(SeExpression.from_buffer_copy(data, 0))))
            c = cls._complex_type_map.get(int(subinfo_type), None)
            if c is not None:
                return c(data, sheet_reader)
        return super().__new__(cls, data, sheet_reader)

    @property
    def complex_type(self):
        return self.expressions[1]

    @property
    def _repr_expression_names(self):
        return "group_id", "complex_type"


class SePayloadPlaceholderMapPositionLink(SePayloadPlaceholderComplex, count=(7, 7), complex_type=3):
    @property
    def territory_type_id(self):
        return self.expressions[2]

    @property
    def map_id(self):
        return self.expressions[3]

    @property
    def raw_x(self):
        return ctypes.c_int32(self.expressions[4]).value

    @property
    def raw_y(self):
        return ctypes.c_int32(self.expressions[5]).value

    @property
    def raw_z(self):
        return ctypes.c_int32(self.expressions[6]).value

    @property
    def x(self):
        return self.raw_x / 1000

    @property
    def y(self):
        return self.raw_y / 1000

    @property
    def z(self):
        return self.raw_z / 1000

    @property
    def display_x(self):
        return self._pixels_to_display_unit(self.x)

    @property
    def display_y(self):
        return self._pixels_to_display_unit(self.y)

    @property
    def display_z(self):
        return self._pixels_to_display_unit(self.z)

    def _pixels_to_display_unit(self, pixels: float):
        c = self.map.size_factor / 100.
        scaled_pos = pixels * c

        # displayed 25.2, 31.3
        # 40.90 (25.2, 31.3, 20.9)
        # 40.89 (25.2, 31.3, 20.8)
        # 40.885 (25.2, 31.2, 20.8)
        # 40.88 (25.2, 31.2, 20.8)
        #
        # displayed 7.3, 29.3
        # 40.90 (7.4, 29.3, 20.9)
        # 40.89 (7.4, 29.3, 20.9)
        #  40.885 (7.4, 29.3, 20.8)
        #
        # ^ rounding doesn't work. maybe it's flooring?

        return 40.885 / c * ((scaled_pos + 1024.) / 2048.) + 1.

    @functools.cached_property
    def map(self) -> typing.Union['MapRow', 'ExdRow']:
        return self._sheet_reader("Map")[self.map_id]

    def _repr_extra(self) -> typing.Optional[str]:
        return f"{self.display_x:.01f}, {self.display_y:.01f}, {self.display_z:.01f}"

    @property
    def _repr_expression_names(self):
        return "group_id", "complex_type", "territory_type_id", "map_id", "raw_x", "raw_y", "raw_z"


class SePayloadPlaceholderSoundEffect(SePayloadPlaceholderComplex, count=(3, 3), complex_type=5):
    @property
    def sound_effect_id(self):
        # <se.1> = 0, <se.1> = 2, etc.
        return self.expressions[2]

    @property
    def _repr_expression_names(self):
        return "group_id", "complex_type", "sound_effect_id"


class SePayloadColorFill(SePayload, payload_type=SePayloadType.ColorFill, count=(1, 1)):
    pass


class SePayloadColorBorder(SePayload, payload_type=SePayloadType.ColorBorder, count=(1, 1)):
    pass


class SePayloadOrdinalValue(SePayload, payload_type=SePayloadType.OrdinalValue, count=(1, 1)):
    pass


class SePayloadInstantContent(SePayload, payload_type=SePayloadType.InstanceContent, count=(1, 1)):
    pass


class SePayloadResetTime(SePayload, payload_type=SePayloadType.ResetTime, count=(1, 2)):
    @property
    def hour_utc9(self):
        return self.expressions[0]

    @property
    def weekday(self):
        try:
            return self.expressions[1]
        except KeyError:
            return None

    @property
    def _repr_expression_names(self):
        return "hour_utc9", "weekday"


class SePayloadSplit(SePayload, payload_type=SePayloadType.Split, count=(3, 3)):
    @property
    def value(self):
        return self.expressions[0]

    @property
    def separator(self):
        return self.expressions[1]

    @property
    def index(self):
        return self.expressions[2]

    @property
    def _repr_expression_names(self):
        return "value", "separator", "index"


class SePayloadIfEndsWithJongseong(SePayload, payload_type=SePayloadType.IfEndsWithJongseong, count=(3, 3)):
    @property
    def text(self):
        return self.expressions[0]

    @property
    def true_value(self):
        return self.expressions[1]

    @property
    def false_value(self):
        return self.expressions[2]

    @property
    def _repr_expression_names(self):
        return "text", "true", "false"


class SePayloadIfEndsWithJongseongExceptRieul(SePayload, payload_type=SePayloadType.IfEndsWithJongseongExceptRieul,
                                              count=(3, 3)):
    @property
    def text(self):
        return self.expressions[0]

    @property
    def true_value(self):
        return self.expressions[1]

    @property
    def false_value(self):
        return self.expressions[2]

    @property
    def _repr_expression_names(self):
        return "text", "true", "false"


class SePayloadDialoguePageSeparator(SePayload, payload_type=SePayloadType.DialoguePageSeparator, count=(1, 1)):
    # Possible forced page separator
    #
    # 여기선 모험가 길드에 소속된 사람들에게<br />
    # &#x27;길드 의뢰&#x27;를 발행하고 있어.<br />
    # <SePayload type="DialoguePageSeparator" />당신이 <switch /> 님께<br />
    # 의뢰를 받을 수 있게 되면<br />
    # 일자리를 알선해줄게.
    pass


class SePayloadActorFullName(SePayload, payload_type=SePayloadType.ActorFullName, count=(1, 1)):
    # Possible actor full name
    #
    # Looks like <0x0a value="(IntegerParameter=1)" /> fished up Lady Luck herself! Here comes a spectral current!
    pass


class SePayloadX19(SePayload, payload_type=SePayloadType.X19, count=(1, 1)):
    # Oh. Well that was...<i>something</i>. I guess. <0x19 value="1" />...Do you want to play again?
    pass


class SePayloadX1b(SePayload, payload_type=SePayloadType.X1b, count=(1, 1)):
    # Used in QuickChatTransient
    pass


class SePayloadX1c(SePayload, payload_type=SePayloadType.X1c, count=(1, 1)):
    # Used in QuickChatTransient
    pass


class SePayloadX16(SePayload, payload_type=SePayloadType.X16, count=(0, 0)):
    pass


class SePayloadX26(SePayload, payload_type=SePayloadType.X26, count=(3, 3)):
    pass


class SePayloadX2d(SePayload, payload_type=SePayloadType.X2d, count=(1, 1)):
    pass


class SePayloadX2f(SePayload, payload_type=SePayloadType.X2f, count=(1, 1)):
    pass


class SePayloadX60(SePayload, payload_type=SePayloadType.X60, count=(1, None)):
    pass


class SePayloadX61(SePayload, payload_type=SePayloadType.X61, count=(1, 1)):
    pass


class SeString:
    START_BYTE = 0x02
    START_BYTE_STR = "\x02"
    END_BYTE = 0x03

    _escaped: typing.Optional[bytes] = None
    _parsed: typing.Optional[str] = None
    _payloads: typing.Optional[typing.Tuple[SePayload]] = None

    def __init__(self, data: typing.Union['SeString', bytes, bytearray, memoryview, str] = b"",
                 *payloads: SePayload, sheet_reader: typing.Optional[SHEET_READER] = None):
        self._sheet_reader = sheet_reader

        if isinstance(data, SeString):
            self._escaped = data._escaped
            self._parsed = data._parsed
            self._payloads = data._payloads

        elif isinstance(data, str):
            payload_count = data.count(SeString.START_BYTE_STR)
            if payload_count != len(payloads):
                raise ValueError(f"Number of provided payloads({len(payloads)})"
                                 f" does not match the number of expected payloads({payload_count})")
            self._parsed = data
            self._payloads = payloads
            payloads = None

        elif isinstance(data, (bytes, bytearray, memoryview)):
            self._escaped = None if data is None else bytes(data)

        if payloads:
            if len(payloads) == len(self):
                self._payloads = payloads
            else:
                raise ValueError(f"Number of provided payloads({len(payloads)})"
                                 f" does not match the number of expected payloads({len(self)}).")

    def set_sheet_reader(self, reader: SHEET_READER):
        self._sheet_reader = reader
        if self._payloads is not None:
            for payload in self._payloads:
                payload.set_sheet_reader(reader)

    def __bytes__(self):
        if self._escaped is not None:
            return self._escaped

        escaped = bytearray()
        payload_index = 0
        for r in self._parsed.encode("utf-8"):
            escaped.append(r)
            if r != SeString.START_BYTE:
                continue

            payload = self._payloads[payload_index]
            escaped_payload = bytes(payload)
            escaped.append(payload.type)
            escaped.extend(bytes(SeExpressionUint32(len(escaped_payload))))
            escaped.extend(escaped_payload)
            escaped.append(SeString.END_BYTE)
            payload_index += 1

        self._escaped = bytes(escaped)
        return self._escaped

    def __bool__(self):
        return (self._parsed is not None and self._parsed != "") or (self._escaped is not None and self._escaped != b"")

    def __str__(self):
        self._parse()
        return self._parsed

    def __getitem__(self, item):
        self._parse()
        return self._payloads[item]

    def __len__(self):
        self._parse()
        return len(self._payloads)

    def __iter__(self):
        self._parse()
        return iter(self._payloads)

    def _parse(self):
        if self._parsed is not None:
            return

        i = 0
        parsed = bytearray()
        payloads: typing.List[SePayload] = []
        while i < len(self._escaped):
            parsed.append(self._escaped[i])
            i += 1

            if parsed[-1] != SeString.START_BYTE:
                continue

            payload_type = self._escaped[i]
            i += 1

            data_len = SeExpression.from_buffer_copy(self._escaped, i, self._sheet_reader)
            i += len(bytes(data_len))

            payload_bytes = self._escaped[i:i + data_len]
            if len(payload_bytes) != data_len:
                raise ValueError("Incomplete payload")
            i += data_len

            if self._escaped[i] != SeString.END_BYTE:
                raise ValueError("End byte not found")
            i += 1

            payloads.append(SePayload.from_bytes(payload_bytes, SePayloadType(payload_type),
                                                 sheet_reader=self._sheet_reader))

        self._parsed = parsed.decode("utf-8")
        self._payloads = tuple(payloads)

    def __repr__(self):
        self._parse()
        if self._parsed is None:
            return "(None)"
        if not self._payloads:
            return self._parsed

        res = []
        for i, text in enumerate(str(self).split(SeString.START_BYTE_STR)):
            res.append(html.escape(text))
            if i == len(self._payloads):  # last item
                break

            res.append(repr(self[i]))
        return "".join(res)
