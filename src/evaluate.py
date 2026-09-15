"""
src/evaluate.py

Compare hand-annotated gold-standard entities against the LLM's extracted
entities for the same pages: precision/recall/F1 per entity type, plus a
categorized error breakdown (type mismatches, partial spans, near-matches,
missed entities, spurious extractions).

Matching rules:
  - Exact match: (mention_text, entity_type) identical.
  - Near match (fuzzy): same entity_type, mention_text similarity above
    FUZZY_MATCH_THRESHOLD (character-level ratio). Catches cases where the
    gold and predicted mentions are the same real entity but differ by a
    minor OCR-variant spelling (e.g. "Pycnonotusjocosus" vs
    "Pycnonotus jocosus"). Reported separately from exact TP, not folded
    silently into the headline precision/recall, so the distinction stays
    visible.

Usage:
    python evaluate.py
"""

import json
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher

GOLD_PATH = Path(__file__).resolve().parent.parent / "data" / "gold_standard" / "annotation_template.json"
EXTRACTED_PATH = Path(__file__).resolve().parent.parent / "data" / "extracted_entities.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "results" / "metrics.md"

FUZZY_MATCH_THRESHOLD = 0.85


def normalise_key(entity: dict) -> tuple:
    return (entity["mention_text"].strip(), entity["entity_type"])


def text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_near_matches(false_negatives: set, false_positives: set) -> list:
    """Pair up FN/FP of the same type with high text similarity."""
    near_matches = []
    used_fp = set()

    for fn_text, fn_type in false_negatives:
        best, best_score = None, 0.0
        for fp_text, fp_type in false_positives:
            if fp_type != fn_type or (fp_text, fp_type) in used_fp:
                continue
            score = text_similarity(fn_text, fp_text)
            if score > best_score:
                best_score, best = score, (fp_text, fp_type)

        if best and best_score >= FUZZY_MATCH_THRESHOLD:
            near_matches.append((fn_text, best[0], fn_type, round(best_score, 2)))
            used_fp.add(best)

    return near_matches


def evaluate_page(gold_entities: list, predicted_entities: list) -> dict:
    gold_keys = {normalise_key(e) for e in gold_entities}
    pred_keys = {normalise_key(e) for e in predicted_entities}

    true_positives = gold_keys & pred_keys
    false_negatives = gold_keys - pred_keys
    false_positives = pred_keys - gold_keys

    near_matches = find_near_matches(false_negatives, false_positives)
    near_fn = {(t, ty) for t, _, ty, _ in near_matches}
    near_fp = {(t, ty) for _, t, ty, _ in near_matches}

    # Remove near-matched pairs from the "genuine" FN/FP sets
    remaining_fn = false_negatives - near_fn
    remaining_fp = false_positives - near_fp

    return {
        "true_positives": true_positives,
        "near_matches": near_matches,
        "false_negatives": remaining_fn,
        "false_positives": remaining_fp,
    }


def categorise_errors(false_negatives: set, false_positives: set) -> dict:
    type_mismatches, partial_spans, missed_entirely, spurious = [], [], [], []
    matched_fp = set()

    for fn_text, fn_type in false_negatives:
        same_text_fp = [(t, ty) for (t, ty) in false_positives if t == fn_text]
        if same_text_fp:
            type_mismatches.append((fn_text, fn_type, same_text_fp[0][1]))
            matched_fp.add(same_text_fp[0])
            continue

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

    counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "near": 0})
    all_near_matches = []
    all_type_mismatches = []
    all_partial_spans = []
    all_missed = []
    all_spurious = []

    for page_id, gold_entities in gold_pages.items():
        predicted_entities = extracted_pages.get(page_id, [])
        result = evaluate_page(gold_entities, predicted_entities)

        for _, etype in result["true_positives"]:
            counts[etype]["tp"] += 1
        for _, _, etype, _ in result["near_matches"]:
            counts[etype]["near"] += 1
        for _, etype in result["false_negatives"]:
            counts[etype]["fn"] += 1
        for _, etype in result["false_positives"]:
            counts[etype]["fp"] += 1

        all_near_matches += [(page_id, *nm) for nm in result["near_matches"]]

        errors = categorise_errors(result["false_negatives"], result["false_positives"])
        all_type_mismatches += [(page_id, *e) for e in errors["type_mismatches"]]
        all_partial_spans += [(page_id, *e) for e in errors["partial_spans"]]
        all_missed += [(page_id, *e) for e in errors["missed_entirely"]]
        all_spurious += [(page_id, *e) for e in errors["spurious"]]

    lines = ["# Evaluation Results\n"]
    lines.append(f"Evaluated on {len(gold_pages)} hand-annotated gold-standard pages.\n")
    lines.append("## Precision / Recall / F1 by entity type (strict exact-match)\n")
    lines.append("| Type | TP | FP | FN | Precision | Recall | F1 |")
    lines.append("|------|----|----|----|-----------|--------|----|")

    for etype in ["taxon", "person", "locality"]:
        c = counts[etype]
        tp, fp, fn = c["tp"], c["fp"], c["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        lines.append(f"| {etype} | {tp} | {fp} | {fn} | {precision:.2f} | {recall:.2f} | {f1:.2f} |")

    lines.append("\n## Precision / Recall / F1 including near-matches (fuzzy, OCR-variant spelling)\n")
    lines.append(f"Near-matches (similarity >= {FUZZY_MATCH_THRESHOLD}) are counted as correct here, "
                  "treating minor OCR-variant spelling differences as the same real entity.\n")
    lines.append("| Type | TP+Near | FP | FN | Precision | Recall | F1 |")
    lines.append("|------|---------|----|----|-----------|--------|----|")

    for etype in ["taxon", "person", "locality"]:
        c = counts[etype]
        tp_plus_near, fp, fn = c["tp"] + c["near"], c["fp"], c["fn"]
        precision = tp_plus_near / (tp_plus_near + fp) if (tp_plus_near + fp) else 0
        recall = tp_plus_near / (tp_plus_near + fn) if (tp_plus_near + fn) else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
        lines.append(f"| {etype} | {tp_plus_near} | {fp} | {fn} | {precision:.2f} | {recall:.2f} | {f1:.2f} |")

    lines.append(f"\n## Near-matches detected ({len(all_near_matches)})")
    lines.append("Same real entity, minor OCR-variant spelling difference between gold and predicted.\n")
    for page_id, fn_text, fp_text, etype, score in all_near_matches:
        lines.append(f"- page {page_id}: gold=\"{fn_text}\" vs predicted=\"{fp_text}\" ({etype}, similarity={score})")

    lines.append(f"\n## Error taxonomy (excludes near-matches above)\n")

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
    print("\n--- Summary (strict exact-match) ---")
    for etype in ["taxon", "person", "locality"]:
        c = counts[etype]
        print(f"{etype}: TP={c['tp']} near={c['near']} FP={c['fp']} FN={c['fn']}")
    print(f"Type mismatches: {len(all_type_mismatches)}")
    print(f"Partial span errors: {len(all_partial_spans)}")
    print(f"Missed entirely: {len(all_missed)}")
    print(f"Spurious: {len(all_spurious)}")


if __name__ == "__main__":
    run()