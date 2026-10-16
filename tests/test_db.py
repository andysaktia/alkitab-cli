import re

import pytest

from alkitab import legal
from alkitab.daily import DAILY
from alkitab.db import HL_OFF, HL_ON, Bible, NotFoundError, RangeError, build_match_query
from alkitab.parser import parse_reference
from alkitab.render import _marked_to_text


@pytest.fixture(scope="module")
def bible():
    return Bible()


def fetch(bible, text):
    return bible.fetch(parse_reference(text))


def test_dataset_integrity(bible):
    meta = bible.meta()
    assert meta["translation"] == "AYT"
    assert int(meta["verse_count"]) == 31102
    counts = bible.chapter_counts()
    assert len(counts) == 66 and sum(counts.values()) == 1189   # 1189 pasal dalam 66 kitab


def test_single_verse(bible):
    p = fetch(bible, "Yoh 3:16")
    assert len(p.verses) == 1
    assert p.verses[0].text.startswith("Karena Allah sangat mengasihi dunia ini")


def test_no_markup_left_in_text(bible):
    for ref in ("Kej 1", "Mat 5", "Mzm 23"):
        for v in fetch(bible, ref).verses:
            assert "<" not in v.text and "  " not in v.text


def test_whole_chapter_and_range(bible):
    assert len(fetch(bible, "Mat 28").verses) == 20
    assert len(fetch(bible, "Mat 28:16-20").verses) == 5
    assert len(fetch(bible, "Kej 1-2").verses) == 31 + 25


def test_cross_chapter_range(bible):
    p = fetch(bible, "Mat 5:3-7:29")
    assert (p.verses[0].chapter, p.verses[0].verse) == (5, 3)
    assert (p.verses[-1].chapter, p.verses[-1].verse) == (7, 29)
    assert len(p.verses) == 109


def test_multi_segment_is_ordered_and_deduplicated(bible):
    p = fetch(bible, "Yoh 3:18,16,16")
    assert [v.verse for v in p.verses] == [16, 18]


def test_single_chapter_book(bible):
    assert fetch(bible, "Yud 3-5").verses[0].verse == 3


def test_headings_present(bible):
    assert fetch(bible, "Kej 1:1").verses[0].heading == "Permulaan Penciptaan"


@pytest.mark.parametrize("text,fragment", [
    ("Mat 99", "28 pasal"),
    ("Mat 28:99", "20 ayat"),
    ("Yud 99", "25 ayat"),
])
def test_range_errors(bible, text, fragment):
    with pytest.raises(RangeError) as e:
        fetch(bible, text)
    assert fragment in e.value.message


def test_random_verse_is_substantial(bible):
    assert len(bible.random_verse().text) >= 40


# --- pencarian ---------------------------------------------------------------
def test_search_phrase_vs_words(bible):
    phrase, _ = bible.search('"kasih karunia"', limit=1)
    words, _ = bible.search("kasih karunia", limit=1)
    assert 0 < phrase <= words


def test_search_prefix_and_book_filter(bible):
    total_all, _ = bible.search("kasih*", limit=1)
    total_mzm, hits = bible.search("kasih*", book=19, limit=5)
    assert total_all > total_mzm > 0
    assert all(h.book == 19 for h in hits)


def test_search_pagination_is_canonical_order(bible):
    _, page1 = bible.search("kasih", limit=3)
    _, page2 = bible.search("kasih", limit=3, offset=3)
    keys = [(h.book, h.chapter, h.verse) for h in page1 + page2]
    assert keys == sorted(keys)


def test_search_highlights_matches(bible):
    _, hits = bible.search("karunia", limit=1)
    assert HL_ON in hits[0].marked
    text = _marked_to_text(hits[0].marked)
    assert HL_ON not in text.plain
    assert any("yellow" in str(s.style) for s in text.spans)


@pytest.mark.parametrize("raw", ['kasih: (-', "AND OR NOT", '"', "kasih*", "^kasih", "a:b", "*"])
def test_search_never_raises_fts_syntax_errors(bible, raw):
    q = build_match_query(raw)
    if q is not None:
        bible.search(raw, limit=1)


def test_build_match_query():
    assert build_match_query('kasih "kasih karunia" setia*') == '"kasih" "kasih karunia" "setia"*'
    assert build_match_query("  ") is None
    assert build_match_query("-- :: ()") is None


# --- ayat harian -------------------------------------------------------------
def test_every_daily_reference_exists_and_is_unique(bible):
    assert len(set(DAILY)) == len(DAILY)
    for ref in DAILY:
        assert fetch(bible, ref).verses, ref


# --- hukum -------------------------------------------------------------------
def test_license_text_contains_required_notices(bible):
    text = legal.license_text(bible.meta())
    for needle in ("Yayasan Lembaga SABDA", "Non-Commercial", "Shareable", "Trademarks", "ylsa@sabda.org",
                   "TIDAK resmi", "sabdacode/ayt", "bukan nasihat hukum"):
        assert needle in text, needle
    assert re.search(r"commit [0-9a-f]{12}", text)
