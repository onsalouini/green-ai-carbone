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

- Plateforme : Kaggle Notebooks (accélérateur « GPU T4 x2 », **un seul GPU utilisé** via `CUDA_VISIBLE_DEVICES=0`)
- GPU : **NVIDIA Tesla T4**, CPU Intel Xeon @ 2,00 GHz (4 threads), RAM 31,3 Go
- Versions : Python 3.13.16, torch 2.11.0+cu130, transformers 5.20.2, CodeCarbon 3.3.2
- Localisation détectée par CodeCarbon : **Iowa, États-Unis** (−95,85 ; 41,26), PUE = 1,0 (valeur par défaut)

## Test court (séance 2, 19/11/2026) : 500 exemples train / 200 test

| Accuracy | Durée entraînement (s) | Durée mesurée CodeCarbon (s) | Énergie (kWh) | Émissions (g CO2eq) | Estimation vrai run (min) |
|---|---|---|---|---|---|
| 0,83 | 5,4 | 56,2 | 0,000563 | 0,162 | 1,8 (< 20 min ✔) |

Source : `resultats/kaggle/emissions_lourd.csv` et `resultats/kaggle/lourd_test_court.json` (sortie Kaggle).

Répartition de l'énergie (CodeCarbon) :

| Composant | Puissance (W) | Énergie (kWh) | Part |
|---|---|---|---|
| RAM | 20,0 (forfait) | 0,000294 | 52 % |
| GPU | 14,7 | 0,000244 | 43 % |
| CPU | 1,7 | 0,000025 | 4 % |
| **Total** | | **0,000563** | |

## Remarques

- **La chaîne fonctionne de bout en bout** sur GPU : données → DistilBERT → accuracy → `emissions.csv`.
  C'est le rendu S2 pour le modèle lourd.
- **Durée mesurée ≠ durée d'entraînement** : CodeCarbon mesure 56 s, dont seulement 5,4 s
  d'entraînement. Le reste correspond au chargement du tokenizer et du modèle, à la tokenisation
  et à l'évaluation. Sur le vrai run, cette part fixe pèsera beaucoup moins.
- **Intensité carbone implicite** : 0,162 g ÷ 0,000563 kWh ≈ **288 g CO2/kWh**, proche de la valeur
  Iowa retenue dans `docs/hypotheses.md` (≈ 295).
- **Estimation du vrai run** (10 000 exemples, 1 époque) : ≈ 1,8 min d'entraînement, largement
  sous la limite des 20 min. Ce n'est qu'une extrapolation linéaire, à confirmer en séance 3.
- **CodeCarbon compte les deux T4** (`gpu_count = 2`, « 2 x Tesla T4 ») alors que l'entraînement n'en
  utilise qu'un : `CUDA_VISIBLE_DEVICES` ne limite pas ce que CodeCarbon lit via NVML. L'énergie GPU
  inclut donc la consommation au repos du second T4 : elle est **surestimée**. À corriger avant le vrai
  run (S3), par exemple `EmissionsTracker(..., gpu_ids=[0])` dans le code commun (décision d'équipe).
- **La RAM pèse plus que le GPU** sur ce test court : sa puissance est un forfait CodeCarbon (20 W), pas
  une mesure, comme l'a noté Boutheina pour Colab (10 W).
- Accuracy de 0,83 sur 500 exemples seulement : à ne pas comparer au modèle léger, ce n'est pas un résultat.
