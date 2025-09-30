#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Liste les fichiers .txt ayant moins de 5 lignes non vides
dans un dossier donné.

Usage :
    python find_empty_txt.py --txt-dir data_taluyers/raster_txt
"""

import argparse
from pathlib import Path


def main(txt_dir: Path, min_lines: int = 5):
    txt_files = sorted(txt_dir.glob("*.txt"))
    if not txt_files:
        print(f"Aucun fichier .txt dans {txt_dir}")
        return

    empty_files = []
    for f in txt_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
            non_empty = [l for l in lines if l.strip()]  # lignes non vides
            if len(non_empty) < min_lines:
                empty_files.append((f, len(non_empty)))
        except Exception as e:
            print(f"Erreur lecture {f}: {e}")

    if not empty_files:
        print("Aucun fichier vide ou quasi-vide trouvé.")
    else:
        print("Fichiers avec moins de 5 lignes non vides :")
        for f, n in empty_files:
            print(f" - {f} ({n} lignes non vides)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt-dir", required=True, help="Dossier contenant les .txt")
    ap.add_argument(
        "--min-lines", type=int, default=5, help="Seuil de lignes non vides"
    )
    args = ap.parse_args()
    main(Path(args.txt_dir), args.min_lines)
