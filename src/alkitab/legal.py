"""Informasi lisensi, atribusi, dan batasan hukum yang ditampilkan `alkitab license`."""
from __future__ import annotations

from typing import Dict

# Kutipan persis dari LICENSE.html pada https://github.com/sabdacode/ayt
AYT_TERMS_ORIGINAL = [
    "AYT is Alkitab Yang Terbuka, PB (2010,..-2024) and PL (2014,...2024).",
    "AYT - text is Copyrighted, YLSA-AYT 2011,2024© -- this is to preserve and protect the quality of the Text. "
    "Suggestions, Comments, Changes, Corrections are encouraged, and can be submitted to YLSA-AYT.",
    "AYT - usage (non-commercial) is CopyLefted, 2011\U0001f12f -- this is to allow free usage/distribution of the text",
    "AYT - derivatives (form, format, media, tools, resources) is CC, YLSA-AYT 2011(cc) -- we encourage you to use the "
    "AYT in creative ways, and to share the results. Creative Commons(CC) type is Credit(BY), Non-Commercial(NC), "
    "Shareable(SA)",
    "AYT - translation license is freely given, 2011-2024 -- information and/or reporting is appreciated, but not required.",
    "AYT permissions are managed by YLSA.",
    "AYT (and Alkitab Yang Terbuka) name are Trademarks associated with the AYT Bible, and AYT ecosystem/tools.",
]

SHORT_ATTRIBUTION = "Alkitab Yang Terbuka (AYT) © Yayasan Lembaga SABDA (YLSA)"
# Sengaja pendek (< 80 kolom) supaya tidak terpotong di terminal sempit.
FOOTER = "Alkitab Yang Terbuka (AYT) © YLSA · ketentuan: alkitab license"

JSON_NOTICE = {
    "translation": "AYT",
    "translation_name": "Alkitab Yang Terbuka",
    "copyright": "© Yayasan Lembaga SABDA (YLSA)",
    "terms": "Pemakaian non-komersial. Turunan: CC BY-NC-SA. Jalankan `alkitab license` untuk ketentuan lengkap.",
    "source": "https://ayt.co",
}

URLS = {
    "AYT": "https://ayt.co",
    "YLSA": "https://ylsa.org",
    "Dataset": "https://github.com/sabdacode/ayt",
    "Kontak": "ylsa@sabda.org",
}


def license_text(meta: Dict[str, str]) -> str:
    """Teks lengkap untuk `alkitab license` (rich markup tidak dipakai: aman untuk dialihkan ke file)."""
    commit = meta.get("source_commit", "unknown")[:12]
    built = meta.get("built_at", "?")
    lines = [
        "TEKS ALKITAB",
        "============",
        "Alkitab Yang Terbuka (AYT), © Yayasan Lembaga SABDA (YLSA).",
        "Teks dalam alat ini bersumber dari dataset resmi AYT:",
        f"  {URLS['Dataset']}  (commit {commit}, dibangun {built})",
        "",
        "Ketentuan asli dari YLSA (dikutip apa adanya, berbahasa Inggris):",
        "",
    ]
    lines += [f"  • {t}" for t in AYT_TERMS_ORIGINAL]
    lines += [
        "",
        "Ringkasan praktis (bukan pengganti ketentuan di atas):",
        "  • Pemakaian NON-KOMERSIAL bebas; teks tidak boleh dijual.",
        "  • Bentuk turunan (termasuk alat seperti ini) berlisensi CC BY-NC-SA:",
        "    cantumkan sumber (BY), non-komersial (NC), bagikan dengan lisensi yang sama (SA).",
        "  • Nama \"AYT\" dan \"Alkitab Yang Terbuka\" adalah merek dagang; izin dikelola YLSA.",
        f"  • Pemakaian di luar ketentuan ini: hubungi YLSA — {URLS['Kontak']} — {URLS['YLSA']}",
        "",
        "ALAT INI (alkitab-cli)",
        "======================",
        "  • Kode program: lisensi MIT (lihat berkas LICENSE).",
        "  • Teks AYT yang disertakan tetap tunduk pada ketentuan YLSA di atas, bukan pada MIT.",
        "  • Proyek ini TIDAK resmi: tidak berafiliasi dengan, disponsori, atau didukung oleh YLSA.",
        "  • Diberikan \"apa adanya\", tanpa jaminan apa pun. Untuk kutipan penting, rujuk Alkitab cetak/resmi.",
        "",
        "Dokumen ini informasi, bukan nasihat hukum.",
    ]
    return "\n".join(lines)
