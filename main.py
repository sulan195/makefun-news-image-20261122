#!/usr/bin/env python3
"""Entry for make.fun news-image-20261122.

Copies the bundled front-page image (entry.png, 1024x1024, drawn
programmatically for Sunday 22 November 2026) to the harness output
directory. Standard library only; no network; deterministic: both
runs write the same bytes.

Exit codes: 0 ok, 2 entry.png missing, 3 entry.png over the 1 MiB
limit, 4 copy mismatch (should never happen), 5 entry.png is not a
valid 1024x1024 PNG, 6 output directory or file cannot be written.
"""

import hashlib
import os
import shutil
import struct
import sys
import zlib

MAX_BYTES = 1_048_576
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
IEND_TRAILER = b"\x00\x00\x00\x00IEND\xaeB`\x82"
SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")


def sha256_of(path):
    """Return the hex SHA-256 of a file's bytes."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_png(path):
    """Walk the PNG chunks, checking CRCs, and require a 1024x1024 IHDR
    plus an IEND trailer. Return an error string, or None if valid."""
    with open(path, "rb") as handle:
        data = handle.read()
    if data[:8] != PNG_MAGIC:
        return "entry.png is not a valid PNG"
    if data[-12:] != IEND_TRAILER:
        return "entry.png has no IEND trailer (truncated?)"
    pos = 8
    saw_ihdr = saw_idat = False
    while pos < len(data) - 12:
        if pos + 8 > len(data):
            return "entry.png has a truncated chunk header"
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        if pos == 8 and (ctype != b"IHDR" or length != 13):
            return "entry.png does not start with a 13-byte IHDR chunk"
        end = pos + 8 + length + 4
        if end > len(data):
            return "entry.png has a truncated chunk: %r" % ctype
        if ctype != b"IEND" and end > len(data) - 12:
            # No chunk but IEND may reach into the final 12 bytes: those
            # bytes are the IEND trailer itself, so a chunk ending past
            # len(data) - 12 would swallow part of it.
            return "entry.png has a chunk reaching into the IEND trailer: %r" % ctype
        chunk = data[pos + 4:end - 4]
        crc = struct.unpack(">I", data[end - 4:end])[0]
        if zlib.crc32(chunk) & 0xFFFFFFFF != crc:
            return "entry.png has a bad CRC in chunk %r" % ctype
        if ctype == b"IHDR":
            width, height = struct.unpack(">II", data[pos + 8:pos + 16])
            if (width, height) != (1024, 1024):
                return "entry.png is %dx%d, not 1024x1024" % (width, height)
            saw_ihdr = True
        if ctype == b"IDAT":
            saw_idat = True
        if ctype == b"IEND":
            if pos != len(data) - 12:
                return "entry.png has data after the IEND chunk"
            break
        pos = end
    if not saw_ihdr:
        return "entry.png has no IHDR chunk"
    if not saw_idat:
        return "entry.png has no IDAT chunk"
    return None


def main(argv):
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    if not os.path.exists(SOURCE):
        print("entry.png is missing next to main.py", file=sys.stderr)
        return 2
    size = os.path.getsize(SOURCE)
    if size > MAX_BYTES:
        print("entry.png is %d bytes, over the 1 MiB limit" % size,
              file=sys.stderr)
        return 3
    error = validate_png(SOURCE)
    if error is not None:
        print(error, file=sys.stderr)
        return 5
    try:
        os.makedirs(out_dir, exist_ok=True)
        dest = os.path.join(out_dir, "entry.png")
        shutil.copyfile(SOURCE, dest)
        if sha256_of(SOURCE) != sha256_of(dest):
            print("copied bytes differ from entry.png", file=sys.stderr)
            return 4
    except OSError as exc:
        print("cannot write output: %s" % exc, file=sys.stderr)
        return 6
    print("wrote %s (%d bytes)" % (dest, size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
