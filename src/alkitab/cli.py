"""Antarmuka baris perintah: `alkitab Yoh 3:16`, `alkitab search kasih`, dll."""
from __future__ import annotations

import datetime as dt
import json
import sys
from typing import List, Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from typer.core import TyperGroup

from . import __version__, clipboard, daily, legal, render
from .books import BOOKS, OLD_TESTAMENT_LAST
from .db import Bible, Passage
from .parser import AlkitabError, Segment, format_label, parse_reference, resolve_book

HELP = """\
Baca Alkitab Yang Terbuka (AYT) dari terminal — offline, tanpa API.

\b
Contoh:
  alkitab Yoh 3:16            satu ayat
  alkitab 1 Kor 13:4-7        rentang ayat
  alkitab Mzm 23              satu pasal
  alkitab Mat 5:3-7:29        lintas pasal
  alkitab Yoh 3:16,18-20      beberapa bagian
  alkitab search "kasih karunia"
  alkitab today | random | list-kitab | license

Nama kitab boleh singkat, lengkap, Indonesia atau Inggris (Yoh, Yohanes, John, I Kor, 1Kor).
"""


class ReferenceGroup(TyperGroup):
    """Kata pertama yang bukan subperintah dianggap referensi: `alkitab Yoh 3:16` == `alkitab read Yoh 3:16`."""

    def resolve_command(self, ctx, args):  # type: ignore[no-untyped-def]
        if args and not args[0].startswith("-") and self.get_command(ctx, args[0]) is None:
            args = ["read", *args]
        return super().resolve_command(ctx, args)


app = typer.Typer(
    cls=ReferenceGroup,
    help=HELP,
    no_args_is_help=True,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)

out = Console()
err = Console(stderr=True)


def _version(value: bool) -> None:
    if value:
        typer.echo(f"alkitab-cli {__version__} (teks: AYT)")
        raise typer.Exit()


@app.callback()
def _root(
    version: bool = typer.Option(False, "--version", "-V", callback=_version, is_eager=True, help="Tampilkan versi."),
) -> None:
    pass


def _fail(exc: AlkitabError, code: int = 2) -> "typer.Exit":
    err.print(f"[bold red]Galat:[/] {escape(exc.message)}")
    if exc.hint:
        err.print(f"[dim]{escape(exc.hint)}[/]")
    return typer.Exit(code)


def _open() -> Bible:
    try:
        return Bible()
    except AlkitabError as exc:
        raise _fail(exc, 1)


def _emit_json(data: object) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _show_passage(passage, *, as_json: bool, plain: bool, copy: bool, headings: bool, title: Optional[str] = None) -> None:
    if as_json:
        _emit_json(render.passage_to_dict(passage))
    elif plain:
        typer.echo(render.to_plain(passage, headings=headings))
    else:
        out.print(render.passage_renderable(passage, headings=headings, title=title), width=render._width(out))
        out.print()
        out.print(render.footer_renderable(), width=render._width(out))
    if copy:
        used = clipboard.copy(render.to_plain(passage, headings=headings))
        if used:
            err.print(f"[dim]Disalin ke clipboard ({used}).[/]")
        else:
            err.print("[yellow]Tidak menemukan utilitas clipboard (pbcopy / wl-copy / xclip / xsel / clip).[/]")


# Opsi yang sama dipakai read / today / random
_JSON = typer.Option(False, "--json", help="Keluaran JSON (untuk skrip).")
_PLAIN = typer.Option(False, "--plain", help="Teks polos tanpa warna/format.")
_COPY = typer.Option(False, "--copy", help="Salin hasil ke clipboard.")
_NOHEAD = typer.Option(False, "--no-headings", help="Sembunyikan judul perikop.")


@app.command("read")
def read(
    reference: Optional[List[str]] = typer.Argument(None, metavar="REFERENSI", show_default=False,
                                                    help='Misalnya: Yoh 3:16 | 1 Kor 13:4-7 | Mzm 23'),
    as_json: bool = _JSON,
    plain: bool = _PLAIN,
    copy: bool = _COPY,
    no_headings: bool = _NOHEAD,
) -> None:
    """Baca ayat, rentang, atau pasal. (Subperintah ini boleh dihilangkan.)"""
    text = " ".join(reference or []).strip()
    if not text:
        raise _fail(AlkitabError("Referensi kosong.", "Contoh: alkitab Yoh 3:16"))
    bible = _open()
    try:
        ref = parse_reference(text)
        if ref.match.how == "fuzzy":
            err.print(f"[dim]“{escape(ref.match.typed)}” dibaca sebagai {escape(ref.book.name)}.[/]")
        if not ref.segments:
            n = bible.chapter_counts()[ref.book.id]
            out.print(f"[bold cyan]{escape(ref.book.name)}[/] ({ref.book.abbr}) — {n} pasal. "
                      f"Contoh: [bold]alkitab {escape(ref.book.abbr)} 1[/]")
            return
        passage = bible.fetch(ref)
    except AlkitabError as exc:
        raise _fail(exc)
    _show_passage(passage, as_json=as_json, plain=plain, copy=copy, headings=not no_headings)


