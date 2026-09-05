# Annotation Guidelines for Historical Ornithological Texts

This document outlines the standard rules for named entity recognition (NER) across historical ornithological literature. The schema strictly uses three entity types: `taxon`, `locality`, and `person`.

---

## 1. Schema Types & Scope

### `taxon`
- **Scientific Names Only:** Annotate binomials, trinomials, genera, and abbreviated scientific names (e.g., *Hcematornis cheela*, *Catarractes*, *C. antarcticus*, *Fr. ccelebs*).
- **Exclude Common Names:** Do **not** annotate vernacular or common names (e.g., exclude "Dugong", "Emeu", "Turkey Buzzard", "Robin", "Green Pigeons").
- **Preserve OCR Artifacts:** Annotate OCR errors exactly as they appear in the source text without silent correction (e.g., `Pa7'us ledouci`, `Corms culminatus`).

### `locality`
- **Specific Geographic Entities:** Includes countries, islands, mountains, towns, bodies of water, and administrative divisions (e.g., "England", "Andalusia", "Andaman Islands", "Cameroon Mountain", "Ambas Bay").
- **Geographic Adjectives:** Adjectival forms derived from locations are included as `locality` (e.g., "Algerian" in *"14 Algerian non-European species"*).
- **Institutions as Localities:** Because the schema lacks a dedicated `institution` entity type, physical institutions, museums, and research centers must be folded into `locality` (e.g., "Calcutta Museum", "Smithsonian Institution").
- **Exclude Broad/Non-Specific Terms:** Exclude general, non-bounded geographical terms such as "the Tropics" or "the Equator".

### `person`
- **Active Participants & Historical Figures:** Annotate all named individuals referenced in the text (e.g., "Mr. G. C. Taylor", "Dr. Henry Bryant", "Sir Joseph Hooker").
- **Taxonomic Authorities & Citation Sources:** Include authors cited in catalog references, authorities, or parenthetical citations (e.g., "Baird" in *"Baird's Catalogue"*, "Gould", "Cassin", "A. Hay", "Temminck").

---

## 2. Text Normalisation & Line Breaks

- **Hyphenated Line Breaks:** Rejoin word tokens split across lines by typesetting hyphens into a single entity string (e.g., `Dryoscopus angolensia o-risescens` or `Pyromelana xantbomelas pboenicomera`). This is a formatting artifact, not genuine textual ambiguity.
- **Abbreviated Taxa:** Retain genus/species abbreviations exactly as rendered in the text (e.g., `C. antarcticus`, `I. indica`, `H. smyrnensis`). Do not expand them to their full form.
- **Exhaustive Exhaustion in Dense Lists:** All valid taxa listed in dense enumerations (e.g., numbered species lists) must be captured completely without skipping entries.