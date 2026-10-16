"""Tampilan terminal (rich), teks polos, dan JSON."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from . import legal
from .books import BOOKS
from .db import HL_OFF, HL_ON, Hit, Passage, Verse
from .parser import format_label, Segment

MAX_WIDTH = 100


def _width(console: Console) -> int:
    return min(console.width, MAX_WIDTH)


# ---------------------------------------------------------------------------
# Rich
# ---------------------------------------------------------------------------
def passage_renderable(passage: Passage, *, headings: bool = True, title: Optional[str] = None) -> Group:
    header = Text()
    header.append(passage.label, style="bold cyan")
    header.append(" (AYT)", style="dim")

    grid = Table.grid(padding=(0, 1))
    grid.add_column(justify="right", style="bold yellow", no_wrap=True)
    grid.add_column(overflow="fold")

    multi_chapter = len({(v.book, v.chapter) for v in passage.verses}) > 1
    prev: Optional[Verse] = None
    for v in passage.verses:
        if multi_chapter and (prev is None or v.chapter != prev.chapter):
            if prev is not None:
                grid.add_row("", "")
            grid.add_row("", Text(f"Pasal {v.chapter}", style="bold underline"))
        elif prev is not None and v.id != prev.id + 1:
            grid.add_row("", Text("⋯", style="dim"))
        if headings and v.heading:
            if prev is not None:
                grid.add_row("", "")
            grid.add_row("", Text(v.heading, style="italic cyan"))
        grid.add_row(str(v.verse), Text(v.text))
        prev = v

    parts: List[Any] = []
    if title:
        parts.append(Text(title, style="bold magenta"))
    parts += [header, Text(""), grid]
    return Group(*parts)


def footer_renderable() -> Text:
    return Text(legal.FOOTER, style="dim")


def _marked_to_text(marked: str) -> Text:
    out = Text()
    on = False
    buf = ""
    for ch in marked:
        if ch in (HL_ON, HL_OFF):
            if buf:
                out.append(buf, style="bold black on yellow" if on else "")
                buf = ""
            on = ch == HL_ON
        else:
            buf += ch
    if buf:
        out.append(buf, style="bold black on yellow" if on else "")
    return out


def search_renderable(query: str, total: int, hits: Iterable[Hit], offset: int) -> Group:
    hits = list(hits)
    grid = Table.grid(padding=(0, 2))
    grid.add_column(no_wrap=True, style="bold cyan")
    grid.add_column(overflow="fold")
    for h in hits:
        label = format_label(BOOKS[h.book], [Segment(h.chapter, h.verse, h.chapter, h.verse)])
        grid.add_row(label, _marked_to_text(h.marked))
    first, last = offset + 1, offset + len(hits)
    summary = Text(f"{total} ayat cocok dengan “{query}”", style="bold")
    if total > len(hits):
        summary.append(f"  (menampilkan {first}–{last}; gunakan --limit / --offset untuk lainnya)", style="dim")
    return Group(summary, Text(""), grid)


# ---------------------------------------------------------------------------
# Teks polos (untuk --plain dan --copy)
# ---------------------------------------------------------------------------
def to_plain(passage: Passage, *, headings: bool = True) -> str:
    lines = [f"{passage.label} (AYT)"]
    multi_chapter = len({(v.book, v.chapter) for v in passage.verses}) > 1
    prev: Optional[Verse] = None
    for v in passage.verses:
        if multi_chapter and (prev is None or v.chapter != prev.chapter):
            lines.append(f"[Pasal {v.chapter}]")
        if headings and v.heading:
            lines.append(f"# {v.heading}")
        lines.append(f"{v.verse} {v.text}")
        prev = v
    return "\n".join(lines)


def hits_to_plain(hits: Iterable[Hit]) -> str:
    lines = []
    for h in hits:
        label = format_label(BOOKS[h.book], [Segment(h.chapter, h.verse, h.chapter, h.verse)])
        lines.append(f"{label}\t{h.marked.replace(HL_ON, '').replace(HL_OFF, '')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def passage_to_dict(passage: Passage) -> Dict[str, Any]:
    return {
        "reference": passage.label,
        "book": {"id": passage.book.id, "name": passage.book.name, "abbr": passage.book.abbr},
        **legal.JSON_NOTICE,
        "verses": [
            {"chapter": v.chapter, "verse": v.verse, "text": v.text, "heading": v.heading or None}
            for v in passage.verses
        ],
    }


def search_to_dict(query: str, total: int, hits: Iterable[Hit], offset: int) -> Dict[str, Any]:
    return {
        "query": query,
        "total": total,
        "offset": offset,
        **legal.JSON_NOTICE,
        "results": [
            {
                "reference": format_label(BOOKS[h.book], [Segment(h.chapter, h.verse, h.chapter, h.verse)]),
                "book": h.book,
                "chapter": h.chapter,
                "verse": h.verse,
                "text": h.marked.replace(HL_ON, "").replace(HL_OFF, ""),
            }
            for h in hits
        ],
    }
