import datetime as dt
import json

import pytest
from typer.testing import CliRunner

from alkitab import daily
from alkitab.cli import app

runner = CliRunner()


def run(*args):
    return runner.invoke(app, list(args))


def test_default_command_reads_reference():
    r = run("Yoh", "3:16")
    assert r.exit_code == 0
    assert "Yohanes 3:16" in r.output and "mengasihi dunia ini" in r.output


def test_explicit_read_equals_implicit():
    assert run("read", "Yoh", "3:16").output == run("Yoh", "3:16").output


def test_numbered_book_as_first_word_is_not_mistaken_for_command():
    r = run("1", "Kor", "13:4-7", "--plain")
    assert r.exit_code == 0
    assert r.output.startswith("1 Korintus 13:4-7 (AYT)")


def test_options_after_reference():
    r = run("Mat", "28:16-20", "--json")
    data = json.loads(r.output)
    assert data["reference"] == "Matius 28:16-20"
    assert [v["verse"] for v in data["verses"]] == [16, 17, 18, 19, 20]


def test_json_carries_license_notice():
    data = json.loads(run("Yoh", "3:16", "--json").output)
    assert data["translation"] == "AYT"
    assert "YLSA" in data["copyright"] and "CC BY-NC-SA" in data["terms"]


def test_rich_output_has_attribution_footer_on_one_line_but_plain_does_not_clutter():
    out = run("Yoh", "3:16").output
    footer = [ln for ln in out.splitlines() if "alkitab license" in ln]
    assert footer and "YLSA" in footer[0] and len(footer[0]) <= 80   # tidak terpotong di terminal 80 kolom
    assert "alkitab license" not in run("Yoh", "3:16", "--plain").output


def test_headings_toggle():
    assert "Permulaan Penciptaan" in run("Kej", "1:1", "--plain").output
    assert "Permulaan Penciptaan" not in run("Kej", "1:1", "--plain", "--no-headings").output


@pytest.mark.parametrize("args,code", [
    (("Xyz", "1:1"), 2),
    (("Kor", "13"), 2),
    (("Mat", "99"), 2),
    (("Mat", "1:5-2"), 2),
    (("read",), 2),
])
def test_errors_exit_2(args, code):
    r = run(*args)
    assert r.exit_code == code


def test_book_only_shows_chapter_count():
    r = run("Yohanes")
    assert r.exit_code == 0 and "21 pasal" in r.output


def test_fuzzy_note_goes_to_stderr_not_json():
    r = run("Yohanse", "3:16", "--json")
    assert r.exit_code == 0
    assert json.loads(r.stdout)["reference"] == "Yohanes 3:16"


def test_search_basic_and_exit_codes():
    assert run("search", "kasih karunia", "-n", "2").exit_code == 0
    r = run("search", "zzzqqq")
    assert r.exit_code == 1 and "Tidak ada ayat" in r.output


def test_search_single_quoted_arg_is_phrase_and_multiple_args_are_and():
    phrase = json.loads(run("search", "kasih karunia", "--json", "-n", "1").stdout)["total"]
    both = json.loads(run("search", "kasih", "karunia", "--json", "-n", "1").stdout)["total"]
    assert 0 < phrase <= both


def test_search_book_filter():
    data = json.loads(run("search", "kasih", "-k", "Mzm", "--json", "-n", "50").stdout)
    assert data["results"] and all(x["reference"].startswith("Mazmur") for x in data["results"])


def test_today_is_deterministic():
    a = run("today", "--date", "2026-12-25", "--plain").output
    assert a == run("today", "--date", "2026-12-25", "--plain").output
    assert daily.pick(dt.date(2026, 12, 25)) in daily.DAILY
    # hari berbeda -> ayat berbeda (daftar tidak berulang dalam 64 hari)
    assert daily.pick(dt.date(2026, 12, 25)) != daily.pick(dt.date(2026, 12, 26))


def test_today_bad_date():
    assert run("today", "--date", "25-12-2026").exit_code == 2


def test_random_json():
    data = json.loads(run("random", "--json").output)
    assert len(data["verses"]) == 1


def test_list_kitab():
    data = json.loads(run("list-kitab", "--json").output)
    assert len(data) == 66 and data[42]["name"] == "Yohanes" and data[42]["chapters"] == 21
    assert sum(b["chapters"] for b in data) == 1189


def test_license_command():
    r = run("license")
    assert r.exit_code == 0 and "Yayasan Lembaga SABDA" in r.output and "MIT" in r.output


def test_no_args_shows_help():
    r = run()
    assert "Contoh:" in r.output and "list-kitab" in r.output


def test_version():
    assert "alkitab-cli" in run("--version").output
