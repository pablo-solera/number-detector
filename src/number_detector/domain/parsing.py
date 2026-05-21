from __future__ import annotations

import re


def extract_part_numbers(text: str, min_digits: int = 3, max_digits: int = 6) -> list[int]:
    """Extract valid part numbers (digits only) from OCR text."""
    nums = re.findall(r"\d+", text or "")
    out: list[int] = []
    for n in nums:
        if min_digits <= len(n) <= max_digits:
            out.append(int(n))
    return sorted(set(out))


def normalize_motor_text(text: str) -> str:
    t = (text or "").upper()
    t = t.replace("\t", "").replace("\r", "")
    t = t.replace(" ", "")
    t = t.replace("—", "-").replace("_", "-").replace("\\", "/")
    return t


def extract_motor_codes(text: str) -> list[str]:
    """Extract engine codes with the formats you described.

    Accepted formats:
      - X.X/XXXX-XXX-XXX
      - X.X/XXXX-XXX
      - X.X/XXXXX
      - /XXXXXXX
    """
    t = normalize_motor_text(text)

    # Remove common noise tokens that appear close to engines
    for tok in ("KW:", "CV:", "IDVEIC", "IDVEIC:"):
        t = t.replace(tok, "")

    patterns = [

       #  r"\b\d\.\d/[A-Z0-9]{4}(?:-[A-Z0-9]{3}){1,2}\b",
        #r"\b\d\.\d/[A-Z0-9]{5}\b",
        #r"\b/[A-Z0-9]{7}\b",
        #r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+',


        # Patron con un guion: 1.6/EP6FADTXHPD-5GQ o /ZKU-ZK02
        r'\d+\.\d+/[A-Z0-9]+-[A-Z0-9]+',
        r'/[A-Z0-9]+-[A-Z0-9]+',

        # Patron medio: 1.5/B38A15P
        r'\d+\.\d+/[A-Z][0-9]+[A-Z]+[0-9]*[A-Z]?',

        # Patron con barra: /XXXXXXX (7 o mas caracteres)
        r'/[A-Z0-9]{7,}',

        # Patron solo letras y numeros: XXXXXXX (7 o mas caracteres alfanumericos)
        #r'\b[A-Z0-9]{7,}\b',

        # Patron con numero y barra: X.X/XXXX
        r'\d+\.\d+/[A-Z0-9]+',
    ]

    found: list[str] = []
    for p in patterns:
        found.extend(re.findall(p, t))

    # Must contain at least one letter
    found = [m for m in found if re.search(r"[A-Z]", m)]
    return sorted(set(found))
