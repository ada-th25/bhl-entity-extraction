## Schema-following failure with the local model (first attempt)

Initial extraction runs with `llama3.1:8b` returned 0/19 pages passing
schema validation. The model correctly identified entities (person names,
localities, taxa) but consistently restructured output into a grouped
`{"taxa": [...], "people": [...], "localities": [...]}` shape rather than
the flat `entities` array specified in the schema and system prompt,
despite temperature=0 and an explicit "return ONLY this schema" instruction.

This is a known limitation of smaller open-weight models: semantic
understanding of the task can be solid while exact structural
instruction-following is weaker than a larger hosted model would likely
provide. Fixed by switching from Ollama's generic `"format": "json"` mode
to passing the full JSON schema directly to `format`, which constrains
token generation rather than relying on prompt compliance alone.

Also encountered several read timeouts on longer pages: increased
timeout from 120s to 300s to account for local (CPU/GPU-bound) inference
being substantially slower than a hosted API.

## Extraction coverage and failure pattern

Final extraction run: 10/19 pages (53%) succeeded within the 120s
wall-clock limit; 9 timed out. Failures were not evenly distributed:
they clustered in the second half of the run, suggesting performance
degraded over the course of sustained local inference (likely thermal
throttling or memory pressure on a laptop, rather than page difficulty
alone, since some later narrative pages of similar length to earlier
successes also failed). This is a concrete illustration of a real
trade-off: a free, local model avoids API costs but is less reliable
for sustained batch workloads than a hosted API would likely be on
dedicated infrastructure. Worth weighing explicitly in any real
production pipeline design.

## Locality scope

"Locality" is defined as a specific, mappable place (country, region,
city, island, mountain, building/institution-as-place) that could
reasonably be matched to a single entry in a gazetteer (e.g. GeoNames).

Broad geographic or climatic zones (e.g. "the Tropics", "the Equator",
"the Arctic") are excluded, since they don't refer to one specific,
linkable place. This is a deliberate scoping decision, not an oversight;
a production system might handle these differently (e.g. as a separate
"region" entity type), but for this project's 3-type schema they fall
outside "locality."

## Evaluation results and interpretation

Exact-match evaluation against 5 gold-standard pages gave F1 scores of
0.92 (taxon), 0.85 (person), 0.77 (locality). Reviewing the categorised
errors rather than trusting the headline numbers alone surfaced two
genuine findings:

1. Several "missed" and "spurious" entities are actually the same
   underlying mention with a minor OCR-variant spelling difference (e.g.
   gold "Pycnonotusjocosus" vs predicted "Pycnonotus jocosus"; gold
   "Buteogallus nigrioollis" vs predicted "Buteogallus nigriorillis").
   Exact-string matching counts these as two separate errors rather than
   one near-miss, meaning the true performance is likely somewhat better
   than the raw numbers suggest. A fuzzy/edit-distance matching pass
   would give a fairer picture, left as a next step given time
   constraints.
2. Locality precision (0.76) is the weakest metric, driven by the model
   extracting broad or contextually-irrelevant place references (e.g.
   "Equator", "Red Sea" mentioned in passing) and, in one case,
   hallucinating a locality from the journal's own title ("The Ibis")
   appearing in a footnote citation. This suggests the extraction prompt
   would benefit from stricter guidance distinguishing "a place actively
   being discussed" from "a place mentioned only in passing or as part of
   a citation."

## GBIF reconciliation methodology

Reconciliation ran on unique mention_text values only (not every
occurrence across pages), since repeated mentions of the same taxon
would waste API calls without adding information. GBIF's own matchType
field (EXACT/FUZZY/HIGHERRANK/NONE) was used directly as the confidence
signal rather than inventing a separate custom scoring scheme, since
GBIF's fuzzy matching already accounts for common spelling variation,
relevant given the OCR noise in this corpus. Unresolved matches were
categorised by likely cause (abbreviated genus, bare epithet from
ditto-mark lists, non-taxon misclassification, genuine OCR damage)
rather than reported as a single undifferentiated failure count.