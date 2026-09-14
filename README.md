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
- [ ] GBIF reconciliation
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
gold-standard pages, using exact-match on (mention_text, entity_type):

| Type     | Precision | Recall | F1   |
|----------|-----------|--------|------|
| taxon    | 0.95      | 0.89   | 0.92 |
| person   | 1.00      | 0.74   | 0.85 |
| locality | 0.76      | 0.79   | 0.77 |

Full breakdown, including a categorised error taxonomy (type mismatches,
partial-span errors, missed entities, spurious extractions), is in
[`results/metrics.md`](results/metrics.md).

**Key findings:**
- **Taxon extraction is strongest** (F1 0.92) — Latin binomials follow a
  consistent, learnable pattern the model handles well even with OCR noise.
- **Locality precision is the weakest area** (0.76) — the model produced
  false positives like extracting "Equator" and "Red Sea" as localities in
  contexts where they don't refer to a specific mentioned place on that
  page, and once hallucinated a locality from a footnote reference ("The
  Ibis," the journal's own title) that isn't a real place at all.
- **Person recall is lower than precision** (0.74 vs 1.00) — the model
  never produced a false person, but consistently missed people named only
  by surname in citation-style text (e.g. "Baird", "Gould", "Cassin" used
  as taxonomic authorities rather than active subjects).
- **Exact-string matching likely undercounts real performance**: several
  "missed" and "spurious" entities are actually the same underlying entity
  with a minor OCR-variant spelling difference (e.g. gold
  "Pycnonotusjocosus" vs predicted "Pycnonotus jocosus"), counted as two
  separate errors rather than one near-miss. A fuzzy-matching evaluation
  pass would give a more accurate picture — noted as a next step.

## Setup

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
```

## Limitations (so far)

- Sample is small (19 pages) and drawn from a single journal title; not
  representative of BHL's full breadth of publication types and languages.
- The page-selection heuristic is intentionally crude and was corrected
  manually rather than automatically — a production pipeline would need a
  more principled content-classification step.