#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["fonttools", "skia-pathops", "uharfbuzz"]
# ///
"""Generate the animated SVGs the profile README embeds."""

import io
import urllib.parse
import urllib.request
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"
FONT_CACHE = ROOT / ".fonts"
FONT_SOURCE = "https://raw.githubusercontent.com/google/fonts/5bd87dfc525c8a0d1d8529d3684716e00c3fc59a/ofl"
MONTSERRAT = "montserrat/Montserrat[wght].ttf"
MERRIWEATHER_ITALIC = "merriweather/Merriweather-Italic[opsz,wdth,wght].ttf"
INTER = "inter/Inter[opsz,wght].ttf"
JETBRAINS_MONO = "jetbrainsmono/JetBrainsMono[wght].ttf"
LATO_BOLD = "lato/Lato-Bold.ttf"
WAWARDEN_WORDMARK = (ROOT / "brand" / "wawarden-wordmark.path").read_text().strip()

W = 840
PAD = 32

SITE = {"navy": "#000080", "gold": "#C5B358", "slate": "#708090"}
SITE_HEADING = {"light": "#000080", "dark": "#DBE5FF"}
STACKORDER = {
    "light": {
        "bg": "#F4F1DE", "edge": "#D5D5C7", "ink": "#2F3E46", "on_ink": "#F4F1DE",
        "accent": "#A4472F", "muted": "#626D6F", "line": "#B7BAB0",
    },
    "dark": {
        "bg": "#1A2930", "edge": "#2F3E46", "ink": "#F4F1DE", "on_ink": "#1A2930",
        "accent": "#F2A28A", "muted": "#B7BAB0", "line": "#48555A",
    },
}
WAWARDEN = {
    "light": {
        "bg": "#FFFFFF", "edge": "#DDE3E7", "ink": "#111B21", "muted": "#4A5A64",
        "line": "#DDE3E7", "stop": "#667781",
    },
    "dark": {
        "bg": "#111B21", "edge": "#2A3942", "ink": "#FFFFFF", "muted": "#AEBAC1",
        "line": "#2A3942", "stop": "#AEBAC1",
    },
}
WAWARDEN_GREEN = "#25D366"
WAWARDEN_INK = "#111B21"
CLAUDE = {
    "light": {
        "bg": "#FAF9F5", "edge": "#E8E6DC", "ink": "#141413", "muted": "#6B6A63",
        "line": "#D1CFC5", "orange": "#D97757", "orange_text": "#B5502F",
    },
    "dark": {
        "bg": "#1F1E1D", "edge": "#3D3D3A", "ink": "#FAF9F5", "muted": "#B0AEA5",
        "line": "#52514C", "orange": "#D97757", "orange_text": "#E38B6D",
    },
}
ACROSS = {
    "light": {
        "bg": "#F4F8F7", "edge": "#E3E8E6", "ink": "#1A1C1B", "muted": "#5C6A66",
        "brand": "#0E7C66",
    },
    "dark": {
        "bg": "#0B1727", "edge": "#1F3149", "ink": "#F2F5F7", "muted": "#9FB0BF",
        "brand": "#5FD3A6",
    },
}
ACROSS_TILE = "#232F3E"
ACROSS_ORANGE = "#FF9900"


def font_file(name: str) -> Path:
    path = FONT_CACHE / name.split("/")[-1]
    if not path.exists():
        FONT_CACHE.mkdir(exist_ok=True)
        urllib.request.urlretrieve(f"{FONT_SOURCE}/{urllib.parse.quote(name)}", path)
    return path


class Face:
    def __init__(self, name: str, **axes: float) -> None:
        self.font = TTFont(font_file(name))
        if axes:
            self.font = instancer.instantiateVariableFont(
                self.font, axes, overlap=instancer.OverlapMode.REMOVE
            )
        buf = io.BytesIO()
        self.font.save(buf)
        self.hb = hb.Font(hb.Face(buf.getvalue()))
        self.upm = self.font["head"].unitsPerEm
        self.glyphs = self.font.getGlyphSet()

    def outlines(
        self, text: str, size: float, x: float, y: float, tracking: float = 0
    ) -> tuple[list[str], float]:
        scale = size / self.upm
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf)
        paths, cursor = [], 0.0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            pen = SVGPathPen(self.glyphs, ntos=num)
            origin = x + (cursor + pos.x_offset) * scale
            self.glyphs[self.font.getGlyphName(info.codepoint)].draw(
                TransformPen(pen, (scale, 0, 0, -scale, origin, y))
            )
            if commands := pen.getCommands():
                paths.append(commands)
            cursor += pos.x_advance + tracking * self.upm
        return paths, (cursor - tracking * self.upm) * scale

    def width(self, text: str, size: float, tracking: float = 0) -> float:
        return self.outlines(text, size, 0, 0, tracking)[1]

    def text(
        self,
        text: str,
        size: float,
        x: float,
        y: float,
        fill: str,
        anchor: str = "start",
        cls: str = "",
        tracking: float = 0,
        opacity: float = 1,
    ) -> str:
        if anchor != "start":
            width = self.width(text, size, tracking)
            x -= width if anchor == "end" else width / 2
        paths, _ = self.outlines(text, size, x, y, tracking)
        attrs = (f' class="{cls}"' if cls else "") + (f' opacity="{opacity}"' if opacity != 1 else "")
        return f'<path{attrs} fill="{fill}" d="{"".join(paths)}"/>'


