"""
src/search_bhl.py

Search BHL for candidate items (books/volumes) to sample pages from.
Run this first to find real, valid ItemIDs before fetching any pages.

Usage:
    python search_bhl.py "Proceedings of the Zoological Society"
    python search_bhl.py "Annals and Magazine of Natural History"
"""

import sys
import json
import requests
from config import BHL_API_KEY

BASE_URL = "https://www.biodiversitylibrary.org/api3"


def search_publications(query: str, max_results: int = 10):
    """Search BHL for titles/items matching a query string."""
    params = {
        "op": "PublicationSearch",
        "searchterm": query,
        "searchtype": "F",   # F = full text, could also try "C" for creator etc.
        "format": "json",
        "apikey": BHL_API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    print("Request URL:", response.url)  # debug: see the exact URL called
    response.raise_for_status()
    data = response.json()

    print("Raw response:", json.dumps(data, indent=2)[:1000])  # debug

    if data.get("Status", "").lower() != "ok":
        print(f"API returned an error: {data.get('ErrorMessage')}")
        return []

    results = data.get("Result", [])[:max_results]
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python search_bhl.py "search term"')
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Searching BHL for: {query}\n")

    results = search_publications(query)

    if not results:
        print("No results found. Try a different search term.")
    else:
        for r in results:
            title = r.get("Title", "Unknown title")
            item_id = r.get("ItemID")
            title_id = r.get("TitleID")
            volume = r.get("Volume", "")
            date = r.get("PublicationDate", "")
            print(f"ItemID: {item_id}  |  TitleID: {title_id}  |  {title} — {volume} ({date})")

    print(
        "\nEach row above is already a specific scanned volume (an Item)."
        "\nPick an ItemID you like and run: python fetch_bhl.py <item_id>"
    )