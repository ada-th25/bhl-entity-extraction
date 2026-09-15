"""
src/reconcile.py

Reconcile extracted taxon mentions against the GBIF Taxonomy Backbone
using GBIF's free, public Species Match API (no key required):
https://www.gbif.org/developer/species#searching

For each unique extracted taxon mention, this asks GBIF: does this name
match a real, recognised species/genus, and if so, what's the accepted
canonical name and how confident is the match?

Design choices (see docs/design_decisions.md for the full rationale):
  - Reconciliation runs on UNIQUE mention_text values, not every
    occurrence, since the same taxon can appear many times across pages
    and re-querying GBIF for duplicates wastes calls for no new
    information.
  - GBIF's own "matchType" field (EXACT, FUZZY, HIGHERRANK, NONE) is
    used directly as the confidence signal, rather than inventing a
    separate scoring scheme -- GBIF's fuzzy matching already accounts
    for common spelling variation, which is relevant given our OCR
    noise.
  - Unresolved matches (matchType == NONE) are logged, not discarded --
    they're a genuine, reportable finding (how much OCR noise is too
    severe even for GBIF's fuzzy matching to resolve), not a pipeline
    failure to hide.

Usage:
    python reconcile.py
"""

import json
import time
import requests
from pathlib import Path

EXTRACTED_PATH = Path(__file__).resolve().parent.parent / "data" / "extracted_entities.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "reconciled_taxa.json"
REPORT_PATH = Path(__file__).resolve().parent.parent / "results" / "reconciliation_report.md"

GBIF_MATCH_URL = "https://api.gbif.org/v1/species/match"


def get_unique_taxa(extracted_pages: list) -> list:
    """Collect every unique taxon mention_text across all extracted pages."""
    seen = set()
    unique_taxa = []
    for page in extracted_pages:
        for entity in page["entities"]:
            if entity["entity_type"] != "taxon":
                continue
            text = entity["mention_text"].strip()
            if text not in seen:
                seen.add(text)
                unique_taxa.append(text)
    return unique_taxa


def match_taxon(name: str) -> dict:
    """Query GBIF's species match API for a single taxon name."""
    response = requests.get(GBIF_MATCH_URL, params={"name": name}, timeout=15)
    response.raise_for_status()
    result = response.json()

    return {
        "query": name,
        "match_type": result.get("matchType", "NONE"),
        "canonical_name": result.get("canonicalName"),
        "rank": result.get("rank"),
        "confidence": result.get("confidence"),
        "status": result.get("status"),
    }


def run():
    with open(EXTRACTED_PATH, encoding="utf-8") as f:
        extracted_pages = json.load(f)

    unique_taxa = get_unique_taxa(extracted_pages)
    print(f"Found {len(unique_taxa)} unique taxon mentions to reconcile.")

    results = []
    for i, name in enumerate(unique_taxa, 1):
        print(f"[{i}/{len(unique_taxa)}] Matching \"{name}\"...")
        try:
            match = match_taxon(name)
            results.append(match)
            print(f"  -> {match['match_type']}: {match['canonical_name']}")
        except requests.RequestException as e:
            print(f"  -> FAILED: {e}")
            results.append({"query": name, "match_type": "ERROR", "error": str(e)})

        time.sleep(0.2)  # be polite to the free public API

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved reconciliation results -> {OUT_PATH}")

    # Build a short summary report
    counts = {}
    for r in results:
        mt = r["match_type"]
        counts[mt] = counts.get(mt, 0) + 1

    lines = ["# GBIF Reconciliation Report\n"]
    lines.append(f"Reconciled {len(unique_taxa)} unique extracted taxon mentions "
                  f"against the GBIF Taxonomy Backbone.\n")
    lines.append("## Match type breakdown\n")
    lines.append("| Match type | Count | % |")
    lines.append("|------------|-------|---|")
    for mt, count in sorted(counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(unique_taxa)
        lines.append(f"| {mt} | {count} | {pct:.0f}% |")

    lines.append("\n## Unresolved (NONE) or errored mentions\n")
    unresolved = [r for r in results if r["match_type"] in ("NONE", "ERROR")]
    for r in unresolved:
        lines.append(f"- \"{r['query']}\"")

    lines.append("\n## Fuzzy matches (name likely contains noise, GBIF still resolved it)\n")
    fuzzy = [r for r in results if r["match_type"] == "FUZZY"]
    for r in fuzzy:
        lines.append(f"- \"{r['query']}\" -> \"{r['canonical_name']}\" (confidence={r.get('confidence')})")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Saved reconciliation report -> {REPORT_PATH}")

    print("\n--- Summary ---")
    for mt, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{mt}: {count}")


if __name__ == "__main__":
    run()