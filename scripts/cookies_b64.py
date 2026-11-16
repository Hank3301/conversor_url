"""Converte um cookies.txt exportado do navegador em COOKIES_B64.

Uso:
    python scripts/cookies_b64.py cookies.txt

Cole a saída no secret COOKIES_B64 do host.
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"Arquivo não encontrado: {path}")
        return 1

    raw = path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    print(f"# {len(raw)} bytes -> {len(encoded)} caracteres em base64")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
