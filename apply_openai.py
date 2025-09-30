#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Applique un prompt (chargé depuis prompt.txt) à un .txt de PV Taluyers via OpenAI GPT-5,
à condition que le fichier commence strictement par l'un des en-têtes autorisés.

Usage:
  # Un fichier
  python apply_openai.py --txt data_taluyers/raster_txt/pv-du-cm-du-30082024.txt --out-dir data_taluyers/json

  # Un dossier (tous les .txt à l'intérieur)
  python apply_openai.py --txt-dir data_taluyers/raster_txt --out-dir data_taluyers/json
"""

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HEADER_1 = "COMPTE RENDU DU CONSEIL MUNICIPAL DE TALUYERS"
HEADER_2 = "PROCES-VERBAL DU CONSEIL MUNICIPAL DE TALUYERS"


def header_matches(text: str) -> bool:
    """Vérifie que l'entête exact est au tout début (après BOM/espaces)."""
    start = text.lstrip("\ufeff").lstrip()
    lines = start.split("\n")
    for line in lines[:10]:
        if HEADER_1 in line or HEADER_2 in line:
            return True
    return False


def build_user_content(prompt_text: str, pv_text: str) -> str:
    """
    Construit le contenu 'user' en insérant le texte du PV sous délimiteurs,
    sans modifier le prompt fourni.
    """
    return f"{prompt_text.rstrip()}\n\nTEXTE_DU_PV:\n<<<PV_START\n{pv_text}\nPV_END>>>"


def process_one_file(
    client: OpenAI,
    txt_path: Path,
    prompt_path: Path,
    out_dir: Path,
    model: str = "gpt-4o",
):
    pv_text = txt_path.read_text(encoding="utf-8", errors="ignore")
    # if not header_matches(pv_text):
    #     print(f"The file '{txt_path}' does not start with the specified text.")
    #     return

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (txt_path.stem + ".json")
    if os.path.exists(out_path):
        print(f"Skipping {txt_path}")
        return

    prompt_text = prompt_path.read_text(encoding="utf-8")
    user_content = build_user_content(prompt_text, pv_text)

    # Appel Chat Completions API — JSON garanti via response_format
    # Docs: https://platform.openai.com/docs/api-reference/chat
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "Tu renvoies UNIQUEMENT du JSON valide UTF-8.",
            },
            {"role": "user", "content": user_content},
        ],
    )

    # La sortie JSON est disponible ici :
    json_str = resp.choices[0].message.content

    # Valider et sauvegarder
    data = json.loads(json_str)  # lève si invalide
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt", type=str, help="Chemin vers un fichier .txt")
    ap.add_argument("--txt-dir", type=str, help="Dossier contenant des .txt")
    ap.add_argument(
        "--out-dir", type=str, required=True, help="Dossier de sortie des .json"
    )
    ap.add_argument(
        "--prompt-file",
        type=str,
        default="prompt.txt",
        help="Chemin vers prompt.txt (UTF-8)",
    )
    ap.add_argument(
        "--model", type=str, default="gpt-4o", help="Nom du modèle (par défaut: gpt-4o)"
    )
    args = ap.parse_args()

    if not args.txt and not args.txt_dir:
        ap.error("Spécifiez --txt ou --txt-dir")

    # Clé API
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY manquant dans l'environnement.")

    client = OpenAI()
    prompt_path = Path(args.prompt_file)
    out_dir = Path(args.out_dir)

    if args.txt:
        process_one_file(client, Path(args.txt), prompt_path, out_dir, model=args.model)
    else:
        txt_dir = Path(args.txt_dir)
        for txt_path in sorted(txt_dir.glob("*.txt")):
            process_one_file(client, txt_path, prompt_path, out_dir, model=args.model)


if __name__ == "__main__":
    main()
