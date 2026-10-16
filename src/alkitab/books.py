"""Data 66 kitab dan tabel alias untuk pengenalan nama kitab.

Tabel alias dibuat dari daftar singkat per kitab (bukan daftar datar yang panjang), lalu
dinormalisasi lewat `normalize()` yang sama dengan yang dipakai parser. Akibatnya
"1 Kor", "1Kor", "I Kor", "1. Kor" dan "1 kor." semuanya menjadi kunci yang sama: `1kor`.

Alias Indonesia dan Inggris sengaja digabung: orang sering mengetik keduanya.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class Book:
    id: int
    name: str      # nama lengkap (Indonesia), dipakai untuk tampilan
    abbr: str      # singkatan resmi dataset AYT
    name_en: str


# (id, nama, singkatan AYT, nama Inggris)
_BOOKS: List[Tuple[int, str, str, str]] = [
    (1, "Kejadian", "Kej", "Genesis"),
    (2, "Keluaran", "Kel", "Exodus"),
    (3, "Imamat", "Im", "Leviticus"),
    (4, "Bilangan", "Bil", "Numbers"),
    (5, "Ulangan", "Ul", "Deuteronomy"),
    (6, "Yosua", "Yos", "Joshua"),
    (7, "Hakim-hakim", "Hak", "Judges"),
    (8, "Rut", "Rut", "Ruth"),
    (9, "1 Samuel", "1Sam", "1 Samuel"),
    (10, "2 Samuel", "2Sam", "2 Samuel"),
    (11, "1 Raja-raja", "1Raj", "1 Kings"),
    (12, "2 Raja-raja", "2Raj", "2 Kings"),
    (13, "1 Tawarikh", "1Taw", "1 Chronicles"),
    (14, "2 Tawarikh", "2Taw", "2 Chronicles"),
    (15, "Ezra", "Ezr", "Ezra"),
    (16, "Nehemia", "Neh", "Nehemiah"),
    (17, "Ester", "Est", "Esther"),
    (18, "Ayub", "Ayb", "Job"),
    (19, "Mazmur", "Mzm", "Psalms"),
    (20, "Amsal", "Ams", "Proverbs"),
    (21, "Pengkhotbah", "Pkh", "Ecclesiastes"),
    (22, "Kidung Agung", "Kid", "Song of Solomon"),
    (23, "Yesaya", "Yes", "Isaiah"),
    (24, "Yeremia", "Yer", "Jeremiah"),
    (25, "Ratapan", "Rat", "Lamentations"),
    (26, "Yehezkiel", "Yeh", "Ezekiel"),
    (27, "Daniel", "Dan", "Daniel"),
    (28, "Hosea", "Hos", "Hosea"),
    (29, "Yoel", "Yl", "Joel"),
    (30, "Amos", "Am", "Amos"),
    (31, "Obaja", "Ob", "Obadiah"),
    (32, "Yunus", "Yun", "Jonah"),
    (33, "Mikha", "Mi", "Micah"),
    (34, "Nahum", "Nah", "Nahum"),
    (35, "Habakuk", "Hab", "Habakkuk"),
    (36, "Zefanya", "Zef", "Zephaniah"),
    (37, "Hagai", "Hag", "Haggai"),
    (38, "Zakharia", "Za", "Zechariah"),
    (39, "Maleakhi", "Mal", "Malachi"),
    (40, "Matius", "Mat", "Matthew"),
    (41, "Markus", "Mrk", "Mark"),
    (42, "Lukas", "Luk", "Luke"),
    (43, "Yohanes", "Yoh", "John"),
    (44, "Kisah Para Rasul", "Kis", "Acts"),
    (45, "Roma", "Rm", "Romans"),
    (46, "1 Korintus", "1Kor", "1 Corinthians"),
    (47, "2 Korintus", "2Kor", "2 Corinthians"),
    (48, "Galatia", "Gal", "Galatians"),
    (49, "Efesus", "Ef", "Ephesians"),
    (50, "Filipi", "Flp", "Philippians"),
    (51, "Kolose", "Kol", "Colossians"),
    (52, "1 Tesalonika", "1Tes", "1 Thessalonians"),
    (53, "2 Tesalonika", "2Tes", "2 Thessalonians"),
    (54, "1 Timotius", "1Tim", "1 Timothy"),
    (55, "2 Timotius", "2Tim", "2 Timothy"),
    (56, "Titus", "Tit", "Titus"),
    (57, "Filemon", "Flm", "Philemon"),
    (58, "Ibrani", "Ibr", "Hebrews"),
    (59, "Yakobus", "Yak", "James"),
    (60, "1 Petrus", "1Ptr", "1 Peter"),
    (61, "2 Petrus", "2Ptr", "2 Peter"),
    (62, "1 Yohanes", "1Yoh", "1 John"),
    (63, "2 Yohanes", "2Yoh", "2 John"),
    (64, "3 Yohanes", "3Yoh", "3 John"),
    (65, "Yudas", "Yud", "Jude"),
    (66, "Wahyu", "Why", "Revelation"),
]

BOOKS: Dict[int, Book] = {b[0]: Book(*b) for b in _BOOKS}
OLD_TESTAMENT_LAST = 39

# Kitab yang hanya punya satu pasal: "Yud 5" berarti ayat 5, bukan pasal 5.
SINGLE_CHAPTER = frozenset({31, 57, 63, 64, 65})

# ---------------------------------------------------------------------------
# Alias kitab tanpa nomor.  Nama lengkap & singkatan AYT sudah otomatis masuk;
# di sini hanya variasi tambahan (Indonesia + Inggris).
# ---------------------------------------------------------------------------
_ALIASES: Dict[int, str] = {
    1: "kejd gen ge gn",
    2: "kluaran exod exo ex",
    3: "ima imm lev lv le",
    4: "bln num nm nu",
    5: "ula deut deu dt de",
    6: "josh jos",
    7: "hakim judg jdg jg",
    8: "rt ru rth",
    15: "ezra",
    16: "ne nh nehemiah",
    17: "es esth esther",
    18: "ay job jb",
    19: "maz mazm psalm ps psa pss psm",
    20: "prov pro prv pr",
    21: "pengkotbah pengkh penk eccl eccles ecc ec qoheleth",
    22: "kidung songofsolomon songofsongs song sos sng canticles",
    23: "yesa isa is",
    24: "jer je",
    25: "lam la",
    26: "yehez ezek eze",
    27: "dn da",
    28: "ho",
    29: "yoe jl joe joel",
    30: "amo",
    31: "oba obad",
    32: "yn jon jnh",
    33: "mik mikah mic",
    34: "na",
    35: "habakkuk hbk",
    36: "zep zeph",
    37: "haggai hg",
    38: "zakaria zak zech zec",
    39: "malaekhi ml",
    40: "mt matt mathew",
    41: "mar mk mr",
    42: "lu lk",
    43: "jhn jn joh",
    44: "kisahrasul kisah kpr act ac",
    45: "roma rom ro",
    48: "ga",
    49: "efe eph ep",
    50: "philippians phil php",
    51: "col",
    56: "tit",
    57: "flmn phm phlm",
    58: "heb",
    59: "yk jas jam jm",
    65: "jude jud",
    66: "wah wahy rev rv revelations wahyuyohanes",
}

# Kitab bernomor: pasangan (nomor, daftar "stem"). Kunci dibentuk f"{nomor}{stem}".
_NUMBERED: Dict[int, Tuple[int, str]] = {
    9: (1, "samuel sam sa"),
    10: (2, "samuel sam sa"),
    11: (1, "rajaraja raja raj ra kings kgs kin ki"),
    12: (2, "rajaraja raja raj ra kings kgs kin ki"),
    13: (1, "tawarikh taw ta chronicles chron chr ch"),
    14: (2, "tawarikh taw ta chronicles chron chr ch"),
    46: (1, "korintus kor ko corinthians cor co"),
    47: (2, "korintus kor ko corinthians cor co"),
    52: (1, "tesalonika tes te thessalonians thess thes th"),
    53: (2, "tesalonika tes te thessalonians thess thes th"),
    54: (1, "timotius tim ti timothy"),
    55: (2, "timotius tim ti timothy"),
    60: (1, "petrus ptr pet pe peter"),
    61: (2, "petrus ptr pet pe peter"),
    62: (1, "yohanes yoh yo john jhn jn joh"),
    63: (2, "yohanes yoh yo john jhn jn joh"),
    64: (3, "yohanes yoh yo john jhn jn joh"),
}

_ROMAN = {"i": "1", "ii": "2", "iii": "3"}
_ROMAN_RE = re.compile(r"^(iii|ii|i)[\s.]+(?=\S)")
_FILLER_RE = re.compile(r"^(kitab|surat|injil|book of|the book of)\s+")
_DROP_RE = re.compile(r"[\s.\-_']+")


def normalize(name: str) -> str:
    """Ubah nama kitab apa pun menjadi kunci pencarian.

    huruf kecil, buang kata pengantar ("Kitab", "Surat", "Injil"), I/II/III -> 1/2/3,
    lalu buang spasi, titik, dan tanda hubung.
    """
    s = name.strip().lower()
    s = _FILLER_RE.sub("", s)
    m = _ROMAN_RE.match(s)
    if m:
        s = _ROMAN[m.group(1)] + " " + s[m.end():]
    return _DROP_RE.sub("", s)


def _build() -> Tuple[Dict[str, int], Dict[str, Set[int]]]:
    exact: Dict[str, int] = {}
    stems: Dict[str, Set[int]] = {}

    def add(key: str, book_id: int) -> None:
        key = normalize(key)
        if not key:
            return
        if exact.get(key, book_id) != book_id:
            raise ValueError(f"alias ganda: {key!r} -> {exact[key]} dan {book_id}")
        exact[key] = book_id

    for book in BOOKS.values():
        add(book.name, book.id)
        add(book.abbr, book.id)
        add(book.name_en, book.id)
        for alias in _ALIASES.get(book.id, "").split():
            add(alias, book.id)
        if book.id in _NUMBERED:
            number, words = _NUMBERED[book.id]
            for stem in words.split():
                add(f"{number}{stem}", book.id)
                stems.setdefault(normalize(stem), set()).add(book.id)
    return exact, stems


# EXACT: kunci -> id kitab.  STEMS: "kor" -> {46, 47} (untuk pesan ambigu saat nomor lupa diketik).
EXACT, STEMS = _build()

# Kata yang tidak boleh dipakai pencocokan awalan karena terlalu pendek/ambigu secara alami.
MIN_PREFIX_LEN = 2
