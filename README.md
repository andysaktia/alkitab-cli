# alkitab-cli

Baca **Alkitab Yang Terbuka (AYT)** langsung dari terminal. Cepat, **offline** (teks ikut terpasang, tanpa API), dan nama kitabnya pintar dikenali.

> Proyek **tidak resmi**: tidak berafiliasi dengan Yayasan Lembaga SABDA (YLSA). Lihat [Lisensi](#lisensi-dan-atribusi).

## Pasang

Kebutuhan: **Python 3.9 atau lebih baru** (cek dengan `python --version`). Internet hanya diperlukan saat memasang; setelah itu `alkitab` berjalan sepenuhnya offline.

Cara yang disarankan memakai **pipx**, yaitu alat yang memasang program Python ke lingkungannya sendiri sehingga perintah `alkitab` bisa dipanggil dari folder mana pun tanpa mengganggu proyek Python lain.

### Langkah 1 - Pasang pipx (sekali saja)

Lewati langkah ini jika `pipx --version` sudah menampilkan versi.

| Sistem | Perintah |
|---|---|
| macOS | `brew install pipx` |
| Ubuntu / Debian / WSL | `sudo apt install pipx` |
| Windows (PowerShell, CMD, atau Git Bash) | `python -m pip install --user pipx` |

Lalu jalankan:

```bash
pipx ensurepath          # di Windows: python -m pipx ensurepath
```

**Tutup terminal dan buka yang baru.** Langkah ini wajib, karena perubahan `PATH` baru terbaca di terminal yang baru dibuka.

### Langkah 2 - Pasang alkitab-cli

```bash
pipx install git+https://github.com/andysaktia/alkitab-cli.git
```

Atau, jika Anda sudah mengunduh/meng-clone folder project ini, jalankan di dalam folder tersebut:

```bash
pipx install .
```

> Di Windows, jika perintah `pipx` tidak dikenali padahal sudah dipasang, tulis `python -m pipx install .` (hasilnya sama).

<!-- Aktifkan baris ini setelah paket dipublikasikan di PyPI:
pipx install alkitab-cli
-->

### Langkah 3 - Coba

Dari folder mana saja:

```bash
alkitab Yoh 3:16
```

Jika ayatnya tampil, pemasangan berhasil.

### Memperbarui dan menghapus

```bash
pipx upgrade alkitab-cli       # perbarui
pipx uninstall alkitab-cli     # hapus (termasuk semua dependensinya)
```

Jika dipasang dari folder lokal, perbarui dengan `pipx install --force .` di folder project.

### Tanpa pipx

`pip install .` juga bisa, tetapi sebagian sistem (Ubuntu dan Debian terbaru, Homebrew di macOS) menolaknya dengan galat `externally-managed-environment`. Jalan keluarnya adalah memakai pipx, atau membuat lingkungan sendiri:

```bash
python3 -m venv ~/.alkitab-env
~/.alkitab-env/bin/pip install .
mkdir -p ~/.local/bin && ln -s ~/.alkitab-env/bin/alkitab ~/.local/bin/alkitab
```

(Di Windows, gunakan pipx; `~/.alkitab-env/Scripts` menggantikan `bin`, dan penautan manual tidak disarankan.)

### Masalah umum

| Gejala | Penyebab dan solusi |
|---|---|
| `pipx: command not found` | pipx belum dipasang (Langkah 1), atau terminal belum dibuka ulang setelah `ensurepath`. Di Windows, gunakan `python -m pipx ...`. |
| `alkitab: command not found` setelah berhasil memasang | Folder `~/.local/bin` belum ada di `PATH`. Jalankan `pipx ensurepath`, lalu **buka terminal baru**. Sementara itu, perintah bisa dipanggil lewat `~/.local/bin/alkitab`. |
| `externally-managed-environment` | Sistem menolak `pip install` global. Pakai pipx (di atas). |
| Tanda kutip atau simbol tampil sebagai kotak | Masalah font/encoding terminal, bukan datanya. Coba `alkitab Yoh 3:16 --plain` atau pakai Windows Terminal. |
| `Kitab '...' tidak dikenal` | Lihat daftar nama dengan `alkitab list-kitab`. |

## Pakai

### Bantuan

```bash
alkitab help                     # daftar semua perintah beserta contoh
alkitab -h                       # sama (juga: alkitab --help)
alkitab search --help            # bantuan dan opsi satu perintah (berlaku untuk semua perintah)
alkitab --version                # versi (singkat: -V)
```

Menjalankan `alkitab` tanpa argumen juga menampilkan bantuan.

### Membaca

```bash
alkitab Yoh 3:16                 # satu ayat
alkitab 1 Kor 13:4-7             # rentang ayat
alkitab Mzm 23                   # satu pasal
alkitab Mat 5-7                  # beberapa pasal berurutan
alkitab Mat 5:3-7:29             # lintas pasal
alkitab Yoh 3:16,18-20           # beberapa bagian sekaligus
alkitab Yud 5                    # kitab satu pasal: angka = ayat
alkitab Yohanes                  # hanya nama kitab: tampil jumlah pasalnya
```

Kata `read` boleh dihilangkan; `alkitab read Yoh 3:16` sama dengan `alkitab Yoh 3:16`.

### Mencari

```bash
alkitab search "kasih karunia"   # frasa (pakai tanda kutip)
alkitab search kasih setia       # semua kata harus ada (tidak harus berdekatan)
alkitab search 'kasih*'          # kata* = awalan (kasih, kasihan, kasihilah, kasihmu...)
alkitab search kasih -k Mzm      # -k / --kitab = batasi pada satu kitab

alkitab search kasih -n 5        # -n / --limit = jumlah hasil (bawaan 20, maksimal 500)
alkitab search kasih -n 20 --offset 20   # halaman berikutnya: lewati 20 hasil pertama
```

Hasil selalu berurutan sesuai susunan kitab, kata yang cocok disorot, dan baris ringkasan menunjukkan jumlah seluruh ayat yang cocok (misalnya "362 ayat cocok dengan “kasih” (menampilkan 1–20 ...)"). Untuk melihat berikutnya, naikkan `--offset` sebesar nilai `--limit`. Beri tanda kutip pada `'kasih*'` supaya tidak diperluas oleh shell.

### Ayat harian dan ayat acak

```bash
alkitab today                    # ayat hari ini (sama untuk semua orang pada tanggal yang sama)
alkitab today --date 2026-12-25  # ayat untuk tanggal tertentu (format YYYY-MM-DD)
alkitab random                   # satu ayat acak
```

### Daftar kitab, lisensi, versi

```bash
alkitab list-kitab               # 66 kitab + singkatan + jumlah pasal + nama Inggris
alkitab list-kitab --json        # sama, dalam JSON
alkitab license                  # lisensi AYT, atribusi, dan batasan pemakaian
```

### Opsi keluaran

| Opsi | Fungsi | Berlaku untuk |
|---|---|---|
| `--plain` | teks polos tanpa warna/format (cocok untuk di-pipe) | baca, `search`, `today`, `random` |
| `--json` | keluaran JSON (untuk skrip) | baca, `search`, `today`, `random`, `list-kitab` |
| `--copy` | salin hasil ke clipboard (memakai `pbcopy` di macOS, `clip` di Windows, `wl-copy`/`xclip`/`xsel` di Linux) | baca, `today`, `random` |
| `--no-headings` | sembunyikan judul perikop | baca, `today`, `random` |
| `-n`, `--limit` / `--offset` / `-k`, `--kitab` | jumlah hasil, lewati hasil, batasi kitab | `search` |
| `--date` | tanggal lain | `today` |

Beberapa opsi boleh digabung, misalnya `alkitab Mat 28:16-20 --plain --copy`.

### Dipakai di skrip

```bash
alkitab Yoh 3:16 --json
alkitab search kasih -k Mzm -n 5 --json
alkitab Mzm 23 --plain > mazmur23.txt
```

- Bidang JSON ayat: `reference`, `book`, `verses[]` (`chapter`, `verse`, `text`, `heading`), ditambah `copyright` dan `terms`. Hasil pencarian ada di `results[]` beserta `total`.
- Data hanya ditulis ke keluaran standar; pesan seperti "'Yohanse' dibaca sebagai Yohanes" dan pesan galat ditulis ke keluaran galat, sehingga tidak merusak JSON.
- Kode keluar: `0` berhasil, `1` pencarian tanpa hasil atau database tidak ditemukan, `2` masukan salah (kitab tidak dikenal atau ambigu, pasal/ayat di luar jangkauan, format salah).

Jika Anda memakai **PowerShell**, beri tanda kutip pada referensi yang memuat koma, misalnya `alkitab "Yoh 3:16,18-20"`, karena koma punya arti khusus di PowerShell. Di Git Bash, CMD, macOS, dan Linux, tanda kutip tidak diperlukan.

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
git clone https://github.com/andysaktia/alkitab-cli && cd alkitab-cli
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