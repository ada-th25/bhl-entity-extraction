# Evaluation Results

Evaluated on 5 hand-annotated gold-standard pages.

## Precision / Recall / F1 by entity type (strict exact-match)

| Type | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|--------|----|
| taxon | 128 | 2 | 11 | 0.98 | 0.92 | 0.95 |
| person | 14 | 0 | 5 | 1.00 | 0.74 | 0.85 |
| locality | 22 | 6 | 5 | 0.79 | 0.81 | 0.80 |

## Precision / Recall / F1 including near-matches (fuzzy, OCR-variant spelling)

Near-matches (similarity >= 0.85) are counted as correct here, treating minor OCR-variant spelling differences as the same real entity.

| Type | TP+Near | FP | FN | Precision | Recall | F1 |
|------|---------|----|----|-----------|--------|----|
| taxon | 133 | 2 | 11 | 0.99 | 0.92 | 0.95 |
| person | 14 | 0 | 5 | 1.00 | 0.74 | 0.85 |
| locality | 23 | 6 | 5 | 0.79 | 0.82 | 0.81 |

## Near-matches detected (6)
Same real entity, minor OCR-variant spelling difference between gold and predicted.

- page 54832638: gold="Irena puella" vs predicted="Irena puella f." (taxon, similarity=0.89)
- page 54832638: gold="Pycnonotusjocosus" vs predicted="Pycnonotus jocosus" (taxon, similarity=0.97)
- page 54832312: gold="Algerian" vs predicted="Algeria" (locality, similarity=0.93)
- page 8330882: gold="Buteogallus nigrioollis" vs predicted="Buteogallus nigriorillis" (taxon, similarity=0.94)
- page 8330882: gold="Buteo insignatus" vs predicted="Buteo insignis" (taxon, similarity=0.87)
- page 8330882: gold="Falco anatam" vs predicted="Falco anatum" (taxon, similarity=0.92)

## Error taxonomy (excludes near-matches above)

### Type mismatches (0)
Same text extracted, but classified as the wrong entity type.


### Partial span errors (1)
Predicted text is a fragment of, or contains, the gold mention.

- page 54832638: gold="Catarractes" (taxon) vs predicted="Catarractes antarcticus"

### Missed entirely (20)
Gold entities with no related prediction at all.

- page 54832638: "C. antarcticus" (taxon)
- page 54832638: "Treron" (taxon)
- page 54832638: "I. indica" (taxon)
- page 54832638: "Nectariniidai" (taxon)
- page 54832312: "F. concolor" (taxon)
- page 54832312: "S. elaica" (taxon)
- page 54832312: "European" (locality)
- page 54832312: "Microcarbo pygmeeus" (taxon)
- page 54832312: "L. meridionalis" (taxon)
- page 54832312: "Gecinus viridis" (taxon)
- page 54832312: "Fr. ccelebs" (taxon)
- page 8330882: "Cassin" (person)
- page 8330882: "Gould" (person)
- page 8330882: "Toronto" (locality)
- page 8330882: "Montreal" (locality)
- page 8330882: "Baird" (person)
- page 8330712: "Smithsonian Institution" (locality)
- page 8330712: "Baird" (person)
- page 8750262: "Mr. D. A. Bannerman" (person)
- page 8750262: "Little Cameroon" (locality)

### Spurious / hallucinated (7)
Predicted entities with no related gold entity.

- page 54832638: "Negrillo" (locality)
- page 54832638: "Nicobarica" (locality)
- page 54832638: "Equator" (locality)
- page 54832312: "Red Sea" (locality)
- page 8330882: "Emeu" (taxon)
- page 8330882: "And no mention of the Red Sea" (locality)
- page 8330712: "The Ibis" (locality)