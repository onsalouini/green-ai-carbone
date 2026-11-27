"""Analyse de sensibilité du coût carbone par point de précision (responsable : Ghayth).

    python -m src.sensibilite
    python -m src.sensibilite --energie-lourd-wh 4.0 --accuracy-lourd 91.0   # scénario manuel

Indicateur étudié (cahier des charges) :

    coût par point = I × PUE × (E_lourd − E_léger) / (acc_lourd − acc_léger)
                     [g CO2eq / point]   avec I en g/kWh, E en kWh, acc en points de %

On fait varier UNE hypothèse à la fois autour d'un scénario de référence et on regarde
de combien bouge l'indicateur (analyse « one-at-a-time », présentée en tornade).

Données :
  - léger : moyenne des runs d'Ali (resultats/emissions_leger.csv), accuracy 88,40 %.
  - lourd : runs « lourd* » (hors test court) de resultats/kaggle/emissions_lourd.csv
    et accuracies des resultats/kaggle/lourd*.json. S'ils sont absents, scénario
    PROVISOIRE fourni par --energie-lourd-wh / --accuracy-lourd (affiché comme tel).
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
N_TEST = 2_000

# Scénario provisoire du modèle lourd tant que les vrais runs ne sont pas poussés.
# Énergie : extrapolation du test court (≈ 108 s d'entraînement GPU à ≈ 100 W
# + ≈ 60 s de chargement / tokenisation / évaluation à ≈ 36 W) ≈ 3,6 Wh, arrondi à 4 Wh.
# Accuracy : ordre de grandeur publié pour DistilBERT 1 époque sur 10 k exemples AG News.
PROVISOIRE_E_WH = 4.0
PROVISOIRE_ACC = 91.0


@dataclass(frozen=True)
class Scenario:
    e_leger_kwh: float
    e_lourd_kwh: float
    acc_leger: float  # points de %
    acc_lourd: float
    intensite: float = 288.0  # g CO2/kWh, Kaggle Iowa (référence commune)
    pue: float = 1.0  # valeur CodeCarbon par défaut
    # Part de l'énergie « RAM » de CodeCarbon (forfait, pas une mesure) conservée : 1 = telle quelle
    facteur_ram: float = 1.0
    e_ram_leger_kwh: float = 0.0
    e_ram_lourd_kwh: float = 0.0
    # Puissance au repos du 2e T4 comptée à tort par CodeCarbon (W), retirée du lourd
    gpu_fantome_w: float = 0.0
    # False si les runs lourds sont mesurés avec gpu_ids=[0] : rien à retirer
    gpu_fantome_present: bool = True
    duree_lourd_s: float = 0.0
    duree_leger_s: float = 0.0
    # Coefficient de variation observé sur l'énergie du lourd (écart-type / moyenne)
    cv_lourd: float = 0.28
    # Fabrication amortie (g CO2eq par run), hors périmètre officiel
    fab_leger_g: float = 0.0
    fab_lourd_g: float = 0.0

    def energie(self) -> tuple[float, float]:
        el = self.e_leger_kwh - (1 - self.facteur_ram) * self.e_ram_leger_kwh
        eh = (
            self.e_lourd_kwh
            - (1 - self.facteur_ram) * self.e_ram_lourd_kwh
            - self.gpu_fantome_w * self.duree_lourd_s / 3.6e6
        )
        return el, eh

    def cout_par_point(self) -> float:
        el, eh = self.energie()
        delta_g = self.intensite * self.pue * (eh - el) + (self.fab_lourd_g - self.fab_leger_g)
        delta_acc = self.acc_lourd - self.acc_leger
        return delta_g / delta_acc if delta_acc > 0 else math.inf


# --------------------------------------------------------------------------- données
def charger(e_lourd_wh: float | None, acc_lourd: float | None) -> tuple[Scenario, str]:
    leger = pd.read_csv(RACINE / "resultats/emissions_leger.csv")
    leger = leger[leger["project_name"].str.startswith("leger_run")]
    accs_leger = [
        json.loads(f.read_text(encoding="utf-8"))["accuracy"] * 100
        for f in (RACINE / "resultats").glob("leger_run*.json")
    ]

    source = "mesures d'Ons (Kaggle T4)"
    lourd = pd.read_csv(RACINE / "resultats/kaggle/emissions_lourd.csv")
    lourd = lourd[
        lourd["project_name"].str.startswith("lourd")
        & ~lourd["project_name"].str.contains("test_court")
    ]
    accs = [
        json.loads(f.read_text(encoding="utf-8"))["accuracy"] * 100
        for f in (RACINE / "resultats/kaggle").glob("lourd*.json")
        if "test_court" not in f.name
    ]

    gpu_fantome_present = True
    cv_lourd = 0.28  # scénario provisoire : CV max observé sur Colab en S2
    if e_lourd_wh is not None or lourd.empty:
        source = "SCÉNARIO PROVISOIRE (vrais runs DistilBERT pas encore disponibles)"
        e = (e_lourd_wh or PROVISOIRE_E_WH) / 1000
        # répartition RAM / durée calquée sur le test court (RAM ≈ 20 W forfaitaires)
        duree = 170.0
        e_ram = 20 * duree / 3.6e6
    else:
        # Avec gpu_ids=[0] (code commun corrigé par Ons), CodeCarbon ne voit plus le 2e T4.
        # Attention : vérifier avec Ons si gpu_count reste à 2 malgré gpu_ids=[0].
        gpu_fantome_present = bool((lourd["gpu_count"] > 1).any())
        if len(lourd) > 1:
            cv_lourd = lourd["energy_consumed"].std() / lourd["energy_consumed"].mean()
        e, e_ram, duree = (
            lourd["energy_consumed"].mean(),
            lourd["ram_energy"].mean(),
            lourd["duration"].mean(),
        )
    acc = acc_lourd if acc_lourd is not None else (sum(accs) / len(accs) if accs else PROVISOIRE_ACC)
    if acc_lourd is None and not accs:
        source += " · accuracy lourde provisoire"

    return (
        Scenario(
            e_leger_kwh=leger["energy_consumed"].mean(),
            e_lourd_kwh=e,
            acc_leger=sum(accs_leger) / len(accs_leger) if accs_leger else 88.40,
            acc_lourd=acc,
            e_ram_leger_kwh=leger["ram_energy"].mean(),
            e_ram_lourd_kwh=e_ram,
            duree_lourd_s=duree,
            duree_leger_s=leger["duration"].mean(),
            cv_lourd=cv_lourd,
            gpu_fantome_present=gpu_fantome_present,
        ),
        source,
    )


# --------------------------------------------------------------------------- fabrication
def fabrication_g(fab_kg: float, vie_ans: float, utilisation: float, duree_s: float) -> float:
    """Part de l'empreinte de fabrication attribuée à un run (amortissement linéaire)."""
    heures_utiles = vie_ans * 8760 * utilisation
    return fab_kg * 1000 / heures_utiles * duree_s / 3600


