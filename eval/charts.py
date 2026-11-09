"""Dependency-free SVG charts for docs/ and slides/ (no matplotlib in requirements.txt).

Design rules (dataviz method): one y-axis per chart (never dual), fixed categorical order (blue, orange, aqua),
bars <= 24px with 4px rounded data-end and square baseline, 2px gaps between touching bars, 2px lines with
>= 8px ringed markers, hairline recessive grid, text in text tokens (never series color), legend for >= 2 series,
native <title> hover on every mark, light and dark themes from the same hues. Every chart also has a table
view in docs/results.md.
"""
from __future__ import annotations

from html import escape

SERIES = ["--s1", "--s2", "--s3"]
STYLE = """<style>
svg{--surface:#fcfcfb;--grid:#e6e5e1;--axis:#c3c2b7;--t1:#0b0b0b;--t2:#52514e;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--ref:#52514e}
@media (prefers-color-scheme: dark){svg{--surface:#1a1a19;--grid:#2e2e2c;--axis:#52514e;--t1:#f0efec;--t2:#c3c2b7;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--ref:#c3c2b7}}
text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;fill:var(--t2);font-size:12px}
.title{fill:var(--t1);font-size:16px;font-weight:600}.sub{font-size:12px}.val{fill:var(--t1);font-size:10px;letter-spacing:-0.3px}
</style>"""

W, H = 760, 400
L, R, T, B = 64, 24, 72, 64


def _fmt(v: float, pct: bool) -> str:
    if pct:
        return f"{v * 100:.0f}%"
    return f"{v:.0f}" if abs(v) >= 10 or v == int(v) else f"{v:.1f}"


def _bar_path(x: float, y0: float, w: float, h: float, r: float = 4) -> str:
    """Bar growing up from baseline y0 with rounded top corners only."""
    if h <= 0:
        return ""
    r = min(r, w / 2, h)
    top = y0 - h
    return (f"M{x:.1f},{y0:.1f}V{top + r:.1f}Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f}"
            f"H{x + w - r:.1f}Q{x + w:.1f},{top:.1f} {x + w:.1f},{top + r:.1f}V{y0:.1f}Z")


def _frame(title: str, subtitle: str, height: int = H) -> list[str]:
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" width="{W}" height="{height}" role="img" aria-label="{escape(title)}">',
            f"<title>{escape(title)}</title>", STYLE,
            f'<rect width="{W}" height="{height}" fill="var(--surface)"/>',
            f'<text class="title" x="{L}" y="28">{escape(title)}</text>',
            f'<text class="sub" x="{L}" y="48">{escape(subtitle)}</text>']


