# Shared test data for the integration tests.

import struct
import zlib

import pytest


@pytest.fixture
def red_blue_png():
    # 256 x 128 picture: left half red, right half blue
    width, height = 256, 128
    row = b"\x00" + b"".join(b"\xff\x00\x00" if x < width // 2 else b"\x00\x00\xff"
                             for x in range(width))

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(row * height)) + chunk(b"IEND", b""))
