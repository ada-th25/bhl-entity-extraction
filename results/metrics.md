# Evaluation Results

Evaluated on 5 hand-annotated gold-standard pages.

## Precision / Recall / F1 by entity type

| Type | TP | FP | FN | Precision | Recall | F1 |
|------|----|----|----|-----------|--------|----|
| taxon | 128 | 7 | 16 | 0.95 | 0.89 | 0.92 |
| person | 14 | 0 | 5 | 1.00 | 0.74 | 0.85 |
| locality | 22 | 7 | 6 | 0.76 | 0.79 | 0.77 |

## Error taxonomy

### Type mismatches (0)
Same text extracted, but classified as the wrong entity type.


### Partial span errors (3)
Predicted text is a fragment of, or contains, the gold mention.

- page 54832638: gold="Irena puella" (taxon) vs predicted="Irena puella f."
- page 54832638: gold="Catarractes" (taxon) vs predicted="Catarractes antarcticus"
- page 54832312: gold="Algerian" (locality) vs predicted="Algeria"

### Missed entirely (24)
Gold entities with no related prediction at all.

- page 54832638: "Pycnonotusjocosus" (taxon)
- page 54832638: "Nectariniidai" (taxon)
- page 54832638: "C. antarcticus" (taxon)
- page 54832638: "I. indica" (taxon)
- page 54832638: "Treron" (taxon)
- page 54832312: "S. elaica" (taxon)
- page 54832312: "Fr. ccelebs" (taxon)
- page 54832312: "F. concolor" (taxon)
- page 54832312: "Gecinus viridis" (taxon)
- page 54832312: "L. meridionalis" (taxon)
- page 54832312: "Microcarbo pygmeeus" (taxon)
- page 54832312: "European" (locality)
- page 8330882: "Falco anatam" (taxon)
- page 8330882: "Baird" (person)
- page 8330882: "Cassin" (person)
- page 8330882: "Gould" (person)
- page 8330882: "Buteo insignatus" (taxon)
- page 8330882: "Montreal" (locality)
- page 8330882: "Buteogallus nigrioollis" (taxon)
- page 8330882: "Toronto" (locality)
- page 8330712: "Smithsonian Institution" (locality)
- page 8330712: "Baird" (person)
- page 8750262: "Little Cameroon" (locality)
- page 8750262: "Mr. D. A. Bannerman" (person)

### Spurious / hallucinated (11)
Predicted entities with no related gold entity.

- page 54832638: "Equator" (locality)
- page 54832638: "Nicobarica" (locality)
- page 54832638: "Pycnonotus jocosus" (taxon)
- page 54832638: "Negrillo" (locality)
- page 54832312: "Red Sea" (locality)
- page 8330882: "And no mention of the Red Sea" (locality)
- page 8330882: "Buteogallus nigriorillis" (taxon)
- page 8330882: "Buteo insignis" (taxon)
- page 8330882: "Emeu" (taxon)
- page 8330882: "Falco anatum" (taxon)
- page 8330712: "The Ibis" (locality)