def _y_axis(out: list[str], y_max: float, pct: bool, top: float, bottom: float, ticks: int = 4) -> None:
    for i in range(ticks + 1):
        v = y_max * i / ticks
        y = bottom - (bottom - top) * i / ticks
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="{"var(--axis)" if i == 0 else "var(--grid)"}" stroke-width="1"/>')
        out.append(f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end">{_fmt(v, pct)}</text>')


def _legend(out: list[str], names: list[str], y: float, ref_label: str | None = None) -> None:
    x = L
    for i, n in enumerate(names):
        out.append(f'<rect x="{x}" y="{y - 9}" width="10" height="10" rx="2" fill="var({SERIES[i]})"/>')
        out.append(f'<text x="{x + 16}" y="{y}">{escape(n)}</text>')
        x += 24 + 7.2 * len(n)
    if ref_label:
        out.append(f'<line x1="{x}" x2="{x + 18}" y1="{y - 4}" y2="{y - 4}" stroke="var(--ref)" stroke-width="1.5" stroke-dasharray="6 4"/>')
        out.append(f'<text x="{x + 24}" y="{y}">{escape(ref_label)}</text>')


def grouped_bars(title: str, subtitle: str, categories: list[str], series: list[tuple[str, list[float | None]]],
                 y_max: float | None = None, pct: bool = False, ref: tuple[float, str] | None = None,
                 value_labels: bool = True) -> str:
    assert 1 <= len(series) <= 3, "fold extra series into another chart; never cycle hues"
    vals = [v for _, vs in series for v in vs if v is not None]
    y_max = y_max or (max(vals + [ref[0] if ref else 0]) * 1.15 or 1)
    out = _frame(title, subtitle)
    top, bottom = T + (16 if len(series) > 1 or ref else 0), H - B
    _y_axis(out, y_max, pct, top, bottom)
    band = (W - L - R) / len(categories)
    bw = min(24, (band * 0.7 - 2 * (len(series) - 1)) / len(series))
    group = bw * len(series) + 2 * (len(series) - 1)
    for ci, cat in enumerate(categories):
        x0 = L + band * ci + (band - group) / 2
        for si, (name, vs) in enumerate(series):
            v = vs[ci]
            x = x0 + si * (bw + 2)
            if v is None:
                out.append(f'<text x="{x + bw / 2:.1f}" y="{bottom - 4}" text-anchor="middle" class="val">n/a</text>')
                continue
            h = (bottom - top) * min(v, y_max) / y_max
            out.append(f'<path d="{_bar_path(x, bottom, bw, h)}" fill="var({SERIES[si]})"><title>{escape(cat)} · {escape(name)}: {_fmt(v, pct)}</title></path>')
            if value_labels:
                out.append(f'<text class="val" x="{x + bw / 2:.1f}" y="{bottom - h - 6:.1f}" text-anchor="middle">{_fmt(v, pct)}</text>')
        lines = cat.split("\n")
        for li, line in enumerate(lines):
            out.append(f'<text x="{L + band * ci + band / 2:.1f}" y="{bottom + 18 + 14 * li}" text-anchor="middle">{escape(line)}</text>')
    if ref:
        y = bottom - (bottom - top) * ref[0] / y_max
        out.append(f'<line x1="{L}" x2="{W - R}" y1="{y:.1f}" y2="{y:.1f}" stroke="var(--ref)" stroke-width="1.5" stroke-dasharray="6 4"><title>{escape(ref[1])}: {_fmt(ref[0], pct)}</title></line>')
    if len(series) > 1 or ref:
        _legend(out, [n for n, _ in series] if len(series) > 1 else [], T - 2, ref[1] if ref else None)
    out.append("</svg>")
    return "\n".join(out)


def line_chart(title: str, subtitle: str, x_labels: list[str], series: list[tuple[str, list[float]]],
               y_max: float = 1.0, pct: bool = True) -> str:
    assert 1 <= len(series) <= 3
    out = _frame(title, subtitle)
    top, bottom = T + (16 if len(series) > 1 else 0), H - B
    _y_axis(out, y_max, pct, top, bottom)
    n = len(x_labels)
    xs = [L + 12 + (W - L - R - 24) * i / max(n - 1, 1) for i in range(n)]
    for i, lab in enumerate(x_labels):
        if n <= 12 or i % 2 == 0 or i == n - 1:
            out.append(f'<text x="{xs[i]:.1f}" y="{bottom + 18}" text-anchor="middle">{escape(lab)}</text>')
    for si, (name, vs) in enumerate(series):
        pts = [(xs[i], bottom - (bottom - top) * min(v, y_max) / y_max) for i, v in enumerate(vs)]
        d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        out.append(f'<path d="{d}" fill="none" stroke="var({SERIES[si]})" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        for i, (x, y) in enumerate(pts):
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="var({SERIES[si]})" stroke="var(--surface)" stroke-width="2">'
                       f'<title>{escape(x_labels[i])} · {escape(name)}: {_fmt(vs[i], pct)}</title></circle>')
        x, y = pts[-1]
        out.append(f'<text class="val" x="{x:.1f}" y="{y - 10:.1f}" text-anchor="end">{_fmt(vs[-1], pct)}</text>')
    if len(series) > 1:
        _legend(out, [n for n, _ in series], T - 2)
    out.append("</svg>")
    return "\n".join(out)


def stacked_panels(svgs: list[str]) -> str:
    """Small multiples: panels sharing an x-axis, each with its own single y-axis (instead of a dual-axis chart)."""
    bodies = []
    for i, s in enumerate(svgs):
        inner = s.split(">", 1)[1].rsplit("</svg>", 1)[0]
        bodies.append(f'<g transform="translate(0,{i * H})">{inner}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H * len(svgs)}" width="{W}" height="{H * len(svgs)}">'
            + "".join(bodies) + "</svg>")
