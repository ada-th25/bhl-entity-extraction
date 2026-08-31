"""
src/build_sample.py

Pull a specific, hand-curated set of PageIDs out of the full raw
volume JSON files (data/raw/item_*.json) into one clean, small
working file: data/sample_pages.json

This is the file the rest of the pipeline (extraction, annotation,
evaluation) will actually work against -- not the full raw volumes.

Edit SELECTED_PAGES below as you refine your sample.
"""

import json
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_pages.json"

# item_id -> list of (page_id, category) tuples
# category is just a label for your own reference ("narrative" vs "index")
SELECTED_PAGES = {
    "239981": [
        ("54832638", "narrative"),
        ("54832512", "narrative"),
        ("54832312", "narrative"),
        ("54832247", "narrative"),
        ("54832653", "index"),
    ],
    "34369": [
        ("8330882", "narrative"),
        ("8330698", "narrative"),
        ("8330712", "narrative"),
        ("8330709", "narrative"),
        ("8331000", "index"),
    ],
    "35484": [
        ("8750262", "narrative"),
        ("8750405", "narrative"),
        ("8750615", "narrative"),
        ("8750608", "index"),
    ],
    "85192": [
        ("26462405", "narrative"),
        ("26462038", "narrative"),
        ("26462039", "narrative"),
        ("26462459", "narrative"),
        ("26462470", "index"),
    ],
}


def build_sample():
    sample = []

    for item_id, page_list in SELECTED_PAGES.items():
        raw_path = RAW_DIR / f"item_{item_id}.json"
        if not raw_path.exists():
            print(f"WARNING: {raw_path} not found, skipping item {item_id}")
            continue

        with open(raw_path, encoding="utf-8") as f:
            item_data = json.load(f)

        # Index the item's pages by PageID for quick lookup
        pages_by_id = {
            str(p.get("PageID")): p for p in item_data.get("Pages", [])
        }

        for page_id, category in page_list:
            page = pages_by_id.get(page_id)
            if page is None:
                print(f"WARNING: PageID {page_id} not found in item {item_id}")
                continue

            sample.append({
                "item_id": item_id,
                "page_id": page_id,
                "category": category,
                "volume": item_data.get("Volume", ""),
                "publication_date": item_data.get("PublicationDate", ""),
                "ocr_text": page.get("OcrText", ""),
            })

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2, ensure_ascii=False)

    print(f"Built sample with {len(sample)} pages -> {OUT_PATH}")

    narrative_count = sum(1 for s in sample if s["category"] == "narrative")
    index_count = sum(1 for s in sample if s["category"] == "index")
    print(f"  {narrative_count} narrative pages, {index_count} index pages")


if __name__ == "__main__":
    build_sample()