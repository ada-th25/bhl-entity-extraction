"""
src/fetch_bhl.py

Fetch a sample of pages (with OCR text) from a given BHL item and
save them locally to data/raw/ as one JSON file per item.

Find ItemIDs first using search_bhl.py + GetTitleMetadata (items=t),
or by browsing biodiversitylibrary.org and reading the ID out of a
book's URL / "Item Details" page.

Usage:
    python fetch_bhl.py <item_id>
"""

import sys
import json
import requests
from pathlib import Path
from config import BHL_API_KEY

BASE_URL = "https://www.biodiversitylibrary.org/api3"
RAW_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def get_item_metadata(item_id: str, include_ocr: bool = True) -> dict:
    """Fetch metadata + pages (+ OCR text) for a single BHL item."""
    params = {
        "op": "GetItemMetadata",
        "id": item_id,
        "idtype": "bhl",
        "pages": "t",
        "ocr": "t" if include_ocr else "f",
        "format": "json",
        "apikey": BHL_API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    if data.get("Status", "").lower() != "ok":
        raise RuntimeError(f"BHL API error: {data.get('ErrorMessage')}")

    return data["Result"][0]  # GetItemMetadata returns a one-item list


def save_item(item_data: dict, item_id: str):
    """Save the raw item JSON (including page OCR text) to data/raw/."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DATA_DIR / f"item_{item_id}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(item_data, f, indent=2, ensure_ascii=False)

    n_pages = len(item_data.get("Pages", []))
    print(f"Saved item {item_id}: {n_pages} pages -> {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_bhl.py <item_id>")
        sys.exit(1)

    item_id = sys.argv[1]
    print(f"Fetching item {item_id} from BHL...")

    item_data = get_item_metadata(item_id)
    save_item(item_data, item_id)