"""
src/schema.py

Defines the structured output schema for LLM entity extraction, plus
a jsonschema definition used to validate the LLM's raw output before
it's trusted anywhere downstream.

Entity types (deliberately scoped to 3 types,
prioritising depth over breadth given project time constraints):
  - taxon: a scientific species/genus name
  - person: a named individual (collector, author, correspondent)
  - locality: a place name

Design choices worth noting:
  - `mention_text` preserves the exact string as it appeared (including
    likely OCR noise), separately from any normalised form. Normalisation
    is a later, separate pipeline stage (reconciliation), not extraction.
  - `confidence` lets the LLM flag its own uncertainty (e.g. ambiguous OCR,
    unclear whether a word is a place or a person), which is useful signal
    for error analysis later.
"""

ENTITY_TYPES = ["taxon", "person", "locality"]

EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "mention_text": {
                        "type": "string",
                        "description": "Exact text of the entity as it appears in the source, including any OCR noise.",
                    },
                    "entity_type": {
                        "type": "string",
                        "enum": ENTITY_TYPES,
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Model's own confidence, e.g. 'low' if OCR noise makes the mention ambiguous.",
                    },
                },
                "required": ["mention_text", "entity_type", "confidence"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["entities"],
    "additionalProperties": False,
}


EXTRACTION_SYSTEM_PROMPT = """You are extracting named entities from OCR'd \
19th/20th century biodiversity literature (ornithology journals).

Extract every mention of:
- taxon: a scientific (Latin) species or genus name, e.g. "Rhea americana", "Falco anatum"
- person: a named individual (author, collector, correspondent), e.g. "Mr. A. Newton", "Dr. Henry Bryant"
- locality: a named place, e.g. "Andaman Islands", "Cameroon Mountain", "Red Sea"

Notes:
- The text may contain OCR errors (misread characters, broken words). Extract \
the entity as best you can identify it, preserving the text as it actually \
appears. Do not silently "correct" it.
- The text may include non-English passages (e.g. German scientific prose). \
Only extract entities from these; do not translate.
- Mark your confidence as "low" if OCR noise or ambiguity makes an entity \
mention unclear.
- Do not extract page numbers, journal titles, or citation numbers as entities.

Return ONLY valid JSON matching the required schema. No preamble, no markdown \
formatting, no explanation, just the JSON object."""