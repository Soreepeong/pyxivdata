import enum
import functools
import html
import typing


class SeExpressionType(enum.IntEnum):
    # https://github.com/xivapi/SaintCoinach/blob/36e9d613f4bcc45b173959eed3f7b5549fd6f540/SaintCoinach/Text/DecodeExpressionType.cs

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
    Xdb = 0xdb
    Xdc = 0xdc
    Xdd = 0xdd
    Xde = 0xde
    Xdf = 0xdf

    GreaterThanOrEqualTo = 0xe0  # Followed by two variables
    GreaterThan = 0xe1  # Followed by one variable
    LessThanOrEqualTo = 0xe2  # Followed by two variables
    LessThan = 0xe3  # Followed by one variable
    Equal = 0xe4  # Followed by two variables
    NotEqual = 0xe5  # TODO: Probably

    # TODO: I /think/ I got these right.
    IntegerParameter = 0xe8  # Followed by one variable
    PlayerParameter = 0xe9  # Followed by one variable
    StringParameter = 0xeA  # Followed by one variable
    ObjectParameter = 0xeB  # Followed by one variable

    SeString = 0xff  # Followed by length (including length) and data


class SePayloadType(enum.IntEnum):
    Empty = 0x00
    ResetTime = 0x06
    Time = 0x07
    If = 0x08
    Switch = 0x09
    IfEquals = 0x0c
    KoreanObjectParticle = 0x0d  # 을/를 (Eul/Rul)
    KoreanDirectionParticle = 0x0e  # 로/으로 (Ro/Euro)
    NewLine = 0x10
    Icon1 = 0x12
    ColorChange = 0x13
    Italics = 0x1a
    Indent = 0x1d
    Icon2 = 0x1e
    Dash = 0x1f
    Value = 0x20
    Format = 0x22
    TwoDigitValue = 0x24  # f"{:02}"
    X23 = 0x23
    X24 = 0x24
    X25 = 0x25
    # Map link at Zadnor (8.4, 24.2) (c9 04 f2 03 cf f2 02 99 fe ff f6 10 bb f6 02 24 4d fe ff ff 8a d0)
    Interactable = 0x27  # Player, Item, Map Link, Status, Quest
    SheetReference = 0x28
    Highlight = 0x29
    Link = 0x2b  # TODO: how are Interactable and Link different?
    Split = 0x2c

    # The Orbonne Monastery (33f20b30):
    #     Completion (category=0x33=51)
    #         Lookup column(2) specified (PlaceName[20-37,39-59,...,2864-2864,...])
    #     PlaceName (row_id=0xb30=2864)
    # Let's do it! (02f0e3)
    #     Completion (category=2, row_id=0xE3=227)
    # Let's rest for a while. (08f2033a)
    #     Completion (category=8, row_id=0x033a=826)
    # <se.##> (c9 06 ##)
    AutoTranslateKey = 0x2e
    SheetReferenceJa = 0x30
    SheetReferenceEn = 0x31
    SheetReferenceDe = 0x32
    SheetReferenceFr = 0x33
    InstanceContent = 0x40
    UiColorFill = 0x48
    UiColorBorder = 0x49
    ZeroPaddedValue = 0x50

    X0a = 0x0a  # Probably source player
    X0f = 0x0f
    X14 = 0x14
    X16 = 0x16
    X17 = 0x17
    X19 = 0x19
    X26 = 0x26
    X2d = 0x2d

    X2f = 0x2f
    X32 = 0x32
    X33 = 0x33
    X51 = 0x51
    X60 = 0x60
    X61 = 0x61

    def __str__(self):
        return f"{self.name}({self.value:02x})"


