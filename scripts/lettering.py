#!/usr/bin/env python3
"""Hand-lettered headings: text set in Kaushan Script (the brush script closest to the logo's "TOURNAMENT"),
converted to one SVG path per letter so the page can draw each letter's outline in, then fill it.

The SVG is decorative (aria-hidden); the page keeps the same words as real text for screen readers and search.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

FONT = TTFont(Path(__file__).resolve().parent / 'fonts/KaushanScript-Regular.ttf')
GLYPHS = FONT.getGlyphSet()
CMAP = FONT.getBestCmap()
KERN = FONT['kern'].kernTables[0].kernTable if 'kern' in FONT else {}
LINE = 1000  # baseline-to-baseline distance in font units
PAD = 30     # room for the drawing stroke at the edges


def lettering(lines, css_class):
    """lines: list of strings, left-aligned. Returns an inline <svg> whose letters carry --i (drawing order)."""
    paths, index, width, top, bottom = [], 0, 0, None, None
    for row, text in enumerate(lines):
        x, prev, base = 0, None, row * LINE
        for ch in text:
            name = CMAP[ord(ch)]
            if prev: x += KERN.get((prev, name), 0)
            glyph = GLYPHS[name]
            bounds = BoundsPen(GLYPHS); glyph.draw(bounds)
            if bounds.bounds:
                xmin, ymin, xmax, ymax = bounds.bounds
                top = min(top, base - ymax) if top is not None else base - ymax
                bottom = max(bottom, base - ymin) if bottom is not None else base - ymin
                width = max(width, x + xmax)
                pen = SVGPathPen(GLYPHS, ntos=lambda v: str(round(v)))
                glyph.draw(TransformPen(pen, (1, 0, 0, -1, x, base)))
                paths.append(f'<path pathLength="1" style="--i:{index}" d="{pen.getCommands()}"/>')
                index += 1
            x += glyph.width; prev = name
    x0, y0 = -PAD, top - PAD
    w, h = width + 2 * PAD, bottom - top + 2 * PAD
    return (f'<svg class="lettering {css_class}" viewBox="{x0} {y0} {round(w)} {round(h)}" style="--letters:{index}" '
            f'aria-hidden="true" focusable="false">{"".join(paths)}</svg>')


if __name__ == '__main__':
    import sys
    print(lettering(sys.argv[1:] or ['Tournament day,', 'from above.'], 'demo'))
