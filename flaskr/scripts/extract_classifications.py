#!/usr/bin/env python3
"""
Script to extract classification data from PDF files.
"""
import PyPDF2
import re
import json
from pathlib import Path


def extract_dzialy() -> dict[str, str]:
    """Extract działów (divisions) from PDF."""
    pdf_path = (
        Path(__file__).parent.parent.parent
        / "docs"
        / "Wyciąg nr 2a z Rozporządzenia - klasyfikacja działów.pdf"
    )

    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

    # Parse działów - pattern: "010 Rolnictwo i łowiectwo"
    # Looking for 3-digit code followed by text
    lines = text.split("\n")
    dzialy = {}

    for line in lines:
        # Match pattern: 3 digits at start, followed by text
        match = re.match(r"^(\d{3})\s+([A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-,]+)", line)
        if match:
            code, name = match.groups()
            # Clean up the name
            name = name.strip()
            # Only keep if it looks like a proper name (not a reference or number)
            if len(name) > 3 and not name[0].isdigit():
                dzialy[code] = name

    return dzialy


def extract_rozdzialy() -> dict[str, str]:
    """Extract rozdziałów (chapters) from PDF."""
    pdf_path = (
        Path(__file__).parent.parent.parent
        / "docs"
        / "Wyciąg nr 2b z Rozporządzenia - klasyfikacja rozdziałów.pdf"
    )

    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extract_text()

    # Parse rozdziałów - pattern: "01009 Spółki wodne"
    lines = text.split("\n")
    rozdzialy = {}

    for line in lines:
        # Match pattern: 5 digits at start, followed by text
        match = re.match(r"^(\d{5})\s+([A-ZĄĆĘŁŃÓŚŹŻ][\w\s\-,]+)", line)
        if match:
            code, name = match.groups()
            # Clean up the name
            name = name.strip()
            # Only keep if it looks like a proper name
            if len(name) > 3 and not name[0].isdigit():
                rozdzialy[code] = name

    return rozdzialy


def create_dzial_rozdzial_mapping(rozdzialy: dict[str, str]) -> dict[str, list[str]]:
    """Create mapping from dział code to its rozdziały."""
    mapping: dict[str, list[str]] = {}
    for rozdzial_code in rozdzialy.keys():
        # First 3 digits are the dział code
        dzial_code = rozdzial_code[:3]
        if dzial_code not in mapping:
            mapping[dzial_code] = []
        mapping[dzial_code].append(rozdzial_code)

    # Sort the lists
    for dzial_code in mapping:
        mapping[dzial_code].sort()

    return mapping


if __name__ == "__main__":
    # Extract data
    dzialy = extract_dzialy()
    rozdzialy = extract_rozdzialy()
    dzial_rozdzial_mapping = create_dzial_rozdzial_mapping(rozdzialy)

    # Save to JSON
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "dzialy.json", "w", encoding="utf-8") as f:
        json.dump(dzialy, f, ensure_ascii=False, indent=2)

    with open(output_dir / "rozdzialy.json", "w", encoding="utf-8") as f:
        json.dump(rozdzialy, f, ensure_ascii=False, indent=2)

    with open(output_dir / "dzial_rozdzial_mapping.json", "w", encoding="utf-8") as f:
        json.dump(dzial_rozdzial_mapping, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(dzialy)} działów")
    print(f"Extracted {len(rozdzialy)} rozdziałów")
    print(f"Created mapping for {len(dzial_rozdzial_mapping)} działów")
    print(f"\nSaved to {output_dir}")