def num(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def pct(seconds: float, duration: float) -> str:
    return f"{max(0.0, min(100.0, seconds / duration * 100)):.2f}%"


def window(name: str, duration: float, on: float, off: float, fade: float = 0.45) -> str:
    return (
        f"@keyframes {name}{{0%,{pct(on, duration)}{{opacity:0}}"
        f"{pct(on + fade, duration)},{pct(off, duration)}{{opacity:1}}"
        f"{pct(off + fade, duration)},100%{{opacity:0}}}}"
        f".{name}{{animation:{name} {duration}s ease-out infinite}}"
    )


def draw(name: str, duration: float, length: float, start: float, end: float, off: float) -> str:
    return (
        f"@keyframes {name}{{0%,{pct(start, duration)}{{stroke-dashoffset:{num(length)};opacity:1}}"
        f"{pct(end, duration)},{pct(off, duration)}{{stroke-dashoffset:0;opacity:1}}"
        f"{pct(off + 0.45, duration)}{{stroke-dashoffset:0;opacity:0}}"
        f"100%{{stroke-dashoffset:{num(length)};opacity:0}}}}"
        f".{name}{{stroke-dasharray:{num(length)};animation:{name} {duration}s ease-in-out infinite}}"
    )


def svg(height: int, label: str, css: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
        f'width="{W}" height="{height}" role="img" aria-label="{label}">'
        f"<title>{label}</title>"
        f"<style>{css}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>"
        f"{body}</svg>\n"
    )


def card(height: int, theme: dict[str, str]) -> str:
    return (
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="14" '
        f'fill="{theme["bg"]}" stroke="{theme["edge"]}"/>'
    )


def hero(display: Face, serif: Face, label: Face) -> str:
    duration, size, tracking = 14, 82, -0.02
    css = [
        ".g{fill:#fff;stroke:#fff;stroke-width:1.5;stroke-linejoin:round;"
        f"animation:apply {duration}s ease-in-out infinite backwards}}",
        "@keyframes apply{0%,6%{fill-opacity:0}8.5%,74%{fill-opacity:1}80%,100%{fill-opacity:0}}",
        "@keyframes plan{0%,27.5%{opacity:1}28.5%,74%{opacity:0}75%,100%{opacity:1}}",
        "@keyframes done{0%,27.5%{opacity:0}28.5%,74%{opacity:1}75%,100%{opacity:0}}",
        f".plan{{opacity:0;animation:plan {duration}s linear infinite}}",
        f".done{{animation:done {duration}s linear infinite}}",
    ]
    body = [f'<rect width="{W}" height="400" rx="14" fill="{SITE["navy"]}"/>']
    index = 0
    for row, line in enumerate(("FRANCIS EYTAN", "DORTORT")):
        x = (W - display.width(line, size, tracking)) / 2
        paths, _ = display.outlines(line, size, x, 124 + row * 88, tracking)
        for path in paths:
            css.append(f".d{index}{{animation-delay:{index * 0.11 + row * 0.3:.2f}s}}")
            body.append(f'<path class="g d{index}" d="{path}"/>')
            index += 1
    body.append(
        serif.text(
            "Senior DevSecOps Engineer & Cloud Solutions Architect",
            23, W / 2, 262, "#fff", anchor="middle", opacity=0.9,
        )
    )
    body.append(f'<rect x="{W / 2 - 1}" y="288" width="2" height="40" fill="{SITE["gold"]}"/>')
    body.append(
        label.text(
            "Plan: secure, scalable, compliant.",
            15, W / 2, 364, SITE["gold"], anchor="middle", cls="plan", tracking=0.04,
        )
    )
    body.append(
        label.text(
            "Apply complete! 20 years in production.",
            15, W / 2, 364, SITE["gold"], anchor="middle", cls="done", tracking=0.04,
        )
    )
    label_text = "Francis Eytan Dortort, Senior DevSecOps Engineer and Cloud Solutions Architect"
    return svg(400, label_text, "".join(css), "".join(body))


def section(display: Face, text: str, mode: str) -> str:
    body = (
        f'<rect y="0" width="{W}" height="1" fill="{SITE["slate"]}" opacity="0.35"/>'
        f'<rect x="0" y="34" width="3" height="40" fill="{SITE["gold"]}"/>'
        + display.text(text, 36, 20, 67, SITE_HEADING[mode], tracking=-0.01)
    )
    return svg(84, text, "", body)


def stackorder(wordmark: Face, label: Face, mono: Face, theme: dict[str, str]) -> str:
    duration, off, height = 12, 10.2, 284
    node_w, node_h, cut = 176, 48, 9
    columns = (PAD, 332, W - PAD - node_w)
    rows = (132, 204)
    waves = (
        (0.8, (("staging/vpc", 0), ("prod/vpc", 1))),
        (2.3, (("staging/eks", 0), ("prod/eks", 1))),
        (3.8, (("prod/apps", 1),)),
    )
    edges = ((0, 0, 1.5), (0, 1, 1.5), (1, 1, 3.0))
    unit = 1.5
    origin_x, origin_y = PAD - 4 * unit, 22 - 6 * unit
    plates = f'transform="translate({origin_x} {origin_y}) scale({unit})"'
    x_height = wordmark.font["OS/2"].sxHeight / wordmark.upm
    css = []
    body = [
        card(height, theme),
        f'<path {plates} fill="{theme["ink"]}" d="M6 6H24V8L22 10H4V8ZM6 22H24V24L22 26H4V24Z"/>',
        f'<path {plates} fill="{theme["accent"]}" d="M10 14H28V16L26 18H8V16Z"/>',
        wordmark.text(
            "stackorder", 12 * unit / x_height, origin_x + 36 * unit, origin_y + 22 * unit, theme["ink"]
        ),
    ]

    def plate(x: float, y: float) -> str:
        return (
            f"M{x + cut} {y}H{x + node_w}V{y + node_h - cut}L{x + node_w - cut} {y + node_h}"
            f"H{x}V{y + cut}Z"
        )

    for wave, (start, nodes) in enumerate(waves):
        x = columns[wave]
        css.append(window(f"w{wave}", duration, start, off))
        body.append(label.text(f"wave {wave}", 14, x, 116, theme["muted"]))
        for name, row in nodes:
            y = rows[row]
            body.append(
                f'<path d="{plate(x, y)}" fill="none" stroke="{theme["line"]}" stroke-width="2"/>'
                + mono.text(name, 15, x + 18, y + 30, theme["muted"])
                + f'<g class="w{wave}"><path d="{plate(x, y)}" fill="{theme["ink"]}" '
                f'stroke="{theme["ink"]}" stroke-width="2"/>'
                + mono.text(name, 15, x + 18, y + 30, theme["on_ink"])
                + "</g>"
            )
    for index, (wave, row, start) in enumerate(edges):
        x1, x2 = columns[wave] + node_w + 10, columns[wave + 1] - 10
        y = rows[row] + node_h / 2
        css.append(draw(f"e{index}", duration, x2 - x1, start, start + 0.8, off))
        body.append(
            f'<path d="M{x1} {y}H{x2}" stroke="{theme["line"]}" stroke-width="2"/>'
            f'<path class="e{index}" d="M{x1} {y}H{x2}" stroke="{theme["accent"]}" stroke-width="3"/>'
        )
    label_text = "Stackorder: five stacks applied in three dependency waves"
    return svg(height, label_text, "".join(css), "".join(body))


def wawarden(label: Face, strong: Face, theme: dict[str, str]) -> str:
    duration, height = 5.6, 292
    lanes = ((128, "Work", False), (168, "Family", True), (208, "School parents", True), (248, "Bank alerts", False))
    pill_w, gate_x, agent_x, agent_y = 176, 456, 652, 188
    start_x = PAD + pill_w + 14
    travel = gate_x - start_x
    reach = agent_x - 10 - start_x
    bounds = BoundsPen(None)
    parse_path(WAWARDEN_WORDMARK, bounds)
    left, top, _, bottom = bounds.bounds
    scale = 30 / (bottom - top)
    css = [
        f".m{{opacity:0;animation-duration:{duration}s;animation-timing-function:linear;"
        "animation-iteration-count:infinite}",
        f"@keyframes stop{{0%{{opacity:0;transform:translate(0,0);fill:{theme['ink']}}}"
        f"6%{{opacity:1}}44%{{transform:translate({travel - 20}px,0);fill:{theme['ink']}}}"
        f"52%{{fill:{theme['stop']}}}70%{{opacity:.55}}"
        f"84%,100%{{opacity:0;transform:translate({travel - 20}px,0);fill:{theme['stop']}}}}}",
        ".stop{animation-name:stop}",
    ]
    body = [
        card(height, theme),
        f'<polyline transform="translate({PAD - 3.4} 21) scale(3.8)" points="1,5 3,9 6,3 8,7 11,1" fill="none" '
        f'stroke="{WAWARDEN_GREEN}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
        f'<path transform="translate({num(PAD + 54 - left * scale)} {num(26 - top * scale)}) scale({scale:.4f})" '
        f'fill="{theme["ink"]}" d="{WAWARDEN_WORDMARK}"/>',
        label.text("allowlist", 14, gate_x, 98, theme["muted"], anchor="middle"),
    ]
    gate, cursor = [], 110
    for index, (y, name, allowed) in enumerate(lanes):
        dy = agent_y - y
        body.append(
            f'<rect x="{PAD}" y="{y - 15}" width="{pill_w}" height="30" rx="15" fill="none" '
            f'stroke="{theme["line"]}" stroke-width="2"/>'
            + label.text(name, 15, PAD + 16, y + 5, theme["ink"])
            + f'<path d="M{start_x - 3} {y}H{gate_x - 12}" stroke="{theme["line"]}" stroke-width="2"/>'
        )
        if allowed:
            gate.append(f"M{gate_x} {cursor}V{y - 13}")
            cursor = y + 13
            css.append(
                f"@keyframes pass{index}{{0%{{opacity:0;transform:translate(0,0);fill:{theme['ink']}}}"
                f"6%{{opacity:1}}44%{{transform:translate({travel}px,0);fill:{theme['ink']}}}"
                f"48%{{fill:{WAWARDEN_GREEN}}}"
                f"88%{{opacity:1;transform:translate({reach}px,{dy}px)}}"
                f"94%,100%{{opacity:0;transform:translate({reach}px,{dy}px);fill:{WAWARDEN_GREEN}}}}}"
                f".pass{index}{{animation-name:pass{index}}}"
            )
            body.append(
                f'<path d="M{gate_x + 12} {y}L{agent_x - 10} {agent_y}" '
                f'stroke="{WAWARDEN_GREEN}" stroke-width="2"/>'
            )
            name_cls = f"pass{index}"
        else:
            name_cls = "stop"
        css.append(f".l{index}{{animation-delay:{index * 1.4:.1f}s}}")
        body.append(f'<circle class="m {name_cls} l{index}" cx="{start_x}" cy="{y}" r="6"/>')
    gate.append(f"M{gate_x} {cursor}V266")
    body.append(
        f'<path d="{"".join(gate)}" stroke="{theme["ink"]}" stroke-width="3" stroke-linecap="round"/>'
        f'<rect x="{agent_x}" y="{agent_y - 21}" width="{W - PAD - agent_x}" height="42" rx="21" '
        f'fill="{WAWARDEN_GREEN}"/>'
        + strong.text("Your agent", 16, (agent_x + W - PAD) / 2, agent_y + 6, WAWARDEN_INK, anchor="middle")
    )
    label_text = "WaWarden: messages from allowlisted chats reach your agent, the rest stop at the gate"
    return svg(height, label_text, "".join(css), "".join(body))


def taintguard(mono: Face, bold: Face, theme: dict[str, str]) -> str:
    duration, off, height = 13, 11.2, 338
    size, left, pitch, first = 15, PAD, 27, 106
    css = [
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}",
        ".caret{animation:blink 1.1s steps(1) infinite}",
    ]
    spark = "".join(
        f'<path d="M0 -11V11" transform="translate({left + 12} 43) rotate({angle})" '
        f'stroke="{theme["orange"]}" stroke-width="3.4" stroke-linecap="round"/>'
        for angle in (0, 45, 90, 135)
    )
    body = [
        card(height, theme),
        spark,
        bold.text("TaintGuard", 27, left + 36, 53, theme["ink"]),
        mono.text("a Claude Code mod", 14, W - PAD, 51, theme["muted"], anchor="end"),
    ]
    steps = (
        ("call", "Edit(src/deploy.ts)", 0.6, None),
        ("call", "Read(.env)", 1.6, None),
        ("call", "WebFetch(https://…)", 3.4, 4.0),
        ("note", "Refused: this session carries secret", 4.0, None),
        ("call", "Bash(curl …)", 5.2, 5.8),
        ("note", "Refused: this session carries secret", 5.8, None),
    )
    for index, (kind, text, shown, refused) in enumerate(steps):
        y = first + index * pitch
        css.append(window(f"t{index}", duration, shown, off, 0.3))
        if kind == "note":
            body.append(
                f'<g class="t{index}"><path d="M{left + 22} {y - 13}v8h9" fill="none" '
                f'stroke="{theme["muted"]}" stroke-width="1.6"/>'
                + mono.text(text, size, left + 42, y, theme["orange_text"])
                + "</g>"
            )
            continue
        dot = f'<circle cx="{left + 6}" cy="{y - 5}" r="5" fill="{theme["ink"]}"/>'
        if refused is not None:
            css.append(window(f"x{index}", duration, refused, off, 0.3))
            dot += f'<circle class="x{index}" cx="{left + 6}" cy="{y - 5}" r="5" fill="{theme["orange"]}"/>'
        body.append(f'<g class="t{index}">{dot}' + bold.text(text, size, left + 22, y, theme["ink"]) + "</g>")
    tag_x = left + 22 + bold.width("Read(.env)", size) + 16
    tag_y = first + pitch
    tag_w = mono.width("+ secret", 13) + 20
    css.append(window("tag", duration, 2.3, off))
    band_y = first + len(steps) * pitch + 8
    body.append(
        f'<g class="tag"><rect x="{num(tag_x)}" y="{tag_y - 18}" width="{num(tag_w)}" height="24" rx="12" '
        f'fill="{theme["orange"]}"/>'
        + mono.text("+ secret", 13, tag_x + 10, tag_y - 1, "#141413")
        + mono.text("TaintGuard · tainted: secret", 14, left + 2, band_y, theme["orange_text"])
        + "</g>"
    )
    box_y = band_y + 12
    body.append(
        f'<rect x="{left}" y="{box_y}" width="{W - 2 * PAD}" height="40" rx="8" fill="none" '
        f'stroke="{theme["line"]}" stroke-width="1.5"/>'
        + mono.text(">", 15, left + 14, box_y + 25, theme["muted"])
        + f'<rect class="caret" x="{left + 34}" y="{box_y + 11}" width="9" height="18" fill="{theme["ink"]}"/>'
    )
    label_text = (
        "TaintGuard in a Claude Code session: after Read(.env) the session carries the label secret, "
        "and WebFetch and Bash are refused"
    )
    return svg(height, label_text, "".join(css), "".join(body))


