"""Modèle léger : TF-IDF + régression logistique (responsable : Ali).

Chaîne complète : données (code commun) -> TF-IDF + LogReg (scikit-learn) -> accuracy
-> emissions_leger.csv (CodeCarbon, via mesurer()).

À lancer sur Google Colab, runtime CPU :

    python -m src.modele_leger             # échauffement + 3 runs mesurés leger_run1..3
    python -m src.modele_leger --runs 5    # autre nombre de runs

Sorties dans resultats/ (format lu par src/tableau.py, src/reproductibilite.py, src/sensibilite.py) :
- emissions_leger.csv : une ligne CodeCarbon par run (project_name = leger_run1, leger_run2…) ;
- leger_runN.json : accuracy, durée, mesures CodeCarbon, hyperparamètres, matériel.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

from src.commun import SEED, load_data, mesurer

# Hyperparamètres du modèle léger (à reporter dans le rapport).
LIGHT_PARAMS: dict[str, Any] = {
    "max_features": 50_000,
    "ngram_range": [1, 2],
    "sublinear_tf": True,
    "max_iter": 1000,
    "random_state": SEED,
}

LIMITE_MINUTES = 20
DOSSIER_SORTIE = "resultats"
FICHIER_EMISSIONS = "emissions_leger.csv"


def train_light(train: Any, test: Any, params: dict[str, Any] | None = None) -> float:
    """Entraîne TF-IDF + régression logistique sur `train`, renvoie l'accuracy sur `test`.

    `train` et `test` sont les datasets renvoyés par load_data() (colonnes text, label).
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score

    p = {**LIGHT_PARAMS, **(params or {})}
    vectorizer = TfidfVectorizer(
        max_features=p["max_features"],
        ngram_range=tuple(p["ngram_range"]),
        sublinear_tf=p["sublinear_tf"],
    )
    X_train = vectorizer.fit_transform(train["text"])
    X_test = vectorizer.transform(test["text"])
    clf = LogisticRegression(max_iter=p["max_iter"], random_state=p["random_state"])
    clf.fit(X_train, train["label"])
    return float(accuracy_score(test["label"], clf.predict(X_test)))


def ligne_codecarbon(chemin_csv: Path, nom: str) -> dict[str, str]:
    """Dernière ligne du CSV CodeCarbon dont project_name == nom."""
    with chemin_csv.open(encoding="utf-8", newline="") as f:
        lignes = [l for l in csv.DictReader(f) if l["project_name"] == nom]
    return lignes[-1] if lignes else {}


def ecrire_json(nom: str, accuracy: float, duree_train: float, n_train: int, n_test: int,
                chemin_csv: Path) -> None:
    import codecarbon
    import sklearn

    cc = ligne_codecarbon(chemin_csv, nom)
    infos = {
        "nom": nom,
        "accuracy": accuracy,
        "n_train": n_train,
        "n_test": n_test,
        "duree_entrainement_s": round(duree_train, 1),
        "respecte_limite_20_min": duree_train / 60 < LIMITE_MINUTES,
        "mesures_codecarbon": {
            "duree_s": float(cc["duration"]),
            "energie_kwh": float(cc["energy_consumed"]),
            "emissions_g": float(cc["emissions"]) * 1000,
            "pays": cc["country_name"],
            "region": cc["region"],
        } if cc else None,
        "hyperparametres": LIGHT_PARAMS,
        "materiel": {
            "device": "cpu",
            "cpu": cc.get("cpu_model") or platform.processor() or platform.machine(),
            "ram_go": round(float(cc["ram_total_size"]), 1) if cc else None,
            "python": platform.python_version(),
        },
        "scikit-learn": sklearn.__version__,
        "codecarbon": codecarbon.__version__,
    }
    chemin = Path(DOSSIER_SORTIE) / f"{nom}.json"
    chemin.write_text(json.dumps(infos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(infos, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Modèle léger mesuré par CodeCarbon")
    parser.add_argument("--runs", type=int, default=3, help="nombre de runs mesurés (leger_run1…)")
    args = parser.parse_args()
    # La console Windows (cp1252) affiche mal les accents : on force l'UTF-8.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    dossier = Path(DOSSIER_SORTIE)
    dossier.mkdir(parents=True, exist_ok=True)
    chemin_csv = dossier / FICHIER_EMISSIONS

    # On repart de fichiers vides : sinon les nouvelles lignes s'ajoutent aux anciennes
    # et deux séries différentes porteraient les mêmes noms leger_run1, leger_run2…
    # (les anciennes mesures restent dans l'historique git).
    anciens = ([chemin_csv] if chemin_csv.exists() else []) + sorted(dossier.glob("leger_run*.json"))
    for f in anciens:
        print(f"Ancien résultat supprimé : {f}")
        f.unlink()

    # 1. Données chargées AVANT toute mesure : on ne mesure pas le téléchargement.
    train, test = load_data()

    # 2. Échauffement NON mesuré : le 1er entraînement est plus lent (caches, chargement
    #    des bibliothèques en mémoire), il fausserait la série.
    print("Échauffement (non mesuré)…")
    train_light(train, test)

    # 3. Runs mesurés.
    # Fréquence de mesure : mon entraînement dure ≈ 10 s. Par défaut CodeCarbon relève la
    # puissance toutes les 15 s, soit moins d'une mesure par run : c'est trop lent.
    # Il faut measure_power_secs=1. On ne recrée PAS de tracker ici : mesurer() de
    # src/commun.py utilise déjà measure_power_secs=1 depuis la séance 3, et accepte des
    # options supplémentaires. On lui passe seulement le dossier et le fichier de sortie,
    # donc la mesure est exactement la même que celle du modèle lourd.
    for i in range(1, args.runs + 1):
        nom = f"leger_run{i}"
        duree: dict[str, float] = {}

        def entrainement_chronometre() -> float:
            debut = time.perf_counter()
            acc = train_light(train, test)
            duree["s"] = time.perf_counter() - debut
            return acc

        accuracy, _ = mesurer(
            nom,
            entrainement_chronometre,
            output_dir=str(dossier),
            output_file=FICHIER_EMISSIONS,
        )
        # Le JSON est écrit APRÈS la mesure (il ne fait pas partie de l'entraînement).
        ecrire_json(nom, accuracy, duree["s"], len(train), len(test), chemin_csv)


if __name__ == "__main__":
    main()