# --------------------------------------------------------------------------- analyse
def variations(ref: Scenario) -> list[tuple[str, str, Scenario, Scenario]]:
    """(hypothèse, bornes affichées, scénario bas, scénario haut)."""
    se = 100 * math.sqrt(  # erreur-type de la différence de deux accuracies (n = 2 000)
        (ref.acc_leger / 100 * (1 - ref.acc_leger / 100) + ref.acc_lourd / 100 * (1 - ref.acc_lourd / 100))
        / N_TEST
    )
    d = ref.duree_lourd_s
    gpu_fantome = (
        [("2e T4 au repos compté par CodeCarbon", "retiré (≈ 10 W) → gardé",
          replace(ref, gpu_fantome_w=10.0), ref)]
        if ref.gpu_fantome_present
        else []  # runs mesurés avec gpu_ids=[0] : biais déjà corrigé à la source
    )
    return gpu_fantome + [
        ("Intensité carbone du réseau", "166 (Oregon) → 560 g/kWh (Tunisie, Ember)",
         replace(ref, intensite=166), replace(ref, intensite=560)),
        ("Gain d'accuracy (± 1 erreur-type, n = 2 000)", f"Δacc ± {se:.2f} pt",
         replace(ref, acc_lourd=ref.acc_lourd + se), replace(ref, acc_lourd=ref.acc_lourd - se)),
        ("PUE du datacenter", "1,0 (défaut CodeCarbon) → 1,56 (moyenne industrie)",
         replace(ref, pue=1.0), replace(ref, pue=1.56)),
        ("Fabrication du matériel incluse", "0 → amortissement haut",
         ref, replace(ref, fab_lourd_g=fabrication_g(150 + 2500 / 4, 4, 0.5, d),
                      fab_leger_g=fabrication_g(2500 * 2 / 96, 4, 0.5, ref.duree_leger_s))),
        ("RAM : forfait CodeCarbon conservé", "0 % → 100 % du forfait",
         replace(ref, facteur_ram=0.0), ref),
        ("Variabilité de la mesure d'énergie lourde", f"± 2 CV = ± {200 * ref.cv_lourd:.0f} % (runs observés)",
         replace(ref, e_lourd_kwh=ref.e_lourd_kwh * (1 - 2 * ref.cv_lourd)),
         replace(ref, e_lourd_kwh=ref.e_lourd_kwh * (1 + 2 * ref.cv_lourd))),
    ]


