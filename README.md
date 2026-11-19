# Green AI : l'empreinte carbone d'un modèle

Projet 1 · Ali · Ons · Boutheina

On mesure et on compare l'empreinte carbone de l'entraînement de deux modèles sur une même
tâche (classification de textes AG News), puis on rédige une charte de sobriété en 5 règles.

- **Modèle léger** : TF-IDF + régression logistique (scikit-learn).
- **Modèle lourd** : fine-tuning de DistilBERT, 1 époque (Hugging Face `Trainer`), sur GPU Kaggle.
- **Mesure** : CodeCarbon (`emissions.csv`).
- **Indicateur clé** : coût carbone par point de précision gagné
  `(CO2 lourd − CO2 léger) / (accuracy lourd − accuracy léger)`.

## Répartition (travail 100 % en parallèle)

| Membre | Partie | Fichiers |
|---|---|---|
| Ali | Modèle léger de bout en bout | `src/modele_leger.py`, `notebooks/leger_*.ipynb` |
| Ons | Modèle lourd de bout en bout (Kaggle GPU) | `src/modele_lourd.py`, `notebooks/lourd_distilbert_kaggle.ipynb`, `docs/modele_lourd.md` |
| Boutheina | Protocole, hypothèses, charte | `docs/hypotheses.md`, `docs/tableau_comparatif.md`, `docs/charte_brouillon.md` |
| Tous | Code commun (données + mesure) | `src/commun.py` : ne pas modifier seul |

Règle : chacun ne modifie que ses fichiers. `git pull` avant de commencer et avant chaque `git push`.

## Installation locale

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancer

```bash
python -m src.modele_lourd --test-court   # 500 exemples : valide la mesure
python -m src.modele_lourd                # vrai run 10 000 / 2 000
```

Chaque run ajoute une ligne à `emissions.csv` et écrit `resultats/<nom>.json`.
Sur Kaggle : ouvrir `notebooks/lourd_distilbert_kaggle.ipynb` (réglages en tête du notebook).
