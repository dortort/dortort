#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["fonttools", "skia-pathops", "uharfbuzz"]
# ///
"""Generate the animated SVGs the profile README embeds."""

import io
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"
FONT = ROOT / "fonts" / "Anybody.ttf"

W = 840
SLAB = "#2338E8"
THEMES = {
    "light": {
        "ink": "#1f2328",
        "muted": "#59636e",
        "line": "#d1d9e0",
        "blue": "#2338E8",
        "hold": "#E79A0C",
    },
    "dark": {
        "ink": "#f0f6fc",
        "muted": "#9198a1",
        "line": "#3d444d",
        "blue": "#4D63FF",
        "hold": "#F2B134",
    },
}
ON_BLUE = "#ffffff"
ON_HOLD = "#1f2328"


class Face:
    def __init__(self, **axes: float) -> None:
        self.font = instancer.instantiateVariableFont(
            TTFont(FONT), axes, overlap=instancer.OverlapMode.REMOVE
        )
        buf = io.BytesIO()
        self.font.save(buf)
        self.hb = hb.Font(hb.Face(buf.getvalue()))
        self.upm = self.font["head"].unitsPerEm
        self.glyphs = self.font.getGlyphSet()

    def outlines(self, text: str, size: float, x: float, y: float) -> tuple[list[str], float]:
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
            cursor += pos.x_advance
        return paths, cursor * scale

    def width(self, text: str, size: float) -> float:
        return self.outlines(text, size, 0, 0)[1]

    def text(
        self,
        text: str,
        size: float,
        x: float,
        y: float,
        fill: str,
        anchor: str = "start",
        cls: str = "",
    ) -> str:
        if anchor != "start":
            width = self.width(text, size)
            x -= width if anchor == "end" else width / 2
        paths, _ = self.outlines(text, size, x, y)
        attr = f' class="{cls}"' if cls else ""
        return f'<path{attr} fill="{fill}" d="{"".join(paths)}"/>'


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


def title(display: Face, text: str, theme: dict[str, str]) -> str:
    return display.text(text, 38, 0, 40, theme["ink"])


def hero(display: Face, label: Face) -> str:
    duration, size, left = 14, 100, 44
    css = [
        ".g{fill:#fff;stroke:#fff;stroke-width:1.5;stroke-linejoin:round;"
        f"animation:apply {duration}s ease-in-out infinite backwards}}",
        "@keyframes apply{0%,6%{fill-opacity:0}8.5%,74%{fill-opacity:1}80%,100%{fill-opacity:0}}",
        "@keyframes plan{0%,27.5%{opacity:.85}28.5%,74%{opacity:0}75%,100%{opacity:.85}}",
        "@keyframes done{0%,27.5%{opacity:0}28.5%,74%{opacity:.85}75%,100%{opacity:0}}",
        f".plan{{opacity:0;animation:plan {duration}s linear infinite}}",
        f".done{{opacity:.85;animation:done {duration}s linear infinite}}",
    ]
    body = [f'<rect width="{W}" height="384" rx="14" fill="{SLAB}"/>']
    index = 0
    for row, word in enumerate(("Francis", "Eytan", "Dortort")):
        paths, _ = display.outlines(word, size, left, 118 + row * 92)
        for path in paths:
            css.append(f".d{index}{{animation-delay:{index * 0.11 + row * 0.3:.2f}s}}")
            body.append(f'<path class="g d{index}" d="{path}"/>')
            index += 1
    body.append(label.text(f"Plan: {index} to add, 0 to change, 0 to destroy.", 17, left, 348, "#fff", cls="plan"))
    body.append(
        label.text(
            f"Apply complete! Resources: {index} added, 0 changed, 0 destroyed.",
            17, left, 348, "#fff", cls="done",
        )
    )
    return svg(384, "Francis Eytan Dortort", "".join(css), "".join(body))


