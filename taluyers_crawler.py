#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Crawler Taluyers -> Télécharge les PDF de conseils municipaux (2014-2025)
-> Extrait le texte avec pdfminer.six
-> Produit un index CSV.

Usage:
    python taluyers_crawler.py \
        --start-urls https://mairie-taluyers.fr/ma-commune/vie-municipale/conseils-municipaux/ \
        --out-dir data_taluyers \
        --from-year 2014 --to-year 2025
"""

import argparse
import csv
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dparser
from pdfminer.high_level import extract_text
from tqdm import tqdm

# -----------------------------
# Heuristiques de pertinence
# -----------------------------
PDF_KEYWORDS = [
    r"conseil",
    r"compte[- ]?rendu",
    r"proc[eé]s[- ]?verbal",
    r"d[ée]lib[ée]ration",
    r"\bcm\b",
    r"\bpv\b",
]
PDF_KEYWORDS_RE = re.compile("|".join(PDF_KEYWORDS), re.IGNORECASE)

# Date dans le nom de fichier ou l'URL: formats FR usuels
DATE_HINT_RE = re.compile(
    r"(?:(\d{1,2})[-_/ ]?(janv|jan|fevr|févr|feb|mars|mar|avr|apr|mai|jun|juin|juil|jul|aout|août|sept|sep|oct|nov|d[eé]c|dec)[-_/ ]?(\d{2,4})|(\d{4})[-_/ ]?(\d{1,2})[-_/ ]?(\d{1,2}))",
    re.IGNORECASE,
)


# Années limites
def in_year_range(dt, y0, y1):
    if not dt:
        return True  # si inconnu on garde
    return y0 <= dt.year <= y1


# -----------------------------
# Utilitaires
# -----------------------------
def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\-.]+", "_", name)
    return name[:255]


def guess_date_from_string(s: str):
    """Essaye d'inférer une date depuis une chaîne FR/EN.
    Retourne un objet datetime ou None.
    """
    if not s:
        return None
    # Tentative robuste (dayfirst True pour FR)
    try:
        dt = dparser.parse(s, dayfirst=True, fuzzy=True, default=None)
        return dt
    except Exception:
        pass

    # Recherche par motif simple (AAAA-MM-JJ etc.)
    m = DATE_HINT_RE.search(s)
    if m:
        try:
            dt = dparser.parse(m.group(0), dayfirst=True, fuzzy=True, default=None)
            return dt
        except Exception:
            return None
    return None


def is_same_domain(base_netloc: str, url: str) -> bool:
    try:
        netloc = urlparse(url).netloc
        return (not netloc) or (netloc == base_netloc)
    except Exception:
        return False


def looks_like_relevant_pdf(href: str) -> bool:
    if not href:
        return False
    if not href.lower().endswith(".pdf"):
        return False
    # heuristique mots-clés
    if PDF_KEYWORDS_RE.search(href):
        return True
    # sinon, garder quand même: certaines pages listent juste "PV.pdf"
    return True


# -----------------------------
# Extraction texte PDF
# -----------------------------
def extract_pdf_text(pdf_path: Path) -> str:
    try:
        return extract_text(str(pdf_path)) or ""
    except Exception as e:
        return f"__PDF_TEXT_EXTRACTION_ERROR__ {e}"


# -----------------------------
# Crawl
# -----------------------------
def crawl_and_download(
    start_urls, out_dir: Path, from_year: int, to_year: int, max_pages=2000
):
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir = out_dir / "pdf"
    txt_dir = out_dir / "txt"
    pdf_dir.mkdir(exist_ok=True)
    txt_dir.mkdir(exist_ok=True)

    index_csv = out_dir / "index.csv"
    seen_urls = set()
    to_visit = []

    # Domaine de départ (on se limite au domaine du premier start_url)
    base_netloc = urlparse(start_urls[0]).netloc

    for u in start_urls:
        to_visit.append(u)

    # Charge index existant si reprise
    existing = {}
    if index_csv.exists():
        with index_csv.open("r", newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                existing[row["url"]] = row

    with index_csv.open("w", newline="", encoding="utf-8") as fcsv:
        fieldnames = [
            "url",
            "local_pdf",
            "local_txt",
            "http_status",
            "guessed_date",
            "kept_by_year_filter",
            "title_or_anchor",
            "source_page",
        ]
        w = csv.DictWriter(fcsv, fieldnames=fieldnames)
        w.writeheader()

        pages_visited = 0
        session = requests.Session()
        session.headers.update(
            {"User-Agent": "TaluyersCouncilCrawler/1.0 (+non-commercial)"}
        )

        pbar = tqdm(total=max_pages, desc="Crawl pages", unit="page")
        while to_visit and pages_visited < max_pages:
            page_url = to_visit.pop(0)
            if page_url in seen_urls:
                continue
            seen_urls.add(page_url)

            # Rester sur le domaine
            if not is_same_domain(base_netloc, page_url):
                continue

            try:
                resp = session.get(page_url, timeout=20)
            except Exception:
                continue

            pages_visited += 1
            pbar.update(1)

            if resp.status_code != 200 or "text/html" not in resp.headers.get(
                "Content-Type", ""
            ):
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            # Collecte des liens
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                abs_url = urljoin(page_url, href)

                # Explore HTML interne
                if abs_url not in seen_urls and is_same_domain(base_netloc, abs_url):
                    # On garde à visiter les pages HTML
                    if not abs_url.lower().endswith(".pdf"):
                        to_visit.append(abs_url)

                # Candidats PDF
                if looks_like_relevant_pdf(href):
                    # Métadonnées
                    title = (a.get_text() or "").strip()
                    guessed_date = guess_date_from_string(
                        href
                    ) or guess_date_from_string(title)

                    keep = in_year_range(guessed_date, from_year, to_year)

                    # Si déjà dans index et téléchargé, on peut réécrire l’entrée telle quelle
                    if abs_url in existing:
                        row = existing[abs_url]
                        # Respect du filtre année (si déjà téléchargé, on garde l’entrée mais on note le filtre)
                        row["kept_by_year_filter"] = str(keep)
                        w.writerow(row)
                        continue

                    local_name = safe_filename(
                        Path(urlparse(abs_url).path).name or "document.pdf"
                    )
                    local_pdf = pdf_dir / local_name

                    # Téléchargement conditionnel: on préfère télécharger si dans période; si pas de date, on télécharge aussi
                    http_status = ""
                    if keep or (guessed_date is None):
                        try:
                            r = session.get(abs_url, timeout=60)
                            http_status = str(r.status_code)
                            if r.status_code == 200 and r.headers.get(
                                "Content-Type", ""
                            ).lower().startswith("application/pdf"):
                                with open(local_pdf, "wb") as outf:
                                    outf.write(r.content)
                            else:
                                # Contenu pas PDF: ignorer
                                local_pdf = Path("")
                        except Exception as e:
                            http_status = f"ERROR:{e}"
                            local_pdf = Path("")
                    else:
                        http_status = "SKIPPED_BY_YEAR_FILTER"
                        local_pdf = Path("")

                    # Extraction texte (si PDF dispo)
                    local_txt = Path("")
                    if local_pdf and local_pdf.exists():
                        text = extract_pdf_text(local_pdf)
                        if text:
                            local_txt = txt_dir / (local_pdf.stem + ".txt")
                            with open(local_txt, "w", encoding="utf-8") as ft:
                                ft.write(text)

                    row = {
                        "url": abs_url,
                        "local_pdf": str(local_pdf) if str(local_pdf) else "",
                        "local_txt": str(local_txt) if str(local_txt) else "",
                        "http_status": http_status,
                        "guessed_date": guessed_date.isoformat()
                        if guessed_date
                        else "",
                        "kept_by_year_filter": str(keep),
                        "title_or_anchor": title,
                        "source_page": page_url,
                    }
                    w.writerow(row)

        pbar.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--start-urls",
        nargs="+",
        required=True,
        help="URLs de départ (pages listant les conseils municipaux).",
    )
    ap.add_argument("--out-dir", default="data_taluyers")
    ap.add_argument("--from-year", type=int, default=2014)
    ap.add_argument("--to-year", type=int, default=2025)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    crawl_and_download(args.start_urls, out_dir, args.from_year, args.to_year)
