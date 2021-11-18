import ctypes
import typing

from pyxivdata.installation.resource_reader import GameResourceReader


class SklbHeader0031(ctypes.LittleEndianStructure):
    _pack_ = 2
    _fields_ = (
        ("signature", ctypes.c_byte * 4),
        ("version", ctypes.c_uint32),
        ("offset_1", ctypes.c_uint32),
        ("hkx_offset", ctypes.c_uint32),
        ("unknown_0x10", ctypes.c_uint32),
        ("skeleton_id", ctypes.c_uint32),
        ("skeleton_ids", ctypes.c_uint32 * 4),
    )

    SIGNATURE = b'blks'
    VERSION = 0x31333030

    signature: bytearray
    version: int
    offset_1: int
    hkx_offset: int
    unknown_0x10: int
    skeleton_id: int
    skeleton_ids: typing.Union[ctypes.Array[ctypes.c_uint32], typing.Sequence[ctypes.c_uint32]]


class PapHeader(ctypes.LittleEndianStructure):
    _pack_ = 2
    _fields_ = (
        ("signature", ctypes.c_byte * 4),
        ("version", ctypes.c_uint32),
        ("animation_count", ctypes.c_uint16),
        ("skeleton_id", ctypes.c_uint32),
        ("info_offset", ctypes.c_uint32),
        ("hkx_offset", ctypes.c_uint32),
        ("timeline_offset", ctypes.c_uint32),
    )

    SIGNATURE = b'pap '
    VERSION = 0x00020001

    signature: bytearray
    version: int
    animation_count: int
    skeleton_id: int
    info_offset: int
    hkx_offset: int
    timeline_offset: int


class PapAnimationInfo(ctypes.LittleEndianStructure):
    _fields_ = (
        ("_name", ctypes.c_char * 0x20),
        ("unknown_0x020", ctypes.c_uint16),
        ("havok_index", ctypes.c_uint16),
        ("unknown_0x024", ctypes.c_uint16),
    )

    _name: bytearray
    unknown_0x020: int
    havok_index: int
    unknown_0x024: int

    @property
    def name(self):
        return self._name.decode("utf-8")

    @name.setter
    def name(self, value: str):
        self._name = bytearray(value.encode("utf-8"))


class PapTimelineElementHeader(ctypes.LittleEndianStructure):
    _pack_ = 2
    _fields_ = (
        ("signature", ctypes.c_char * 4),
        ("size", ctypes.c_uint32),
    )

    signature: bytearray
    size: int

    def __str__(self):
        return f"{self.signature.decode('utf-8')}(size={self.size})"

    def __repr__(self):
        return self.__str__()


class PapTimelineBlockHeader(PapTimelineElementHeader):
    _pack_ = 2
    _fields_ = (
        ("count", ctypes.c_uint32),
    )

    SIGNATURE = b'TMLB'

    signature: bytearray
    size: int
    count: int


class PapTimelineAC(PapTimelineElementHeader):
    _fields_ = (
        ("index", ctypes.c_uint8),
        ("unknown_0x009", ctypes.c_uint8),
        ("unknown_0x00a", ctypes.c_uint8),
        ("unknown_0x00b", ctypes.c_uint8),
        ("unknown_0x00c", ctypes.c_uint32),
        ("unknown_0x010", ctypes.c_uint32),
        ("unknown_0x014", ctypes.c_uint32),
        ("tmtr_count", ctypes.c_uint32),
    )

    SIGNATURE = b'TMAC'

    index: int
    unknown_0x009: int
    unknown_0x00a: int
    unknown_0x00b: int
    unknown_0x00c: int
    unknown_0x010: int
    unknown_0x014: int
    tmtr_count: int  # Track? Translation? Tolerance?

    def __str__(self):
        return (f"{self.signature.decode('utf-8')}({self.index}:{self.size}, {self.unknown_0x009}, "
                f"{self.unknown_0x00a}, {self.unknown_0x00b}, {self.unknown_0x00c}, {self.unknown_0x010}, "
                f"{self.unknown_0x014}, {self.tmtr_count})")