def stackorder(display: Face, label: Face, theme: dict[str, str]) -> str:
    duration, off = 12, 10.2
    node_w, node_h = 176, 48
    columns = (1, 332, 663)
    rows = (98, 164)
    waves = (
        (0.8, (("staging/vpc", 0), ("prod/vpc", 1))),
        (2.3, (("staging/eks", 0), ("prod/eks", 1))),
        (3.8, (("prod/apps", 1),)),
    )
    edges = ((0, 0, 1.5), (0, 1, 1.5), (1, 1, 3.0))
    css, body = [], [title(display, "Stackorder", theme)]
    for wave, (start, nodes) in enumerate(waves):
        x = columns[wave]
        css.append(window(f"w{wave}", duration, start, off))
        body.append(label.text(f"wave {wave}", 14, x, 82, theme["muted"]))
        for name, row in nodes:
            y = rows[row]
            body.append(
                f'<rect x="{x}" y="{y}" width="{node_w}" height="{node_h}" rx="5" '
                f'fill="none" stroke="{theme["line"]}" stroke-width="2"/>'
                + label.text(name, 16, x + 16, y + 30, theme["muted"])
                + f'<g class="w{wave}"><rect x="{x - 1}" y="{y - 1}" width="{node_w + 2}" '
                f'height="{node_h + 2}" rx="6" fill="{theme["blue"]}"/>'
                + label.text(name, 16, x + 16, y + 30, ON_BLUE)
                + "</g>"
            )
    for index, (wave, row, start) in enumerate(edges):
        x1, x2 = columns[wave] + node_w + 10, columns[wave + 1] - 10
        y = rows[row] + node_h / 2
        css.append(draw(f"e{index}", duration, x2 - x1, start, start + 0.8, off))
        body.append(
            f'<path d="M{x1} {y}H{x2}" stroke="{theme["line"]}" stroke-width="2"/>'
            f'<path class="e{index}" d="M{x1} {y}H{x2}" stroke="{theme["blue"]}" stroke-width="2"/>'
        )
    label_text = "Stackorder: five stacks applied in three dependency waves"
    return svg(234, label_text, "".join(css), "".join(body))


def wawarden(display: Face, label: Face, theme: dict[str, str]) -> str:
    duration = 5.6
    lanes = ((100, "Work", False), (140, "Family", True), (180, "School parents", True), (220, "Bank alerts", False))
    pill_w, gate_x, agent_x, agent_y = 168, 440, 680, 160
    css = [
        f".m{{opacity:0;animation-duration:{duration}s;animation-timing-function:linear;"
        "animation-iteration-count:infinite}",
        f"@keyframes stop{{0%{{opacity:0;transform:translate(0,0);fill:{theme['ink']}}}"
        f"6%{{opacity:1}}44%{{transform:translate(248px,0);fill:{theme['ink']}}}"
        f"52%{{fill:{theme['hold']}}}74%{{opacity:1}}"
        f"86%,100%{{opacity:0;transform:translate(248px,0);fill:{theme['hold']}}}}}",
        ".stop{animation-name:stop}",
    ]
    body = [
        title(display, "WaWarden", theme),
        label.text("allowlist", 14, gate_x, 70, theme["muted"], anchor="middle"),
    ]
    gate = []
    cursor = 82
    for index, (y, name, allowed) in enumerate(lanes):
        dy = agent_y - y
        body.append(
            f'<rect x="1" y="{y - 15}" width="{pill_w}" height="30" rx="15" fill="none" '
            f'stroke="{theme["line"]}" stroke-width="2"/>'
            + label.text(name, 15, 16, y + 5, theme["ink"])
            + f'<path d="M{pill_w + 11} {y}H{gate_x - 12}" stroke="{theme["line"]}" stroke-width="2"/>'
        )
        if allowed:
            gate.append(f"M{gate_x} {cursor}V{y - 13}")
            cursor = y + 13
            css.append(
                f"@keyframes pass{index}{{0%{{opacity:0;transform:translate(0,0);fill:{theme['ink']}}}"
                f"6%{{opacity:1}}44%{{transform:translate(260px,0);fill:{theme['ink']}}}"
                f"48%{{fill:{theme['blue']}}}"
                f"88%{{opacity:1;transform:translate(488px,{dy}px)}}"
                f"94%,100%{{opacity:0;transform:translate(488px,{dy}px);fill:{theme['blue']}}}}}"
                f".pass{index}{{animation-name:pass{index}}}"
            )
            body.append(
                f'<path d="M{gate_x + 12} {y}L{agent_x - 10} {agent_y}" '
                f'stroke="{theme["blue"]}" stroke-width="2"/>'
            )
            name_cls = f"pass{index}"
        else:
            body.append(
                f'<rect x="{gate_x - 10}" y="{y - 9}" width="5" height="18" rx="2" fill="{theme["hold"]}"/>'
            )
            name_cls = "stop"
        css.append(f".l{index}{{animation-delay:{index * 1.4:.1f}s}}")
        body.append(f'<circle class="m {name_cls} l{index}" cx="{pill_w + 14}" cy="{y}" r="6"/>')
    gate.append(f"M{gate_x} {cursor}V238")
    body.append(
        f'<path d="{"".join(gate)}" stroke="{theme["ink"]}" stroke-width="3" stroke-linecap="round"/>'
        f'<rect x="{agent_x}" y="{agent_y - 20}" width="{W - agent_x}" height="40" rx="20" fill="{theme["blue"]}"/>'
        + label.text("Your agent", 16, (agent_x + W) / 2, agent_y + 6, ON_BLUE, anchor="middle")
    )
    label_text = "WaWarden: messages from allowlisted chats reach your agent, the rest stop at the gate"
    return svg(258, label_text, "".join(css), "".join(body))


