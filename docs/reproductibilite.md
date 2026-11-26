# Test de reproductibilité (responsable : Ghayth)

Séance 3 · 26/11/2026 · script : `src/reproductibilite.py`

## Question

Si une autre personne relance notre code sur une autre machine, obtient-elle les mêmes résultats ?
On sépare deux choses :

- le **résultat** du modèle (accuracy) : il doit être identique (graine fixe, mêmes données) ;
- la **mesure** de l'énergie : elle varie forcément un peu. On veut savoir de combien.

## Protocole

Le modèle léger d'Ali (TF-IDF + régression logistique) est relancé **à l'identique** sur une autre
machine : même code (recopié du notebook `leger_tfidf_colab.ipynb`), mêmes données (`load_data()`, seed 42),
même mesure (CodeCarbon, `measure_power_secs=1`), un échauffement non mesuré puis 5 runs mesurés.

```bash
python -m src.reproductibilite --relancer-leger 5 --machine pc_ghayth   # relance + analyse
python -m src.reproductibilite                                         # analyse seule
```

|                       | Ali (référence)                       | Ghayth (reproduction)                      |
|-----------------------|---------------------------------------|--------------------------------------------|
| Machine               | Google Colab, CPU (Oregon, États-Unis) | PC portable, Windows 11 (Tunisie)          |
| CPU                   | Intel Xeon 2,20 GHz, 2 threads        | AMD Ryzen 7 7435HS, 8 cœurs / 16 threads  |
| GPU                   | aucun                                 | NVIDIA RTX 2050 (présent, **non utilisé**)  |
| RAM                   | 12,7 Go                               | 31,8 Go                                    |
| Python / scikit-learn | 3.13.18 / 1.6.1                       | 3.11.9 / 1.9.1                             |
| CodeCarbon            | 3.3.2                                 | 3.3.3                                      |

Résultats bruts : `resultats/emissions_leger.csv` (Ali) et `resultats/repro/emissions_leger_pc_ghayth.csv`
(région et coordonnées GPS effacées : un PC personnel n'a pas à être localisé, seul le pays compte).

## Résultats

### 1. Le résultat du modèle est parfaitement reproductible

| Run | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Accuracy Ali (Colab) | 0,8840 | 0,8840 | 0,8840 | 0,8840 | 0,8840 |
| Accuracy Ghayth (PC) | 0,8840 | 0,8840 | 0,8840 | 0,8840 | 0,8840 |

Accuracy **identique à 4 décimales** sur 10 runs, 2 machines, 2 OS, 2 versions de Python et de scikit-learn.

### 2. La mesure d'énergie varie, mais reste du même ordre

| Série | n | Durée (s) | CV | Énergie (Wh) | CV | Puissance moy. (W) | Intensité (g CO₂/kWh) | Émissions (g CO₂eq) |
|---|---|---|---|---|---|---|---|---|
| Colab CPU (Ali) | 5 | 12,0 ± 3,0 | 25 % | 0,0541 ± 0,0149 | 28 % | 16,1 | 166 (Oregon) | 0,0090 ± 0,0025 |
| PC portable (Ghayth) | 5 | 7,1 ± 0,6 | 9 % | 0,0537 ± 0,0041 | 8 % | 27,4 | 560 (Tunisie) | 0,0301 ± 0,0023 |

CV = coefficient de variation = écart-type ÷ moyenne.

Répartition de l'énergie sur le PC (moyenne des 5 runs) : CPU ≈ 54 %, RAM ≈ 31 % (forfait 20 W),
GPU ≈ 15 %, **alors que le GPU ne sert pas**.

## Analyse

1. **Sur une même machine, l'énergie varie de 8 à 28 %.** Chez Ali, la variation vient de la **durée**
   (le run 5 dure 17 s contre ≈ 10 s pour les autres) et pas de la puissance (CV 3 %). Sur un serveur
   partagé comme Colab, d'autres utilisateurs ralentissent parfois la machine. Un seul run ne suffit
   donc pas : il faut **au moins 3 runs et donner moyenne ± écart-type**, comme prévu dans nos hypothèses.

2. **D'une machine à l'autre, l'énergie est presque la même (0,054 Wh), mais par hasard.** Le PC
   va 1,7 fois plus vite mais consomme 1,7 fois plus de puissance. Sa répartition est aussi très
   différente (GPU inutile compté, RAM forfaitaire 2 fois plus élevée). Il ne faut pas en conclure
   que l'énergie ne dépend pas du matériel.

3. **Les émissions, elles, ne sont pas reproductibles d'une machine à l'autre : × 3,4.** Pour la
   même énergie, le PC en Tunisie émet 0,030 g contre 0,009 g sur Colab en Oregon. Seule
   l'intensité carbone du réseau change. Cela confirme le choix de nos hypothèses : **comparer
   d'abord l'énergie (kWh)**, puis recalculer les émissions avec une intensité commune.

4. **CodeCarbon compte les GPU présents, même inutilisés.** La RTX 2050 au repos (7 à 12 W) est
   ajoutée à la mesure d'un modèle qui tourne sur CPU. C'est le même biais que le 2ᵉ T4 de Kaggle
   relevé par Ons. Correction possible (décision d'équipe, `src/commun.py`) :
   `EmissionsTracker(..., gpu_ids=[])` pour le modèle léger et `gpu_ids=[0]` pour le lourd.

5. **CodeCarbon utilise 560 g CO₂/kWh pour la Tunisie, et non 483.** C'est la valeur Ember / Our World
   in Data, alors que `hypotheses.md` retient 483 (LowCarbonPower) comme référence. Il faut le signaler dans
   le tableau comparatif : si on recalcule à 483, les émissions mesurées en Tunisie baissent de 14 %.

## Conclusion

| Critère | Verdict |
|---|---|
| Accuracy reproductible | ✔ identique (0,8840) sur 2 machines |
| Énergie reproductible sur la même machine | ✔ à ± 8–28 % : publier moyenne ± écart-type sur ≥ 3 runs |
| Énergie reproductible entre machines | ~ même ordre de grandeur, mais pas la même composition |
| Émissions reproductibles entre machines | ✘ dépendent du lieu : comparer en kWh, intensité commune |

## À faire quand les runs DistilBERT d'Ons seront poussés

Ajouter la série dans l'analyse (déjà prévu dans le script : lignes `lourd_run*` de
`resultats/kaggle/emissions_lourd.csv`), puis relancer `python -m src.reproductibilite`. La
reproductibilité de l'accuracy est moins garantie sur GPU (opérations CUDA non déterministes en fp16) :
on s'attend à de petits écarts d'un run à l'autre, à vérifier.
