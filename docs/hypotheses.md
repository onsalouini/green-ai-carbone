# Hypothèses et protocole de mesure (responsable : Boutheina)

Équipe : Ali Ben Jannet, Ons, Boutheina Rjab · 5DS1 · ESPRIM

Séance 2 · 19/11/2026

## 1. Test de l'outil de mesure

Nous avons validé CodeCarbon (v3.3.2) sur Google Colab avec un test de 20 s sans calcul. Machine : CPU Intel Xeon 2,20 GHz (2 threads), 12,7 Go de RAM, sans GPU.

Résultat : 0,000061 kWh consommés, soit 0,018 g CO₂eq.

CodeCarbon détecte automatiquement la localisation du serveur : **Iowa (États-Unis)**. L’intensité carbone utilisée est donc d’environ **295 g CO₂/kWh** (calculée : émissions ÷ énergie = 0,000018 kg ÷ 0,000061 kWh).**

Hypothèse :** les mesures faites sur Colab utilisent le réseau électrique de l’Iowa, et celles faites sur un PC en Tunisie utilisent le réseau tunisien (environ 483 g CO₂/kWh, source LowCarbonPower 2025). Pour comparer les deux modèles de façon équitable, nous comparerons d’abord l’**énergie (kWh)**, puis nous recalculerons les émissions avec **la même intensité carbone** pour les deux.**

Limite observée :** la puissance de la RAM est estimée de façon forfaitaire (10 W), il ne s’agit pas d’une mesure réelle.

![Test CodeCarbon sur Colab](img/test_codecarbon.png)

## 2. Hypothèses de mesure

**Formule utilisée par CodeCarbon**

Émissions (g CO₂eq) = Énergie consommée (kWh) × Intensité carbone du réseau électrique (g CO₂eq/kWh).  
L’énergie est estimée à partir de la consommation du CPU, du GPU et de la RAM pendant l’entraînement.

**Intensité carbone retenue**

- Colab (serveur dans l’Iowa, États-Unis) : ≈ 295 g CO₂/kWh (valeur utilisée par CodeCarbon, voir section 1).

- PC local en Tunisie : ≈ 483 g CO₂/kWh (LowCarbonPower, 2025 : électricité produite à près de 99 % à partir de gaz). Une autre source (Ember / Our World in Data) donne ≈ 560 g CO₂/kWh. Nous gardons 483 comme valeur de référence, et cet écart entre sources fait partie de l’incertitude.

**PUE (énergie supplémentaire du datacenter : refroidissement, etc.)**

- Colab : PUE moyen des datacenters Google = 1,09 en 2024 (moyenne de l’industrie : 1,56).

- PC local : PUE = 1 (pas de datacenter).

**Remarque :** CodeCarbon utilise par défaut un PUE de 1 (paramètre « pue » modifiable). Les mesures faites sur Colab sous-estiment donc légèrement la consommation réelle (d’environ 9 % avec un PUE de 1,09).**

Périmètre de la mesure**

- Inclus : l’électricité consommée pendant l’entraînement et l’évaluation des modèles.

- Exclus : la fabrication du matériel (discutée en section 4), le téléchargement du jeu de données, le pré-entraînement de DistilBERT (réalisé par Hugging Face) et l’utilisation des modèles en production.

**Reproductibilité**

- Graine aléatoire fixe : seed = 42 pour les deux modèles.

- Mêmes données pour les deux modèles : AG News, 10 000 exemples d’entraînement et 2 000 de test.

- Chaque modèle est entraîné 3 fois, et nous donnons la moyenne ± l’écart-type.

**Matériel utilisé**

|                                                           | Ali (modèle léger) | Ons (modèle lourd) |
|-----------------------------------------------------------|--------------------|--------------------|
| Machine                                                   |                    |                    |
| CPU / GPU                                                 |                    |                    |
| RAM                                                       |                    |                    |
| Versions (Python, codecarbon, scikit-learn, transformers) |                    |                    |

