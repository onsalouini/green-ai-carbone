# Test de reproductibilité (responsable : Ghayth)

Séance 3 · 27/11/2026 · script : `src/reproductibilite.py`

## Question

Si une autre personne relance notre code sur une autre machine, obtient-elle les mêmes résultats ?
On sépare deux choses :

- le **résultat** du modèle (accuracy) : il doit être identique (graine fixe, mêmes données) ;
- la **mesure** de l'énergie : elle varie forcément un peu. On veut savoir de combien.

## Protocole

Le modèle léger d'Ali (TF-IDF + régression logistique) est relancé **à l'identique** sur une autre
machine : même code, mêmes données (`load_data()`, seed 42), même mesure (CodeCarbon,
`measure_power_secs=1`), un échauffement non mesuré puis 5 runs mesurés. Le code commun `mesurer()`
mesure désormais lui aussi toutes les secondes : toutes les séries ci-dessous sont comparables.

```bash
python -m src.reproductibilite --relancer-leger 5 --machine pc_ghayth   # relance + analyse
python -m src.reproductibilite                                         # analyse seule
```

|                       | Ali (référence)                        | Ghayth (reproduction)                      |
|-----------------------|----------------------------------------|--------------------------------------------|
| Machine               | Google Colab, CPU (Oregon en S2, Nevada en S3) | PC portable, Windows 11 (Tunisie)  |
| CPU                   | Intel Xeon 2,20 GHz, 2 threads         | AMD Ryzen 7 7435HS, 8 cœurs / 16 threads  |
| GPU                   | aucun                                  | NVIDIA RTX 2050 (présent, **non utilisé**)  |
| RAM                   | 12,7 Go                                | 31,8 Go                                    |
| Python / scikit-learn | 3.13.18 / 1.6.1                        | 3.11.9 / 1.9.1                             |
| CodeCarbon            | 3.3.2 (S2) · 3.3.3 (S3)                | 3.3.3                                      |

Les 3 runs DistilBERT d'Ons (Kaggle, Tesla T4) sont analysés de la même façon.

