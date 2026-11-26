# Tableau comparatif (responsable : Boutheina)

| **Modèle**                     | **Accuracy (%)** | **Durée (s)** | **Énergie (kWh)** | **Émissions (g CO₂eq)** | **Matériel** |
|--------------------------------|------------------|---------------|-------------------|-------------------------|--------------|
| TF-IDF + Régression logistique | 88,4             | 12,0 ± 3,0    | 0,000054 ± 0,000015 | 0,0090 ± 0,0025       | Colab CPU Intel Xeon 2,20 GHz (Oregon) |
| DistilBERT                     | 90,45            | 34,2 ± 4,1    | 0,000791 ± 0,000037 | 0,228 ± 0,011         | Kaggle GPU Tesla T4 (Iowa) |
| Écart (lourd − léger)          | + 2,05 points    | + 22,2 (× 2,9) | + 0,000737 (× 14,6) | + 0,219 (× 25)       | |

Moyenne ± écart-type : 5 runs pour le léger (Ali), 3 runs pour DistilBERT (Ons, `lourd_run1..3`).
L'accuracy est **identique sur tous les runs** de chaque modèle (88,40 % et 90,45 %, graine 42).
Durée DistilBERT = durée mesurée par CodeCarbon (chargement + entraînement + évaluation), dont ≈ 29 s
d'entraînement pur. Sources : `resultats/emissions_leger.csv`, `resultats/kaggle/emissions_lourd.csv`,
`resultats/kaggle/lourd_run*.json`.

⚠️ Les émissions brutes ne sont **pas comparables** : le léger a tourné en Oregon (≈ 166 g CO₂/kWh),
le lourd dans l'Iowa (≈ 288 g CO₂/kWh). On compare donc l'**énergie**, puis on recalcule à intensité commune.

## Résultat : coût carbone par point de précision gagné

Calcul à intensité commune : Coût = I × (E_lourd − E_léger) ÷ (acc_lourd − acc_léger),
avec E_lourd − E_léger = 0,737 Wh et acc_lourd − acc_léger = 2,05 points.

| Intensité carbone retenue | Coût par point (g CO₂eq / point) |
|---|---|
| 166 g/kWh (Oregon, Colab) | 0,060 |
| **288 g/kWh (Iowa, Kaggle) : référence** | **0,104** |
| 483 g/kWh (Tunisie, LowCarbonPower) | 0,174 |
| 560 g/kWh (Tunisie, Ember, valeur CodeCarbon) | 0,201 |

**Lecture :** DistilBERT consomme **14,6 fois plus d'énergie** que TF-IDF + LogReg pour **2 points
d'accuracy en plus** : chaque point gagné coûte ≈ 0,1 g CO₂eq (à 288 g/kWh), soit ≈ 7 fois les
émissions totales d'un entraînement du modèle léger à la même intensité (0,016 g).

**Incertitude :** avec 2 000 exemples de test, le gain d'accuracy vaut 2,05 ± 1,9 points (IC 95 %,
de 0,15 à 3,95 points). Le coût par point est donc très incertain (≈ 0,05 à 1,4 g / point à 288 g/kWh) ;
détails dans `docs/sensibilite.md`. La conclusion qualitative, elle, est nette : beaucoup plus d'énergie
pour un petit gain.

**Indicateur principal : coût carbone par point de précision gagné**

Coût carbone par point = (Émissions DistilBERT − Émissions LogReg) ÷ (Accuracy DistilBERT − Accuracy LogReg)  
(émissions en g CO₂eq, accuracy en points de %)

*Exemple fictif pour illustrer :* si DistilBERT émet 40 g CO₂ contre 0,5 g pour LogReg, et atteint 94 % de précision contre 90 %, alors :  
(40 − 0,5) ÷ (94 − 90) = 39,5 ÷ 4 ≈ **9,9 g CO₂ par point de précision gagné**.

**Règles de calcul**

- Chaque valeur est la moyenne d'au moins 3 entraînements (± écart-type).

- Pour comparer équitablement, les émissions des deux modèles sont recalculées avec la même intensité carbone (énergie × 288 g CO₂/kWh pour l’Iowa/Kaggle en référence ; Tunisie : 483 selon LowCarbonPower, 560 selon Ember, valeur utilisée par CodeCarbon).

- Les valeurs viennent des colonnes du fichier emissions.csv : duration → Durée, energy_consumed → Énergie, emissions → Émissions (en kg, à multiplier par 1 000 pour avoir des grammes).