## 3. Choix du jeu de données

**Jeu de données choisi : AG News**

AG News est un jeu de données public très utilisé pour tester les modèles de classification de textes. Il a été construit par Xiang Zhang, Junbo Zhao et Yann LeCun (2015) à partir d’un grand corpus d’articles de presse.

**Caractéristiques**

- Tâche : classer un article de presse dans l’une de 4 catégories : World, Sports, Business, Sci/Tech.

- Taille complète : 120 000 exemples d’entraînement et 7 600 de test (30 000 et 1 900 par classe, donc des classes équilibrées).

- Accessible directement depuis Hugging Face (load_dataset("ag_news")).

**Pourquoi ce choix**

- **Tâche simple et classique :** c’est ce que demande le cahier des charges.

- **Public :** tout le monde peut refaire nos expériences, ce qui sert la reproductibilité.

- **Classes équilibrées :** l’accuracy est une mesure fiable ici.

- **Adapté aux deux modèles :** le modèle léger (TF-IDF + LogReg) et le modèle lourd (DistilBERT) peuvent tous les deux le traiter, donc la comparaison est juste.**

**Sous-ensemble utilisé**

Nous utilisons 10 000 exemples d’entraînement et 2 000 de test, tirés au hasard avec seed = 42, pour respecter la contrainte de moins de 20 minutes par entraînement. Utiliser moins de données est aussi un choix de sobriété, dans l’esprit du projet.**

**Licence**

La fiche Hugging Face indique une licence « unknown ». Le corpus est mis à disposition par la communauté académique pour la recherche. Notre usage est pédagogique et non commercial.

## 4. Fabrication du matériel

**Une empreinte que nous ne mesurons pas, mais qui existe**

Notre mesure ne couvre que l’**électricité consommée pendant l’entraînement**, c’est-à-dire la phase d’**usage**. Mais avant d’être utilisé, le matériel informatique (GPU, processeurs, serveurs, ordinateurs) a dû être **fabriqué**. Cette fabrication émet aussi des gaz à effet de serre :

- extraction des métaux et des terres rares ;

- fabrication des puces électroniques, très gourmande en énergie et en eau ;

- assemblage et transport ;

- fin de vie (recyclage ou déchets).

C’est ce qu’on appelle l’**empreinte « grise »** (ou intrinsèque) du matériel.**

Pourquoi elle est exclue de notre mesure**

- Le cahier des charges limite le périmètre à l’usage.

- Elle est difficile à mesurer : les fabricants publient peu de données précises.

- Pour l’attribuer à notre entraînement, il faudrait la **répartir sur toute la durée de vie** du matériel : chaque heure de calcul porte une petite part de l’empreinte de fabrication. Cette répartition dépend de nombreuses hypothèses (durée de vie, taux d’utilisation, partage du serveur entre utilisateurs).**

Conséquences pour nos résultats**

- Nos chiffres **sous-estiment l’empreinte réelle** des deux modèles.

- Le modèle lourd est probablement encore plus pénalisé : il utilise un GPU, un matériel dont la fabrication est coûteuse, et l’occupe plus longtemps.

**Ce qu’on peut en retenir**

- Réutiliser le matériel existant et le garder plus longtemps réduit l’empreinte totale.

- Utiliser un serveur partagé (cloud) répartit l’empreinte de fabrication entre beaucoup d’utilisateurs.

- Ne pas mobiliser un GPU quand un CPU suffit.

## 5. Sources

- Intensité carbone Tunisie : LowCarbonPower, 2025 (≈ 483 g CO₂/kWh) ; Ember / Our World in Data (≈ 560 g CO₂/kWh)

- PUE Google : datacenters.google/efficiency (1,09 en 2024 ; moyenne de l’industrie 1,56)

- AG News : Zhang, Zhao & LeCun (2015), *Character-level Convolutional Networks for Text Classification* ; fiche Hugging Face « ag_news »

- Outil : CodeCarbon v3.3.2