@app.command("search")
def search(
    query: List[str] = typer.Argument(..., metavar="KATA...", help='Kata kunci. Gunakan "frasa" atau kata* (awalan).'),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=500, help="Jumlah hasil."),
    offset: int = typer.Option(0, "--offset", min=0, help="Lewati N hasil pertama."),
    kitab: Optional[str] = typer.Option(None, "--kitab", "-k", help="Batasi pada satu kitab, mis. -k Yoh"),
    as_json: bool = _JSON,
    plain: bool = _PLAIN,
) -> None:
    """Cari kata/frasa di seluruh Alkitab (hasil berurutan sesuai susunan kitab)."""
    # satu argumen berspasi (hasil kutipan di shell) = frasa; beberapa argumen = semua kata harus ada
    raw = f'"{query[0]}"' if len(query) == 1 and " " in query[0].strip() and '"' not in query[0] else " ".join(query)
    shown = " ".join(query)
    bible = _open()
    try:
        book_id = resolve_book(kitab).book.id if kitab else None
        total, hits = bible.search(raw, book=book_id, limit=limit, offset=offset)
    except AlkitabError as exc:
        raise _fail(exc)
    if as_json:
        _emit_json(render.search_to_dict(shown, total, hits, offset))
    elif plain:
        typer.echo(render.hits_to_plain(hits))
    elif not hits:
        out.print(f"Tidak ada ayat yang cocok dengan “{escape(shown)}”.")
    else:
        out.print(render.search_renderable(shown, total, hits, offset), width=render._width(out))
        out.print()
        out.print(render.footer_renderable(), width=render._width(out))
    if total == 0:
        raise typer.Exit(1)


@app.command("random")
def random_(as_json: bool = _JSON, plain: bool = _PLAIN, copy: bool = _COPY, no_headings: bool = _NOHEAD) -> None:
    """Tampilkan satu ayat acak."""
    bible = _open()
    v = bible.random_verse()
    book = BOOKS[v.book]
    passage = Passage(book, format_label(book, [Segment(v.chapter, v.verse, v.chapter, v.verse)]), [v])
    _show_passage(passage, as_json=as_json, plain=plain, copy=copy, headings=not no_headings, title="Ayat acak")


@app.command("today")
def today(
    date: Optional[str] = typer.Option(None, "--date", help="Tanggal lain, format YYYY-MM-DD."),
    as_json: bool = _JSON,
    plain: bool = _PLAIN,
    copy: bool = _COPY,
    no_headings: bool = _NOHEAD,
) -> None:
    """Ayat hari ini (sama untuk semua orang pada tanggal yang sama)."""
    try:
        day = dt.date.fromisoformat(date) if date else dt.date.today()
    except ValueError:
        raise _fail(AlkitabError(f"Tanggal tidak valid: '{date}'.", "Gunakan format YYYY-MM-DD, mis. 2026-12-25"))
    bible = _open()
    try:
        passage = bible.fetch(parse_reference(daily.pick(day)))
    except AlkitabError as exc:
        raise _fail(exc, 1)
    _show_passage(passage, as_json=as_json, plain=plain, copy=copy, headings=not no_headings,
                  title=f"Ayat hari ini · {daily.format_date_id(day)}")


@app.command("list-kitab")
def list_kitab(as_json: bool = _JSON) -> None:
    """Daftar 66 kitab beserta singkatan dan jumlah pasal."""
    counts = _open().chapter_counts()
    if as_json:
        _emit_json([
            {"id": b.id, "name": b.name, "abbr": b.abbr, "name_en": b.name_en, "chapters": counts[b.id],
             "testament": "PL" if b.id <= OLD_TESTAMENT_LAST else "PB"}
            for b in BOOKS.values()
        ])
        return
    table = Table(show_edge=False, pad_edge=False)
    table.add_column("No", justify="right", style="dim")
    table.add_column("Kitab", style="bold cyan")
    table.add_column("Singkatan")
    table.add_column("Pasal", justify="right")
    table.add_column("Inggris", style="dim")
    for b in BOOKS.values():
        table.add_row(str(b.id), b.name, b.abbr, str(counts[b.id]), b.name_en)
        if b.id == OLD_TESTAMENT_LAST:
            table.add_section()
    out.print(table)


@app.command("license")
def license_() -> None:
    """Tampilkan lisensi AYT, atribusi, dan batasan pemakaian."""
    typer.echo(legal.license_text(_open().meta()))


@app.command("help", hidden=True)
def help_(ctx: typer.Context) -> None:
    typer.echo((ctx.parent or ctx).get_help())


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, ValueError):
            pass
    app()


if __name__ == "__main__":
    main()