def main() -> None:
    p = argparse.ArgumentParser(description="Analyse de sensibilité du coût carbone par point")
    p.add_argument("--energie-lourd-wh", type=float, help="forcer l'énergie moyenne du lourd (Wh)")
    p.add_argument("--accuracy-lourd", type=float, help="forcer l'accuracy moyenne du lourd (%%)")
    args = p.parse_args()

    ref, source = charger(args.energie_lourd_wh, args.accuracy_lourd)
    c0 = ref.cout_par_point()
    print(f"Source modèle lourd : {source}")
    print(
        f"Référence : E_léger = {ref.e_leger_kwh * 1000:.4f} Wh, E_lourd = {ref.e_lourd_kwh * 1000:.3f} Wh, "
        f"acc {ref.acc_leger:.2f} % → {ref.acc_lourd:.2f} %, I = {ref.intensite:.0f} g/kWh, PUE = {ref.pue}"
    )
    print(f"Coût carbone par point (référence) : {c0:.3f} g CO2eq / point\n")

    lignes = []
    for nom, bornes, bas, haut in variations(ref):
        cb, ch = bas.cout_par_point(), haut.cout_par_point()
        lignes.append((max(abs(cb - c0), abs(ch - c0)), nom, bornes, cb, ch))
    lignes.sort(reverse=True)

    print("| Hypothèse | Plage testée | Coût / point bas | Coût / point haut | Écart max |")
    print("|---|---|---|---|---|")
    for amp, nom, bornes, cb, ch in lignes:
        print(f"| {nom} | {bornes} | {cb:.3f} | {ch:.3f} | ±{100 * amp / c0:.0f} % |")

    # Pire et meilleur cas combinés
    v = {nom: (bas, haut) for nom, _, bas, haut in variations(ref)}
    acc_bas, acc_haut = v["Gain d'accuracy (± 1 erreur-type, n = 2 000)"]
    fab_haut = v["Fabrication du matériel incluse"][1]
    meilleur = replace(ref, intensite=166, pue=1.0, facteur_ram=0.0,
                       gpu_fantome_w=10.0 if ref.gpu_fantome_present else 0.0,
                       acc_lourd=acc_bas.acc_lourd, e_lourd_kwh=ref.e_lourd_kwh * (1 - 2 * ref.cv_lourd))
    pire = replace(fab_haut, intensite=560, pue=1.56, acc_lourd=acc_haut.acc_lourd,
                   e_lourd_kwh=ref.e_lourd_kwh * (1 + 2 * ref.cv_lourd))
    print(f"\nTout favorable  : {meilleur.cout_par_point():.3f} g CO2eq / point")
    print(f"Tout défavorable: {pire.cout_par_point():.3f} g CO2eq / point")
    print(f"Rapport max/min : × {pire.cout_par_point() / meilleur.cout_par_point():.0f}")

    print("\nFabrication amortie par run (hypothèses de docs/fabrication_materiel.md) :")
    for nom, fab, vie, u, duree, e_wh in [
        ("lourd · T4 + 1/4 serveur (Kaggle)", 150 + 2500 / 4, 4, 0.5, ref.duree_lourd_s, ref.e_lourd_kwh * 1000),
        ("lourd · bas : T4 + 1/8 serveur, 6 ans, 85 %", 50 + 2500 / 8, 6, 0.85, ref.duree_lourd_s, ref.e_lourd_kwh * 1000),
        ("léger · 2 vCPU / 96 d'un serveur (Colab)", 2500 * 2 / 96, 4, 0.5, ref.duree_leger_s, ref.e_leger_kwh * 1000),
        ("léger · PC portable (Ghayth)", 250, 4, 0.2, 7.1, 0.0537),
    ]:
        g = fabrication_g(fab, vie, u, duree)
        usage = e_wh / 1000 * ref.intensite
        print(f"  {nom:<45} fabrication {g:.4f} g | usage {usage:.4f} g | part fabrication {100 * g / (g + usage):.0f} %")

    fab_bas = replace(ref, fab_lourd_g=fabrication_g(50 + 2500 / 8, 6, 0.85, ref.duree_lourd_s),
                      fab_leger_g=fabrication_g(2500 * 2 / 96, 6, 0.85, ref.duree_leger_s))
    print(f"\nCoût par point avec fabrication : bas {fab_bas.cout_par_point():.3f} "
          f"(+{100 * (fab_bas.cout_par_point() / c0 - 1):.0f} %) | haut {fab_haut.cout_par_point():.3f} "
          f"(+{100 * (fab_haut.cout_par_point() / c0 - 1):.0f} %)")


if __name__ == "__main__":
    main()
