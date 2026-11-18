"""IMMY — генератор assets/icon.ico (256x256 PNG внутри ICO, только stdlib)."""

import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from immy.icon import PALETTE, grid32


def build_png(scale):
    rows = grid32()
    raw = b""
    for row in rows:
        for _sub in range(scale):
            line = bytearray((0,))
            for ch in row:
                col = PALETTE.get(ch)
                if col is None:
                    line += b"\x00\x00\x00\x00" * scale
                else:
                    line += bytes((int(col[1:3], 16), int(col[3:5], 16),
                                   int(col[5:7], 16), 255)) * scale
            raw += bytes(line)
    ihdr = struct.pack(">IIBBBBB", 32 * scale, 32 * scale, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw, 9)

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat)
            + chunk(b"IEND", b""))


def wrap_ico(png, size):
    ico = struct.pack("<HHH", 0, 1, 1)
    ico += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(png), 22)
    return ico + png


def main():
    png = build_png(8)
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "assets", "icon.ico")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(wrap_ico(png, 256))
    print("written %s (%d bytes)" % (out, 22 + len(png)))


if __name__ == "__main__":
    main()
