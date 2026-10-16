import pytest

from alkitab.books import BOOKS, EXACT, normalize
from alkitab.parser import (
    AmbiguousBookError,
    ReferenceSyntaxError,
    Segment,
    UnknownBookError,
    format_label,
    parse_reference,
    resolve_book,
)


# --- tabel alias ------------------------------------------------------------
def test_66_books_and_every_book_reachable_by_name_abbr_and_english():
    assert len(BOOKS) == 66
    for b in BOOKS.values():
        for alias in (b.name, b.abbr, b.name_en):
            assert EXACT[normalize(alias)] == b.id, alias


@pytest.mark.parametrize("typed", ["1 Kor", "1Kor", "I Kor", "i kor", "1. Kor", "1 kor.", "1 Korintus", "1 Cor", "I Corinthians", "Surat 1 Korintus"])
def test_numbered_book_variants(typed):
    assert resolve_book(typed).book.id == 46


@pytest.mark.parametrize("typed,book_id", [
    ("yoh", 43), ("Yohanes", 43), ("John", 43), ("Injil Yohanes", 43),
    ("Kisah Para Rasul", 44), ("kis", 44), ("Acts", 44),
    ("Hakim-hakim", 7), ("hakim hakim", 7),
    ("Kidung Agung", 22), ("Song of Songs", 22),
    ("Dan", 27), ("Daniel", 27),            # Daniel tidak ada di peta alias PHP lama
    ("II Tesalonika", 53),                  # di PHP lama salah menunjuk ke 54
    ("Im", 3), ("Ibr", 58), ("Why", 66), ("Rev", 66),
    ("Mzm", 19), ("Ps", 19), ("Mazmur", 19),
])
def test_exact_aliases(typed, book_id):
    m = resolve_book(typed)
    assert m.book.id == book_id and m.how == "exact"


def test_unambiguous_prefix():
    m = resolve_book("yehezk")
    assert (m.book.id, m.how) == (26, "prefix")


@pytest.mark.parametrize("typed,expected", [("Yohanse", 43), ("Mathius", 40), ("Efesuss", 49), ("1 Korintos", 46)])
def test_typo_is_accepted_only_when_clearly_best(typed, expected):
    m = resolve_book(typed)
    assert (m.book.id, m.how) == (expected, "fuzzy")


@pytest.mark.parametrize("typed", ["Kor", "Sam", "Tes", "Tim", "Ma", "Fil", "Yo"])
def test_ambiguous_names_are_not_guessed(typed):
    with pytest.raises(AmbiguousBookError):
        resolve_book(typed)


def test_unknown_book_has_hint():
    with pytest.raises(UnknownBookError) as e:
        resolve_book("zzzz")
    assert "list-kitab" in e.value.hint


# --- referensi --------------------------------------------------------------
def seg(*a):
    return Segment(*a)


@pytest.mark.parametrize("text,book_id,segments,label", [
    ("Yoh 3:16", 43, [seg(3, 16, 3, 16)], "Yohanes 3:16"),
    ("yoh3:16", 43, [seg(3, 16, 3, 16)], "Yohanes 3:16"),
    ("Mat 28:16-20", 40, [seg(28, 16, 28, 20)], "Matius 28:16-20"),
    ("Mzm 23", 19, [seg(23, None, 23, None)], "Mazmur 23"),
    ("Mat 5-7", 40, [seg(5, None, 7, None)], "Matius 5-7"),
    ("Mat 5:3-7:29", 40, [seg(5, 3, 7, 29)], "Matius 5:3-7:29"),
    ("Yoh 3:16,18-20", 43, [seg(3, 16, 3, 16), seg(3, 18, 3, 20)], "Yohanes 3:16,18-20"),
    ("Mat 5,7", 40, [seg(5, None, 5, None), seg(7, None, 7, None)], "Matius 5,7"),
    ("1Kor13:4–7", 46, [seg(13, 4, 13, 7)], "1 Korintus 13:4-7"),   # en dash
    ("II Tes 2", 53, [seg(2, None, 2, None)], "2 Tesalonika 2"),
])
def test_references(text, book_id, segments, label):
    ref = parse_reference(text)
    assert ref.book.id == book_id
    assert ref.segments == segments
    assert format_label(ref.book, ref.segments) == label


def test_single_chapter_books_treat_number_as_verse():
    ref = parse_reference("Yud 5")
    assert ref.segments == [seg(1, 5, 1, 5)]
    assert format_label(ref.book, ref.segments) == "Yudas 5"
    assert parse_reference("3 Yoh 4-6").segments == [seg(1, 4, 1, 6)]
    assert parse_reference("Obaja 1:3").segments == [seg(1, 3, 1, 3)]


def test_book_only_has_no_segments():
    ref = parse_reference("Yohanes")
    assert ref.segments == [] and ref.book.id == 43


@pytest.mark.parametrize("bad", ["Mat 1:5-2", "Mat 7-5", "Yoh 0:1", "Yoh 3:0", "Yoh 3:16:2", "Yoh 3::16"])
def test_bad_syntax(bad):
    with pytest.raises(ReferenceSyntaxError):
        parse_reference(bad)


def test_empty():
    with pytest.raises(ReferenceSyntaxError):
        parse_reference("   ")
