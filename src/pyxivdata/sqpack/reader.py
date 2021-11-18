import contextlib
import ctypes
import functools
import io
import os
import pathlib
import typing
from bisect import bisect_left

from pyxivdata.common import CorruptDataException, SqPathSpec
from pyxivdata.sqpack.entry_decoder import decode_entry
from pyxivdata.sqpack.structures import SqIndexHeader, SqpackHeader, SqIndexPathHashLocator, SqIndexPairHashLocator, \
    SqIndexFullHashLocator, SqIndexDataLocator, SqIndexPairHashWithTextLocator, \
    SqIndexFullHashWithTextLocator


class SqIndexReader(typing.ContextManager):
    _fp1: typing.Union[io.RawIOBase, typing.BinaryIO] = None
    _fp2: typing.Union[io.RawIOBase, typing.BinaryIO] = None

    def __init__(self, index1: typing.Union[str, os.PathLike], index2: typing.Union[str, os.PathLike]):
        self._fp1 = pathlib.Path(index1).open("rb")
        self._fp2 = pathlib.Path(index2).open("rb")
        try:
            self.header1 = SqpackHeader()
            self._fp1.readinto(self.header1)
            if self.header1.header_size != ctypes.sizeof(self.header1):
                raise CorruptDataException(f"1.SqpackHeader.header_size != {ctypes.sizeof(self.header1)}")

            self._fp1.seek(self.header1.header_size)
            self.index1 = SqIndexHeader()
            self._fp1.readinto(self.index1)
            if self.index1.header_size != ctypes.sizeof(self.index1):
                raise CorruptDataException(f"1.SqIndexHeader.header_size != {ctypes.sizeof(self.index1)}")

            self.header2 = SqpackHeader()
            self._fp2.readinto(self.header2)
            if self.header2.header_size != ctypes.sizeof(self.header2):
                raise CorruptDataException(f"2.SqpackHeader.header_size != {ctypes.sizeof(self.header2)}")

            self._fp2.seek(self.header2.header_size)
            self.index2 = SqIndexHeader()
            self._fp2.readinto(self.index2)
            if self.index2.header_size != ctypes.sizeof(self.index2):
                raise CorruptDataException(f"2.SqIndexHeader.header_size != {ctypes.sizeof(self.index2)}")

        except BaseException:
            if self._fp1 is not None:
                self._fp1.close()
            if self._fp2 is not None:
                self._fp2.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fp1.close()
        self._fp2.close()

    @functools.cached_property
    def pair_hash_locators(self) -> typing.Union[ctypes.Array[SqIndexPairHashLocator],
                                                 typing.Sequence[SqIndexPairHashLocator]]:
        self._fp1.seek(self.index1.hash_locator_segment.offset)
        data = self._fp1.read(self.index1.hash_locator_segment.size)
        return (SqIndexPairHashLocator * (len(data) // ctypes.sizeof(SqIndexPairHashLocator))
                ).from_buffer_copy(data)

    @functools.cached_property
    def full_path_hash_locators(self) -> typing.Union[ctypes.Array[SqIndexFullHashLocator],
                                                 typing.Sequence[SqIndexFullHashLocator]]:
        self._fp2.seek(self.index2.hash_locator_segment.offset)
        data = self._fp2.read(self.index2.hash_locator_segment.size)
        return (SqIndexFullHashLocator * (len(data) // ctypes.sizeof(SqIndexFullHashLocator))
                ).from_buffer_copy(data)

    @functools.cached_property
    def pair_hash_with_text_locators(self) -> typing.Union[ctypes.Array[SqIndexPairHashWithTextLocator],
                                                           typing.Sequence[SqIndexPairHashWithTextLocator]]:
        self._fp1.seek(self.index1.text_locator_segment.offset)
        data = self._fp1.read(self.index1.text_locator_segment.size)
        return (SqIndexPairHashWithTextLocator * (len(data) // ctypes.sizeof(SqIndexPairHashWithTextLocator))
                ).from_buffer_copy(data)

    @functools.cached_property
    def full_path_hash_with_text_locators(self) -> typing.Union[ctypes.Array[SqIndexFullHashWithTextLocator],
                                                           typing.Sequence[SqIndexFullHashWithTextLocator]]:
        self._fp2.seek(self.index2.text_locator_segment.offset)
        data = self._fp2.read(self.index2.text_locator_segment.size)
        return (SqIndexFullHashWithTextLocator * (len(data) // ctypes.sizeof(SqIndexFullHashWithTextLocator))
                ).from_buffer_copy(data)

    @functools.cached_property
    def index1_unknown_segment_3(self) -> bytes:
        self._fp1.seek(self.index1.unknown_segment_3.offset)
        return self._fp1.read(self.index1.unknown_segment_3.size)

    @functools.cached_property
    def index2_unknown_segment_3(self) -> bytes:
        self._fp2.seek(self.index1.unknown_segment_3.offset)
        return self._fp2.read(self.index2.unknown_segment_3.size)

    @functools.cached_property
    def path_hash_locators(self) -> typing.Union[ctypes.Array[SqIndexPathHashLocator],
                                                 typing.Sequence[SqIndexPathHashLocator]]:
        self._fp1.seek(self.index1.path_hash_locator_segment.offset)
        data = self._fp1.read(self.index1.path_hash_locator_segment.size)
        return (SqIndexPathHashLocator * (len(data) // ctypes.sizeof(SqIndexPathHashLocator))
                ).from_buffer_copy(data)

    def name_hash_locators(self, path_hash: int) -> typing.Union[ctypes.Array[SqIndexPairHashLocator],
                                                                 typing.Sequence[SqIndexPairHashLocator]]:
        folders = self.path_hash_locators
        i = bisect_left(folders, path_hash, key=lambda x: x.path_hash)
        if i == len(folders):
            raise KeyError(f"Path ~{path_hash:08x} not found")

        folder = folders[i]
        if folder.path_hash != path_hash:
            raise KeyError(f"Path ~{path_hash:08x} not found")

        files1 = self.pair_hash_locators
        if not (self.index1.hash_locator_segment.offset
                <= folder.pair_hash_locator_offset
                < self.index1.hash_locator_segment.offset + self.index1.hash_locator_segment.size):
            raise KeyError(f"Path ~{path_hash:08x} not found (file offset from folder out of range)")

        start_index = ((folder.pair_hash_locator_offset - self.index1.hash_locator_segment.offset)
                       // ctypes.sizeof(SqIndexPairHashLocator))
        to_index = min(len(files1),
                       start_index + folder.pair_hash_locator_size // ctypes.sizeof(SqIndexPairHashLocator))
        return files1[start_index:to_index]


class SqpackFile:
    def __init__(self, path_spec: SqPathSpec, fp: typing.BinaryIO, offset: int, read_size: int):
        self._path_spec = path_spec
        self._fp = fp
        self._offset = offset
        self._read_size = read_size

    @property
    def path_spec(self):
        return self._path_spec

    @functools.cached_property
    def data(self) -> bytearray:
        return decode_entry(self._fp, self._offset, self._read_size)


class SqpackReader:
    index: SqIndexReader
    _fp_data: typing.List[typing.Union[io.RawIOBase, typing.BinaryIO]]

    def __init__(self, index_path: typing.Union[str, os.PathLike]):
        self._cleanup = contextlib.ExitStack()
        index_path = pathlib.Path(index_path)

        self._name = str(index_path.with_suffix("").with_suffix(""))

        try:
            self.index = SqIndexReader(index_path.with_suffix(".index"),
                                       index_path.with_suffix(".index2"))
            self._cleanup.enter_context(self.index)

            self._fp_data = []
            for i in range(self.index.index1.text_locator_segment.count):
                path = pathlib.Path(index_path.with_suffix(f".dat{i}"))
                self._fp_data.append(path.open("rb"))
                self._cleanup.enter_context(self._fp_data[-1])

        except BaseException:
            self._cleanup.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self._cleanup.close()

    def get_locator(self, item: typing.Union[SqPathSpec, str, bytes, os.PathLike]):
        item = SqPathSpec(item)
        if item.has_path_name_hash():
            try:
                files = self.index.name_hash_locators(item.path_hash)
            except KeyError:
                raise KeyError(f"{item} not found in {self._name} (path was not found)") from None

            i = bisect_left(files, item.name_hash, key=lambda x: x.name_hash)
            if i == len(files):
                raise KeyError(f"{item} not found in {self._name} (path was found)")

            file = files[i]
            if file.name_hash != item.name_hash:
                raise KeyError(f"{item} not found in {self._name} (path was found)")

            if file.locator.synonym:
                if not item.has_full_path():
                    raise KeyError(f"{item} found in {self._name}, but is ambiguous")
                
                files = self.index.pair_hash_with_text_locators
                i = bisect_left(files, (item.path_hash, item.name_hash), key=lambda x: (x.path_hash, x.name_hash))
                while (i < len(files)
                       and files[i].path_hash != SqIndexPairHashWithTextLocator.SENTINEL
                       and files[i].name_hash != SqIndexPairHashWithTextLocator.SENTINEL
                       and files[i].conflict_index != SqIndexPairHashWithTextLocator.SENTINEL):
                    file = files[i]
                    full_path = file.full_path
                    if full_path.lower() == item.full_path.lower():
                        break
                else:
                    raise KeyError(f"{item} not found in {self._name} (not in synonym table)")

            return file.locator

        if item.has_full_path_hash():
            files = self.index.full_path_hash_locators
            i = bisect_left(files, item.full_path_hash, key=lambda x: x.full_path_hash)
            if i == len(files):
                raise KeyError(f"{item} not found in {self._name}")

            file = files[i]
            if file.full_path_hash != item.full_path_hash:
                raise KeyError(f"{item} not found in {self._name}")

            if file.locator.synonym:
                if not item.has_full_path():
                    raise KeyError(f"{item} found in {self._name}, but is ambiguous")

                files = self.index.full_path_hash_with_text_locators
                i = bisect_left(files, item.full_path, key=lambda x: x.full_path_hash)
                while (i < len(files)
                       and files[i].full_path_hash != SqIndexPairHashWithTextLocator.SENTINEL
                       and files[i].unused_hash != SqIndexPairHashWithTextLocator.SENTINEL
                       and files[i].conflict_index != SqIndexPairHashWithTextLocator.SENTINEL):
                    file = files[i]
                    full_path = file.full_path
                    if full_path.lower() == item.full_path.lower():
                        break
                else:
                    raise KeyError(f"{item} not found in {self._name} (not in synonym table)")

            return file.locator

        raise KeyError(f"path is empty")

    def get_stored_size(self, locator: SqIndexDataLocator):
        offsets = self._get_data_offsets()[locator.index]
        next_offset = bisect_left(offsets, locator.offset) + 1
        fp = self._fp_data[locator.index]
        if next_offset >= len(offsets):
            fp.seek(0, os.SEEK_END)
            next_offset = fp.tell()
        else:
            next_offset = offsets[next_offset]
        return next_offset - locator.offset

    @functools.cache
    def _get_data_offsets(self):
        res = [[] for _ in range(self.index.index1.text_locator_segment.count)]
        for f in self.index.pair_hash_locators:
            res[f.locator.index].append(f.locator.offset)
        return [sorted(x) for x in res]

    def __getitem__(self, item: typing.Union[SqPathSpec, str, bytes, os.PathLike]):
        item = SqPathSpec(item)

        if item.has_full_path() and item.full_path[-1] == '/':
            result = []
            for f in self.index.name_hash_locators(item.path_hash):
                if not f.locator.synonym:
                    result.append(SqpackFile(SqPathSpec(path_hash=f.path_hash, name_hash=f.name_hash),
                                             self._fp_data[f.locator.index], f.locator.offset,
                                             self.get_stored_size(f.locator)))
            for f in self.index.pair_hash_with_text_locators:
                if f.name_hash == f.SENTINEL and f.path_hash == f.SENTINEL and f.conflict_index == f.SENTINEL:
                    break
                path_spec = f.path_spec
                if path_spec.full_path.lower().startswith(item.full_path):
                    result.append(SqpackFile(path_spec,
                                             self._fp_data[f.locator.index], f.locator.offset,
                                             self.get_stored_size(f.locator)))
            return result

        locator = self.get_locator(item)
        return SqpackFile(item, self._fp_data[locator.index], locator.offset, self.get_stored_size(locator))
