# BHL Entity Extraction & Reconciliation

A small, self-contained pipeline for extracting structured entities (taxa,
people, localities) from OCR'd biodiversity literature sourced from the
[Biodiversity Heritage Library](https://www.biodiversitylibrary.org/) (BHL),
and reconciling extracted taxon names against [GBIF](https://www.gbif.org/).

Built as a hands-on exploration of the data-engineering and LLM-extraction
problems involved in turning large, historical, OCR'd text archives into
structured, queryable data.

## Status

🚧 In progress. Currently complete:
- [x] BHL search + fetch pipeline (`search_bhl.py`, `fetch_bhl.py`)
- [x] Curated a 19-page working sample across 4 volumes (1859–1915)
- [ ] Entity schema definition
- [ ] LLM extraction pipeline with structured/validated output
- [ ] Hand-annotated gold-standard evaluation set
- [ ] Evaluation + error analysis
- [ ] GBIF reconciliation
- [ ] Final write-up and results

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

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in your real API keys
```

Requires an OpenAI API key and a free [BHL API key](https://www.biodiversitylibrary.org/getapikey.aspx).

## Pipeline

```
src/search_bhl.py    -> search BHL for candidate volumes
src/fetch_bhl.py      -> pull full OCR'd text for a given volume
src/select_pages.py   -> heuristic pre-filter for content-rich pages
src/build_sample.py   -> extract a curated page set into data/sample_pages.json
```

(More stages to be added as the project progresses — see Status above.)

## Limitations (so far)

- Sample is small (19 pages) and drawn from a single journal title; not
  representative of BHL's full breadth of publication types and languages.
- The page-selection heuristic is intentionally crude and was corrected
  manually rather than automatically — a production pipeline would need a
  more principled content-classification step.