def across_amazon(label: Face, strong: Face, theme: dict[str, str]) -> str:
    duration, off, height = 12, 10.4, 284
    bar_x, bar_h, pitch, top = PAD + 136, 22, 38, 124
    stores = (
        ("amazon.com", (450, 55, 85)),
        ("amazon.de", (360, 45, 55)),
        ("amazon.co.uk", (430, 76, 104)),
        ("amazon.co.jp", (400, 66, 76)),
    )
    tones = (0.55, 0.32, 0.16)
    ranked = sorted(range(len(stores)), key=lambda i: sum(stores[i][1]))
    css = [
        window("win", duration, 4.3, off),
        f"@keyframes lose{{0%,{pct(4.3, duration)}{{opacity:1}}{pct(4.75, duration)},100%{{opacity:0}}}}"
        f".lose{{opacity:0;animation:lose {duration}s ease-out infinite}}",
    ]
    tile = (
        f'<g transform="translate({PAD} 20)"><rect width="46" height="46" rx="10" fill="{ACROSS_TILE}"/>'
        '<g fill="none" stroke="#fff" stroke-width="2.2">'
        '<circle cx="23" cy="21" r="12.5"/><ellipse cx="23" cy="21" rx="5.6" ry="12.5"/>'
        '<path d="M10.5 21h25M12.6 14.6h20.8M12.6 27.4h20.8"/></g>'
        f'<path d="M6.5 27.5c10 7.4 22.5 7.2 33-.6" fill="none" stroke="{ACROSS_ORANGE}" '
        'stroke-width="3.6" stroke-linecap="round"/>'
        f'<path d="M34.2 23.6l7.3.4-2.800 6.700z" fill="{ACROSS_ORANGE}"/></g>'
    )
    body = [card(height, theme), tile, strong.text("Across Amazon", 27, PAD + 60, 53, theme["ink"], tracking=-0.01)]
    x = W - PAD
    for name, tone in reversed(list(zip(("item", "shipping", "import fees"), tones))):
        x -= label.width(name, 14)
        body.append(label.text(name, 14, x, 49, theme["muted"]))
        x -= 20
        body.append(f'<rect x="{num(x)}" y="37" width="13" height="13" rx="2" fill="{theme["ink"]}" opacity="{tone}"/>')
        x -= 18
    for index, (name, parts) in enumerate(stores):
        rank = ranked.index(index)
        y = top + rank * pitch
        shift = (index - rank) * pitch
        grow = 0.5 + index * 0.45
        css.append(
            f"@keyframes row{index}{{0%{{opacity:0;transform:translateY({shift}px)}}"
            f"{pct(0.4, duration)},{pct(3.2, duration)}{{opacity:1;transform:translateY({shift}px)}}"
            f"{pct(4.0, duration)},{pct(off, duration)}{{opacity:1;transform:translateY(0)}}"
            f"{pct(off + 0.45, duration)}{{opacity:0;transform:translateY(0)}}"
            f"100%{{opacity:0;transform:translateY({shift}px)}}}}"
            f".row{index}{{animation:row{index} {duration}s ease-in-out infinite}}"
            f"@keyframes bar{index}{{0%,{pct(grow, duration)}{{transform:scaleX(0)}}"
            f"{pct(grow + 0.7, duration)},100%{{transform:scaleX(1)}}}}"
            f".bar{index}{{animation:bar{index} {duration}s ease-out infinite}}"
        )
        segments, winner, cursor = [], [], 0
        for part, tone in zip(parts, tones):
            rect = f'<rect x="{cursor}" y="{-bar_h / 2}" width="{part - 2}" height="{bar_h}" rx="3" '
            segments.append(rect + f'fill="{theme["ink"]}" opacity="{tone}"/>')
            winner.append(rect + f'fill="{theme["brand"]}" opacity="{min(1.0, tone + 0.45):.2f}"/>')
            cursor += part
        best, lose = "", ""
        if rank == 0:
            lose = ' class="lose"'
            best = (
                f'<g class="win">{"".join(winner)}'
                + strong.text("lowest delivered total", 14, cursor + 10, 5, theme["brand"])
                + "</g>"
            )
        body.append(
            f'<g class="row{index}">'
            + label.text(name, 15, PAD, y + 5, theme["ink"])
            + f'<g transform="translate({bar_x} {y})"><g class="bar{index}"><g{lose}>{"".join(segments)}</g></g>{best}</g></g>'
        )
    label_text = "Across Amazon: four Amazon stores ranked by item, shipping and import fees, lowest delivered total first"
    return svg(height, label_text, "".join(css), "".join(body))


