"""Parser referensi Alkitab: "Yoh 3:16", "1 Kor 13:4-7", "Mat 5:3-7:29", "Yud 5", "Mzm 23".

Urutan pengenalan nama kitab:
  1. cocok persis dengan alias           ("yoh", "1kor", "kisah para rasul")
  2. cocok awalan yang tidak ambigu       ("yehez" -> Yehezkiel)
  3. salah ketik dengan kemiripan tinggi  ("yohanse" -> Yohanes, diberi tahu ke pengguna)
Selain itu pengguna diberi pesan yang jelas: ambigu ("Kor" -> 1 Korintus / 2 Korintus)
atau tidak dikenal (disertai saran).
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set

from .books import BOOKS, EXACT, MIN_PREFIX_LEN, SINGLE_CHAPTER, STEMS, Book, normalize


# ---------------------------------------------------------------------------
# Galat
# ---------------------------------------------------------------------------
class AlkitabError(Exception):
    """Galat yang aman ditampilkan apa adanya ke pengguna."""

    def __init__(self, message: str, hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.hint = hint


class UnknownBookError(AlkitabError):
    pass


class AmbiguousBookError(AlkitabError):
    pass


class ReferenceSyntaxError(AlkitabError):
    pass


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Segment:
    """Rentang ayat. v1=None berarti awal pasal ch1; v2=None berarti akhir pasal ch2."""

    ch1: int
    v1: Optional[int]
    ch2: int
    v2: Optional[int]


@dataclass
class BookMatch:
    book: Book
    how: str  # "exact" | "prefix" | "fuzzy"
    typed: str


@dataclass
class Reference:
    match: BookMatch
    segments: List[Segment] = field(default_factory=list)

    @property
    def book(self) -> Book:
        return self.match.book


# ---------------------------------------------------------------------------
# Pengenalan kitab
# ---------------------------------------------------------------------------
_KEYS_UNNUMBERED = [k for k in EXACT if not k[0].isdigit()]
_KEYS_ALL = list(EXACT)


def _names(ids: Sequence[int]) -> str:
    return ", ".join(BOOKS[i].name for i in sorted(ids))


def resolve_book(typed: str) -> BookMatch:
    key = normalize(typed)
    if not key:
        raise UnknownBookError("Nama kitab kosong.", "Contoh: alkitab Yoh 3:16")

    # 1. persis
    if key in EXACT:
        return BookMatch(BOOKS[EXACT[key]], "exact", typed)

    # 2. awalan / nomor kitab terlupa (hanya diterima jika tidak ambigu)
    if len(key) >= MIN_PREFIX_LEN:
        cands: Set[int] = {EXACT[k] for k in EXACT if k.startswith(key)}
        if not key[0].isdigit():
            for stem, ids in STEMS.items():
                if stem.startswith(key):
                    cands |= ids
        if len(cands) == 1:
            return BookMatch(BOOKS[next(iter(cands))], "prefix", typed)
        if len(cands) > 1:
            numbered_only = all(BOOKS[i].name[0].isdigit() for i in cands)
            raise AmbiguousBookError(
                f"'{typed}' bisa berarti: {_names(cands)}.",
                f"Tambahkan nomor kitab, misalnya: 1 {typed}" if numbered_only
                else "Ketik sedikit lebih panjang, misalnya nama kitabnya.",
            )

    # 3. salah ketik
    pool = _KEYS_ALL if key[0].isdigit() else _KEYS_UNNUMBERED + list(STEMS)
    score: Dict[int, float] = {}          # id kitab -> kemiripan terbaik
    for cand in difflib.get_close_matches(key, pool, n=10, cutoff=0.6):
        ratio = difflib.SequenceMatcher(None, key, cand).ratio()
        for book_id in ({EXACT[cand]} if cand in EXACT else STEMS[cand]):
            score[book_id] = max(score.get(book_id, 0.0), ratio)
    ranked = sorted(score.items(), key=lambda kv: -kv[1])
    # diterima otomatis hanya bila jelas unggul: cukup mirip DAN tidak ada pesaing yang hampir sama
    if ranked and len(key) >= 4 and ranked[0][1] >= 0.8 and (len(ranked) == 1 or ranked[1][1] <= ranked[0][1] - 0.08):
        return BookMatch(BOOKS[ranked[0][0]], "fuzzy", typed)
    if ranked:
        suggestions = ", ".join(BOOKS[i].name for i, r in ranked[:3] if r >= ranked[0][1] - 0.15)
        raise UnknownBookError(f"Kitab '{typed}' tidak dikenal.", f"Maksud Anda: {suggestions}?")
    raise UnknownBookError(f"Kitab '{typed}' tidak dikenal.", "Lihat daftar kitab dengan: alkitab list-kitab")


# ---------------------------------------------------------------------------
# Pasal & ayat
# ---------------------------------------------------------------------------
_LEADING_NUM_RE = re.compile(r"([123])\s*\.?\s*(?=[^\W\d_])")
_NAME_REF_RE = re.compile(r"(?P<name>[^\W\d_][^\d:]*?)\s*(?P<ref>\d.*)?$", re.UNICODE)
_ITEM_RE = re.compile(r"(\d+)(?::(\d+))?(?:-(\d+)(?::(\d+))?)?")


def _num(value: str) -> int:
    n = int(value)
    if n < 1:
        raise ReferenceSyntaxError("Nomor pasal dan ayat dimulai dari 1.")
    return n


def parse_spec(spec: str, single_chapter: bool) -> List[Segment]:
    """Urai bagian angka: '3:16', '28:16-20', '3:16,18-20', '5:3-7:29', '1-3', '5,7'."""
    spec = re.sub(r"[\s]", "", spec.replace("–", "-").replace("—", "-"))
    segments: List[Segment] = []
    ctx_chapter: Optional[int] = 1 if single_chapter else None
    verse_mode = single_chapter

    for item in spec.split(","):
        if not item:
            continue
        m = _ITEM_RE.fullmatch(item)
        if not m:
            raise ReferenceSyntaxError(
                f"Format pasal/ayat tidak dikenali: '{item}'.",
                "Contoh yang benar: 3:16  28:16-20  3:16,18  5:3-7:29",
            )
        a, b, c, d = m.groups()
        if b is None and d is None:                       # "a" atau "a-c"
            lo = _num(a)
            hi = _num(c) if c else lo
            if hi < lo:
                raise ReferenceSyntaxError(f"Rentang terbalik: '{item}'.")
            if verse_mode:
                segments.append(Segment(ctx_chapter or 1, lo, ctx_chapter or 1, hi))
            else:
                segments.append(Segment(lo, None, hi, None))
        elif b is not None:                               # "a:b", "a:b-d", "a:b-c:d"
            ch, v1 = _num(a), _num(b)
            if c is None:
                ch2, v2 = ch, v1
            elif d is None:
                ch2, v2 = ch, _num(c)
            else:
                ch2, v2 = _num(c), _num(d)
            if (ch2, v2) < (ch, v1):
                raise ReferenceSyntaxError(f"Rentang terbalik: '{item}'.")
            segments.append(Segment(ch, v1, ch2, v2))
            ctx_chapter, verse_mode = ch2, True
        else:                                             # "a-c:d": dari awal pasal a sampai c:d
            ch, ch2, v2 = _num(a), _num(c), _num(d)
            if ch2 < ch:
                raise ReferenceSyntaxError(f"Rentang terbalik: '{item}'.")
            segments.append(Segment(ch, None, ch2, v2))
    return segments


def parse_reference(text: str) -> Reference:
    """Urai teks bebas menjadi Reference. Tanpa angka -> segments kosong (hanya nama kitab)."""
    s = text.strip()
    if not s:
        raise ReferenceSyntaxError("Referensi kosong.", "Contoh: alkitab Yoh 3:16")

    prefix = ""
    m = _LEADING_NUM_RE.match(s)
    if m:
        prefix, s = m.group(1), s[m.end():]

    m = _NAME_REF_RE.match(s)
    if not m:
        raise ReferenceSyntaxError(
            f"Tidak bisa membaca referensi '{text}'.",
            "Contoh: alkitab Yoh 3:16  |  alkitab 1 Kor 13  |  alkitab Mat 28:16-20",
        )
    name = (prefix + " " if prefix else "") + m.group("name").strip()
    match = resolve_book(name)
    ref_part = (m.group("ref") or "").strip()
    segments = parse_spec(ref_part, match.book.id in SINGLE_CHAPTER) if ref_part else []
    return Reference(match, segments)


# ---------------------------------------------------------------------------
# Format tampilan
# ---------------------------------------------------------------------------
def format_label(book: Book, segments: Sequence[Segment]) -> str:
    """Susun label rapi: 'Matius 28:16-20', 'Yohanes 3:16,18-20', 'Yudas 5'."""
    if not segments:
        return book.name
    single = book.id in SINGLE_CHAPTER
    parts: List[str] = []
    last_chapter: Optional[int] = None
    prev_whole = False
    for s in segments:
        if s.v1 is None and s.v2 is None:                 # pasal penuh
            text = str(s.ch1) if s.ch1 == s.ch2 else f"{s.ch1}-{s.ch2}"
            if prev_whole:
                parts[-1] += f",{text}"
            else:
                parts.append(text)
            prev_whole, last_chapter = True, None
            continue
        prev_whole = False
        v1 = s.v1 if s.v1 is not None else 1
        if s.ch1 == s.ch2:
            vs = str(v1) if s.v2 == v1 else f"{v1}-{s.v2}"
            if single:
                parts.append(vs)
            elif last_chapter == s.ch1:
                parts[-1] += f",{vs}"
            else:
                parts.append(f"{s.ch1}:{vs}")
        else:
            end = f"{s.ch2}:{s.v2}" if s.v2 is not None else str(s.ch2)
            parts.append(f"{s.ch1}:{v1}-{end}")
            last_chapter = None
            continue
        last_chapter = s.ch1
    return f"{book.name} " + "; ".join(parts)
