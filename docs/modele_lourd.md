# Modèle lourd : DistilBERT (responsable : Ons)

## Hyperparamètres (source : `HEAVY_PARAMS` dans `src/modele_lourd.py`)

| Paramètre | Valeur |
|---|---|
| Modèle | `distilbert-base-uncased` |
| Époques | 1 |
| Batch size (entraînement) | 16 |
| Learning rate | 5e-5 |
| Weight decay | 0.01 |
| Longueur max (tokens) | 128 |
| Précision | fp16 sur GPU |
| Graine | 42 |

## Matériel

- Plateforme : Kaggle
- GPU : _à remplir (ex. Tesla T4, 1 seul GPU utilisé)_

## Test court (séance 2) : 500 exemples train / 200 test

| Accuracy | Durée entraînement (s) | Énergie (kWh) | Émissions (g CO2eq) | Estimation vrai run (min) |
|---|---|---|---|---|
| | | | | |

Source : `emissions.csv` et `resultats/lourd_test_court.json` (sortie Kaggle).
