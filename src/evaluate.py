"""
src/evaluate.py

Compare the hand-annotated gold-standard entities against the LLM's
extracted entities for the same pages, computing precision/recall/F1
per entity type, plus a categorized error breakdown (not just a single
accuracy number).

Matching rule: an extracted entity is a "hit" if its (mention_text,
entity_type) pair exactly matches a gold entity on the same page.
Exact-string matching is a deliberate, simple starting point. See
docs/design_decisions.md for why fuzzy/normalised matching is a
separate, later concern (reconciliation), not part of extraction
evaluation itself.

Usage:
    python evaluate.py
"""

import json
from pathlib import Path
from collections import defaultdict

GOLD_PATH = Path(__file__).resolve().parent.parent / "data" / "gold_standard" / "annotation_template.json"
EXTRACTED_PATH = Path(__file__).resolve().parent.parent / "data" / "extracted_entities.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "metrics.md"


def normalise_key(entity: dict) -> tuple:
    """(mention_text, entity_type) as the matching key, exact string match."""
    return (entity["mention_text"].strip(), entity["entity_type"])


def evaluate_page(gold_entities: list, predicted_entities: list) -> dict:
    gold_keys = {normalise_key(e) for e in gold_entities}
    pred_keys = {normalise_key(e) for e in predicted_entities}

    true_positives = gold_keys & pred_keys
    false_negatives = gold_keys - pred_keys   # missed by the model
    false_positives = pred_keys - gold_keys   # model said it, gold didn't

    return {
        "true_positives": true_positives,
        "false_negatives": false_negatives,
        "false_positives": false_positives,
    }


def categorise_errors(false_negatives: set, false_positives: set) -> dict:
    """
    Split raw false negatives/positives into a rough error taxonomy:
      - type_mismatch: same mention_text appears in both sets but with
        a different entity_type (e.g. "Negrillo" gold=person, pred=locality)
      - partial_span: predicted text is a substring of a gold mention or
        vice versa (e.g. gold "Calcenas nicobarica" vs pred "Nicobarica")
      - missed_entirely: false negative with no related prediction at all
      - spurious: false positive with no related gold entity at all
    This is a heuristic categorisation to guide manual review, not a
    fully automated ground truth -- worth spot-checking by hand.
    """
    fn_texts = {text for text, _ in false_negatives}
    fp_texts = {text for text, _ in false_positives}

    type_mismatches = []
    partial_spans = []
    missed_entirely = []
    spurious = []

    matched_fp = set()

    for fn_text, fn_type in false_negatives:
        # same text, different type -> type mismatch
        same_text_fp = [(t, ty) for (t, ty) in false_positives if t == fn_text]
        if same_text_fp:
            type_mismatches.append((fn_text, fn_type, same_text_fp[0][1]))
            matched_fp.add(same_text_fp[0])
            continue

        # substring relationship -> partial span error
        partial_match = None
        for fp_text, fp_type in false_positives:
            if (fp_text, fp_type) in matched_fp:
                continue
            if fn_text.lower() in fp_text.lower() or fp_text.lower() in fn_text.lower():
                partial_match = (fp_text, fp_type)
                break
        if partial_match:
            partial_spans.append((fn_text, fn_type, partial_match[0]))
            matched_fp.add(partial_match)
            continue

        missed_entirely.append((fn_text, fn_type))

    for fp in false_positives:
        if fp not in matched_fp:
            spurious.append(fp)

    return {
        "type_mismatches": type_mismatches,
        "partial_spans": partial_spans,
        "missed_entirely": missed_entirely,
        "spurious": spurious,
    }


def run():
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold_pages = {p["page_id"]: p["gold_entities"] for p in json.load(f)}

    with open(EXTRACTED_PATH, encoding="utf-8") as f:
        extracted_pages = {p["page_id"]: p["entities"] for p in json.load(f)}

    # Per-type counts across all annotated pages
    counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    all_type_mismatches = []
    all_partial_spans = []
    all_missed = []
    all_spurious = []

    for page_id, gold_entities in gold_pages.items():
        predicted_entities = extracted_pages.get(page_id, [])
        result = evaluate_page(gold_entities, predicted_entities)

        for _, etype in result["true_positives"]:
            counts[etype]["tp"] += 1
        for _, etype in result["false_negatives"]:
            counts[etype]["fn"] += 1
        for _, etype in result["false_positives"]:
            counts[etype]["fp"] += 1

        errors = categorise_errors(result["false_negatives"], result["false_positives"])
        all_type_mismatches += [(page_id, *e) for e in errors["type_mismatches"]]
        all_partial_spans += [(page_id, *e) for e in errors["partial_spans"]]
        all_missed += [(page_id, *e) for e in errors["missed_entirely"]]
        all_spurious += [(page_id, *e) for e in errors["spurious"]]

    # Build the report
    lines = ["# Evaluation Results\n"]
    lines.append(f"Evaluated on {len(gold_pages)} hand-annotated gold-standard pages.\n")
    lines.append("## Precision / Recall / F1 by entity type\n")
    lines.append("| Type | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|------|----|----|----|-----------|--------|----|")

    for etype in ["taxon", "person", "locality"]:
        c = counts[etype]
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        lines.append(f"| {etype} | {tp} | {fp} | {fn} | {precision:.2f} | {recall:.2f} | {f1:.2f} |")

    lines.append("\n## Error taxonomy\n")

    lines.append(f"### Type mismatches ({len(all_type_mismatches)})")
    lines.append("Same text extracted, but classified as the wrong entity type.\n")
    for page_id, text, gold_type, pred_type in all_type_mismatches:
        lines.append(f"- page {page_id}: \"{text}\" — gold={gold_type}, predicted={pred_type}")

    lines.append(f"\n### Partial span errors ({len(all_partial_spans)})")
    lines.append("Predicted text is a fragment of, or contains, the gold mention.\n")
    for page_id, text, gold_type, pred_text in all_partial_spans:
        lines.append(f"- page {page_id}: gold=\"{text}\" ({gold_type}) vs predicted=\"{pred_text}\"")

    lines.append(f"\n### Missed entirely ({len(all_missed)})")
    lines.append("Gold entities with no related prediction at all.\n")
    for page_id, text, gold_type in all_missed:
        lines.append(f"- page {page_id}: \"{text}\" ({gold_type})")

    lines.append(f"\n### Spurious / hallucinated ({len(all_spurious)})")
    lines.append("Predicted entities with no related gold entity.\n")
    for page_id, text, pred_type in all_spurious:
        lines.append(f"- page {page_id}: \"{text}\" ({pred_type})")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report written to {OUT_PATH}")
    print("\n--- Summary ---")
    for etype in ["taxon", "person", "locality"]:
        c = counts[etype]
        print(f"{etype}: TP={c['tp']} FP={c['fp']} FN={c['fn']}")
    print(f"Type mismatches: {len(all_type_mismatches)}")
    print(f"Partial span errors: {len(all_partial_spans)}")
    print(f"Missed entirely: {len(all_missed)}")
    print(f"Spurious: {len(all_spurious)}")


if __name__ == "__main__":
    run()