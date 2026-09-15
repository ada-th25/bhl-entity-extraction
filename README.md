# BHL Entity Extraction & Reconciliation

A small, self-contained pipeline for extracting structured entities (taxa,
people, localities) from OCR'd biodiversity literature sourced from the
[Biodiversity Heritage Library](https://www.biodiversitylibrary.org/) (BHL),
and reconciling extracted taxon names against [GBIF](https://www.gbif.org/).

Built as a hands-on exploration of the data-engineering and LLM-extraction
problems involved in turning large, historical, OCR'd text archives into
structured, queryable data.

## Status

🚧 In progress. Core pipeline complete for a small (19-page) sample:
- [x] BHL search + fetch pipeline (`search_bhl.py`, `fetch_bhl.py`)
- [x] Curated a 19-page working sample across 4 volumes (1859–1915)
- [x] Entity schema definition (`schema.py`)
- [x] LLM extraction pipeline with structured/validated output (`extract.py`)
- [x] Hand-annotated gold-standard evaluation set (5 pages, `gold_standard/`)
- [x] Evaluation + error analysis (`evaluate.py`, see Results below)
- [x] GBIF reconciliation
- [ ] Second annotation pass for inter-annotator agreement

## Problem

BHL has digitised tens of millions of pages of historical biodiversity
literature, but a scanned page image (even with OCR text) isn't yet usable
as *data*. Turning this archive into something researchers can query (e.g. "every mention of this species," "every specimen collected by this person") requires extracting structured entities from noisy historical text and
linking them to authoritative reference data. This project builds a small,
honest version of that pipeline.

## Data sample

Rather than sampling randomly, I selected a deliberately varied set of 19
pages across four *Ibis* (British Ornithologists' Union) journal volumes
spanning 1859–1915, split roughly:
- **15 narrative pages**: species accounts, correspondence, expedition
  notes, real sentences with entities embedded in context, mixing English,
  German, and Latin.
- **4 index pages**: dense alphabetical species listings, included as an
  "easy" contrast case.

An initial automated pre-filter (page length + a rough "Capitalised word
pair" heuristic meant to catch Latin binomials) over-selected index pages,
since they're structurally dense with exactly that pattern. Index pages
are a poor test of real extraction, since they have no surrounding
sentence context, so I manually reviewed the shortlist and re-weighted
toward narrative content. This turned out to matter: narrative pages
contain named people, localities, and multilingual text that a
list-based heuristic would never surface on its own.

See `data/sample_pages.json` for the curated sample and `src/select_pages.py`
/ `src/build_sample.py` for the selection process.

## Results

Evaluated LLM extraction (Llama 3.1 8B, local) against 5 hand-annotated
gold-standard pages. Two matching strategies are reported: strict exact
string match, and a fuzzy variant that also counts near-identical
OCR-variant spellings (similarity >= 0.85) as correct, since several
"errors" turned out to be the same real entity read slightly differently
by the annotator and the model (e.g. "Pycnonotusjocosus" vs "Pycnonotus
jocosus").

| Type     | Precision (strict) | Recall (strict) | F1 (strict) | F1 (fuzzy) |
|----------|--------------------|------------------|-------------|------------|
| taxon    | 0.98               | 0.92             | 0.95        | 0.95       |
| person   | 1.00               | 0.74             | 0.85        | 0.85       |
| locality | 0.79               | 0.81             | 0.80        | 0.81       |

Full breakdown, including the categorised error taxonomy, is in
[`results/metrics.md`](results/metrics.md).

**Key findings:**
- **Taxon extraction is strongest** (F1 0.95) even under OCR noise, since
  Latin binomials follow a consistent, learnable pattern.
- **The model reliably misses abbreviated genus back-references** e.g.
  "C. antarcticus" after "Catarractes" was introduced earlier in the same
  passage. All but one of the "missed entirely" taxon errors fit this
  exact pattern, suggesting the model doesn't reliably track a
  previously-mentioned genus across a passage the way a human reader
  would. This is a specific, addressable prompt-engineering target, not
  a generic weakness.
- **Person recall (0.74) is driven entirely by missed taxonomic
  authority citations** e.g. "Cassin", "Gould", "Baird" used as
  "Buteo insignatus of Cassin" rather than as active subjects. The model
  never produced a false person (precision 1.00), suggesting it is
  conservative rather than simply weak at person detection.
- **Locality precision (0.79) is the weakest metric**, driven by the
  model extracting broad/contextually-passing place references (e.g.
  "Equator", "Red Sea"), a journal title mistaken for a place ("The
  Ibis"), and one case of extracting an entire clause rather than
  isolating the place name within it ("And no mention of the Red Sea"
  instead of "Red Sea"); a distinct span-boundary failure, not a
  classification error.
- Six additional matches were only identified once fuzzy matching was
  applied, indicating strict exact-match evaluation modestly
  understates real extraction performance when OCR noise causes
  legitimate spelling variation between annotator and model readings.

## GBIF Reconciliation

Reconciled all 203 unique extracted taxon mentions against the GBIF
Taxonomy Backbone via GBIF's public Species Match API. Full results in
[`results/reconciliation_report.md`](results/reconciliation_report.md).

| Match type | Count | % |
|------------|-------|---|
| HIGHERRANK | 75    | 37% |
| EXACT      | 52    | 26% |
| NONE       | 50    | 25% |
| FUZZY      | 26    | 13% |

**Key findings:**
- **GBIF's own fuzzy matching absorbs a meaningful share of OCR noise
  without any custom normalisation logic** 26 mentions with OCR-damaged
  spelling (e.g. "Sus andamensis" -> "Sus andamanensis", "Sylvia elaica"
  -> "Sylvia elata") were still correctly resolved. This is a useful
  architectural finding: a production pipeline may not need extensive
  custom fuzzy-matching before reconciliation if the downstream authority
  source already has reasonable noise tolerance built in.
- **Unresolved (NONE) mentions fall into distinct, actionable categories**,
  not one generic "failure" bucket:
  - *Abbreviated genus references* ("C. skua", "M. manei") GBIF's
    matcher cannot resolve a single-letter genus abbreviation regardless
    of OCR quality. This is a structural limitation of matching
    abbreviated forms directly, not an OCR problem. Expanding
    abbreviated genus references to their full form (by tracking the
    most recently mentioned full genus in the same passage) before
    querying GBIF would likely resolve most of these.
  - *Bare species epithets with no genus* ("nigrivestis", "affinis",
    "minor"), traced back to the extraction stage: these come from
    numbered species lists using ditto marks ("2. „ nigrivestis.") to
    imply the same genus as the entry above, which the model extracted
    as if the epithet were a complete, standalone name. This is an
    extraction-stage limitation, not a reconciliation one. A concrete
    target for future prompt refinement (e.g. explicitly instructing the
    model to resolve ditto-mark list continuations against the prior
    genus).
  - *Non-taxa misclassified as taxon* ("Emeu", a common name; "Ruff",
    "Tringinae" -- subfamily/general anatomical terminology from a
    single dense ornithological-classification page) -- a small number
    of genuine entity-type extraction errors, distinct from OCR or
    reconciliation issues.
  - *Genuinely unresolvable OCR damage* (e.g. "Teplnrodornis griseola"),
    the expected residual noise floor even with authority-source fuzzy
    matching.

This reconciliation step, and the categorised breakdown of *why* matches
failed rather than just how many failed, was more informative than a
single match-rate number would have been on its own.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your BHL API key
```

Requires a free [BHL API key](https://www.biodiversitylibrary.org/getapikey.aspx),
and a local [Ollama](https://ollama.com) installation with `llama3.1:8b`
pulled (`ollama pull llama3.1:8b`) for the extraction step — no paid API
needed.

## Pipeline

```
src/search_bhl.py              -> search BHL for candidate volumes
src/fetch_bhl.py                -> pull full OCR'd text for a given volume
src/select_pages.py             -> heuristic pre-filter for content-rich pages
src/build_sample.py             -> extract a curated page set into data/sample_pages.json
src/schema.py                   -> entity schema + extraction prompt
src/extract.py                  -> LLM extraction pipeline (Ollama, structured output)
src/make_annotation_template.py -> generate blind annotation template for gold-standard labelling
src/evaluate.py                 -> compare gold-standard vs. extracted entities, error taxonomy
src/reconcile.py                -> Reconcile extracted taxon mentions against the GBIF Taxonomy Backbone
```

## Limitations (so far)

- Sample is small (19 pages) and drawn from a single journal title; not
  representative of BHL's full breadth of publication types and languages.
- The page-selection heuristic is intentionally crude and was corrected
  manually rather than automatically — a production pipeline would need a
  more principled content-classification step.