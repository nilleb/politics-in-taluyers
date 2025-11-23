#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Génère un tableau de présence (CSV) à partir de fichiers JSON.
- Une colonne par séance (triées par date croissante).
- Une ligne par élu (liste agrégée sur l'ensemble des fichiers).
- Valeur = 1 si présent (ou mandataire d'un pouvoir), sinon 0.

Usage:
    uv run python build_presence_matrix.py data_taluyers/json -o presence.csv
"""

import argparse
import csv
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

_TITLE_RE = re.compile(
    r"^\s*(?:M\.?|Mr\.?|Mme\.?|Mlle\.?|Madame|Monsieur)\s+", re.IGNORECASE
)

FORCED_EQUIVALENCE = {
    # left side = normalised key produced by this function
    # right side = canonical key
    "BRACHETCONVERT": "BRACHET",  # force BRACHET-CONVERT / BRACHETCONVERT → BRACHET
}


def last_name_key(fullname: str) -> str:
    """
    Retourne une clé normalisée pour le nom de famille :
      - supprime M., Mme, etc. en tête
      - récupère les derniers tokens en MAJUSCULES comme nom de famille
        (gère les noms composés : 'SAYER CORTAZZI', 'ROMAN-CLAVELLOUX', etc.)
        sinon, prend le dernier token
      - enlève accents, espaces, tirets, apostrophes, points
      - renvoie en MAJUSCULES
    """
    if not fullname:
        return ""

    s = _TITLE_RE.sub("", fullname.strip())

    # Tokens
    toks = s.split()
    # Prend la séquence terminale de tokens tout en MAJUSCULES
    tail_upper = []
    for tok in reversed(toks):
        if tok.isupper():
            tail_upper.insert(0, tok)
        else:
            break
    last_name = " ".join(tail_upper) if tail_upper else (toks[-1] if toks else "")

    # Normalisation unicode (suppression des accents)
    nfd = unicodedata.normalize("NFD", last_name)
    no_accents = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")

    # Supprime tirets, espaces, apostrophes, points
    cleaned = re.sub(r"[-\s.'’]", "", no_accents).upper()

    return FORCED_EQUIVALENCE.get(cleaned, cleaned)


def canon_name(s: str) -> str:
    """Normalise un nom: strip + collapse espaces internes."""
    if not isinstance(s, str):
        return s
    return last_name_key(" ".join(s.strip().split()))


def safe_list(x):
    return x if isinstance(x, list) else []


def get_mandate(session_index: int) -> int:
    """
    Détermine le numéro de mandat pour une séance donnée.
    - Mandat 1: sessions 0-1 (premières 2 séances en 2014)
    - Mandat 2: sessions 2-37 (36 séances suivantes)
    - Mandat 3: sessions 38+ (séances restantes)
    """
    if session_index < 2:
        return 1
    elif session_index < 2 + 36:  # sessions 2 à 37 (36 sessions)
        return 2
    else:
        return 3


def load_session(fp: Path):
    """Charge un fichier JSON et retourne (date_iso, meta_dict)."""
    with fp.open("r", encoding="utf-8") as f:
        data = json.load(f)

    seance = data.get("seance", {})
    date_str = seance.get("date")
    if not date_str:
        raise ValueError(f"Fichier {fp} : 'seance.date' manquant")

    # Valide/parse la date ISO (YYYY-MM-DD)
    try:
        d = date.fromisoformat(date_str)
    except Exception as e:
        raise ValueError(f"Fichier {fp} : date invalide '{date_str}'") from e

    presence = seance.get("presence", {}) or {}

    present = {canon_name(n) for n in safe_list(presence.get("PRESENT", []))}
    excuse = {canon_name(n) for n in safe_list(presence.get("EXCUSE", []))}
    absent = {canon_name(n) for n in safe_list(presence.get("ABSENT", []))}

    # EXCUSE_AVEC_POUVOIR : liste d'objets {mandant, mandataire}
    pouvoirs = presence.get("EXCUSE_AVEC_POUVOIR", []) or []
    mandants = set()
    mandataires = set()
    for p in pouvoirs:
        if isinstance(p, dict):
            mandants.add(canon_name(p.get("mandant", "")))
            mandataires.add(canon_name(p.get("mandataire", "")))

    # Ensemble des présents effectifs = PRESENT ∪ mandataires
    presents_effectifs = (
        {n for n in present if n}
        | {n for n in mandataires if n}
        | {n for n in mandants if n}  # <-- ajoute les mandants comme "présents"
    )
    # Liste complète des noms vus dans ce fichier (pour construire le référentiel des élus)
    all_names = set()
    all_names |= set(n for n in present if n)
    all_names |= set(n for n in excuse if n)
    all_names |= set(n for n in absent if n)
    all_names |= set(n for n in mandants if n)
    all_names |= set(n for n in mandataires if n)

    # Prépare un identifiant/entête de colonne lisible
    commune = data.get("commune", "")
    lieu = seance.get("lieu", "")
    # Exemple d’en-tête: 2021-11-22 (Mairie)
    header = (
        f"{date_str}{f' ({lieu})' if lieu else ''}{f' – {commune}' if commune else ''}"
    )

    return {
        "path": str(fp),
        "date_obj": d,
        "date_str": date_str,
        "header": header,
        "presents": presents_effectifs,
        "all_names": all_names,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Construit un CSV de présence par séance/élu."
    )
    parser.add_argument(
        "input_dir", type=Path, help="Dossier contenant les fichiers JSON"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("presence.csv"),
        help="Chemin du CSV de sortie",
    )
    parser.add_argument(
        "--status-present", default="1", help="Valeur pour présent (par défaut: 1)"
    )
    parser.add_argument(
        "--status-absent", default="0", help="Valeur pour absent (par défaut: 0)"
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        raise SystemExit(f"Dossier introuvable: {args.input_dir}")

    # Charge toutes les séances
    sessions = []
    for fp in sorted(args.input_dir.glob("*.json")):
        try:
            sess = load_session(fp)
            sessions.append(sess)
        except Exception as e:
            # On choisit de continuer malgré un fichier invalide
            print(f"[WARN] Ignoré {fp}: {e}")

    if not sessions:
        raise SystemExit("Aucune séance valide trouvée.")

    # Agrège la liste des élus
    all_elus = set()
    for s in sessions:
        all_elus |= s["all_names"]

    # Trie les élus (ordre alphabétique insensible à la casse/accents)
    # On applique casefold pour une comparaison plus robuste
    elus_sorted = sorted(all_elus, key=lambda x: (x.casefold(), x))

    # Trie les séances par date croissante
    sessions_sorted = sorted(sessions, key=lambda s: s["date_obj"])

    # Construit et écrit le CSV
    headers = ["Elu"] + [s["header"] for s in sessions_sorted]

    with args.output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        # Ajoute une ligne avec le numéro de mandat pour chaque séance
        mandate_row = ["Mandat"] + [str(get_mandate(i)) for i in range(len(sessions_sorted))]
        writer.writerow(mandate_row)

        for elu in elus_sorted:
            row = [elu]
            for s in sessions_sorted:
                row.append(
                    args.status_present if elu in s["presents"] else args.status_absent
                )
            writer.writerow(row)

    print(
        f"OK: {args.output} écrit ({len(elus_sorted)} élus × {len(sessions_sorted)} séances)."
    )
    print(
        "Légende: présent = {p}, absent = {a}".format(
            p=args.status_present, a=args.status_absent
        )
    )

    recap_presence(args.output)


def recap_presence(csv_file: Path):
    """
    Lit un CSV 'Élu, séance1, séance2, ...'
    et imprime la liste des élus triés par nb de présences décroissant.
    Affiche aussi les pourcentages de présence par mandat.
    """
    with csv_file.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)  # skip header row
        mandate_row = next(reader)  # read mandate row
        session_count = len(headers) - 1
        
        # Parse mandate numbers for each session (skip first column "Mandat")
        mandates = [int(m) for m in mandate_row[1:]]

        recap = []
        for row in reader:
            name = row[0]
            # Get presence values for each session
            presence_values = [int(x) if x.strip().isdigit() else 0 for x in row[1:]]
            
            # Calculate total presences
            presences = sum(presence_values)
            
            # Calculate presences per mandate
            mandate_presences = {1: 0, 2: 0, 3: 0}
            mandate_totals = {1: 0, 2: 0, 3: 0}
            
            for i, mandate_num in enumerate(mandates):
                if i < len(presence_values):
                    mandate_totals[mandate_num] += 1
                    if presence_values[i] == 1:
                        mandate_presences[mandate_num] += 1
            
            # Calculate percentages per mandate
            mandate_pcts = {}
            for m in [1, 2, 3]:
                total = mandate_totals[m]
                pct = (mandate_presences[m] * 100 / total) if total > 0 else 0.0
                mandate_pcts[m] = pct
            
            recap.append((name, presences, session_count, mandate_pcts))

    # tri par nombre de présences décroissant
    recap.sort(key=lambda x: x[1], reverse=True)

    print(f"\n--- Recap présence ({session_count} séances) ---")
    print(f"{'Elu':30s} {'Total':>8s} {'Pct M1':>8s} {'Pct M2':>8s} {'Pct M3':>8s}")
    print("-" * 70)
    for name, presences, total, mandate_pcts in recap:
        pct = presences * 100 / total if total else 0
        pct_m1 = mandate_pcts[1]
        pct_m2 = mandate_pcts[2]
        pct_m3 = mandate_pcts[3]
        print(f"{name:30s} {presences:3d}/{total:3d} ({pct:4.1f}%) {pct_m1:6.1f}% {pct_m2:6.1f}% {pct_m3:6.1f}%")


if __name__ == "__main__":
    main()
