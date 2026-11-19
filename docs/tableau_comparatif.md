# Tableau comparatif (responsable : Boutheina)

| **Modèle**                     | **Accuracy (%)** | **Durée (s)** | **Énergie (kWh)** | **Émissions (g CO₂eq)** | **Matériel** |
|--------------------------------|------------------|---------------|-------------------|-------------------------|--------------|
| TF-IDF + Régression logistique |                  |               |                   |                         |              |
| DistilBERT                     |                  |               |                   |                         |              |
| Écart (lourd − léger)          |                  |               |                   |                         |              |

**Indicateur principal : coût carbone par point de précision gagné**

Coût carbone par point = (Émissions DistilBERT − Émissions LogReg) ÷ (Accuracy DistilBERT − Accuracy LogReg)  
(émissions en g CO₂eq, accuracy en points de %)

*Exemple fictif pour illustrer :* si DistilBERT émet 40 g CO₂ contre 0,5 g pour LogReg, et atteint 94 % de précision contre 90 %, alors :  
(40 − 0,5) ÷ (94 − 90) = 39,5 ÷ 4 ≈ **9,9 g CO₂ par point de précision gagné**.**

Règles de calcul**

- Chaque valeur est la moyenne de 3 entraînements (± écart-type).

- Pour comparer équitablement, les émissions des deux modèles sont recalculées avec la même intensité carbone (énergie × 483 g CO₂/kWh pour la Tunisie, ou × 295 g CO₂/kWh pour l’Iowa).

- Les valeurs viennent des colonnes du fichier emissions.csv : duration → Durée, energy_consumed → Énergie, emissions → Émissions (en kg, à multiplier par 1 000 pour avoir des grammes).
