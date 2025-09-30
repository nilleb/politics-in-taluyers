import glob
import json
import os
from collections import defaultdict
from typing import Any

SAMPLE_DELIBERATION = {
    "id": "20140908-01",
    "titre": "Agencement intérieur des locaux commerciaux",
    "resume": "Attribution du marché d'agencement intérieur des locaux commerciaux au rez-de-chaussée Place de la Bascule.",
    "themes": ["urbanisme"],
    "vote": {
        "mode": "UNANIMITE",
        "detail": {"POUR": [], "CONTRE": [], "ABSTENTION": []},
        "compteur": {"pour": 19, "contre": 0, "abstention": 0},
    },
    "page_approx": None,
    "notes": None,
}


def safe_get(d: dict, key: str, default: Any):
    return d.get(key, default) or default


total_deliberations = 0
conflictual_deliberations = defaultdict(list)
for fpath in glob.glob("data_taluyers/json/*.json"):
    with open(fpath, "r") as fd:
        data = json.load(fd)
    deliberations = data.get("deliberations")
    total_deliberations += len(deliberations)
    for deliberation in deliberations:
        vote = deliberation.get("vote")
        mode = vote.get("mode")
        if mode != "UNANIMITE":
            fname = os.path.basename(fpath)
            dt = data.get("seance").get("date")
            conflictual_deliberations[dt].append(
                {
                    "date": dt,
                    "fpath": fpath,
                    "mode": mode,
                    "titre": deliberation.get("titre"),
                    "pour": {
                        "count": safe_get(vote, "compteur", {}).get("pour"),
                        "detail": vote.get("detail").get("POUR"),
                    },
                    "contre": {
                        "count": safe_get(vote, "compteur", {}).get("contre"),
                        "detail": vote.get("detail").get("CONTRE"),
                    },
                    "abstention": {
                        "count": safe_get(vote, "compteur", {}).get("abstention"),
                        "detail": vote.get("detail").get("ABSTENTION"),
                    },
                }
            )

count = 0
per_year = defaultdict(int)
for key in sorted(conflictual_deliberations.keys(), reverse=1):
    print(f"# {key}")
    for cd in conflictual_deliberations[key]:
        print(f"## {cd.get('titre')} ({cd.get('fpath')})")
        print(f"{cd.get('mode')}")
        print(f" - contre: {cd.get('contre')}")
        print(f" - pour: {cd.get('pour')}")
        print(f" - abstention: {cd.get('abstention')}")
    print("\n")
    per_year[key[:4]] += 1
    count += len(conflictual_deliberations[key])

print(
    f"Total Séances conflictuelles: {len(conflictual_deliberations)}, total déliberations conflictuelles {count}, total délibérations: {total_deliberations}"
)

print("Par année")
for key, value in per_year.items():
    print(f"{key}: {value} séances conflictuelles")
