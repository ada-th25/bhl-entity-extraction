"""
src/select_pages.py

Scan the fetched BHL volumes (data/raw/item_*.json) and shortlist pages
that look content-rich (reasonable text length, some capitalised/Latin-
looking words that could be taxon names) rather than blank pages,
indices, or front matter.

This is a pre-filter, not a final decision: it prints a shortlist for
you to skim and manually pick your final sample from -- the human
judgement step is the point, not just automating everything away.

Usage:
    python select_pages.py
"""

import json
import re
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MIN_TEXT_LENGTH = 400          # skip very short/blank pages
MAX_CANDIDATES_PER_ITEM = 15   # shortlist size to review per volume

# Rough heuristic: two consecutive Capitalised words, e.g. "Rhea americana"
LATIN_LIKE_PATTERN = re.compile(r"\b[A-Z][a-z]+\s[a-z]{3,}\b")


def score_page(text: str) -> int:
    """Very rough content-richness score, higher = more promising."""
    if not text or len(text) < MIN_TEXT_LENGTH:
        return -1
    latin_like_matches = len(LATIN_LIKE_PATTERN.findall(text))
    return latin_like_matches


def shortlist_item(filepath: Path):
    with open(filepath, encoding="utf-8") as f:
        item_data = json.load(f)

    item_id = item_data.get("ItemID", filepath.stem)
    pages = item_data.get("Pages", [])

    scored = []
    for page in pages:
        text = page.get("OcrText", "") or ""
        score = score_page(text)
        if score > 0:
            scored.append((score, page.get("PageID"), text[:120].replace("\n", " ")))

    scored.sort(reverse=True)  # highest score first
    top = scored[:MAX_CANDIDATES_PER_ITEM]

    print(f"\n=== Item {item_id} ({filepath.name}) ===")
    print(f"{len(pages)} total pages, {len(scored)} passed the basic filter\n")
    for score, page_id, preview in top:
        print(f"  PageID {page_id}  (score {score}):  {preview}...")


if __name__ == "__main__":
    files = sorted(RAW_DIR.glob("item_*.json"))
    if not files:
        print(f"No files found in {RAW_DIR}. Run fetch_bhl.py first.")
    else:
        for filepath in files:
            shortlist_item(filepath)

        print(
            "\nReview the shortlists above and manually note down ~5-8 "
            "PageIDs per item that look genuinely interesting (species "
            "names, people, localities) -- this becomes your working "
            "sample for annotation and extraction."
        )