def taintguard(display: Face, label: Face, theme: dict[str, str]) -> str:
    duration, off = 12, 10.4
    chip_w, chip_h, y = 170, 46, 136
    xs = (1, 224, 447, 669)
    calls = (("Edit", 0.6, None), ("Read .env", 1.8, None), ("WebFetch", 3.3, 3.9), ("Bash", 4.9, 5.5))
    css, body = [], [title(display, "TaintGuard", theme)]
    for index in range(3):
        x1, x2 = xs[index] + chip_w + 8, xs[index + 1] - 8
        tainted = index > 0
        start = (1.2, 2.7, 4.3)[index]
        css.append(draw(f"s{index}", duration, x2 - x1, start, start + 0.5, off))
        body.append(
            f'<path d="M{x1} {y}H{x2}" stroke="{theme["line"]}" stroke-width="2"/>'
            f'<path class="s{index}" d="M{x1} {y}H{x2}" '
            f'stroke="{theme["hold"] if tainted else theme["blue"]}" stroke-width="{4 if tainted else 2}"/>'
        )
    for index, (name, shown, refused) in enumerate(calls):
        x, top = xs[index], y - chip_h / 2
        center = x + chip_w / 2
        css.append(window(f"c{index}", duration, shown, off))
        if refused is None:
            body.append(
                f'<g class="c{index}"><rect x="{x}" y="{top}" width="{chip_w}" height="{chip_h}" rx="5" '
                f'fill="{theme["blue"]}"/>'
                + label.text(name, 16, center, y + 6, ON_BLUE, anchor="middle")
                + "</g>"
            )
            continue
        css.append(window(f"r{index}", duration, refused, off))
        body.append(
            f'<g class="c{index}"><rect x="{x}" y="{top}" width="{chip_w}" height="{chip_h}" rx="5" '
            f'fill="none" stroke="{theme["line"]}" stroke-width="2"/>'
            + label.text(name, 16, center, y + 6, theme["ink"], anchor="middle")
            + f'<g class="r{index}"><rect x="{x}" y="{top}" width="{chip_w}" height="{chip_h}" rx="5" '
            f'fill="none" stroke="{theme["hold"]}" stroke-width="3"/>'
            + label.text("refused", 14, center, y + 50, theme["muted"], anchor="middle")
            + "</g></g>"
        )
    tag_x = xs[1] + chip_w / 2
    tag_w = label.width("secret", 14) + 24
    css.append(window("tag", duration, 2.4, off))
    body.append(
        f'<g class="tag"><path d="M{tag_x} {y - chip_h / 2 - 12}v8" stroke="{theme["hold"]}" stroke-width="3"/>'
        f'<rect x="{num(tag_x - tag_w / 2)}" y="{y - chip_h / 2 - 38}" width="{num(tag_w)}" height="26" rx="13" '
        f'fill="{theme["hold"]}"/>'
        + label.text("secret", 14, tag_x, y - chip_h / 2 - 20, ON_HOLD, anchor="middle")
        + "</g>"
    )
    label_text = (
        "TaintGuard: after a session reads an .env file it carries the label secret, "
        "and WebFetch and Bash are refused"
    )
    return svg(212, label_text, "".join(css), "".join(body))


