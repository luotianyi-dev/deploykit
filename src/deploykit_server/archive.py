import io
import os
import tarfile
from typing import Optional, Sequence, Tuple
from fastapi import UploadFile
from zstandard import ZstdDecompressor


def is_path_safe(path: str, linkname: Optional[str] = None) -> bool:
    if (linkname is not None) and (not is_path_safe(linkname)):
        return False
    if os.path.isabs(path):
        return False
    for char in ["/", "..", os.sep]:
        if path.startswith(char):
            return False
    return True


def safe_filter(members: Sequence[tarfile.TarInfo], destnation: str) -> Sequence[tarfile.TarInfo]:
    result = []
    for member in members:
        if member.ischr() or member.isblk() or member.isfifo() or member.isdev():
            continue
        if not is_path_safe(member.name, getattr(member, "linkname", None)):
            continue
        if member.issym() or member.islnk():
            link_abspath = os.path.abspath(os.path.join(destnation, member.linkname))
            dest_abspath = os.path.abspath(destnation)
            if not link_abspath.startswith(dest_abspath):
                continue

        if member.isdir() or member.issym():
            member.mode = 0o755
        else:
            member.mode = 0o644
        member.gid = member.uid = member.uname = member.gname = None
        result.append(member)
    return result


def decompress(upload: UploadFile, destnation: str) -> Tuple[int, int]:
    zstd_stream = upload.file
    zstd_size = upload.size
    with io.BytesIO() as tar_stream:
        decompressor = ZstdDecompressor()
        decompressor.copy_stream(zstd_stream, tar_stream)
        tar_size = tar_stream.tell()
        tar_stream.seek(0)
        with tarfile.open(fileobj=tar_stream) as tar_file:
            members = tar_file.getmembers()
            members = safe_filter(members, destnation)
            for member in members:
                tar_file.extract(member, destnation)
    return zstd_size, tar_size
