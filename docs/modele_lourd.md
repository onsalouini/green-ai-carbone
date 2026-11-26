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
- Versions : Python 3.13.16, torch 2.11.0+cu130, transformers 5.20.2, CodeCarbon 3.3.2 (S2) puis 3.3.3 (S3)
- Localisation détectée par CodeCarbon : **Iowa, États-Unis** (−95,85 ; 41,26), PUE = 1,0 (valeur par défaut)

## Vrais runs (séance 3, 26/11/2026) : 10 000 exemples train / 2 000 test

Commande : `python -m src.modele_lourd --runs 3` (notebook `notebooks/lourd_distilbert_kaggle.ipynb`),
mesure CodeCarbon chaque seconde, `gpu_ids=[0]`. Sources : `resultats/kaggle/emissions_lourd.csv`
et `resultats/kaggle/lourd_run1..3.json`.

| Run | Accuracy | Entraînement (s) | Durée mesurée (s) | Énergie (Wh) | Émissions (g CO2eq) |
|---|---|---|---|---|---|
| lourd_run1 | 0,9045 | 29,1 | 39,0 | 0,833 | 0,240 |
| lourd_run2 | 0,9045 | 29,0 | 31,7 | 0,768 | 0,221 |
| lourd_run3 | 0,9045 | 29,5 | 32,1 | 0,772 | 0,222 |
| **Moyenne ± écart-type** | **0,9045** | **29,2** | **34,2 ± 4,1** | **0,791 ± 0,037** (CV 5 %) | **0,228 ± 0,011** |

Répartition de l'énergie (moyenne des 3 runs) : **GPU 74 %**, RAM 24 % (forfait 20 W), CPU 2 %.
Intensité implicite : 288 g CO2/kWh (Iowa).

**Constats :**

- **Accuracy parfaitement reproductible** : 0,9045 sur les 3 runs, malgré le GPU et le fp16.
- **Énergie stable** : CV de 5 %, contre 28 % pour le léger sur Colab. Le run 1 est un peu plus long
  (39 s contre 32 s) : premier chargement du modèle et des noyaux CUDA.
- **Bien sous la limite des 20 min** : ≈ 30 s d'entraînement, 34 s mesurées au total. L'estimation de la S2
  (1,8 min) était pessimiste : le test court sur 500 exemples était dominé par le temps de démarrage.
- **2ᵉ T4 encore probablement compté** : malgré `gpu_ids=[0]`, le CSV indique toujours `gpu_count = 2`
  (« 2 x Tesla T4 ») et une puissance GPU qui atteint 82 W au run 2, au-dessus des 70 W maximum d'un seul T4.
  L'énergie GPU est donc peut-être surestimée d'environ 10 W × 34 s ≈ 0,09 Wh (≈ 12 %). Ce biais est
  couvert par la ligne « 2ᵉ T4 au repos » de `docs/sensibilite.md` (− 13 % sur le coût par point).
- Comparaison avec le modèle léger : voir `docs/tableau_comparatif.md`.

## Test court (séance 2, 19/11/2026) : 500 exemples train / 200 test

| Accuracy | Durée entraînement (s) | Durée mesurée CodeCarbon (s) | Énergie (kWh) | Émissions (g CO2eq) | Estimation vrai run (min) |
|---|---|---|---|---|---|
| 0,83 | 5,4 | 56,2 | 0,000563 | 0,162 | 1,8 (< 20 min ✔) |

Source : `resultats/kaggle/s2/emissions_lourd_s2.csv` et `resultats/kaggle/s2/lourd_test_court_s2.json` (sortie Kaggle S2).

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
