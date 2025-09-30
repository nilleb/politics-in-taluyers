#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Apply prompt -> JSON structuré (motions, votes, présence)
- Ne traite que les textes dont l'entête correspond exactement à l'un des deux libellés demandés.

Usage:
  python apply_prompt_if_header.py --txt-dir data_taluyers/txt_ocr --out-dir data_taluyers/json
"""

import argparse
import json
import os
from pathlib import Path

from mistralai import Mistral

HEADER_1 = "COMPTE RENDU DU CONSEIL MUNICIPAL DE TALUYERS"
HEADER_2 = "PROCES-VERBAL DU CONSEIL MUNICIPAL DE TALUYERS"

SYSTEM_PROMPT = """Tu es un extracteur fiable d'information juridique/administrative pour des procès-verbaux de conseils municipaux français. Tu renvoies UNIQUEMENT du JSON valide UTF-8."""

# Prompt utilisateur (raccourci – conforme à ce que nous avons défini)
USER_PROMPT_TEMPLATE = r"""
À partir du texte brut d’un procès-verbal (PV) de conseil municipal de TALUYERS, extrais une structure JSON conforme au SCHÉMA ci-dessous. Respecte strictement les RÈGLES.

RÈGLES:
- Ne fabrique pas de noms. Si une info manque, mets null ou [].
- Normalise les positions de vote: "POUR", "CONTRE", "ABSTENTION".
- Présence: catégories exclusives "PRESENT", "EXCUSE", "EXCUSE_AVEC_POUVOIR", "ABSENT" (pour EXCUSE_AVEC_POUVOIR: {mandant, mandataire}).
- Si "à l’unanimité" sans noms: mode="UNANIMITE", pas de listes; ne déduis pas les noms individuellement.
- Si des CONTRE/ABSTENTIONS nominatifs sont listés: renseigne ces noms; les autres présents sont considérés "POUR".
- Mets "commune": "Taluyers". Dates en ISO "YYYY-MM-DD" si possible.

SCHÉMA:
{
  "commune": "Taluyers",
  "seance": {
    "date": "YYYY-MM-DD | null",
    "lieu": "string | null",
    "lien_source_pdf": "string | null",
    "autres_participants": ["string", ...],
    "presence": {
      "PRESENT": ["Nom Prénom", ...],
      "EXCUSE": ["Nom Prénom", ...],
      "EXCUSE_AVEC_POUVOIR": [
        {"mandant": "Nom Prénom", "mandataire": "Nom Prénom"}
      ],
      "ABSENT": ["Nom Prénom", ...]
    }
  },
  "deliberations": [
    {
      "id": "string | null",
      "titre": "string | null",
      "resume": "string | null",
      "themes": ["budget|urbanisme|marches|subventions|RH|autre", ...],
      "vote": {
        "mode": "UNANIMITE | MAJORITE | AUTRE | INCONNU",
        "detail": {
          "POUR": ["Nom Prénom", ...],
          "CONTRE": ["Nom Prénom", ...],
          "ABSTENTION": ["Nom Prénom", ...]
        },
        "compteur": {
          "pour": "int | null",
          "contre": "int | null",
          "abstention": "int | null"
        }
      },
      "page_approx": "int | null",
      "notes": "string | null"
    }
  ]
}

TEXTE_DU_PV:
<<<PV_START
{pv_text}
PV_END>>>

Retourne UNIQUEMENT le JSON (pas de texte libre).
"""


def header_matches(file_path: Path) -> bool:
    """Vérifie que le texte commence EXACTEMENT par l'un des deux entêtes demandés (après BOM/espaces)."""
    raw = file_path.read_text(encoding="utf-8", errors="ignore")
    # Normalisation: strip BOM, trim leading whitespace, upper sans accents conservés
    start = raw.lstrip("\ufeff").lstrip()
    # On ne tolère pas du texte avant l'entête
    for hdr in (HEADER_1, HEADER_2):
        if start.startswith(hdr):
            return True
    return False


def call_mistral_chat(client: Mistral, prompt: str) -> str:
    """
    Appelle /v1/chat/completions avec contrainte JSON.
    Retourne la chaîne JSON.
    """
    resp = client.chat.complete(
        model="mistral-large-latest",
        temperature=0.1,
        response_format={"type": "json_object"},  # forcer JSON
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    # SDK retourne un objet avec choices[0].message.content
    return resp.choices[0].message["content"]  # JSON en str


def main(txt_dir: Path, out_dir: Path):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY manquant dans l'environnement.")
    client = Mistral(api_key=api_key)

    out_dir.mkdir(parents=True, exist_ok=True)
    txt_files = sorted([p for p in txt_dir.glob("*.txt") if p.is_file()])

    for txt in txt_files:
        if not header_matches(txt):
            print(f"The file '{txt}' does not start with the specified text.")
            continue

        out_path = out_dir / f"{txt.stem}.json"
        if os.path.exists(out_path):
            print(f"Skipping {txt}")
            return

        pv_text = txt.read_text(encoding="utf-8", errors="ignore")
        user_prompt = USER_PROMPT_TEMPLATE.format(pv_text=pv_text)

        try:
            json_str = call_mistral_chat(client, user_prompt)
            # Validation JSON élémentaire
            data = json.loads(json_str)
        except Exception as e:
            # En cas d'échec JSON, on logge un .error.json
            (out_dir / f"{txt.stem}.error.json").write_text(
                json.dumps({"error": str(e)}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            continue

        # Sauvegarde
        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--txt-dir", required=True, help="Dossier des .txt à traiter")
    ap.add_argument("--out-dir", required=True, help="Dossier de sortie des .json")
    args = ap.parse_args()
    main(Path(args.txt_dir), Path(args.out_dir))
