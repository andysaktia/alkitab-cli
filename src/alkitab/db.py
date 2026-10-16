"""Akses database AYT (SQLite, hanya-baca) yang ikut terpasang di dalam paket."""
from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .books import BOOKS, Book
from .parser import AlkitabError, Reference, Segment, format_label

HL_ON, HL_OFF = "\x02", "\x03"   # penanda sorotan FTS; diubah menjadi gaya oleh render.py
_BIG = 10**6


class RangeError(AlkitabError):
    """Pasal/ayat di luar jangkauan kitab."""


class NotFoundError(AlkitabError):
    pass


@dataclass(frozen=True)
class Verse:
    id: int
    book: int
    chapter: int
    verse: int
    text: str
    heading: str = ""


@dataclass
class Passage:
    book: Book
    label: str
    verses: List[Verse]


@dataclass(frozen=True)
class Hit:
    book: int
    chapter: int
    verse: int
    marked: str   # teks dengan penanda HL_ON/HL_OFF


def default_db_path() -> Path:
    override = os.environ.get("ALKITAB_DB")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "data" / "ayt.db"


class Bible:
    def __init__(self, path: Optional[Path] = None):
        path = Path(path) if path else default_db_path()
        if not path.exists():
            raise AlkitabError(
                f"Database tidak ditemukan: {path}",
                "Bangun dengan: python scripts/build_db.py --csv <ayt.csv>",
            )
        self._con = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        self._con.row_factory = sqlite3.Row

    # -- metadata -----------------------------------------------------------
    def meta(self) -> Dict[str, str]:
        return {r["key"]: r["value"] for r in self._con.execute("SELECT key, value FROM meta")}

    def chapter_counts(self) -> Dict[int, int]:
        rows = self._con.execute("SELECT book, MAX(chapter) AS n FROM verses GROUP BY book")
        return {r["book"]: r["n"] for r in rows}

    def _max_verse(self, book: int, chapter: int) -> Optional[int]:
        row = self._con.execute(
            "SELECT MAX(verse) AS n FROM verses WHERE book=? AND chapter=?", (book, chapter)
        ).fetchone()
        return row["n"]

    # -- baca ---------------------------------------------------------------
    def _validate(self, book: Book, seg: Segment, max_chapter: int) -> None:
        for ch in (seg.ch1, seg.ch2):
            if ch > max_chapter:
                raise RangeError(
                    f"{book.name} hanya memiliki {max_chapter} pasal." if max_chapter > 1
                    else f"{book.name} hanya memiliki 1 pasal.",
                )
        for ch, v in ((seg.ch1, seg.v1), (seg.ch2, seg.v2)):
            if v is None:
                continue
            top = self._max_verse(book.id, ch)
            if top is None or v > top:
                where = f"{book.name} {ch}" if max_chapter > 1 else book.name
                raise RangeError(f"{where} hanya memiliki {top} ayat.")

    def _rows(self, book_id: int, seg: Segment) -> List[Verse]:
        lo = (seg.ch1, seg.v1 if seg.v1 is not None else 1)
        hi = (seg.ch2, seg.v2 if seg.v2 is not None else _BIG)
        rows = self._con.execute(
            "SELECT id, book, chapter, verse, text, title FROM verses "
            "WHERE book=? AND (chapter, verse) >= (?, ?) AND (chapter, verse) <= (?, ?) ORDER BY id",
            (book_id, *lo, *hi),
        )
        return [Verse(r["id"], r["book"], r["chapter"], r["verse"], r["text"], r["title"]) for r in rows]

    def fetch(self, ref: Reference) -> Passage:
        book = ref.book
        max_chapter = self.chapter_counts()[book.id]
        verses: List[Verse] = []
        seen = set()
        for seg in ref.segments:
            self._validate(book, seg, max_chapter)
            for v in self._rows(book.id, seg):
                if v.id not in seen:
                    seen.add(v.id)
                    verses.append(v)
        if not verses:
            raise NotFoundError(f"Tidak ada ayat untuk {format_label(book, ref.segments)}.")
        verses.sort(key=lambda v: v.id)
        return Passage(book, format_label(book, ref.segments), verses)

    def random_verse(self, min_length: int = 40) -> Verse:
        r = self._con.execute(
            "SELECT id, book, chapter, verse, text, title FROM verses "
            "WHERE length(text) >= ? ORDER BY random() LIMIT 1",
            (min_length,),
        ).fetchone()
        return Verse(r["id"], r["book"], r["chapter"], r["verse"], r["text"], r["title"])

    # -- cari ---------------------------------------------------------------
    def search(
        self, query: str, *, book: Optional[int] = None, limit: int = 20, offset: int = 0
    ) -> Tuple[int, List[Hit]]:
        match = build_match_query(query)
        if match is None:
            raise AlkitabError("Kata kunci pencarian kosong.", 'Contoh: alkitab search "kasih karunia"')
        where = "verses_fts MATCH ?" + (" AND v.book = ?" if book else "")
        params: List[object] = [match] + ([book] if book else [])
        total = self._con.execute(
            f"SELECT count(*) FROM verses_fts JOIN verses v ON v.id = verses_fts.rowid WHERE {where}", params
        ).fetchone()[0]
        rows = self._con.execute(
            f"SELECT v.book, v.chapter, v.verse, highlight(verses_fts, 0, ?, ?) AS marked "
            f"FROM verses_fts JOIN verses v ON v.id = verses_fts.rowid WHERE {where} "
            f"ORDER BY v.id LIMIT ? OFFSET ?",
            [HL_ON, HL_OFF, *params, limit, offset],
        )
        return total, [Hit(r["book"], r["chapter"], r["verse"], r["marked"]) for r in rows]

    def close(self) -> None:
        self._con.close()


_QUERY_TOKEN_RE = re.compile(r'"([^"]+)"|(\S+)')
_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


def build_match_query(raw: str) -> Optional[str]:
    """Ubah input pengguna menjadi kueri FTS5 yang aman.

    - kata biasa digabung dengan AND
    - "frasa dalam tanda kutip" dicari sebagai frasa
    - kata*  -> pencarian awalan
    Karakter khusus FTS5 (: - ( ) ^ dll.) dibuang sehingga tidak pernah menimbulkan galat sintaks.
    """
    parts: List[str] = []
    for phrase, word in _QUERY_TOKEN_RE.findall(raw):
        if phrase:
            words = _WORD_RE.findall(phrase)
            if words:
                parts.append('"' + " ".join(words) + '"')
        else:
            words = _WORD_RE.findall(word)
            if not words:
                continue
            for i, w in enumerate(words):
                star = "*" if (word.endswith("*") and i == len(words) - 1) else ""
                parts.append(f'"{w}"{star}')
    return " ".join(parts) if parts else None


def book_by_id(book_id: int) -> Book:
    return BOOKS[book_id]