class SeExpression:
    _buffer: typing.Optional[bytes] = None

    def __bytes__(self):
        return self._buffer

    def __int__(self):
        raise TypeError

    @classmethod
    def from_value(cls, value: typing.Union[int, str, 'SeExpression']):
        if isinstance(value, SeExpression):
            return value
        elif type(value) is int:
            return SeExpressionUint32(value)
        elif isinstance(value, str):
            return SeExpressionSeString(SeString(value))
        elif isinstance(value, SeString):
            return SeExpressionSeString(value)
        raise TypeError(f"Value {value} is not implicitly convertible to a SeExpression.")

    @classmethod
    def from_buffer_copy(cls, data: typing.Union[bytes, bytearray, memoryview], offset: typing.Optional[int] = None):
        if offset is None:
            offset = 0

        if cls is not SeExpression:
            self = super(cls, SeExpression).__new__(cls)
            self._buffer = data[offset:]
            return self

        begin = offset
        marker = data[offset]
        offset += 1
        if marker < 0xD0:
            value = marker - 1
            self = SeExpressionUint32(value)

        elif 0xD0 <= marker <= 0xDF:
            self = SeExpressionPredefinedParameter(SeExpressionType(marker))

        elif marker in (0xE0, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5):
            operand1 = SeExpression.from_buffer_copy(data, offset)
            offset += len(bytes(operand1))
            operand2 = SeExpression.from_buffer_copy(data, offset)
            offset += len(bytes(operand2))
            self = SeExpressionBinary(SeExpressionType(marker), operand1, operand2)

        elif marker in (0xE8, 0xE9, 0xEA, 0xEB):
            operand = SeExpression.from_buffer_copy(data, offset)
            offset += len(bytes(operand))
            self = SeExpressionUnary(SeExpressionType(marker), operand)

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
            se_string_len = SeExpression.from_buffer_copy(data, offset)
            offset += len(bytes(se_string_len))
            se_string = SeString(data[offset:offset + se_string_len])
            offset += len(bytes(se_string))
            self = SeExpressionSeString(se_string)

        else:
            raise ValueError(f"Marker 0x{marker:02x} is not a valid SeUint32.")
        self._buffer = data[begin:offset]
        return self


class SeExpressionSeString(SeExpression):
    def __init__(self, data: 'SeString'):
        self._data = data

    def __bytes__(self):
        if self._buffer is not None:
            return self._buffer

        self._buffer = bytes((SeExpressionType.SeString,)) + bytes(self._data)
        return self._buffer

    def __repr__(self):
        return repr(self._data)


class SeExpressionPredefinedParameter(SeExpression):
    def __init__(self, expression_type: SeExpressionType):
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
    def __init__(self, expression_type: SeExpressionType, operand: SeExpression):
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
    def __init__(self, expression_type: SeExpressionType, operand1: SeExpression, operand2: SeExpression):
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

    ESCAPE_TYPE: typing.ClassVar[typing.Optional[SePayloadType]]

    _buffer: bytes

    def __init_subclass__(cls, escape_type: typing.Optional[SePayloadType] = None, **kwargs):
        cls.ESCAPE_TYPE = escape_type
        if escape_type is not None:
            cls._implemented_payload_types[escape_type] = cls

    @classmethod
    def from_bytes(cls, escape_type: SePayloadType, data: typing.Union[bytearray, bytes, memoryview]):
        t = cls._implemented_payload_types.get(escape_type, None)
        if t is None:
            return SePayloadUnknown(escape_type, data)
        return t(data)

    def __init__(self, data: typing.Union[bytearray, bytes, memoryview] = b""):
        self._buffer = bytes(data)

    @property
    def type(self) -> SePayloadType:
        return self.ESCAPE_TYPE

    def __bytes__(self):
        return self._buffer

    def __repr__(self):
        if not self._buffer:
            return f"<{self.type.name} />"
        return f"<{self.type.name}>{self._buffer.hex()}</{self.type.name}>"


class SePayloadUnknown(SePayload):
    def __init__(self, escape_type: SePayloadType, data: typing.Union[bytearray, bytes, memoryview]):
        super().__init__(data)
        self._escape_type = escape_type

    @property
    def type(self):
        return self._escape_type


class SePayloadNewLine(SePayload, escape_type=SePayloadType.NewLine):
    pass


class SePayloadDash(SePayload, escape_type=SePayloadType.Dash):
    pass


class SePayloadWithExpression1(SePayload):
    @classmethod
    def from_value(cls, value: typing.Union[int, str, SeExpression]):
        return SePayloadWithExpression1(bytes(SeExpression.from_value(value)))

    @functools.cached_property
    def value(self):
        return SeExpression.from_buffer_copy(self._buffer)

    def __bool__(self):
        return self.value != 0

    def __repr__(self):
        return f"""<{self.type.name} value="{self.value}" />"""


class SePayloadUiColorBorder(SePayloadWithExpression1, escape_type=SePayloadType.UiColorBorder):
    pass


class SePayloadUiColorFill(SePayloadWithExpression1, escape_type=SePayloadType.UiColorFill):
    pass


class SePayloadHighlight(SePayloadWithExpression1, escape_type=SePayloadType.Highlight):
    pass


class SePayloadTwoDigitValue(SePayloadWithExpression1, escape_type=SePayloadType.TwoDigitValue):
    pass


class SePayloadValue(SePayloadWithExpression1, escape_type=SePayloadType.Value):
    pass


class SePayloadTime(SePayloadWithExpression1, escape_type=SePayloadType.Time):
    pass


class SePayloadItalics(SePayloadWithExpression1, escape_type=SePayloadType.Italics):
    pass


