#!/usr/bin/env python3
"""Bangun src/alkitab/data/ayt.db dari dataset CSV resmi AYT.

Sumber data : https://github.com/sabdacode/ayt  (folder csv/ayt.csv)
Pemakaian   : python scripts/build_db.py --csv /path/ke/ayt.csv [--commit <sha>]

Skema:
  verses(id, book, chapter, verse, text, title)   -- teks bersih, tanpa penanda <t />
  verses_fts                                       -- indeks FTS5 (tanpa aksen, tidak peka huruf besar/kecil)
  meta(key, value)                                 -- asal-usul data, dipakai oleh `alkitab license`
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sqlite3
import sys
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parent.parent / "src" / "alkitab" / "data" / "ayt.db"
SOURCE_URL = "https://github.com/sabdacode/ayt"

TAG_RE = re.compile(r"<[^>]*>")
SPACE_RE = re.compile(r"\s+")


def clean(value: str, *, br_as_space: bool = False) -> str:
    """Buang penanda inline (<t />, <br/>) dan rapikan spasi."""
    if br_as_space:
        value = re.sub(r"<br\s*/?>", " ", value)
    value = TAG_RE.sub("", value)
    return SPACE_RE.sub(" ", value).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", required=True, type=Path, help="path ke ayt.csv dari repo sabdacode/ayt")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--commit", default="unknown", help="SHA commit repo sumber (dicatat di meta)")
    args = ap.parse_args()

    with args.csv.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    # --- validasi dasar supaya data rusak tidak ikut terkemas ---
    books = {int(r["book"]) for r in rows}
    if books != set(range(1, 67)):
        sys.exit(f"Galat: harus ada 66 kitab (1..66), ditemukan: {sorted(books)[:5]}...")
    ids = [int(r["id"]) for r in rows]
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        sys.exit("Galat: kolom id tidak berurutan/unik")
    keys = [(int(r["book"]), int(r["chapter"]), int(r["verse"])) for r in rows]
    if len(set(keys)) != len(keys):
        sys.exit("Galat: ada ayat ganda (kitab, pasal, ayat)")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        args.out.unlink()

    db = sqlite3.connect(args.out)
    db.executescript(
        """
        CREATE TABLE verses (
            id      INTEGER PRIMARY KEY,
            book    INTEGER NOT NULL,
            chapter INTEGER NOT NULL,
            verse   INTEGER NOT NULL,
            text    TEXT    NOT NULL,
            title   TEXT    NOT NULL DEFAULT ''
        );
        CREATE UNIQUE INDEX idx_verses_ref ON verses (book, chapter, verse);
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """
    )
    empty = 0
    for r in rows:
        text = clean(r["text"])
        if not text:
            empty += 1
        db.execute(
            "INSERT INTO verses (id, book, chapter, verse, text, title) VALUES (?,?,?,?,?,?)",
            (int(r["id"]), int(r["book"]), int(r["chapter"]), int(r["verse"]), text, clean(r["title"], br_as_space=True)),
        )
    if empty:
        sys.exit(f"Galat: {empty} ayat berteks kosong setelah dibersihkan")

    db.executescript(
        """
        CREATE VIRTUAL TABLE verses_fts USING fts5(
            text, content='verses', content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        );
        INSERT INTO verses_fts(verses_fts) VALUES ('rebuild');
        INSERT INTO verses_fts(verses_fts) VALUES ('optimize');
        """
    )
    meta = {
        "translation": "AYT",
        "translation_name": "Alkitab Yang Terbuka",
        "source_url": SOURCE_URL,
        "source_commit": args.commit,
        "built_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "verse_count": str(len(rows)),
    }
    db.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())
    db.commit()
    db.execute("VACUUM")
    db.close()

    size = args.out.stat().st_size / 1_048_576
    print(f"OK: {len(rows)} ayat -> {args.out} ({size:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
