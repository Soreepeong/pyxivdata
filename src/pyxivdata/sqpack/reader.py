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
from pyxivdata.sqpack.structures import SqIndexHeader, SqpackHeader, SqIndexFolderSegmentEntry, SqIndexFileSegmentEntry, \
    SqIndex2FileSegmentEntry, SqIndexType


class SqIndexReader(typing.ContextManager):
    _fp: typing.Union[io.RawIOBase, typing.BinaryIO]

    def __init__(self, path: typing.Union[str, os.PathLike]):
        self._fp = pathlib.Path(path).open("rb")
        try:
            self.sqpack_header = SqpackHeader()
            self._fp.readinto(self.sqpack_header)
            if self.sqpack_header.header_size != ctypes.sizeof(self.sqpack_header):
                raise CorruptDataException(f"SqpackHeader.header_size != {ctypes.sizeof(self.sqpack_header)}")

            self.sqindex_header = SqIndexHeader()
            self._fp.readinto(self.sqindex_header)
            if self.sqindex_header.header_size != ctypes.sizeof(self.sqindex_header):
                raise CorruptDataException(f"SqIndexHeader.header_size != {ctypes.sizeof(self.sqindex_header)}")
        except BaseException:
            self._fp.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._fp.close()

    @functools.cached_property
    def files1(self) -> typing.Union[ctypes.Array[SqIndexFileSegmentEntry],
                                     typing.Sequence[SqIndexFileSegmentEntry]]:
        if self.sqindex_header.index_type != SqIndexType.Index:
            raise KeyError("Not a .index file")
        self._fp.seek(self.sqindex_header.file_segment.offset)
        data = self._fp.read(self.sqindex_header.file_segment.size)
        return (SqIndexFileSegmentEntry * (len(data) // ctypes.sizeof(SqIndexFileSegmentEntry))
                ).from_buffer_copy(data)

    @functools.cached_property
    def files2(self) -> typing.Union[ctypes.Array[SqIndex2FileSegmentEntry],
                                     typing.Sequence[SqIndex2FileSegmentEntry]]:
        if self.sqindex_header.index_type != SqIndexType.Index2:
            raise KeyError("Not a .index2 file")
        self._fp.seek(self.sqindex_header.file_segment.offset)
        data = self._fp.read(self.sqindex_header.file_segment.size)
        return (SqIndex2FileSegmentEntry * (len(data) // ctypes.sizeof(SqIndex2FileSegmentEntry))
                ).from_buffer_copy(data)

    @functools.cached_property
    def data_files_segment(self) -> bytes:
        self._fp.seek(self.sqindex_header.data_files_segment.offset)
        return self._fp.read(self.sqindex_header.data_files_segment.size)

    @functools.cached_property
    def unknown_segment_3(self) -> bytes:
        self._fp.seek(self.sqindex_header.unknown_segment_3.offset)
        return self._fp.read(self.sqindex_header.unknown_segment_3.size)

    @functools.cached_property
    def folders(self) -> typing.Union[ctypes.Array[SqIndexFolderSegmentEntry],
                                      typing.Sequence[SqIndexFolderSegmentEntry]]:
        self._fp.seek(self.sqindex_header.folder_segment.offset)
        data = self._fp.read(self.sqindex_header.folder_segment.size)
        return (SqIndexFolderSegmentEntry * (len(data) // ctypes.sizeof(SqIndexFolderSegmentEntry))
                ).from_buffer_copy(data)


class SqpackReader:
    index1: SqIndexReader
    index2: SqIndexReader
    _fp_data: typing.List[typing.Union[io.RawIOBase, typing.BinaryIO]]

    def __init__(self, index_path: typing.Union[str, os.PathLike]):
        self._cleanup = contextlib.ExitStack()
        index_path = pathlib.Path(index_path)

        self._name = str(index_path.with_suffix("").with_suffix(""))

        try:
            self.index1 = SqIndexReader(index_path)
            self._cleanup.enter_context(self.index1)

            self.index2 = SqIndexReader(index_path.with_suffix(".index2"))
            self._cleanup.enter_context(self.index2)

            self._fp_data = []
            for i in range(self.index1.sqindex_header.data_files_segment.count):
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
            folders = self.index1.folders
            i = bisect_left(folders, item.path_hash, key=lambda x: x.path_hash)
            if i == len(folders):
                raise KeyError(f"{item} not found in {self._name}")

            folder = folders[i]
            if folder.path_hash != item.path_hash:
                raise KeyError(f"{item} not found in {self._name}")

            files1 = self.index1.files1
            if not (self.index1.sqindex_header.file_segment.offset
                    <= folder.file_segment_offset
                    < self.index1.sqindex_header.file_segment.offset + self.index1.sqindex_header.file_segment.size):
                raise KeyError(f"{item} not found in {self._name} (file offset from folder out of range)")

            start_index = ((folder.file_segment_offset - self.index1.sqindex_header.file_segment.offset)
                           // ctypes.sizeof(SqIndexFileSegmentEntry))
            to_index = min(len(files1),
                           start_index + folder.file_segment_size // ctypes.sizeof(SqIndexFileSegmentEntry))
            files1 = files1[start_index:to_index]
            i = bisect_left(files1, item.name_hash, key=lambda x: x.name_hash)
            if i == len(files1):
                raise KeyError(f"{item} not found in {self._name} (folder was found)")

            file = files1[i]
            if file.name_hash != item.name_hash:
                raise KeyError(f"{item} not found in {self._name} (folder was found)")
            return file.locator

        if item.has_full_path_hash():
            files2 = self.index2.files2
            i = bisect_left(files2, item.full_path_hash, key=lambda x: x.full_path_hash)
            if i == len(files2):
                raise KeyError(f"{item} not found in {self._name}")

            file = files2[i]
            if file.full_path_hash != item.full_path_hash:
                raise KeyError(f"{item} not found in {self._name}")
            return file.locator

        raise KeyError(f"path is empty")

    @functools.cache
    def _get_data_offsets(self):
        res = [[] for _ in range(self.index1.sqindex_header.data_files_segment.count)]
        for f in self.index1.files1:
            res[f.locator.index].append(f.locator.offset)
        return [sorted(x) for x in res]

    def __getitem__(self, item: typing.Union[SqPathSpec, str, bytes, os.PathLike]):
        locator = self.get_locator(item)
        offsets = self._get_data_offsets()[locator.index]
        next_offset = bisect_left(offsets, locator.offset) + 1
        fp = self._fp_data[locator.index]
        if next_offset >= len(offsets):
            fp.seek(0, os.SEEK_END)
            next_offset = fp.tell()
        else:
            next_offset = offsets[next_offset]
        return decode_entry(self._fp_data[locator.index], locator.offset, next_offset - locator.offset)
