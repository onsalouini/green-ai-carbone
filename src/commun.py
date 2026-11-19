"""Code commun : identique pour tous (mêmes données, même mesure).

Copié tel quel de la fiche de répartition (séance 2). Ne pas modifier seul :
toute modification se décide en équipe, sinon les mesures ne sont plus comparables.
"""

from datasets import load_dataset
from codecarbon import EmissionsTracker

SEED = 42


def load_data(n_train=10_000, n_test=2_000, seed=SEED):
    # "ag_news" seul est refusé par huggingface_hub récent (id « namespace/name » exigé) :
    # fancyzhx/ag_news est le même jeu de données sous son identifiant actuel.
    ds = load_dataset("fancyzhx/ag_news")
    train = ds["train"].shuffle(seed=seed).select(range(n_train))
    test = ds["test"].shuffle(seed=seed).select(range(n_test))
    return train, test  # colonnes : "text", "label" (4 classes)


def mesurer(nom, fonction_entrainement):
    tracker = EmissionsTracker(project_name=nom, output_file="emissions.csv")
    tracker.start()
    accuracy = fonction_entrainement()
    kg = tracker.stop()
    print(f"{nom} | accuracy={accuracy:.4f} | {kg*1000:.3f} g CO2eq")
    return accuracy, kg


# Ali : mesurer("leger", train_light)    Ons : mesurer("lourd", train_heavy)
