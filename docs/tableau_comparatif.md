# Tableau comparatif (responsable : Boutheina)

| **Modèle**                     | **Accuracy (%)** | **Durée (s)** | **Énergie (kWh)** | **Émissions (g CO₂eq)** | **Matériel** |
|--------------------------------|------------------|---------------|-------------------|-------------------------|--------------|
| TF-IDF + Régression logistique | 88,40            | 9,0 ± 0,4     | 0,000040 ± 0,000003 | 0,0116 ± 0,0009       | Colab CPU Intel Xeon 2,20 GHz (Nevada) |
| DistilBERT                     | 90,45            | 34,2 ± 4,1    | 0,000791 ± 0,000036 | 0,228 ± 0,011         | Kaggle GPU Tesla T4 (Iowa) |
| Écart (lourd − léger)          | + 2,05 points    | + 25,3 (× 3,8) | + 0,000751 (× 19,9) | + 0,216 (× 19,6)     | |

Moyenne ± écart-type : 3 runs pour le léger (Ali, `leger_run1..3`), 3 runs pour DistilBERT (Ons, `lourd_run1..3`).
L'accuracy est **identique sur tous les runs** de chaque modèle (88,40 % et 90,45 %, graine 42).
Durée DistilBERT = durée mesurée par CodeCarbon (chargement + entraînement + évaluation), dont ≈ 29 s
d'entraînement pur. Sources : `resultats/emissions_leger.csv`, `resultats/leger_run*.json`,
`resultats/kaggle/emissions_lourd.csv`, `resultats/kaggle/lourd_run*.json`. Tableau régénérable avec
`python -m src.tableau` (sortie : `resultats/tableau_comparatif.md`).

⚠️ Les émissions brutes ne sont **pas comparables** : le léger a tourné au Nevada (≈ 292 g CO₂/kWh),
le lourd dans l'Iowa (≈ 288 g CO₂/kWh). La région Colab change d'une session à l'autre (Oregon en S2,
Nevada en S3) : on compare donc l'**énergie**, puis on recalcule à intensité commune.

## Résultat : coût carbone par point de précision gagné

Calcul à intensité commune : Coût = I × (E_lourd − E_léger) ÷ (acc_lourd − acc_léger),
avec E_lourd − E_léger = 0,751 Wh et acc_lourd − acc_léger = 2,05 points.

| Intensité carbone retenue | Émissions léger (g) | Émissions DistilBERT (g) | Coût par point (g CO₂eq / point) |
|---|---|---|---|
| 166 g/kWh (Oregon) | 0,0066 | 0,131 | 0,061 |
| **288 g/kWh (Iowa, mesurée par CodeCarbon sur les runs Kaggle) : référence** | **0,0114** | **0,228** | **0,106** |
| 483 g/kWh (Tunisie, LowCarbonPower) | 0,0192 | 0,382 | 0,177 |
| 560 g/kWh (Tunisie, Ember, valeur CodeCarbon) | 0,0223 | 0,443 | 0,205 |

**Lecture :** DistilBERT consomme **19,9 fois plus d'énergie** que TF-IDF + LogReg pour **2 points
d'accuracy en plus** : chaque point gagné coûte ≈ 0,11 g CO₂eq (à 288 g/kWh), soit ≈ 9 fois les
émissions totales d'un entraînement du modèle léger à la même intensité (0,0114 g).

**Incertitude :** avec 2 000 exemples de test, le gain d'accuracy vaut 2,05 ± 1,9 points (IC 95 %,
de 0,15 à 3,95 points). Le coût par point est donc très incertain (≈ 0,05 à 1,4 g / point à 288 g/kWh) ;
détails dans `docs/sensibilite.md`. La conclusion qualitative, elle, est nette : beaucoup plus d'énergie
pour un petit gain.

**Règles de calcul**

- Chaque valeur est la moyenne ± écart-type de 3 runs pour chaque modèle.

- Pour comparer équitablement, les émissions des deux modèles sont recalculées avec la même intensité carbone (énergie × 288 g CO₂/kWh pour l’Iowa/Kaggle en référence, valeur mesurée par CodeCarbon sur les runs d'Ons ; Tunisie : 483 selon LowCarbonPower, 560 selon Ember, valeur utilisée par CodeCarbon).

- Les valeurs viennent des colonnes du fichier emissions.csv : duration → Durée, energy_consumed → Énergie, emissions → Émissions (en kg, à multiplier par 1 000 pour avoir des grammes).
