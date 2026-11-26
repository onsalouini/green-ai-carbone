"""Test de reproductibilité des mesures (responsable : Ghayth).

Deux usages :

    # 1. Relancer le modèle léger sur SA machine (même code, mêmes données, seed 42)
    python -m src.reproductibilite --relancer-leger 3 --machine pc_ghayth

    # 2. Analyser toutes les séries de mesures disponibles (CSV CodeCarbon)
    python -m src.reproductibilite

Questions posées :
  - Reproductibilité du RÉSULTAT : l'accuracy est-elle identique d'un run à l'autre,
    et d'une machine à l'autre ? (doit l'être : seed fixe, algorithme déterministe)
  - Reproductibilité de la MESURE : quelle dispersion (coefficient de variation) sur la
    durée, l'énergie et les émissions ? Sur la même machine, puis entre machines.

Le code d'entraînement du modèle léger est celui du notebook d'Ali
(notebooks/leger_tfidf_colab.ipynb), recopié à l'identique : src/modele_leger.py est vide.
"""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
DOSSIER_REPRO = RACINE / "resultats" / "repro"

# Séries à comparer : nom affiché -> (fichier CSV, filtre sur project_name)
SERIES = {
    "léger · Colab CPU (Ali)": ("resultats/emissions_leger.csv", "leger_run"),
    "lourd · Kaggle T4 (Ons)": ("resultats/kaggle/emissions_lourd.csv", "lourd_run"),
}


# --------------------------------------------------------------------------- relance
def relancer_leger(n_runs: int, machine: str) -> None:
    from codecarbon import EmissionsTracker
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score

    from src.commun import SEED, load_data

    train, test = load_data()  # téléchargement HORS mesure (comme Ali)

    def train_light() -> float:
        vectorizer = TfidfVectorizer(max_features=50_000, ngram_range=(1, 2), sublinear_tf=True)
        X_train = vectorizer.fit_transform(train["text"])
        X_test = vectorizer.transform(test["text"])
        clf = LogisticRegression(max_iter=1000, random_state=SEED)
        clf.fit(X_train, train["label"])
        return float(accuracy_score(test["label"], clf.predict(X_test)))

    DOSSIER_REPRO.mkdir(parents=True, exist_ok=True)
    csv = DOSSIER_REPRO / f"emissions_leger_{machine}.csv"
    if csv.exists():
        csv.unlink()

    train_light()  # échauffement non mesuré (comme Ali)

    accuracies = []
    for i in range(1, n_runs + 1):
        tracker = EmissionsTracker(
            project_name=f"leger_run{i}",
            output_dir=str(DOSSIER_REPRO),
            output_file=csv.name,
            measure_power_secs=1,
            log_level="error",
        )
        tracker.start()
        acc = train_light()
        kg = tracker.stop()
        accuracies.append(acc)
        print(f"leger_run{i} | accuracy={acc:.4f} | {kg * 1000:.4f} g CO2eq")

    # Vie privée : un PC personnel n'est pas un datacenter, on ne publie pas sa position.
    # Seul le pays compte pour l'intensité carbone.
    df = pd.read_csv(csv)
    df[["region", "longitude", "latitude"]] = None
    df.to_csv(csv, index=False)

    import codecarbon
    import sklearn

    infos = {
        "machine": machine,
        "accuracies": accuracies,
        "os": platform.platform(),
        "cpu": platform.processor(),
        "python": platform.python_version(),
        "scikit-learn": sklearn.__version__,
        "codecarbon": codecarbon.__version__,
    }
    (DOSSIER_REPRO / f"leger_{machine}.json").write_text(
        json.dumps(infos, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# --------------------------------------------------------------------------- analyse
def stats_serie(df: pd.DataFrame) -> dict[str, float]:
    df = df.assign(
        emissions_g=df["emissions"] * 1000,
        puissance_w=df["energy_consumed"] * 3.6e6 / df["duration"],
        intensite=df["emissions"] * 1000 / df["energy_consumed"],
    )
    out: dict[str, float] = {"n": len(df)}
    for col in ["duration", "energy_consumed", "emissions_g", "puissance_w", "intensite"]:
        m, s = df[col].mean(), df[col].std(ddof=1) if len(df) > 1 else 0.0
        out[f"{col}_moy"], out[f"{col}_std"], out[f"{col}_cv"] = m, s, 100 * s / m
    out["region"] = df["region"].iloc[0]
    out["materiel"] = df["cpu_model"].iloc[0] + (
        f" + {df['gpu_model'].iloc[0]}" if isinstance(df["gpu_model"].iloc[0], str) else ""
    )
    return out


def analyser() -> None:
    series = dict(SERIES)
    for f in sorted(DOSSIER_REPRO.glob("emissions_leger_*.csv")):
        series[f"léger · {f.stem.removeprefix('emissions_leger_')} (Ghayth)"] = (
            str(f.relative_to(RACINE)),
            "leger_run",
        )

    lignes = []
    for nom, (fichier, prefixe) in series.items():
        chemin = RACINE / fichier
        if not chemin.exists():
            print(f"(absent) {nom} : {fichier}")
            continue
        df = pd.read_csv(chemin)
        df = df[df["project_name"].str.startswith(prefixe)]
        if df.empty:
            print(f"(aucun run '{prefixe}*') {nom} : {fichier}")
            continue
        lignes.append((nom, stats_serie(df)))

    print("\n| Série | n | Durée (s) | CV | Énergie (Wh) | CV | Puissance moy. (W) | CV | g CO2/kWh |")
    print("|---|---|---|---|---|---|---|---|---|")
    for nom, s in lignes:
        print(
            f"| {nom} | {s['n']} "
            f"| {s['duration_moy']:.1f} ± {s['duration_std']:.1f} | {s['duration_cv']:.0f} % "
            f"| {s['energy_consumed_moy'] * 1000:.4f} ± {s['energy_consumed_std'] * 1000:.4f} "
            f"| {s['energy_consumed_cv']:.0f} % "
            f"| {s['puissance_w_moy']:.1f} | {s['puissance_w_cv']:.0f} % "
            f"| {s['intensite_moy']:.0f} |"
        )

    for f in sorted(DOSSIER_REPRO.glob("leger_*.json")):
        infos = json.loads(f.read_text(encoding="utf-8"))
        print(f"\nAccuracies {infos['machine']} : {infos['accuracies']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--relancer-leger", type=int, metavar="N", help="relancer N runs du modèle léger")
    parser.add_argument("--machine", default="pc_local", help="nom court de la machine")
    args = parser.parse_args()
    if args.relancer_leger:
        relancer_leger(args.relancer_leger, args.machine)
    analyser()


if __name__ == "__main__":
    main()
