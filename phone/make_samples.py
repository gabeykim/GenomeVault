#!/usr/bin/env python3
"""Draw small pharmacy-label PNGs in the GenomeVault palette, carrying the label text as an iTXt chunk with
keyword gv:label (A's capture.py embedded-text format). Pure stdlib. Synthetic text only (I1)."""
import struct, sys, zlib

W, H = 160, 104
MID, RAISED, WHITE, BLUE, MELON, LINE = (2, 7, 10), (11, 22, 29), (242, 237, 228), (2, 151, 222), (252, 115, 77), (190, 186, 178)

def draw(accent, lines):
    px = [[MID] * W for _ in range(H)]
    def rect(x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(H, y1)):
            for x in range(max(0, x0), min(W, x1)):
                px[y][x] = c
    rect(8, 8, W - 8, H - 8, WHITE)            # the label card
    rect(8, 8, W - 8, 26, BLUE)                # pharmacy header band
    rect(14, 13, 34, 21, WHITE)                # "Rx" block in the header
    rect(14, 34, 22, 42, accent)               # Rx / OTC tag
    for i, w in enumerate(lines):              # "printed" text lines
        rect(28 if i == 0 else 14, 35 + i * 11, 28 + w if i == 0 else 14 + w, 40 + i * 11, MID if i == 0 else LINE)
    rect(14, H - 22, W - 14, H - 19, accent)   # bottom stripe
    return px

def png(px, text):
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)
    def chunk(t, body): return struct.pack(">I", len(body)) + t + body + struct.pack(">I", zlib.crc32(t + body))
    itxt = b"gv:label" + b"\x00\x00\x00\x00\x00" + text.encode()
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
            + chunk(b"iTXt", itxt) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

out = sys.argv[1] if len(sys.argv) > 1 else "phone/samples"   # usage: python phone/make_samples.py
open(f"{out}/clopidogrel.png", "wb").write(png(draw(MELON, [96, 120, 80, 104]),
     "CLOPIDOGREL 75 MG TABLET\nGeneric for: PLAVIX\nTake 1 tablet by mouth daily"))
open(f"{out}/ibuprofen.png", "wb").write(png(draw(BLUE, [84, 112, 96, 64]),
     "IBUPROFEN 200 MG TABLET\nPain reliever / fever reducer"))
