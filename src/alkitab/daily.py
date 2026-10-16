"""Daftar ayat pilihan untuk `alkitab today`.

Hanya berisi referensi (bukan teks); teksnya selalu diambil dari database AYT.
Ayat dipilih berdasarkan tanggal, jadi semua orang mendapat ayat yang sama pada hari yang sama.
"""
from __future__ import annotations

import datetime as dt
from typing import List

DAILY: List[str] = [
    "Yoh 3:16", "Mzm 23:1-4", "Flp 4:6-7", "Rm 8:28", "Yer 29:11", "Yes 41:10", "Ams 3:5-6", "Mat 11:28-30",
    "Mat 6:33", "Rm 12:2", "Yos 1:9", "Mzm 121:1-2", "1Kor 13:4-7", "Gal 5:22-23", "Ef 2:8-9", "Mzm 119:105",
    "2Tim 1:7", "Ibr 11:1", "1Yoh 4:19", "2Kor 5:17", "Mzm 27:1", "Mzm 37:4-5", "Mzm 91:1-2", "Mzm 118:24",
    "Yes 40:31", "Rat 3:22-23", "Mi 6:8", "Ul 31:6", "Mat 28:19-20", "Mrk 12:30-31", "Luk 1:37", "Yoh 14:6",
    "Yoh 14:27", "Yoh 15:5", "Kis 1:8", "Rm 5:8", "Rm 6:23", "Rm 10:9", "Rm 15:13", "1Kor 10:13",
    "2Kor 12:9", "Kol 3:23", "1Tes 5:16-18", "Ibr 4:16", "Ibr 13:8", "Yak 1:5", "1Ptr 5:7", "1Yoh 1:9",
    "Why 21:4", "Ams 18:10", "Ams 16:3", "Pkh 3:1", "Yes 26:3", "Yes 43:2", "Yeh 36:26", "Hab 3:17-18",
    "Zef 3:17", "Mat 7:7-8", "Mat 5:16", "Luk 6:31", "Kej 1:1", "Kel 14:14", "Bil 6:24-26", "Ayb 19:25",
]


def pick(day: dt.date) -> str:
    return DAILY[day.toordinal() % len(DAILY)]


_DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_MONTHS = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def format_date_id(day: dt.date) -> str:
    return f"{_DAYS[day.weekday()]}, {day.day} {_MONTHS[day.month - 1]} {day.year}"
