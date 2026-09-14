"""
src/make_annotation_template.py

Generate a blank annotation template for a subset of successfully
extracted pages, so you can hand-label gold-standard entities WITHOUT
seeing the model's own extractions first (avoids anchoring bias).

Produces data/gold_standard/annotation_template.json. Fill in the
"gold_entities" list for each page yourself, reading only "ocr_text".

Usage:
    python make_annotation_template.py
"""

import json
from pathlib import Path

EXTRACTED_PATH = Path(__file__).resolve().parent.parent / "data" / "extracted_entities.json"
SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_pages.json"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "gold_standard"
OUT_PATH = OUT_DIR / "annotation_template.json"

# Pick a subset of the successfully-extracted pages to annotate.
PAGES_TO_ANNOTATE = [
    "54832638",  # narrative, correspondence
    "54832312",  # narrative, Ornithology of Northern Africa
    "8330882",   # narrative, International Exhibition
    "8330712",   # narrative, Florida bird list w/ Dr. Henry Bryant
    "8750262",   # narrative, Cameroon Mountain collection
]


def build_template():
    with open(EXTRACTED_PATH, encoding="utf-8") as f:
        extracted = {e["page_id"]: e for e in json.load(f)}

    with open(SAMPLE_PATH, encoding="utf-8") as f:
        pages = {p["page_id"]: p for p in json.load(f)}

    template = []
    for page_id in PAGES_TO_ANNOTATE:
        if page_id not in extracted:
            print(f"WARNING: {page_id} not in extracted results, skipping.")
            continue

        page = pages[page_id]
        template.append({
            "page_id": page_id,
            "item_id": page["item_id"],
            "ocr_text": page["ocr_text"],
            "gold_entities": [
                # Fill in manually, one entry per entity you find, e.g.:
                # {"mention_text": "Rhea americana", "entity_type": "taxon"},
                # {"mention_text": "Mr. A. Newton", "entity_type": "person"},
                # {"mention_text": "Cameroon Mountain", "entity_type": "locality"},
            ],
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"Built annotation template for {len(template)} pages -> {OUT_PATH}")
    print("Open this file, read each 'ocr_text', and fill in 'gold_entities' by hand.")


if __name__ == "__main__":
    build_template()