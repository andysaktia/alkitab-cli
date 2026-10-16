# alkitab-cli

Baca **Alkitab Yang Terbuka (AYT)** langsung dari terminal. Cepat, **offline** (teks ikut terpasang, tanpa API), dan nama kitabnya pintar dikenali.

> Proyek **tidak resmi**: tidak berafiliasi dengan Yayasan Lembaga SABDA (YLSA). Lihat [Lisensi](#lisensi-dan-atribusi).

## Pasang

```bash
pipx install alkitab-cli        # disarankan: terisolasi, perintah `alkitab` langsung tersedia
# atau
pip install alkitab-cli
# atau dari sumber
pip install git+https://github.com/<username>/alkitab-cli.git
```

## Pakai

```bash
alkitab Yoh 3:16                 # satu ayat
alkitab 1 Kor 13:4-7             # rentang ayat
alkitab Mzm 23                   # satu pasal
alkitab Mat 5:3-7:29             # lintas pasal
alkitab Yoh 3:16,18-20           # beberapa bagian sekaligus
alkitab Yud 5                    # kitab satu pasal: angka = ayat

alkitab search "kasih karunia"   # frasa (pakai tanda kutip)
alkitab search kasih setia       # semua kata harus ada
alkitab search kasih* -k Mzm     # kata* = awalan; -k = batasi satu kitab

alkitab today                    # ayat hari ini
alkitab random                   # ayat acak
alkitab list-kitab               # 66 kitab + singkatan + jumlah pasal
alkitab license                  # lisensi & atribusi
```

Opsi untuk perintah baca: `--json` (untuk skrip), `--plain` (tanpa warna), `--copy` (ke clipboard), `--no-headings` (tanpa judul perikop).

### Pengenalan nama kitab

Semua ini dikenali sebagai Yohanes / 1 Korintus:

| Diketik | Hasil |
|---|---|
| `yoh`, `Yohanes`, `John`, `Injil Yohanes` | Yohanes |
| `1 Kor`, `1Kor`, `I Kor`, `1. Kor`, `1 Korintus`, `1 Cor` | 1 Korintus |
| `Kisah Para Rasul`, `Kis`, `Acts` | Kisah Para Rasul |
| `yehez` (awalan, tidak ambigu) | Yehezkiel |
| `Mathius`, `Yohanse` (salah ketik, jelas unggul) | Matius, Yohanes (diberi tahu) |
| `Kor`, `Sam`, `Ma` | pesan ambigu + pilihan, bukan tebakan |

## Pengembangan

```bash
git clone https://github.com/<username>/alkitab-cli && cd alkitab-cli
pip install -e ".[dev]"
pytest

# membangun ulang database dari dataset AYT
git clone https://github.com/sabdacode/ayt /tmp/ayt
python scripts/build_db.py --csv /tmp/ayt/csv/ayt.csv --commit "$(git -C /tmp/ayt rev-parse HEAD)"
```

Data disimpan sebagai SQLite (`src/alkitab/data/ayt.db`, ~8 MB) dengan indeks FTS5 untuk pencarian.

## Lisensi dan atribusi

- **Teks AYT** © Yayasan Lembaga SABDA (YLSA). Pemakaian **non-komersial**; bentuk turunan berlisensi **CC BY-NC-SA** (cantumkan sumber, non-komersial, bagikan dengan lisensi sama). Nama "AYT" dan "Alkitab Yang Terbuka" adalah merek dagang; izin dikelola YLSA (ylsa@sabda.org).
- **Kode program** berlisensi MIT ([LICENSE](LICENSE)); teks AYT yang ikut terkemas **tidak** tercakup MIT.
- Ketentuan lengkap: [NOTICE.md](NOTICE.md) atau jalankan `alkitab license`.
- Setiap tampilan memuat atribusi singkat, dan keluaran `--json` memuat bidang `copyright` dan `terms`.

Sumber teks: <https://ayt.co> · dataset: <https://github.com/sabdacode/ayt>
