"""
src/extract.py

Run LLM-based entity extraction over the curated sample pages
(data/sample_pages.json), validating each response against the JSON
schema in schema.py, and saving results to data/extracted_entities.json.

Uses a locally-run Ollama model (no API cost, runs entirely on-device)
rather than a hosted API. This is a deliberate scoping choice -- see
docs/design_decisions.md for the trade-offs vs. a hosted LLM API
(mainly: no cost, but generally less reliable at strictly following a
JSON schema, which is itself a useful thing to measure and report on).

Requires Ollama running locally (https://ollama.com) with a model pulled,
e.g.: ollama pull llama3.1:8b

Failures (malformed JSON, schema violations) are logged rather than
silently dropped. This becomes part of the error analysis later.

Usage:
    python extract.py
"""

import json
import time
import requests
from pathlib import Path

import jsonschema

from schema import EXTRACTION_JSON_SCHEMA, EXTRACTION_SYSTEM_PROMPT

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_pages.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "extracted_entities.json"
LOG_PATH = Path(__file__).resolve().parent.parent / "data" / "extraction_errors.json"

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1:8b"
MAX_SECONDS_PER_PAGE = 120  # hard wall-clock cutoff, enforced manually below


def extract_entities(ocr_text: str) -> dict:
    """
    Call the local Ollama model on a single page's OCR text, requesting
    structured JSON output. Streams the response and enforces a real
    wall-clock timeout (requests' built-in timeout resets on every small
    chunk received, so a slow-but-still-trickling response can otherwise
    run indefinitely -- this happened in practice on a long index page).
    Returns the parsed+validated dict, or raises on failure.
    """
    start = time.monotonic()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": ocr_text},
            ],
            "format": EXTRACTION_JSON_SCHEMA,
            "stream": True,
            "options": {
                "temperature": 0,
                "num_predict": 2000,  # hard cap on output length
            },
        },
        stream=True,
        timeout=30,  # only guards the initial connection, not total duration
    )
    response.raise_for_status()

    chunks = []
    for line in response.iter_lines():
        if time.monotonic() - start > MAX_SECONDS_PER_PAGE:
            response.close()
            raise TimeoutError(
                f"Exceeded {MAX_SECONDS_PER_PAGE}s wall-clock limit for this page"
            )
        if not line:
            continue
        piece = json.loads(line)
        chunks.append(piece.get("message", {}).get("content", ""))
        if piece.get("done"):
            break

    raw_content = "".join(chunks)

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Response was not valid JSON: {e}\nRaw: {raw_content[:300]}")

    jsonschema.validate(instance=parsed, schema=EXTRACTION_JSON_SCHEMA)

    return parsed


def run():
    with open(SAMPLE_PATH, encoding="utf-8") as f:
        pages = json.load(f)

    # Resume support: if a previous run already produced output, load it
    # and skip pages we've already successfully extracted.
    results = []
    errors = []
    already_done_ids = set()

    if OUT_PATH.exists():
        with open(OUT_PATH, encoding="utf-8") as f:
            results = json.load(f)
        already_done_ids = {r["page_id"] for r in results}
        print(f"Resuming: {len(already_done_ids)} pages already extracted, skipping those.")

    for page in pages:
        page_id = page["page_id"]

        if page_id in already_done_ids:
            continue

        print(f"Extracting page {page_id} ({page['category']})...")

        try:
            extraction = extract_entities(page["ocr_text"])
            results.append({
                "item_id": page["item_id"],
                "page_id": page_id,
                "category": page["category"],
                "entities": extraction["entities"],
            })
            print(f"  -> {len(extraction['entities'])} entities extracted")

        except (ValueError, jsonschema.ValidationError, requests.RequestException, TimeoutError) as e:
            print(f"  -> FAILED: {e}")
            errors.append({
                "item_id": page["item_id"],
                "page_id": page_id,
                "error": str(e),
            })

        # Save progress after every page, not just at the end -- so an
        # interruption (e.g. laptop sleep, network hiccup) doesn't lose
        # everything computed so far.
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        if errors:
            with open(LOG_PATH, "w", encoding="utf-8") as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} successful extractions -> {OUT_PATH}")
    if errors:
        print(f"Logged {len(errors)} extraction failures -> {LOG_PATH}")


if __name__ == "__main__":
    run()