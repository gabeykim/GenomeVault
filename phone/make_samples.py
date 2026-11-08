#!/usr/bin/env python3
"""Synthetic pharmacy-label PNGs for the S2 photo beat (I1: every name and line here is made up).

Each label is flat black-on-white printed text, so a camera, tesseract or A's local VLM can read it like a
real label, AND it carries the same text as an iTXt chunk with keyword `gv:label` (A's capture.py embedded
format), so the demo reads it with no model at all. One shared set: A tests capture.from_image against it.

    python phone/make_samples.py              # writes phone/samples/*.png and phone/samples/labels.json
Pure stdlib (zlib, struct): no imaging dependency.
"""
import json
import struct
import sys
import zlib

# label file -> exact label text (A-014 gave the amoxicillin wording; the warning line is dropped by A-013)
LABELS = {
    "aspirin.png": "ASPIRIN 81 MG TABLET\nLow-dose aspirin\nTAKE 1 TABLET BY MOUTH DAILY",
    "clopidogrel.png": "CLOPIDOGREL 75 MG TABLET\nGeneric for: PLAVIX\nTake 1 tablet by mouth daily",
    "omeprazole.png": "OMEPRAZOLE 20 MG CAPSULE\nGeneric for: PRILOSEC\nTAKE 1 CAPSULE BY MOUTH DAILY BEFORE BREAKFAST",
    "simvastatin.png": "SIMVASTATIN 40 MG TABLET\nGeneric for: ZOCOR\nTAKE 1 TABLET BY MOUTH AT BEDTIME",
    "lisinopril.png": "LISINOPRIL 10 MG TABLET\nGeneric for: ZESTRIL\nTAKE 1 TABLET BY MOUTH DAILY",
    "amoxicillin.png": ("AMOXICILLIN 500 MG CAPSULE\nGeneric for: AMOXIL\nTAKE 1 CAPSULE BY MOUTH THREE TIMES DAILY\n"
                        "Do not take if you are allergic to penicillin."),
    "ibuprofen.png": "IBUPROFEN 200 MG TABLET\nPain reliever / fever reducer",
}

# 5x7 pixel font, uppercase + digits + punctuation (lowercase is drawn uppercase)
F = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01111 10000 10000 10000 10000 10000 01111", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01111 10000 10000 10011 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "11111 00100 00100 00100 00100 00100 11111", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000", ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000", ":": "00000 01100 01100 00000 01100 01100 00000",
    "-": "00000 00000 00000 11111 00000 00000 00000", "/": "00001 00010 00010 00100 01000 01000 10000",
    "(": "00010 00100 01000 01000 01000 00100 00010", ")": "01000 00100 00010 00010 00010 00100 01000",
    "'": "00100 00100 01000 00000 00000 00000 00000",
}
WHITE, INK, BLUE, GRAY = (255, 255, 255), (2, 7, 10), (2, 151, 222), (120, 128, 134)
W, SCALE, MARGIN, WRAP = 960, 3, 36, 46


def wrap(line: str) -> list[str]:
    out, cur = [], ""
    for word in line.split(" "):
        if len(cur) + len(word) + 1 > WRAP and cur:
            out.append(cur); cur = word
        else:
            cur = f"{cur} {word}".strip()
    return out + ([cur] if cur else [])


def render(text: str) -> list[list[tuple]]:
    header = "DEMO PHARMACY   RX FOR: ALEX (SYNTHETIC)"
    body = [l for raw in text.split("\n") for l in wrap(raw)]
    line_h = 7 * SCALE + 14
    h = MARGIN + 48 + 18 + len(body) * line_h + 22 + MARGIN
    px = [[WHITE] * W for _ in range(h)]

    def rect(x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(h, y1)):
            row = px[y]
            for x in range(max(0, x0), min(W, x1)):
                row[x] = c

    def text_at(x, y, s, color, scale):
        for ch in s.upper():
            glyph = F.get(ch, F[" "]).split()
            for gy, bits in enumerate(glyph):
                for gx, b in enumerate(bits):
                    if b == "1":
                        rect(x + gx * scale, y + gy * scale, x + (gx + 1) * scale, y + (gy + 1) * scale, color)
            x += 6 * scale

    rect(0, 0, W, 8, BLUE)                                     # brand stripe
    rect(MARGIN, MARGIN, W - MARGIN, MARGIN + 48, INK)         # header band
    text_at(MARGIN + 14, MARGIN + 13, header, WHITE, 3)
    y = MARGIN + 48 + 18
    for i, line in enumerate(body):
        text_at(MARGIN, y, line, INK if i == 0 or not line.lower().startswith("do not") else GRAY, 4 if i == 0 else SCALE)
        y += line_h + (8 if i == 0 else 0)
    rect(MARGIN, h - MARGIN - 6, W - MARGIN, h - MARGIN, BLUE)  # bottom rule
    return px


def png(px, text: str) -> bytes:
    h, w = len(px), len(px[0])
    raw = b"".join(b"\x00" + bytes(c for p in row for c in p) for row in px)

    def chunk(t, body):
        return struct.pack(">I", len(body)) + t + body + struct.pack(">I", zlib.crc32(t + body))
    itxt = b"gv:label" + b"\x00\x00\x00\x00\x00" + text.encode()
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"iTXt", itxt) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "phone/samples"
    for name, text in LABELS.items():
        open(f"{out}/{name}", "wb").write(png(render(text), text))
    json.dump({n: t for n, t in LABELS.items()}, open(f"{out}/labels.json", "w"), indent=2)
    print(f"wrote {len(LABELS)} labels to {out}")
