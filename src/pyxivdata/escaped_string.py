import enum
import html
import typing


class SqEscapeType(enum.IntEnum):
    Empty = 0x00
    Time = 0x07
    If = 0x08
    Switch = 0x09
    KoreanObjectParticle = 0x0d  # 을/를 (Eul/Rul)
    KoreanDirectionParticle = 0x0e  # 로/으로 (Ro/Euro)
    NewLine = 0x10
    Icon1 = 0x12
    ColorChange = 0x13
    Italics = 0x1a
    Indent = 0x1d
    Icon2 = 0x1e
    Dash = 0x1f
    ServerValue0 = 0x20
    ServerValue1 = 0x21
    ServerValue2 = 0x22
    ServerValue3 = 0x24
    ServerValue4 = 0x25
    PlayerLink = 0x27
    Reference = 0x28
    Info = 0x29
    Link = 0x2b
    Split = 0x2c
    ItemLookup = 0x31
    Reference2 = 0x40

    # Following two can be actually in the other way around, as these two are not confirmed
    PresetColorChange = 0x48  # \xf2\x01\xf8 ... \x01
    PresetBorderChange = 0x49  # \xf2\x01\xf9 ... \x01

    Unknown_06 = 0x06
    Unknown_0a = 0x0a  # Probably source player
    Unknown_0f = 0x0f
    Unknown_14 = 0x14
    Unknown_16 = 0x16
    Unknown_17 = 0x17
    Unknown_19 = 0x19
    Unknown_26 = 0x26
    Unknown_2d = 0x2d
    Unknown_2e = 0x2e
    Unknown_2f = 0x2f
    Unknown_32 = 0x32
    Unknown_33 = 0x33
    Unknown_50 = 0x50
    Unknown_51 = 0x51
    Unknown_60 = 0x60
    Unknown_61 = 0x61

    def __str__(self):
        return f"{self.name}({self.value})"


class SqEscapedString:
    START_BYTE = 0x02
    END_BYTE = 0x03

    _escaped: typing.Optional[bytes] = None
    _parsed: typing.Optional[str] = None
    _components: typing.Optional[typing.List[typing.Tuple[typing.Union[SqEscapeType, int], any]]]

    def __init__(self, escaped: typing.Union[bytes, bytearray, memoryview, None] = None,
                 parsed: typing.Optional[str] = None,
                 components: typing.Optional[typing.Sequence[typing.Union[bytes, bytearray, memoryview]]] = None):
        self._escaped = None if escaped is None else bytes(escaped)
        self._parsed = parsed
        self._components = None if components is None else [bytes(x) for x in components]

    @property
    def escaped(self) -> typing.Optional[bytes]:
        self._escape()
        return self._escaped

    @property
    def parsed(self) -> typing.Optional[str]:
        self._parse()
        return self._parsed

    @property
    def components(self):
        self._parse()
        return self._components

    def _parse(self):
        if self._parsed is not None or self._escaped is None:
            return

        i = 0
        parsed = bytearray()
        components = []
        while i < len(self._escaped):
            parsed.append(self._escaped[i])

            if self._escaped[i] != SqEscapedString.START_BYTE:
                i += 1
                continue

            if len(self._escaped) - i < 3:
                raise ValueError("sentinel character occurred but there are less than 3 remaining bytes")

            escaped_len = self._escaped[i + 2]
            if escaped_len == 0xF0:
                data_len = self._escaped[i + 3]
                data_ptr = i + 4
            elif escaped_len == 0xF1:
                data_len = self._escaped[i + 3] << 8
                data_ptr = i + 4
            elif escaped_len == 0xF2:
                data_len = int.from_bytes(self._escaped[i + 3:i + 5], "big", signed=False)
                data_ptr = i + 5
            elif escaped_len == 0xFA:
                data_len = int.from_bytes(self._escaped[i + 3:i + 6], "big", signed=False)
                data_ptr = i + 6
            elif escaped_len == 0xFE:
                data_len = int.from_bytes(self._escaped[i + 3:i + 7], "big", signed=False)
                data_ptr = i + 7
            else:
                data_len = escaped_len - 1
                data_ptr = i + 3

            if self._escaped[data_ptr + data_len] != SqEscapedString.END_BYTE:
                raise ValueError("End byte not found")

            escape_type = self._escaped[i + 1]
            component = self._escaped[data_ptr:data_ptr + data_len]
            if len(component) != data_len:
                raise ValueError("Incomplete component")
            try:
                escape_type = SqEscapeType(escape_type)
            except ValueError:
                pass
            components.append((escape_type, component))
            i = data_ptr + data_len + 1

        self._parsed = parsed.decode("utf-8")
        self._components = components

    def _escape(self):
        if self._escaped is not None or self._parsed is None:
            return

        escaped = bytearray()
        component_index = 0
        for r in self._parsed.encode("utf-8"):
            escaped.append(r)
            if r != SqEscapedString.START_BYTE:
                continue

            escaped.append(int(self._components[component_index][0]))
            component = bytes(self._components[component_index][1])
            if len(component) + 1 < 0xD0:
                escaped.append(len(component) + 1)
            elif len(component) <= 0xFF:
                escaped.append(0xF0)
                escaped.append(len(component))
            elif len(component) & 0xFF == 0:
                escaped.append(0xF1)
                escaped.append(len(component) >> 8)
            elif len(component) <= 0xFFFF:
                escaped.append(0xF2)
                escaped.append(len(component) >> 8)
                escaped.append(len(component) & 0xFF)
            elif len(component) <= 0xFFFFFF:
                escaped.append(0xFA)
                escaped.append(len(component) >> 16)
                escaped.append((len(component) >> 8) & 0xFF)
                escaped.append(len(component) & 0xFF)
            elif len(component) <= 0xFFFFFFFF:
                escaped.append(0xFE)
                escaped.append(len(component) >> 24)
                escaped.append((len(component) >> 16) & 0xFF)
                escaped.append((len(component) >> 8) & 0xFF)
                escaped.append(len(component) & 0xFF)
            escaped.extend(component)
            escaped.append(SqEscapedString.END_BYTE)
            component_index += 1

        self._escaped = escaped

    def __str__(self):
        self._parse()
        if self._parsed is None:
            return "(None)"
        if not self._components:
            return self._parsed

        res = []
        for i, component in enumerate(self.parsed.split("\x02")):
            res.append(html.unescape(component))
            if i == len(self._components):  # last item
                break

            escape_type, escaped = self._components[i]
            if isinstance(escape_type, SqEscapeType):
                escape_type_name = escape_type.name
            else:
                escape_type_name = f"Unknown_{escape_type:02x}"
                print(escape_type_name)

            if not escaped:
                res.append(f"<{escape_type_name} />")
            else:
                if isinstance(escaped, (bytes, bytearray)):
                    escaped = escaped.hex()
                res.append(f"<{escape_type_name}>{escaped}</{escape_type_name}>")
        return "".join(res)
