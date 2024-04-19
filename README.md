# metanet_automatic_annotation
Annotazione automatica di MetaNet 

## Ordine di esecuzione dei file

### Costruzione file necessari
1. `py data/buildLexicalUnits.py`
2. `py data/buildMetaphorAncestors.py`

### Annotazione automatica
#### Versione di Davide
3. `py metanet_automatic_annotation.py`
4. `py evaluation.py`

#### Versione di Stefano
5. `py bot_v2.py`
6. `py bot_vs_annotations.py`

#### Comparazione delle due
7. `py compare_solutions.py`

#### Analisi delle differenze
8. `py analyzer.py` 
Quest'ultimo file è da modificare a seconda di ciò che si vuole analizzare