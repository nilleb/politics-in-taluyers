#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OCR Taluyers - Mistral Document AI OCR
- Envoie des PDF (y compris raster) à l'API Mistral OCR
- Exporte le texte (markdown concaténé) en .txt
- Ecrit un log CSV

Usage:
  python ocr_mistral.py --pdf-dir data_taluyers/pdf --out-dir data_taluyers/txt_ocr
"""

import argparse
import base64
import csv
import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from mistralai import Mistral
from tqdm import tqdm

load_dotenv()

MISTRAL_MODEL = "mistral-ocr-latest"  # modèle OCR courant


def pdf_to_data_url(pdf_path: Path) -> str:
    b64 = base64.b64encode(pdf_path.read_bytes()).decode("utf-8")
    return f"data:application/pdf;base64,{b64}"


def ocr_pdf(
    client: Mistral, pdf_path: Path, max_retries: int = 5, backoff: float = 2.0
):
    """Appelle l'OCR Mistral et renvoie l'objet de réponse (pas un dict)."""
    data_url = pdf_to_data_url(pdf_path)
    attempt = 0
    while True:
        try:
            # NOTE: selon le SDK, cette méthode peut s'appeler .ocr.process / .ocr.documents.process
            # Gardez la vôtre si elle marche; la clé est de NE PLUS utiliser .get() ensuite.
            return client.ocr.process(
                model=MISTRAL_MODEL,
                document={"type": "document_url", "document_url": data_url},
                include_image_base64=False,
            )
        except Exception:
            attempt += 1
            if attempt >= max_retries:
                raise
            time.sleep(backoff * attempt)


def extract_pages_from_ocr_response(resp) -> list:
    """
    Normalise la réponse OCR Mistral pour obtenir une liste de pages, chacune avec une clé 'markdown'.
    Gère: Pydantic v2 (.model_dump), v1 (.dict), .json(), ou attributs (.pages[i].markdown).
    """
    # 1) Essayer d'obtenir un dict
    data = None
    for to_dict in ("model_dump", "dict"):
        if hasattr(resp, to_dict):
            try:
                data = getattr(resp, to_dict)()
                break
            except Exception:
                pass
    if data is None and hasattr(resp, "json"):
        try:
            data = json.loads(resp.json())
        except Exception:
            data = None

    # 2) Si on a un dict avec 'pages'
    if isinstance(data, dict) and "pages" in data:
        pages = data["pages"] or []
        # Uniformiser: assurer la présence de la clé 'markdown'
        norm = []
        for p in pages:
            if isinstance(p, dict):
                norm.append({"markdown": p.get("markdown", "")})
            else:
                md = getattr(p, "markdown", "") if hasattr(p, "markdown") else ""
                norm.append({"markdown": md})
        return norm

    # 3) Essayer via attributs (objet)
    if hasattr(resp, "pages"):
        pages_attr = getattr(resp, "pages")
        norm = []
        if isinstance(pages_attr, list):
            for p in pages_attr:
                if isinstance(p, dict):
                    norm.append({"markdown": p.get("markdown", "")})
                else:
                    md = getattr(p, "markdown", "") if hasattr(p, "markdown") else ""
                    norm.append({"markdown": md})
            return norm

    # 4) Rien reconnu
    raise TypeError(
        "Format de réponse OCR inattendu: impossible d'extraire 'pages'. "
        "Activez un log brut pour debug."
    )


def concat_markdown(pages: list) -> str:
    parts = []
    for i, p in enumerate(pages):
        md = (p.get("markdown", "") if isinstance(p, dict) else "") or ""
        sep = "\n\n---\n\n" if i > 0 else ""
        parts.append(f"{sep}{md}".strip())
    return "\n".join(parts).strip()


def main(pdf_dir: Path, out_dir: Path):
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY manquant dans l'environnement.")

    client = Mistral(api_key=api_key)
    out_dir.mkdir(parents=True, exist_ok=True)
    log_csv = out_dir / "ocr_log.csv"

    pdf_files = sorted([p for p in Path(pdf_dir).glob("*.pdf") if p.is_file()])
    if not pdf_files:
        print(f"Aucun PDF trouvé dans {pdf_dir}")
        return

    with log_csv.open("w", newline="", encoding="utf-8") as fcsv:
        writer = csv.DictWriter(
            fcsv, fieldnames=["pdf", "txt", "status", "pages", "error"]
        )
        writer.writeheader()

        for pdf in tqdm(pdf_files, desc="OCR PDFs", unit="pdf"):
            txt_path = out_dir / (pdf.stem + ".txt")
            status = "OK"
            pages_count = 0
            err_msg = ""

            # Skip si déjà produit
            if txt_path.exists() and txt_path.stat().st_size > 0:
                writer.writerow(
                    {
                        "pdf": str(pdf),
                        "txt": str(txt_path),
                        "status": "SKIPPED_EXISTS",
                        "pages": "",
                        "error": "",
                    }
                )
                continue

            try:
                resp_obj = ocr_pdf(client, pdf)
                try:
                    pages = extract_pages_from_ocr_response(resp_obj)
                except Exception:
                    # Sauvegarde brute pour diagnostic
                    (out_dir / f"{pdf.stem}.raw.json").write_text(
                        getattr(resp_obj, "json", lambda: "{}")(), encoding="utf-8"
                    )
                    raise

                md = concat_markdown(pages) if pages else ""
                txt_path.write_text(
                    md, encoding="utf-8"
                )  # Selon la doc, la sortie contient un tableau 'pages' avec 'markdown'
                pages_count = len(pages)
                md = concat_markdown(pages) if pages else ""
                txt_path.write_text(md, encoding="utf-8")
            except Exception as e:
                status = "ERROR"
                err_msg = str(e)

            writer.writerow(
                {
                    "pdf": str(pdf),
                    "txt": str(txt_path),
                    "status": status,
                    "pages": pages_count,
                    "error": err_msg[:500],
                }
            )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", required=True, help="Dossier des PDF en entrée")
    ap.add_argument(
        "--out-dir", required=True, help="Dossier de sortie pour les .txt OCR"
    )
    args = ap.parse_args()
    main(Path(args.pdf_dir), Path(args.out_dir))
