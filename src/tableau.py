"""Tableau comparatif léger / lourd (responsable : Ali).

    python -m src.tableau
    python -m src.tableau --pue 1.09                 # ajoute le PUE des datacenters Google
    python -m src.tableau --resultats autre_dossier  # lire les résultats ailleurs (tests)

Lit les runs des deux modèles (CSV CodeCarbon + JSON) et écrit :
- resultats/tableau_comparatif.md : tableau Markdown (mêmes colonnes que docs/tableau_comparatif.md),
  émissions recalculées à intensité commune et coût carbone par point de précision gagné ;
- resultats/tableau_comparatif.csv : les mêmes chiffres, lisibles par un tableur.

Pas de dépendance externe (bibliothèque standard seulement).
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent

# Intensités carbone communes (g CO2eq / kWh), valeurs de docs/hypotheses.md.
# Les runs n'ont pas tourné dans la même région (Colab Oregon/Iowa, Kaggle Iowa…) :
# on recalcule les émissions des deux modèles avec la MÊME intensité.
INTENSITES: dict[str, float] = {
    "Tunisie": 483.0,  # LowCarbonPower 2025
    "Iowa": 295.0,     # Colab, mesuré par CodeCarbon (séance 2)
}
PUE_DEFAUT = 1.0       # valeur CodeCarbon ; option --pue 1.09 (datacenters Google 2024)

# Modèle -> (fichier CSV, dossier des JSON, préfixe des runs), chemins relatifs au dossier résultats.
MODELES: dict[str, tuple[str, str, str]] = {
    "TF-IDF + Régression logistique": ("emissions_leger.csv", ".", "leger_run"),
    "DistilBERT": ("kaggle/emissions_lourd.csv", "kaggle", "lourd_run"),
}

COLONNES_DOC = ["Modèle", "Accuracy (%)", "Durée (s)", "Énergie (kWh)", "Émissions (g CO₂eq)", "Matériel"]


@dataclass
class Stats:
    nom: str
    n_runs: int = 0
    acc: list[float] = field(default_factory=list)       # %
    duree: list[float] = field(default_factory=list)     # s
    energie: list[float] = field(default_factory=list)   # kWh
    emissions: list[float] = field(default_factory=list)  # g, mesurées (intensité locale)
    materiel: str = ""
    manques: list[str] = field(default_factory=list)


def moy(v: list[float]) -> float:
    return statistics.fmean(v)


def et(v: list[float]) -> float:
    """Écart-type d'échantillon (ddof = 1, comme pandas), 0 s'il n'y a qu'un run."""
    return statistics.stdev(v) if len(v) > 1 else 0.0


def court(p: Path) -> str:
    """Chemin relatif au dépôt si possible (plus lisible)."""
    return str(p.relative_to(RACINE)) if p.is_relative_to(RACINE) else str(p)


def charger(nom: str, dossier: Path, fichier_csv: str, dossier_json: str, prefixe: str) -> Stats:
    s = Stats(nom)
    chemin_csv = dossier / fichier_csv
    if chemin_csv.exists():
        with chemin_csv.open(encoding="utf-8", newline="") as f:
            lignes = [l for l in csv.DictReader(f) if l["project_name"].startswith(prefixe)]
        s.n_runs = len(lignes)
        s.duree = [float(l["duration"]) for l in lignes]
        s.energie = [float(l["energy_consumed"]) for l in lignes]
        s.emissions = [float(l["emissions"]) * 1000 for l in lignes]
        if lignes:
            l = lignes[0]
            region = l["region"] or l["country_name"]
            s.materiel = f"CPU {l['cpu_model']}" + (f" ({region})" if region else "")
        else:
            s.manques.append(f"aucun run « {prefixe}* » dans {court(chemin_csv)}")
    else:
        s.manques.append(f"fichier absent : {court(chemin_csv)}")

    jsons = sorted((dossier / dossier_json).glob(f"{prefixe}*.json"))
    gpu = None
    for f in jsons:
        infos = json.loads(f.read_text(encoding="utf-8"))
        s.acc.append(infos["accuracy"] * 100)
        gpu = (infos.get("materiel") or {}).get("gpu") or gpu
    if gpu:  # le JSON du lourd sait quel GPU a vraiment calculé (le CSV compte les 2 T4 présents)
        s.materiel = f"GPU {gpu} + " + s.materiel
    if not jsons:
        s.manques.append(f"aucun {prefixe}*.json dans {court(dossier / dossier_json)} (accuracy inconnue)")
    return s


# --------------------------------------------------------------------------- formatage
def fr(x: float, dec: int) -> str:
    """Nombre au format français (virgule décimale)."""
    return f"{x:.{dec}f}".replace(".", ",")


def pm(v: list[float], dec: int) -> str:
    if not v:
        return "n/d"
    return f"{fr(moy(v), dec)} ± {fr(et(v), dec)}"


def ecart(a: list[float], b: list[float], dec: int, ratio: bool = True) -> str:
    if not a or not b:
        return "n/d"
    d = moy(b) - moy(a)
    txt = f"{'+' if d >= 0 else '−'} {fr(abs(d), dec)}"
    return f"{txt} (× {fr(moy(b) / moy(a), 1)})" if ratio else txt


# --------------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser(description="Tableau comparatif léger / lourd")
    parser.add_argument("--resultats", default=str(RACINE / "resultats"), help="dossier des résultats")
    parser.add_argument("--pue", type=float, default=PUE_DEFAUT, help="PUE appliqué aux émissions recalculées")
    args = parser.parse_args()
    # La console Windows (cp1252) ne sait pas afficher ⚠️, −, ₂ : on force l'UTF-8.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    dossier = Path(args.resultats).resolve()
    pue = args.pue

    leger, lourd = (charger(nom, dossier, *cfg) for nom, cfg in MODELES.items())
    modeles = [m for m in (leger, lourd) if m.energie]
    complet = bool(leger.energie and lourd.energie)

    md: list[str] = ["# Tableau comparatif (généré par `python -m src.tableau`)", ""]
    for m in (leger, lourd):
        for manque in m.manques:
            print(f"⚠️  {m.nom} : {manque}")
            md.append(f"> ⚠️ {m.nom} : {manque}")
    if leger.manques or lourd.manques:
        md.append("")

    # 1. Tableau principal (colonnes de docs/tableau_comparatif.md)
    md += ["| " + " | ".join(COLONNES_DOC) + " |", "|" + "---|" * len(COLONNES_DOC)]
    for m in modeles:
        md.append(f"| {m.nom} | {pm(m.acc, 2)} | {pm(m.duree, 1)} | {pm(m.energie, 6)} "
                  f"| {pm(m.emissions, 4)} | {m.materiel} |")
    if complet:
        d_acc = moy(lourd.acc) - moy(leger.acc) if leger.acc and lourd.acc else None
        acc_txt = f"{'+' if d_acc >= 0 else '−'} {fr(abs(d_acc), 2)} points" if d_acc is not None else "n/d"
        md.append(f"| Écart (lourd − léger) | {acc_txt} | {ecart(leger.duree, lourd.duree, 1)} "
                  f"| {ecart(leger.energie, lourd.energie, 6)} | {ecart(leger.emissions, lourd.emissions, 4)} | |")
    md += ["", "Moyenne ± écart-type sur les runs : "
           + ", ".join(f"{m.n_runs} runs pour {m.nom}" for m in modeles) + ".",
           "Émissions = émissions **mesurées** par CodeCarbon, avec l'intensité de la région de chaque run : "
           "elles ne sont pas comparables entre elles si les régions diffèrent.", ""]

    # 2. Émissions recalculées à intensité commune
    suffixe_pue = f" × PUE {fr(pue, 2)}" if pue != 1 else ""
    md += [f"## Émissions à intensité commune (énergie × intensité{suffixe_pue})", "",
           "| Modèle | " + " | ".join(f"{k} ({fr(v, 0)} g/kWh)" for k, v in INTENSITES.items()) + " |",
           "|---|" + "---|" * len(INTENSITES)]
    recalc = {m.nom: {k: [e * i * pue for e in m.energie] for k, i in INTENSITES.items()} for m in modeles}
    for m in modeles:
        md.append(f"| {m.nom} | " + " | ".join(pm(recalc[m.nom][k], 4) for k in INTENSITES) + " |")
    if complet:
        md.append("| Écart (lourd − léger) | " + " | ".join(
            ecart(recalc[leger.nom][k], recalc[lourd.nom][k], 4) for k in INTENSITES) + " |")
    md += ["", "Valeurs en g CO₂eq par run (moyenne ± écart-type).", ""]

    # 3. Coût carbone par point de précision gagné
    couts: dict[str, float | None] = {}
    ratio_energie = moy(lourd.energie) / moy(leger.energie) if complet else None
    if complet and leger.acc and lourd.acc:
        d_acc = moy(lourd.acc) - moy(leger.acc)
        d_e = moy(lourd.energie) - moy(leger.energie)
        md += ["## Coût carbone par point de précision gagné", "",
               "Coût = (CO₂ lourd − CO₂ léger) ÷ (accuracy lourd − accuracy léger), "
               "avec les émissions recalculées à intensité commune.", "",
               "| Intensité commune | Coût (g CO₂eq / point) |", "|---|---|"]
        for k, i in INTENSITES.items():
            couts[k] = i * pue * d_e / d_acc if d_acc > 0 else None
            md.append(f"| {k} ({fr(i, 0)} g/kWh) | "
                      + (fr(couts[k], 3) if couts[k] is not None else "non défini (pas de gain d'accuracy)") + " |")
        md += ["", f"Gain d'accuracy : {fr(d_acc, 2)} points ; énergie en plus : {fr(d_e * 1000, 3)} Wh ; "
               f"ratio d'énergie lourd / léger : **× {fr(ratio_energie, 1)}**.", ""]
    else:
        md += ["## Coût carbone par point de précision gagné", "",
               "Non calculable : il manque les résultats d'un des deux modèles (voir les avertissements en haut).", ""]

    sortie_md = dossier / "tableau_comparatif.md"
    sortie_md.write_text("\n".join(md), encoding="utf-8")

    # CSV (point décimal, sans arrondi d'affichage)
    entetes = ["modele", "n_runs", "accuracy_pct_moy", "accuracy_pct_et", "duree_s_moy", "duree_s_et",
               "energie_kwh_moy", "energie_kwh_et", "emissions_mesurees_g_moy", "emissions_mesurees_g_et"]
    entetes += [f"emissions_{k.lower()}_g_moy" for k in INTENSITES] + ["materiel", "valeur"]
    lignes_csv = []
    for m in modeles:
        r = [m.nom, m.n_runs]
        for v in (m.acc, m.duree, m.energie, m.emissions):
            r += [moy(v), et(v)] if v else ["", ""]
        r += [moy(recalc[m.nom][k]) for k in INTENSITES] + [m.materiel, ""]
        lignes_csv.append(r)
    if complet:
        r = ["Écart (lourd − léger)", ""]
        for a, b in ((leger.acc, lourd.acc), (leger.duree, lourd.duree),
                     (leger.energie, lourd.energie), (leger.emissions, lourd.emissions)):
            r += [moy(b) - moy(a) if a and b else "", ""]
        r += [moy(recalc[lourd.nom][k]) - moy(recalc[leger.nom][k]) for k in INTENSITES] + ["", ""]
        lignes_csv.append(r)
        # Indicateurs à une seule valeur : colonne « valeur » (la dernière).
        vide = [""] * (len(entetes) - 2)
        lignes_csv.append(["Ratio énergie (lourd / léger)", *vide, ratio_energie])
        for k, c in couts.items():
            lignes_csv.append([f"Coût par point {k} (g CO2eq / point)", *vide, c if c is not None else ""])
    # 6 chiffres significatifs : 88.4 au lieu de 88.40000000000002
    lignes_csv = [[f"{x:.6g}" if isinstance(x, float) else x for x in r] for r in lignes_csv]
    sortie_csv = dossier / "tableau_comparatif.csv"
    with sortie_csv.open("w", encoding="utf-8-sig", newline="") as f:  # utf-8-sig : accents OK dans Excel
        w = csv.writer(f)
        w.writerow(entetes)
        w.writerows(lignes_csv)

    print("\n".join(md))
    print(f"\nÉcrit : {sortie_md}\nÉcrit : {sortie_csv}")


if __name__ == "__main__":
    main()