Résultats bruts : `resultats/emissions_leger.csv` (Ali, S3), `resultats/kaggle/emissions_lourd.csv` (Ons),
`resultats/repro/emissions_leger_pc_ghayth.csv` (région et coordonnées GPS effacées : un PC
personnel n'a pas à être localisé, seul le pays compte). Les 5 runs d'Ali de la séance 2 sont dans
l'historique Git (commit `942d6d4`).

## Résultats

### 1. Le résultat des modèles est parfaitement reproductible

| Série | Runs | Accuracy |
|---|---|---|
| Léger · Colab, Oregon (Ali, S2) | 5 | 0,8840 à chaque run |
| Léger · Colab, Nevada (Ali, S3) | 3 | 0,8840 à chaque run |
| Léger · PC portable (Ghayth) | 5 | 0,8840 à chaque run |
| Lourd · Kaggle T4 (Ons) | 3 | 0,9045 à chaque run |

Accuracy **identique à 4 décimales** pour les deux modèles : 13 runs du modèle léger sur 3 machines,
2 OS et 2 versions de scikit-learn. Les 3 runs de DistilBERT sur GPU sont eux aussi identiques,
malgré le calcul en fp16 sur CUDA (qui n'est pas garanti déterministe).

### 2. La mesure d'énergie varie, mais reste du même ordre

| Série | n | Durée (s) | CV | Énergie (Wh) | CV | Puissance moy. (W) | Intensité (g CO₂/kWh) | Émissions (g CO₂eq) |
|---|---|---|---|---|---|---|---|---|
| Léger · Colab, Oregon (Ali, S2) | 5 | 12,0 ± 3,0 | 25 % | 0,0541 ± 0,0149 | 28 % | 16,1 | 166 | 0,0090 ± 0,0025 |
| Léger · Colab, Nevada (Ali, S3) | 3 | 9,0 ± 0,4 | 4 % | 0,0397 ± 0,0030 | 7 % | 15,9 | 292 | 0,0116 ± 0,0009 |
| Léger · PC portable (Ghayth) | 5 | 7,1 ± 0,6 | 9 % | 0,0537 ± 0,0041 | 8 % | 27,4 | 560 | 0,0301 ± 0,0023 |
| Lourd · Kaggle T4 (Ons) | 3 | 34,2 ± 4,1 | 12 % | 0,791 ± 0,037 | 5 % | 83,6 | 288 | 0,228 ± 0,011 |

CV = coefficient de variation = écart-type ÷ moyenne.

Répartition de l'énergie sur le PC (moyenne des 5 runs) : CPU ≈ 54 %, RAM ≈ 31 % (forfait 20 W),
GPU ≈ 15 %, **alors que le GPU ne sert pas**.

## Analyse

1. **Sur une même machine, l'énergie varie de 5 à 28 %.** Le pire cas est la série S2 d'Ali : la
   variation venait de la **durée** (un run de 17 s contre ≈ 10 s pour les autres) et non de la
   puissance (CV 3 %). Sur un serveur partagé comme Colab, d'autres utilisateurs ralentissent parfois
   la machine. Les séries S3 sont plus stables (5 à 8 %). Un seul run ne suffit donc pas : il faut
   **au moins 3 runs et donner moyenne ± écart-type**.

2. **Entre deux sessions Colab, l'énergie du modèle léger change de 27 %** (0,054 → 0,040 Wh) pour le
   même code sur le « même » matériel annoncé. La machine physique et sa charge changent d'une
   session à l'autre. Un écart inférieur à ≈ 30 % entre deux modèles légers n'est donc pas significatif.

3. **D'une machine à l'autre, l'énergie reste du même ordre**, mais pas pour les mêmes raisons. Le PC
   est plus rapide, mais consomme plus de puissance, et sa mesure compte un GPU inutilisé. L'écart
   entre modèles (× 20 entre DistilBERT et le léger) est bien plus grand que l'écart entre machines
   (≈ 30 %) : **la comparaison des deux modèles est robuste**.

4. **Les émissions, elles, ne sont pas reproductibles d'une machine à l'autre : jusqu'à × 3,4.** Pour
   une énergie voisine, le PC en Tunisie émet 0,030 g contre 0,009 g sur Colab en Oregon. Seule
   l'intensité carbone du réseau change. Cela confirme le choix de l'équipe : **comparer d'abord
   l'énergie (kWh)**, puis recalculer les émissions avec une intensité commune (288 g/kWh).

5. **CodeCarbon compte les GPU présents, même inutilisés.** La RTX 2050 au repos (7 à 12 W) est
   ajoutée à la mesure d'un modèle qui tourne sur CPU. Ons a corrigé le code commun avec `gpu_ids=[0]`
   pour Kaggle. **À vérifier :** le CSV de ses runs indique encore `gpu_count = 2` (« 2 x Tesla T4 »).

6. **CodeCarbon utilise 560 g CO₂/kWh pour la Tunisie** (Ember / Our World in Data), alors que
   `hypotheses.md` retient 483 (LowCarbonPower) pour la Tunisie. Recalculées à 483, les émissions
   mesurées sur le PC baissent de 14 %.

## Conclusion

| Critère | Verdict |
|---|---|
| Accuracy reproductible | ✔ identique sur tous les runs : 0,8840 (léger, 3 machines) et 0,9045 (lourd, GPU) |
| Énergie reproductible sur la même machine | ✔ à ± 5–28 % : publier moyenne ± écart-type sur ≥ 3 runs |
| Énergie reproductible entre machines / sessions | ~ même ordre de grandeur (± 30 %), bien en dessous de l'écart entre modèles (× 20) |
| Émissions reproductibles entre machines | ✘ dépendent du lieu : comparer en kWh, à intensité commune |