def across_amazon(display: Face, label: Face, theme: dict[str, str]) -> str:
    duration, off = 12, 10.4
    bar_x, bar_h, pitch, top = 150, 22, 38, 88
    stores = (
        ("amazon.com", (470, 60, 90)),
        ("amazon.de", (400, 50, 60)),
        ("amazon.co.uk", (450, 80, 110)),
        ("amazon.co.jp", (420, 70, 80)),
    )
    tones = (0.55, 0.32, 0.16)
    ranked = sorted(range(len(stores)), key=lambda i: sum(stores[i][1]))
    css = [
        window("win", duration, 4.3, off),
        f"@keyframes lose{{0%,{pct(4.3, duration)}{{opacity:1}}{pct(4.75, duration)},100%{{opacity:0}}}}"
        f".lose{{opacity:0;animation:lose {duration}s ease-out infinite}}",
    ]
    body = [title(display, "Across Amazon", theme)]
    x = W
    for name, tone in reversed(list(zip(("item", "shipping", "import fees"), tones))):
        x -= label.width(name, 14)
        body.append(label.text(name, 14, x, 36, theme["muted"]))
        x -= 20
        body.append(f'<rect x="{num(x)}" y="24" width="13" height="13" rx="2" fill="{theme["ink"]}" opacity="{tone}"/>')
        x -= 20
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
            rect = f'<rect x="{cursor}" y="{-bar_h / 2}" width="{part - 2}" height="{bar_h}" rx="2" '
            segments.append(rect + f'fill="{theme["ink"]}" opacity="{tone}"/>')
            winner.append(rect + f'fill="{theme["blue"]}" opacity="{min(1.0, tone + 0.45):.2f}"/>')
            cursor += part
        best, lose = "", ""
        if rank == 0:
            lose = ' class="lose"'
            best = (
                f'<g class="win">{"".join(winner)}'
                + label.text("lowest delivered total", 14, cursor + 10, 5, theme["blue"])
                + "</g>"
            )
        body.append(
            f'<g class="row{index}">'
            + label.text(name, 15, 0, y + 5, theme["ink"])
            + f'<g transform="translate({bar_x} {y})"><g class="bar{index}"><g{lose}>{"".join(segments)}</g></g>{best}</g></g>'
        )
    label_text = "Across Amazon: four Amazon stores ranked by item, shipping and import fees, lowest delivered total first"
    return svg(234, label_text, "".join(css), "".join(body))


def writing(display: Face, theme: dict[str, str]) -> str:
    width = display.width("Writing", 38)
    css = (
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        ".caret{animation:blink 1.1s steps(1) infinite}"
    )
    body = title(display, "Writing", theme) + (
        f'<rect class="caret" x="{num(width + 10)}" y="10" width="7" height="32" fill="{theme["blue"]}"/>'
    )
    return svg(52, "Writing", css, body)


def main() -> None:
    display = Face(wdth=150, wght=900)
    label = Face(wdth=100, wght=500)
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero(display, label))
    for mode, theme in THEMES.items():
        (OUT / f"stackorder-{mode}.svg").write_text(stackorder(display, label, theme))
        (OUT / f"wawarden-{mode}.svg").write_text(wawarden(display, label, theme))
        (OUT / f"taintguard-{mode}.svg").write_text(taintguard(display, label, theme))
        (OUT / f"across-amazon-{mode}.svg").write_text(across_amazon(display, label, theme))
        (OUT / f"writing-{mode}.svg").write_text(writing(display, theme))


if __name__ == "__main__":
    main()
