# Analyse de sensibilité (responsable : Ghayth)

Séance 3 · 27/11/2026 · script : `src/sensibilite.py`

## Question

Notre indicateur clé est :

> **Coût carbone par point** = I × PUE × (E_lourd − E_léger) ÷ (acc_lourd − acc_léger)  [g CO₂eq / point]

Il repose sur des hypothèses : intensité du réseau, PUE, forfaits de CodeCarbon, taille du jeu de test…
**Lesquelles changent vraiment la conclusion ?** On fait varier **une hypothèse à la fois** autour d'un
scénario de référence, et on mesure l'écart sur l'indicateur.

```bash
python -m src.sensibilite      # lit resultats/emissions_leger.csv et resultats/kaggle/
```

## Scénario de référence (mesures de la séance 3)

| Paramètre | Valeur | Source |
|---|---|---|
| E_léger | 0,0397 Wh | 3 runs d'Ali (Colab CPU, Nevada) |
| E_lourd | 0,791 Wh | 3 runs d'Ons (Kaggle T4, Iowa) |
| acc_léger → acc_lourd | 88,40 % → 90,45 % (Δacc = 2,05 points) | idem (identiques sur les 3 runs) |
| Intensité I | 288 g CO₂/kWh | Iowa, référence de l'équipe |
| PUE | 1,0 | défaut CodeCarbon |
| **Coût par point** | **0,106 g CO₂eq / point** | identique à `resultats/tableau_comparatif.md` |

## Résultats (tornade, de l'hypothèse la plus influente à la moins influente)

| Hypothèse | Plage testée | Coût / point bas | Coût / point haut | Écart max |
|---|---|---|---|---|
| Fabrication du matériel incluse | 0 → amortissement haut (voir `fabrication_materiel.md`) | 0,106 | 0,307 | **+ 191 %** |
| Intensité carbone du réseau | 166 (Oregon) → 560 g/kWh (Tunisie, Ember) | 0,061 | 0,205 | **± 94 %** |
| Gain d'accuracy (± 1 erreur-type, n = 2 000) | Δacc = 2,05 ± 0,97 point | 0,072 | 0,201 | **± 90 %** |
| PUE du datacenter | 1,0 → 1,56 (moyenne industrie) | 0,106 | 0,165 | + 56 % |
| RAM : forfait CodeCarbon | retiré → conservé | 0,083 | 0,106 | − 22 % |
| 2ᵉ T4 au repos compté par CodeCarbon | retiré (≈ 10 W) → conservé | 0,092 | 0,106 | − 13 % |
| Variabilité de la mesure d'énergie lourde | ± 2 CV = ± 9 % (3 runs d'Ons) | 0,095 | 0,116 | ± 10 % |

**Tous les choix favorables combinés : 0,023 g / point. Tous défavorables : 1,05 g / point. Rapport : × 46.**

*Ligne « 2ᵉ T4 » :* Ons mesure désormais avec `gpu_ids=[0]`. Mais le CSV de ses runs indique encore
`gpu_count = 2` (« 2 x Tesla T4 »), donc le script garde la ligne par prudence. Si Ons confirme que
seul le GPU 0 est mesuré, cette ligne disparaît et le rapport passe à × 37.

## Ce qu'il faut retenir

1. **Le lieu de calcul pèse presque autant que le choix du modèle.** Entre l'Oregon et la Tunisie,
   l'indicateur est multiplié par 3,4. → Argument pour la règle « choisir où calculer » de la charte.

2. **Le dénominateur est fragile.** Le gain de DistilBERT n'est que de 2,05 points. Avec 2 000 exemples
   de test, il est connu à ± 0,97 point près (1 erreur-type), soit **± 1,9 point à 95 %** : le gain est
   à peine significatif, et l'indicateur peut varier de ± 90 % pour cette seule raison. (Calcul
   prudent : les deux modèles étant testés sur les mêmes exemples, un test apparié de McNemar donnerait
   une marge un peu plus étroite.) → Toujours donner Δacc **avec son intervalle de confiance**, et utiliser
   le test complet d'AG News (7 600 exemples) quand l'écart est faible.

3. **La fabrication du matériel n'est pas un détail.** L'amortir ajoute entre **+ 34 % et + 191 %** au
   coût par point (détails dans `fabrication_materiel.md`). Elle est exclue du périmètre officiel,
   mais il faut le dire.

4. **Les forfaits et biais de CodeCarbon (RAM, GPU au repos) jouent moins** (≈ 10–20 %). Ils
   **surestiment** les deux modèles : sans eux, le coût par point baisse. Ils ne changent pas la
   conclusion, mais doivent être signalés.

5. **La mesure elle-même est stable** : les 3 runs DistilBERT ne varient que de 5 % en énergie (CV).
   L'incertitude vient donc **des hypothèses**, pas de l'appareil de mesure.

6. **Dans tous les cas, la conclusion qualitative tient** : DistilBERT consomme ≈ 20 fois plus
   d'énergie que le modèle léger (× 19,9) pour 2 points d'accuracy. Ce qui change, c'est le **chiffre**
   du coût par point (de 0,02 à 1,05 g / point). Il faut donc le publier **avec ses hypothèses**
   (I, PUE, n_test) et, idéalement, avec une fourchette.

## Recommandations pour le tableau comparatif et la charte (Boutheina, Ali)

- Afficher le coût par point **à intensité commune** (288 g/kWh), et indiquer à côté la fourchette
  166–560 g/kWh (0,061 à 0,205 g / point).
- Écrire Δacc avec son intervalle de confiance à 95 % : 2,05 ± 1,9 points.
- Règle proposée pour la charte : *« Publier chaque mesure avec ses hypothèses (lieu, intensité,
  PUE, matériel, n_test) et une fourchette, jamais un chiffre seul. »* (vérifiable : la ligne
  d'hypothèses est présente sous le tableau).

## Limites de cette analyse

- Variation **une à une** : les hypothèses ne sont pas indépendantes (le PUE et l'intensité dépendent
  tous deux du datacenter). Le « tout défavorable » est un cas extrême, pas un cas probable.
- Les bornes de chaque hypothèse sont des choix (sources dans `hypotheses.md` et `fabrication_materiel.md`).
- Seulement 3 runs par modèle : l'écart-type est lui-même peu précis.
