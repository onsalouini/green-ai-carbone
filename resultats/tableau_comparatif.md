# Tableau comparatif (généré par `python -m src.tableau`)

| Modèle | Accuracy (%) | Durée (s) | Énergie (kWh) | Émissions (g CO₂eq) | Matériel |
|---|---|---|---|---|---|
| TF-IDF + Régression logistique | 88,40 ± 0,00 | 9,0 ± 0,4 | 0,000040 ± 0,000003 | 0,0116 ± 0,0009 | CPU Intel(R) Xeon(R) CPU @ 2.20GHz (nevada) |
| DistilBERT | 90,45 ± 0,00 | 34,2 ± 4,1 | 0,000791 ± 0,000036 | 0,2276 ± 0,0105 | GPU Tesla T4 + CPU Intel(R) Xeon(R) CPU @ 2.00GHz (iowa) |
| Écart (lourd − léger) | + 2,05 points | + 25,3 (× 3,8) | + 0,000751 (× 19,9) | + 0,2160 (× 19,6) | |

Moyenne ± écart-type sur les runs : 3 runs pour TF-IDF + Régression logistique, 3 runs pour DistilBERT.
Émissions = émissions **mesurées** par CodeCarbon, avec l'intensité de la région de chaque run : elles ne sont pas comparables entre elles si les régions diffèrent.

## Émissions à intensité commune (énergie × intensité)

| Modèle | Tunisie (483 g/kWh) | Iowa (295 g/kWh) |
|---|---|---|
| TF-IDF + Régression logistique | 0,0192 ± 0,0014 | 0,0117 ± 0,0009 |
| DistilBERT | 0,3822 ± 0,0176 | 0,2334 ± 0,0108 |
| Écart (lourd − léger) | + 0,3630 (× 19,9) | + 0,2217 (× 19,9) |

Valeurs en g CO₂eq par run (moyenne ± écart-type).

## Coût carbone par point de précision gagné

Coût = (CO₂ lourd − CO₂ léger) ÷ (accuracy lourd − accuracy léger), avec les émissions recalculées à intensité commune.

| Intensité commune | Coût (g CO₂eq / point) |
|---|---|
| Tunisie (483 g/kWh) | 0,177 |
| Iowa (295 g/kWh) | 0,108 |

Gain d'accuracy : 2,05 points ; énergie en plus : 0,751 Wh ; ratio d'énergie lourd / léger : **× 19,9**.
