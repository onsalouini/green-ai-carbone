"""Modèle lourd : fine-tuning de DistilBERT, 1 époque (responsable : Ons).

Chaîne complète : données (code commun) -> DistilBERT (HF Trainer) -> accuracy
-> emissions.csv (CodeCarbon, via mesurer()).

À lancer sur Kaggle avec un GPU T4 (notebooks/lourd_distilbert_kaggle.ipynb) :

    python -m src.modele_lourd --test-court     # 500 exemples : valide la mesure
    python -m src.modele_lourd --runs 3         # vrais runs lourd_run1..3 : 10 000 / 2 000

Sorties dans resultats/kaggle/ (format lu par src/reproductibilite.py et src/sensibilite.py) :
- emissions_lourd.csv : une ligne CodeCarbon par run (project_name = lourd_test_court, lourd_run1…) ;
- <nom>.json : accuracy, durée, GPU, hyperparamètres, estimation de durée du vrai run.
"""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

from src.commun import SEED, load_data, mesurer

# Hyperparamètres du modèle lourd (à reporter dans docs/modele_lourd.md).
HEAVY_PARAMS: dict[str, Any] = {
    "model_name": "distilbert-base-uncased",
    "num_labels": 4,
    "epochs": 1,
    "batch_size": 16,
    "learning_rate": 5e-5,
    "weight_decay": 0.01,
    "max_length": 128,
}

N_TRAIN_VRAI_RUN = 10_000
LIMITE_MINUTES = 20
DOSSIER_SORTIE = "resultats/kaggle"
FICHIER_EMISSIONS = "emissions_lourd.csv"


def infos_materiel() -> dict[str, Any]:
    """Décrit le matériel utilisé (pour le document « Hypothèses »)."""
    import torch

    infos: dict[str, Any] = {
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "cpu": platform.processor() or platform.machine(),
        "torch": torch.__version__,
    }
    if torch.cuda.is_available():
        infos["gpu"] = torch.cuda.get_device_name(0)
    return infos


def train_heavy(
    train: Any,
    test: Any,
    n_train: int | None = None,
    n_test: int | None = None,
    params: dict[str, Any] | None = None,
    nom: str = "lourd",
    dossier_resultats: str = DOSSIER_SORTIE,
) -> float:
    """Fine-tune DistilBERT sur `train`, renvoie l'accuracy sur `test`.

    `train` et `test` sont les datasets renvoyés par load_data() (colonnes text, label).
    n_train / n_test limitent le nombre d'exemples (test court).
    """
    import torch
    import transformers
    from sklearn.metrics import accuracy_score
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    p = {**HEAVY_PARAMS, **(params or {})}
    set_seed(SEED)

    if n_train is not None:
        train = train.select(range(min(n_train, len(train))))
    if n_test is not None:
        test = test.select(range(min(n_test, len(test))))

    tokenizer = AutoTokenizer.from_pretrained(p["model_name"])

    def encoder(batch: dict[str, list]) -> dict[str, list]:
        return tokenizer(batch["text"], truncation=True, max_length=p["max_length"])

    ds_train = train.map(encoder, batched=True, remove_columns=["text"])
    ds_test = test.map(encoder, batched=True, remove_columns=["text"])

    model = AutoModelForSequenceClassification.from_pretrained(
        p["model_name"], num_labels=p["num_labels"]
    )
    args = TrainingArguments(
        output_dir=f"outputs/{nom}",
        num_train_epochs=p["epochs"],
        per_device_train_batch_size=p["batch_size"],
        per_device_eval_batch_size=p["batch_size"] * 2,
        learning_rate=p["learning_rate"],
        weight_decay=p["weight_decay"],
        seed=SEED,
        fp16=torch.cuda.is_available(),
        save_strategy="no",
        report_to="none",
        logging_steps=50,
    )
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_train,
        data_collator=DataCollatorWithPadding(tokenizer),
    )

    debut = time.perf_counter()
    trainer.train()
    duree_train = time.perf_counter() - debut

    preds = trainer.predict(ds_test).predictions.argmax(axis=-1)
    accuracy = float(accuracy_score(ds_test["label"], preds))

    # Estimation linéaire de la durée d'entraînement du vrai run (10 000 exemples).
    estimation_min = duree_train / len(ds_train) * N_TRAIN_VRAI_RUN * p["epochs"] / 60
    infos = {
        "nom": nom,
        "accuracy": accuracy,
        "n_train": len(ds_train),
        "n_test": len(ds_test),
        "duree_entrainement_s": round(duree_train, 1),
        "estimation_vrai_run_min": round(estimation_min, 1),
        "respecte_limite_20_min": estimation_min < LIMITE_MINUTES,
        "hyperparametres": p,
        "materiel": infos_materiel(),
        "transformers": transformers.__version__,
    }
    Path(dossier_resultats).mkdir(exist_ok=True)
    chemin = Path(dossier_resultats) / f"{nom}.json"
    chemin.write_text(json.dumps(infos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(infos, indent=2, ensure_ascii=False))
    return accuracy


def main() -> None:
    parser = argparse.ArgumentParser(description="Modèle lourd mesuré par CodeCarbon")
    parser.add_argument(
        "--test-court", action="store_true", help="500 exemples train / 200 test"
    )
    parser.add_argument(
        "--runs", type=int, default=1, help="nombre de vrais runs (lourd_run1, lourd_run2…)"
    )
    parser.add_argument("--premier", type=int, default=1, help="numéro du premier run")
    args = parser.parse_args()

    import torch

    Path(DOSSIER_SORTIE).mkdir(parents=True, exist_ok=True)
    options_tracker: dict[str, Any] = {
        "output_dir": DOSSIER_SORTIE,
        "output_file": FICHIER_EMISSIONS,
    }
    if torch.cuda.is_available():
        # Ne mesurer que le GPU qui calcule (Kaggle en fournit deux).
        options_tracker["gpu_ids"] = [0]

    train, test = load_data()
    if args.test_court:
        taches = [("lourd_test_court", 500, 200)]
    else:
        taches = [
            (f"lourd_run{i}", None, None) for i in range(args.premier, args.premier + args.runs)
        ]

    for nom, n_train, n_test in taches:
        mesurer(
            nom,
            lambda: train_heavy(train, test, n_train, n_test, nom=nom),
            **options_tracker,
        )


if __name__ == "__main__":
    main()
