# Analyse de sensibilité (responsable : Ghayth)

Séance 3 · 26/11/2026 · script : `src/sensibilite.py`

## Question

Notre indicateur clé est :

> **Coût carbone par point** = I × PUE × (E_lourd − E_léger) ÷ (acc_lourd − acc_léger)  [g CO₂eq / point]

Il repose sur des hypothèses : intensité du réseau, PUE, forfaits de CodeCarbon, taille du jeu de test…
**Lesquelles changent vraiment la conclusion ?** On fait varier **une hypothèse à la fois** autour d'un
scénario de référence, et on mesure l'écart sur l'indicateur.

> ⚠️ **Chiffres provisoires.** Les vrais runs DistilBERT (10 000 / 2 000) ne sont pas encore poussés.
> Le modèle lourd est pour l'instant un **scénario** : 4 Wh (extrapolé du test court : ≈ 108 s
> d'entraînement GPU à ≈ 100 W + ≈ 60 s de chargement et d'évaluation à ≈ 36 W) et 91 % d'accuracy.
> Dès que les runs d'Ons seront dans `resultats/kaggle/`, le script les lit tout seul :
> `python -m src.sensibilite`. Le **classement** des hypothèses ci-dessous changera peu, car
> l'indicateur est proportionnel à la plupart d'entre elles.

## Scénario de référence

| Paramètre | Valeur | Source |
|---|---|---|
| E_léger | 0,0541 Wh | moyenne des 5 runs d'Ali |
| E_lourd | 4,0 Wh *(provisoire)* | extrapolation du test court d'Ons |
| acc_léger → acc_lourd | 88,40 % → 91,0 % *(provisoire)* | Ali / ordre de grandeur |
| Intensité I | 288 g CO₂/kWh | Kaggle, Iowa (mesure CodeCarbon) |
| PUE | 1,0 | défaut CodeCarbon |
| **Coût par point** | **0,44 g CO₂eq / point** *(provisoire)* | |

## Résultats (tornade, de l'hypothèse la plus influente à la moins influente)

| Hypothèse | Plage testée | Coût / point bas | Coût / point haut | Écart max |
|---|---|---|---|---|
| Fabrication du matériel incluse | 0 → amortissement haut (voir `fabrication_materiel.md`) | 0,44 | 1,24 | **+183 %** |
| Intensité carbone du réseau | 166 (Oregon) → 560 g/kWh (Tunisie) | 0,25 | 0,85 | **± 94 %** |
| Gain d'accuracy (± 1 erreur-type, n = 2 000) | Δacc ± 0,96 point | 0,32 | 0,69 | ± 59 % |
| PUE du datacenter | 1,0 → 1,56 (moyenne industrie) | 0,44 | 0,68 | + 56 % |
| Variabilité de la mesure d'énergie | ± 28 % (CV max observé, voir `reproductibilite.md`) | 0,31 | 0,56 | ± 28 % |
| RAM : forfait CodeCarbon | retiré → conservé | 0,34 | 0,44 | − 23 % |
| 2ᵉ T4 au repos compté par CodeCarbon | retiré (≈ 10 W) → conservé | 0,39 | 0,44 | − 12 % |

*Ligne « 2ᵉ T4 » :* elle ne concerne que les mesures prises avant la correction d'Ons. Le code commun
mesure désormais avec `gpu_ids=[0]`, donc CodeCarbon ne voit plus le second T4. Le script
détecte ces runs (`gpu_count = 1`) et n'affiche alors plus cette ligne.

**Tous les choix favorables combinés : 0,07 g / point. Tous défavorables : 3,97 g / point. Rapport : × 59.**

## Ce qu'il faut retenir

1. **Le lieu de calcul pèse autant que le choix du modèle.** Entre l'Oregon et la Tunisie, l'indicateur
   est multiplié par 3,4. Faire tourner DistilBERT dans une région peu carbonée réduit plus les
   émissions que la plupart des optimisations de code. → Argument pour la règle « choisir où calculer »
   de la charte.

2. **Le dénominateur est fragile.** Avec 2 000 exemples de test, l'accuracy est connue à ± 0,7 point
   près pour chaque modèle (± 1,4 point à 95 %). Si le gain réel est de 2 à 3 points, cette incertitude
   change l'indicateur de près de 60 %. Si le gain est inférieur à ≈ 1 point, **l'indicateur n'a plus de
   sens** (division par un nombre proche de zéro, ou même négatif). → Toujours donner Δacc **avec son
   intervalle de confiance**, et un test plus grand (7 600 exemples, le test complet d'AG News) quand
   l'écart est faible.

3. **La fabrication du matériel n'est pas un détail.** Même avec des hypothèses prudentes, l'amortir
   ajoute entre 33 % et 180 % au coût par point (détails dans `fabrication_materiel.md`). Elle est
   exclue du périmètre officiel, mais il faut le dire.

4. **Les forfaits et biais de CodeCarbon (RAM, GPU au repos) jouent moins** (≈ 10–25 %). Ils
   **surestiment** les deux modèles : sans eux le coût par point baisse. Ils ne changent pas la conclusion,
   mais doivent être signalés.

5. **Dans tous les cas, la conclusion qualitative tient** : le modèle lourd consomme de l'ordre de
   75 fois plus d'énergie que le léger (scénario provisoire, ≈ 95 fois sans les forfaits RAM et GPU), pour quelques points d'accuracy. Ce
   qui change, c'est le **chiffre** du coût par point. Il faut donc le publier **avec ses hypothèses**
   (I, PUE, n_test) et, idéalement, avec une fourchette.

## Recommandations pour le tableau comparatif et la charte (Boutheina, Ali)

- Afficher le coût par point **à intensité commune** (288 g/kWh), et indiquer à côté la fourchette
  166–560 g/kWh.
- Écrire Δacc avec son intervalle de confiance à 95 % : ± 1,96 × √(p₁(1−p₁)/n + p₂(1−p₂)/n).
- Proposition de règle pour la charte : *« Publier chaque mesure avec ses hypothèses (lieu, intensité,
  PUE, matériel, n_test) et une fourchette, jamais un chiffre seul. »* (vérifiable : la ligne
  d'hypothèses est présente sous le tableau).

## Limites de cette analyse

- Variation **une à une** : les hypothèses ne sont pas indépendantes (ex. le PUE et l'intensité
  dépendent tous deux du datacenter). Le « tout défavorable » est un cas extrême, pas un cas probable.
- Les bornes de chaque hypothèse sont des choix (sources dans `hypotheses.md` et `fabrication_materiel.md`).
- Valeurs du modèle lourd provisoires (voir encadré).
