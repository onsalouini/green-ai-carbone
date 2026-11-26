# Charte Green AI : version 1 (responsable : Boutheina)

Équipe : Ali Ben Jannet, Ons, Boutheina Rjab, Ghayth · 5DS1 · ESPRIM
Séance 3 · 26/11/2026 · relecture : Ghayth

*Objectif : 5 règles simples, applicables et vérifiables pour une équipe de data scientists.
Elles s'appuient sur nos mesures (AG News, TF-IDF + régression logistique contre DistilBERT, CodeCarbon).*

> Chiffres tirés du tableau comparatif (`docs/tableau_comparatif.md`) : TF-IDF + LogReg 88,40 %,
> 0,054 Wh ; DistilBERT 90,45 %, 0,791 Wh (3 runs, Kaggle T4). Intensité de référence : 288 g CO₂/kWh (Iowa).

---

## Règle 1 : Toujours mesurer

Chaque entraînement est suivi avec CodeCarbon (ou un outil équivalent). L'énergie (kWh) et les
émissions (g CO₂eq) sont écrites dans le rapport, à côté de la performance (accuracy).

- **Pourquoi (nos résultats) :** sans mesure, on ne voit pas l'écart réel entre les modèles.
  Dans notre cas, DistilBERT consomme **14,6 fois plus d'énergie** que la régression logistique
  (0,791 Wh contre 0,054 Wh) pour la même tâche.
- **Vérifiable :** un fichier `emissions.csv` existe pour chaque expérience et ses valeurs
  figurent dans le rapport.

## Règle 2 : Commencer simple, justifier chaque montée en puissance

On entraîne toujours d'abord un modèle léger comme référence. On ne passe à un modèle plus
lourd que si le **coût carbone par point de précision gagné** reste sous un seuil fixé à l'avance.

Coût carbone par point = (Émissions lourd − Émissions léger) ÷ (Accuracy lourd − Accuracy léger)

- **Pourquoi (nos résultats) :** DistilBERT gagne seulement **2,05 points** d'accuracy (90,45 % contre
  88,40 %) pour **14,6 fois plus d'énergie**. Chaque point gagné coûte **≈ 0,10 g CO₂eq** à 288 g/kWh
  (0,17 g à 483 g/kWh, 0,20 g à 560 g/kWh), soit environ 7 fois l'entraînement complet du modèle léger.
  Et avec 2 000 exemples de test, ce gain est incertain : 2,05 ± 1,9 points (IC 95 %).
- **Critère proposé par l'équipe (à valider) :** on garde le modèle lourd seulement si (1) le gain
  d'accuracy dépasse la marge d'erreur du test (borne basse de l'IC 95 % > 0) et (2) ce gain est utile
  pour le besoin métier. Sinon, on garde le modèle léger. *Dans notre cas, le gain est à peine significatif :
  pour classer des actualités, le modèle léger suffit.*
- **Vérifiable :** le rapport contient toujours un modèle de référence et la valeur de l'indicateur.

## Règle 3 : Tester petit avant de lancer grand

On débogue et on règle le code sur un petit échantillon de données avant de lancer
l'entraînement complet.

- **Pourquoi (nos résultats) :** le test court de DistilBERT (500 exemples d'entraînement,
  200 de test) a validé le code et la mesure, et a estimé la durée du vrai run à environ
  2 minutes. Le respect de la limite de 20 minutes a donc été vérifié avant de lancer le calcul.
- **Vérifiable :** un run « test court » apparaît avant chaque entraînement long dans `emissions.csv`.

## Règle 4 : Fixer un budget d'expérimentation

Avant de commencer, on fixe un nombre maximal d'entraînements (recherche d'hyperparamètres
comprise). On utilise l'arrêt anticipé (early stopping) et on ferme les sessions GPU
(Colab, Kaggle, machines virtuelles) dès que le calcul est terminé. On ne réserve pas de GPU
quand un CPU suffit.

- **Pourquoi :** chaque run supplémentaire ajoute des émissions, et un GPU coûte aussi cher en
  carbone à fabriquer (voir le périmètre). Une session GPU ouverte sans
  calcul consomme aussi de l'énergie (notre test à vide de 20 s : 0,000061 kWh).
- **Vérifiable :** le budget est écrit dans le protocole, et le nombre de runs dans
  `emissions.csv` ne le dépasse pas.

## Règle 5 : Publier chaque mesure avec ses hypothèses, jamais un chiffre seul

Chaque résultat est publié avec ses hypothèses (lieu du serveur, intensité carbone, PUE, matériel,
taille du jeu de test) et une fourchette (minimum, maximum). Quand c'est possible, on choisit une
région dont l'électricité est peu carbonée et on réutilise des modèles pré-entraînés.

- **Pourquoi (nos résultats) :** pour la même énergie, l'intensité carbone varie de 166 g CO₂/kWh
  (Oregon) à 560 g CO₂/kWh (Tunisie, valeur utilisée par CodeCarbon) : le modèle léger émet
  3,4 fois plus en Tunisie qu'en Oregon (test de reproductibilité de Ghayth). Entre le meilleur et
  le pire cas, le coût carbone par point varie d'un facteur 59 (`docs/sensibilite.md`).
- **Vérifiable :** chaque résultat indique la région, l'intensité carbone, le PUE, le matériel,
  la taille du test et une fourchette.

---

## Périmètre et limites

- Cette charte porte sur l'**usage** : l'électricité consommée pendant l'entraînement et l'évaluation.
- La **fabrication du matériel** (GPU, serveurs, ordinateurs) est exclue des mesures, mais elle
  est discutée dans `docs/fabrication_materiel.md` : une fois amortie sur la durée de vie du
  matériel, elle représenterait **25 à 64 %** de l'empreinte d'un run DistilBERT. On ne peut donc
  pas la négliger : préférer du matériel partagé et bien utilisé, et prolonger sa durée de vie.
- Les mesures de CodeCarbon sont des estimations (par exemple, la puissance de la RAM est estimée
  de façon forfaitaire), d'où l'importance de déclarer les hypothèses.