class SePayloadWithSequentialExpressionsBase(SePayload):
    _min_expressions: typing.ClassVar[typing.Optional[int]] = None
    _max_expressions: typing.ClassVar[typing.Optional[int]] = None

    def __init_subclass__(cls, max_expressions: typing.Optional[int] = None,
                          min_expressions: typing.Optional[int] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._max_expressions = max_expressions
        cls._min_expressions = min_expressions

    @classmethod
    def from_values(cls, *values: typing.Union[int, str, SeExpression]):
        if cls._min_expressions is not None and len(values) < cls._min_expressions:
            raise ValueError(f"Number of expressions({len(values)} < Min number of expression({cls._min_expressions}")
        if cls._max_expressions is not None and len(values) > cls._max_expressions:
            raise ValueError(f"Number of expressions({len(values)} > Max number of expression({cls._max_expressions}")
        return SePayloadWithSequentialExpressionsBase(b"".join(bytes(SeExpression.from_value(v)) for v in values))

    @functools.cached_property
    def expressions(self):
        offset = 0
        res = []
        while offset < len(self._buffer):
            res.append(SeExpression.from_buffer_copy(self._buffer, offset))
            offset += len(bytes(res[-1]))
        if self._min_expressions is not None and len(res) < self._min_expressions:
            raise ValueError(f"Number of expressions({len(res)} < Min number of expression({self._min_expressions}")
        if self._max_expressions is not None and len(res) > self._max_expressions:
            raise ValueError(f"Number of expressions({len(res)} > Max number of expression({self._max_expressions}")
        return tuple(res)

    def __repr__(self):
        res = [f"""<{self.type.name}>"""]
        for k, v in enumerate(self.expressions):
            res.append(f"""<expression index="{k}">{repr(v)}</case>""")
        res.append(f"</{self.type.name}>")
        return "".join(res)


class SePayloadFormat(SePayloadWithSequentialExpressionsBase, escape_type=SePayloadType.Format, max_expressions=2):
    @property
    def value(self):
        return self.expressions[0]

    @property
    def format(self):
        return self.expressions[1]

    def __repr__(self):
        return f"""<{self.type.name} value="{self.value}" format="{self.format}" />"""


class SePayloadSheetReference(SePayloadWithSequentialExpressionsBase, escape_type=SePayloadType.SheetReference,
                              min_expressions=2):
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

    def __repr__(self):
        res = [
            f"<{self.type.name}",
            f' sheet="{html.escape(repr(self.sheet_name))}"',
            f' row="{html.escape(repr(self.row_id))}"',
        ]
        if self.column_id is not None:
            res.append(f' column="{html.escape(repr(self.column_id))}"')
        res.append(">")
        if self.parameters:
            for i, p in enumerate(self.parameters):
                res.append(f"""<param index="{i}">{repr(p)}</param>""")
        res.append(f"</{self.type.name}>")
        return "".join(res)


class SePayloadSheetLanguageReference(SePayloadWithSequentialExpressionsBase, min_expressions=3):
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

    def __repr__(self):
        res = [
            f"<{self.type.name}",
            f' sheet="{html.escape(repr(self.sheet_name))}"',
            f' row="{html.escape(repr(self.row_id))}"',
        ]
        if self.column_id is not None:
            res.append(f' column="{html.escape(repr(self.column_id))}"')
        res.append(">")
        res.append(f"<attribute>{repr(self.attribute)}</attribute>")
        if self.parameters:
            for i, p in enumerate(self.parameters):
                res.append(f"""<param index="{i}">{repr(p)}</param>""")
        res.append(f"</{self.type.name}>")
        return "".join(res)


class SePayloadSheetLanguageReferenceJa(SePayloadSheetLanguageReference, escape_type=SePayloadType.SheetReferenceJa):
    pass


class SePayloadSheetLanguageReferenceEn(SePayloadSheetLanguageReference, escape_type=SePayloadType.SheetReferenceEn):
    pass


class SePayloadSheetLanguageReferenceDe(SePayloadSheetLanguageReference, escape_type=SePayloadType.SheetReferenceDe):
    pass


class SePayloadSheetLanguageReferenceFr(SePayloadSheetLanguageReference, escape_type=SePayloadType.SheetReferenceFr):
    pass


class SePayloadConditionalExpressionBase(SePayloadWithSequentialExpressionsBase):
    @property
    def cases(self) -> typing.Dict[any, typing.Optional[SeExpression]]:
        raise NotImplementedError

    def _repr_condition(self) -> str:
        raise NotImplementedError

    def __repr__(self):
        res = [f"""<{self.type.name} condition="{html.escape(self._repr_condition())}">"""]
        for k, v in self.cases.items():
            res.append(f"""<case when="{k}">{repr(v)}</case>""")
        res.append(f"</{self.type.name}>")
        return "".join(res)


class SePayloadIf(SePayloadConditionalExpressionBase, escape_type=SePayloadType.If):
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
    def cases(self) -> typing.Dict[any, typing.Optional[SeExpression]]:
        # noinspection PyTypeChecker
        return {
            True: self.true_value,
            False: self.false_value,
            **dict(enumerate(self.misc_values))
        }

    def _repr_condition(self) -> str:
        return repr(self.condition)


class SePayloadIfEquals(SePayloadConditionalExpressionBase, escape_type=SePayloadType.IfEquals):
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
    def cases(self) -> typing.Dict[any, typing.Optional[SeExpression]]:
        # noinspection PyTypeChecker
        return {
            True: self.true_value,
            False: self.false_value,
            **dict(enumerate(self.misc_values))
        }

    def _repr_condition(self) -> str:
        return f"{self.left} == {self.right}"


class SePayloadSwitch(SePayloadConditionalExpressionBase, escape_type=SePayloadType.Switch):
    @property
    def condition(self):
        return self.expressions[0]

    @property
    def cases(self):
        return {i: x for i, x in enumerate(self.expressions[1:], 1)}

    def _repr_condition(self) -> str:
        return repr(self.condition)


class SeString:
    START_BYTE = 0x02
    START_BYTE_STR = "\x02"
    END_BYTE = 0x03

    _escaped: typing.Optional[bytes] = None
    _parsed: typing.Optional[str] = None
    _components: typing.Optional[typing.Tuple[SePayload]] = None

    def __init__(self, data: typing.Union['SeString', bytes, bytearray, memoryview, str] = b"",
                 *components: SePayload):
        if isinstance(data, SeString):
            self._escaped = data._escaped
            self._parsed = data._parsed
            self._components = data._components

        elif isinstance(data, str):
            component_count = data.count(SeString.START_BYTE_STR)
            if component_count != len(components):
                raise ValueError(f"Number of provided components({len(components)})"
                                 f" does not match the number of expected components({component_count})")
            self._parsed = data
            self._components = components
            components = None

        elif isinstance(data, (bytes, bytearray, memoryview)):
            self._escaped = None if data is None else bytes(data)

        if components:
            if len(components) == len(self):
                self._components = components
            else:
                raise ValueError(f"Number of provided components({len(components)})"
                                 f" does not match the number of expected components({len(self)}).")

    def __bytes__(self):
        if self._escaped is not None:
            return self._escaped

        escaped = bytearray()
        component_index = 0
        for r in self._parsed.encode("utf-8"):
            escaped.append(r)
            if r != SeString.START_BYTE:
                continue

            component = self._components[component_index]
            escaped_payload = bytes(component)
            escaped.append(component.type)
            escaped.extend(bytes(SeExpressionUint32(len(escaped_payload))))
            escaped.extend(escaped_payload)
            escaped.append(SeString.END_BYTE)
            component_index += 1

        self._escaped = bytes(escaped)
        return self._escaped

    def __bool__(self):
        return (self._parsed is not None and self._parsed != "") or (self._escaped is not None and self._escaped != b"")

    def __str__(self):
        self._parse()
        return self._parsed

    def __getitem__(self, item):
        self._parse()
        return self._components[item]

    def __len__(self):
        self._parse()
        return len(self._components)

    def __iter__(self):
        self._parse()
        return iter(self._components)

    def _parse(self):
        if self._parsed is not None:
            return

        i = 0
        parsed = bytearray()
        components: typing.List[SePayload] = []
        while i < len(self._escaped):
            parsed.append(self._escaped[i])
            i += 1

            if parsed[-1] != SeString.START_BYTE:
                continue

            escape_type = self._escaped[i]
            i += 1

            data_len = SeExpression.from_buffer_copy(self._escaped, i)
            i += len(bytes(data_len))

            component = self._escaped[i:i + data_len]
            if len(component) != data_len:
                raise ValueError("Incomplete component")
            i += data_len

            if self._escaped[i] != SeString.END_BYTE:
                raise ValueError("End byte not found")
            i += 1

            components.append(SePayload.from_bytes(SePayloadType(escape_type), component))

        self._parsed = parsed.decode("utf-8")
        self._components = tuple(components)

    def __repr__(self):
        self._parse()
        if self._parsed is None:
            return "(None)"
        if not self._components:
            return self._parsed

        res = []
        for i, text in enumerate(str(self).split("\x02")):
            res.append(html.escape(text))
            if i == len(self._components):  # last item
                break

            res.append(repr(self[i]))
        return "".join(res)
