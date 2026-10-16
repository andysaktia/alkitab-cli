"""Salin teks ke clipboard tanpa dependensi tambahan (memakai utilitas bawaan OS)."""
from __future__ import annotations

import shutil
import subprocess
from typing import List, Optional

_CANDIDATES: List[List[str]] = [
    ["pbcopy"],                              # macOS
    ["wl-copy"],                             # Linux Wayland
    ["xclip", "-selection", "clipboard"],    # Linux X11
    ["xsel", "--clipboard", "--input"],      # Linux X11
    ["clip.exe"],                            # Windows / WSL
    ["clip"],
]


def copy(text: str) -> Optional[str]:
    """Kembalikan nama utilitas yang berhasil dipakai, atau None bila tidak ada/gagal."""
    for cmd in _CANDIDATES:
        if shutil.which(cmd[0]) is None:
            continue
        try:
            subprocess.run(cmd, input=text.encode("utf-8"), check=True, timeout=5,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return cmd[0]
        except (subprocess.SubprocessError, OSError):
            continue
    return None
