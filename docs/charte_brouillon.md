# Charte Green AI : brouillon (responsable : Boutheina)

*Objectif : 5 règles simples et vérifiables pour une équipe de data scientists. Voici 8 propositions. L’équipe choisira les 5 finales en séance 3, en s’appuyant sur nos résultats.*

1.  **Commencer simple.** Entraîner d’abord un modèle léger comme référence. On ne passe à un modèle lourd que si le gain de précision dépasse un seuil fixé à l’avance.  
    → *Vérifiable : le rapport contient toujours un modèle de référence.*

2.  **Toujours mesurer.** Chaque entraînement est suivi avec CodeCarbon (ou un outil équivalent). L’énergie (kWh) et les émissions (g CO₂) sont écrites dans le rapport, à côté de l’accuracy.  
    → *Vérifiable : présence du fichier emissions.csv.*

3.  **Justifier le coût carbone.** Calculer le coût carbone par point de précision gagné avant de choisir un modèle plus lourd.  
    → *Vérifiable : l’indicateur figure dans le rapport.*

4.  **Tester petit avant de lancer grand.** Déboguer et régler le code sur un petit échantillon de données avant de lancer l’entraînement complet.  
    → *Vérifiable : un test court précède chaque entraînement long.*

5.  **Réutiliser plutôt que tout réentraîner.** Partir de modèles pré-entraînés et faire un fine-tuning léger, au lieu d’entraîner depuis zéro.

6.  **Choisir où et quand calculer.** Quand c’est possible, utiliser une région de cloud dont l’électricité est peu carbonée. *(Notre test : Iowa ≈ 295 g CO₂/kWh contre ≈ 483 g CO₂/kWh en Tunisie.)*

7.  **Limiter les essais inutiles.** Fixer un budget maximal d’entraînements pour la recherche d’hyperparamètres et utiliser l’arrêt anticipé (early stopping).

8.  **Éteindre ce qui ne sert pas.** Fermer les sessions GPU inactives (Colab, machines virtuelles) et supprimer les fichiers de sauvegarde inutiles.