class PapTimelineDH(PapTimelineElementHeader):
    _fields_ = (
        ("index", ctypes.c_uint8),
        ("unknown_0x009", ctypes.c_uint8),
        ("unknown_0x00a", ctypes.c_uint8),
        ("unknown_0x00b", ctypes.c_uint8),
        ("unknown_0x00c", ctypes.c_uint16),
        ("unknown_0x00e", ctypes.c_uint16),
    )

    SIGNATURE = b'TMDH'

    index: int
    unknown_0x009: int
    unknown_0x00a: int
    unknown_0x00b: int
    unknown_0x00c: int
    unknown_0x00e: int

    def __str__(self):
        return (f"{self.signature.decode('utf-8')}({self.index}:{self.size}, {self.unknown_0x009}, "
                f"{self.unknown_0x00a}, {self.unknown_0x00b}, {self.unknown_0x00c}, {self.unknown_0x00e})")


class PapTimelineAL(PapTimelineElementHeader):
    _fields_ = (
        ("index", ctypes.c_uint8),
        ("unknown_0x009", ctypes.c_uint8),
        ("unknown_0x00a", ctypes.c_uint8),
        ("unknown_0x00b", ctypes.c_uint8),
        ("unknown_0x00c", ctypes.c_uint32),
    )

    SIGNATURE = b'TMAL'

    index: int
    unknown_0x009: int
    unknown_0x00a: int
    unknown_0x00b: int
    unknown_0x00c: int

    def __str__(self):
        return (f"{self.signature.decode('utf-8')}({self.index}:{self.size}, {self.unknown_0x009}, "
                f"{self.unknown_0x00a}, {self.unknown_0x00b}, {self.unknown_0x00c})")


class PapTimelineBlock:
    def __init__(self, data: bytearray, offset: int):
        self.header = PapTimelineBlockHeader.from_buffer(data, offset)
        if self.header.signature != PapTimelineBlockHeader.SIGNATURE:
            raise RuntimeError

        self.elements = []
        ptr = offset + ctypes.sizeof(self.header)
        for _ in range(self.header.count):
            eh = PapTimelineElementHeader.from_buffer(data, ptr)
            if eh.signature == PapTimelineAC.SIGNATURE:
                eh = PapTimelineAC.from_buffer(data, ptr)
            elif eh.signature == PapTimelineDH.SIGNATURE:
                eh = PapTimelineDH.from_buffer(data, ptr)
            elif eh.signature == PapTimelineAL.SIGNATURE:
                eh = PapTimelineAL.from_buffer(data, ptr)
            self.elements.append((eh, data[ptr + ctypes.sizeof(eh):ptr + eh.size]))
            ptr += self.elements[-1][0].size

        self.rest = data[ptr:offset + self.header.size]


def __main__():
    with open("z:/m0489.skl.hkx", "rb") as fp:
        assert fp.read(8) == b'\x1e\x0d\xb0\xca\xce\xfa\x11\xd0'
        while True:
            cmd = fp.read(1)[0]
            if cmd == 2:
                version = fp.read(1)[0]
            elif cmd == 4:
                len2 = fp.read(1)[0] // 2
                kwd = fp.read(len2)
                print(kwd)
            else:
                breakpoint()
    with GameResourceReader() as game:
        sklb_data = game["chara/monster/m0489/skeleton/base/b0001/skl_m0489b0001.sklb"].data
        sklb_header = SklbHeader0031.from_buffer(sklb_data, 0)
        sklb_alph = sklb_data[sklb_header.offset_1:sklb_header.hkx_offset]
        sklb_hkx = sklb_data[sklb_header.hkx_offset:]
        open("z:/m0489.skl.alph", "wb").write(sklb_alph)
        open("z:/m0489.skl.hkx", "wb").write(sklb_hkx)

        # pap_data = game["chara/monster/m0489/animation/a0001/bt_common/loop_sp/"][0].data
        pap_data = game["chara/monster/m0489/animation/a0001/bt_common/resident/monster.pap"].data
        pap_header = PapHeader.from_buffer(pap_data, 0)
        pap_info = (PapAnimationInfo * pap_header.animation_count).from_buffer(pap_data, pap_header.info_offset)
        pap_hkx = pap_data[pap_header.hkx_offset:pap_header.timeline_offset]
        pap_timeline = pap_data[pap_header.timeline_offset:]
        open("z:/m0489.pap.hkx", "wb").write(pap_hkx)
        open("z:/m0489.pap.timeline", "wb").write(pap_timeline)

        ptr = 0
        blocks = []
        while ptr < len(pap_timeline):
            blocks.append(PapTimelineBlock(pap_timeline, ptr))
            ptr += (blocks[-1].header.size + 3) // 4 * 4

        pass


if __name__ == "__main__":
    exit(__main__())
