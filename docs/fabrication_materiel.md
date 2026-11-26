# Fabrication du matériel : discussion chiffrée (responsable : Ghayth)

Séance 3 · 26/11/2026 · calcul : `src/sensibilite.py` (fonction `fabrication_g`)

Le cahier des charges exclut la fabrication du matériel **des mesures**, mais demande de la **discuter**.
La section 4 de `hypotheses.md` explique pourquoi cette empreinte existe et pourquoi on l'exclut.
Ici, on essaie d'en donner **un ordre de grandeur**, pour savoir si on peut la négliger.

## Méthode : amortir la fabrication sur la durée de vie

Une machine émet une quantité F de CO₂ à sa fabrication, puis sert pendant toute sa vie. On attribue
à chaque run une part de F proportionnelle à son temps d'utilisation :

> **Fabrication attribuée au run** = F ÷ (durée de vie × 8 760 h × taux d'utilisation) × durée du run

Le taux d'utilisation compte : une machine qui ne sert que la moitié du temps doit « rembourser » sa
fabrication sur deux fois moins d'heures.

## Hypothèses

| Matériel | F (kg CO₂eq) | Durée de vie | Utilisation | Source / justification |
|---|---|---|---|---|
| GPU de datacenter | 150 (haut) · 50 (bas) | 4–6 ans | 50–85 % | 150 kg par GPU A100 : Luccioni et al. (2023), empreinte de BLOOM. Le T4 est une carte plus petite (70 W), d'où la valeur basse. |
| Serveur (hors GPU) | 2 500 | 4–6 ans | 50–85 % | Luccioni et al. (2023), même étude |
| Part du serveur pour Kaggle | 1/4 à 1/8 | | | on suppose 4 à 8 GPU par serveur |
| Part du serveur pour Colab CPU | 2/96 | 4 ans | 50 % | 2 vCPU sur un serveur d'environ 96 vCPU (hypothèse) |
| PC portable | 250 | 4 ans | 20 % (≈ 5 h/jour) | ordre de grandeur des fiches carbone des fabricants (≈ 200 à 350 kg en cycle de vie, en grande majorité pour la fabrication) |

Toutes ces valeurs sont **incertaines à un facteur 2 ou 3** : les fabricants publient peu de données
détaillées (c'est justement une raison de l'exclusion).

## Résultats (par run, à 288 g CO₂/kWh pour l'usage)

| Cas | Fabrication attribuée (g) | Usage mesuré (g) | Part de la fabrication |
|---|---|---|---|
| **Lourd** · T4 + 1/4 serveur, 4 ans, 50 % (haut) | 2,09 | 1,15 *(provisoire)* | **64 %** |
| **Lourd** · T4 « petit » + 1/8 serveur, 6 ans, 85 % (bas) | 0,38 | 1,15 *(provisoire)* | 25 % |
| **Léger** · Colab, 2 vCPU d'un serveur | 0,010 | 0,016 | 39 % |
| **Léger** · PC portable de Ghayth | 0,070 | 0,016 | **82 %** |

(Usage du lourd provisoire : 4 Wh, voir `sensibilite.md`. Le calcul se met à jour avec
`python -m src.sensibilite` quand les vrais runs seront disponibles.)

## Analyse

1. **On ne peut pas négliger la fabrication.** Selon les hypothèses, elle représente **entre un quart et
   deux tiers** de l'empreinte totale d'un run DistilBERT. En l'excluant, nos chiffres **sous-estiment**
   l'empreinte réelle d'un facteur 1,3 à 3.

2. **Elle pénalise surtout le modèle lourd en valeur absolue.** Un GPU coûte cher à fabriquer, et le run
   lourd l'occupe ≈ 15 fois plus longtemps que le run léger n'occupe un CPU. Inclure la fabrication
   **augmente l'écart** entre les deux modèles, et donc le coût par point (+ 33 % à + 180 %,
   voir `sensibilite.md`). Notre conclusion « le léger est plus sobre » est donc **prudente** : la
   réalité est encore plus nette.

3. **Plus l'électricité est propre, plus la fabrication pèse en proportion.** À 166 g/kWh (Oregon),
   l'usage diminue mais la fabrication reste la même. Dans les régions décarbonées, la fabrication
   devient la principale source d'émissions. Changer de région ne règle pas tout.

4. **Le taux d'utilisation compte.** Sur un PC personnel peu utilisé (20 %), la fabrication représente
   82 % de l'empreinte d'un run léger. Sur un serveur partagé et très utilisé (cloud), elle est répartie
   entre beaucoup d'utilisateurs et pèse beaucoup moins par heure. **Mutualiser le matériel est un
   levier de sobriété**, au même titre que choisir un petit modèle.

5. **Ce que nous ne comptons pas non plus** : le pré-entraînement de DistilBERT par Hugging Face
   (fabrication et usage), le stockage et le transfert des données, le refroidissement par eau (CodeCarbon
   affiche `water_consumed = 0`), et la fin de vie du matériel.

## Conséquences pratiques (propositions pour la charte)

- **Ne pas réserver un GPU quand un CPU suffit** : on évite aussi d'immobiliser du matériel coûteux à fabriquer.
- **Préférer du matériel partagé et bien utilisé** (cloud, serveur d'équipe) à l'achat de matériel
  dédié peu utilisé.
- **Prolonger la durée de vie du matériel** : passer de 4 à 6 ans réduit d'un tiers la fabrication
  attribuée à chaque heure de calcul.
- **Dans le rapport, toujours écrire que la fabrication est exclue**, et donner un ordre de grandeur
  (ex. « + 33 à 180 % »), pour que le lecteur ne prenne pas nos chiffres pour l'empreinte totale.

## Sources

- A. S. Luccioni, S. Viguier, A.-L. Ligozat (2023), *Estimating the Carbon Footprint of BLOOM, a 176B
  Parameter Language Model*, JMLR 24(253) : hypothèses de fabrication GPU (≈ 150 kg CO₂eq) et serveur
  (≈ 2 500 kg CO₂eq), durée de vie et taux d'utilisation.
- Fiches « Product Carbon Footprint » des fabricants d'ordinateurs portables (Dell, HP, Lenovo) : ordre de grandeur 200–350 kg CO₂eq.
- Voir aussi `hypotheses.md`, section 4 (discussion qualitative).