def main() -> None:
    montserrat_bold = Face(MONTSERRAT, wght=700)
    montserrat_semibold = Face(MONTSERRAT, wght=600)
    merriweather = Face(MERRIWEATHER_ITALIC, opsz=24, wdth=100, wght=300)
    inter = Face(INTER, opsz=14, wght=500)
    inter_strong = Face(INTER, opsz=24, wght=650)
    mono = Face(JETBRAINS_MONO, wght=500)
    mono_bold = Face(JETBRAINS_MONO, wght=700)
    lato = Face(LATO_BOLD)
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero(montserrat_bold, merriweather, montserrat_semibold))
    for mode in ("light", "dark"):
        (OUT / f"section-open-source-{mode}.svg").write_text(section(montserrat_bold, "Open source", mode))
        (OUT / f"section-writing-{mode}.svg").write_text(section(montserrat_bold, "Writing", mode))
        (OUT / f"stackorder-{mode}.svg").write_text(stackorder(lato, inter, mono, STACKORDER[mode]))
        (OUT / f"wawarden-{mode}.svg").write_text(wawarden(inter, inter_strong, WAWARDEN[mode]))
        (OUT / f"taintguard-{mode}.svg").write_text(taintguard(mono, mono_bold, CLAUDE[mode]))
        (OUT / f"across-amazon-{mode}.svg").write_text(across_amazon(inter, inter_strong, ACROSS[mode]))


if __name__ == "__main__":
    main()
