# Politics in Taluyers

I live in Taluyers. I create software for the living. I can better understand things with data.
So I wrote these scripts, to get a grasp of what is the politics in Taluyers (given that next March we'll have to take a decision).

This is actually work in progress, I will update this file as the data flows.

## Time spans

The data covers the last 10 years - hence three different councils. The presence rate may be quite meaningless because the people in charge has changed.
We can say that Brachet, Jullian, Outrebon, Tamisier, Siché Chol, Courbon, Miotto were certainly elected over the last three mandates.
The presences.csv is better at visualizing when the mandates changed.

```sh
uv run python build_presence_matrix.py data_taluyers/json -o presence.csv
```

```
OK: presence.csv écrit (42 élus × 93 séances).
Légende: présent = 1, absent = 0

--- Recap présence (93 séances) ---
BRACHET                         90 / 93 ( 96.8%)
JULLIAN                         90 / 93 ( 96.8%)
OUTREBON                        89 / 93 ( 95.7%)
TAMISIER                        89 / 93 ( 95.7%)
SICHECHOL                       88 / 93 ( 94.6%)
COURBON                         87 / 93 ( 93.5%)
MIOTTO                          85 / 93 ( 91.4%)
CUBLIER                         67 / 93 ( 72.0%)
FONS                            65 / 93 ( 69.9%)
MICHALLET                       65 / 93 ( 69.9%)
BERTHOUD                        51 / 93 ( 54.8%)
NAULIN                          51 / 93 ( 54.8%)
ROUAND                          51 / 93 ( 54.8%)
RAVET                           50 / 93 ( 53.8%)
GUITTET                         45 / 93 ( 48.4%)
NAVARRO                         45 / 93 ( 48.4%)
VIOLLET                         44 / 93 ( 47.3%)
CASCHETTA                       41 / 93 ( 44.1%)
GRAU                            39 / 93 ( 41.9%)
MONTCEL                         39 / 93 ( 41.9%)
TREVISANI                       39 / 93 ( 41.9%)
DANIEL                          38 / 93 ( 40.9%)
PETIT                           37 / 93 ( 39.8%)
ROMANCLAVELLOUX                 37 / 93 ( 39.8%)
SICARD                          36 / 93 ( 38.7%)
GOUTTENOIRE                     33 / 93 ( 35.5%)
SEGURA                          27 / 93 ( 29.0%)
MARCONNET                       25 / 93 ( 26.9%)
FORISSIER                       13 / 93 ( 14.0%)
JOUFFRE                         12 / 93 ( 12.9%)
LEMARCHAND                       8 / 93 (  8.6%)
SAYERCORTAZZI                    8 / 93 (  8.6%)
PATRIER                          6 / 93 (  6.5%)
CHAPUT                           2 / 93 (  2.2%)
CHOLLET                          2 / 93 (  2.2%)
MARY                             2 / 93 (  2.2%)
MICHAUDON                        2 / 93 (  2.2%)
ROUXLAFORIE                      2 / 93 (  2.2%)
CHAIZE                           1 / 93 (  1.1%)
FERRARI                          0 / 93 (  0.0%)
LAMOUILLE                        0 / 93 (  0.0%)
VERPILLIEUX                      0 / 93 (  0.0%)
```

Donc la palme de la présence revient à Odile Brachet et Charles Jullian. Bravo!

## Déliberations

```sh
uv run deliberations.py > deliberations.md
```

Au cours de 10 années ont été voté 868 déliberations différentes.
Seules 51 d'entre elles n'ont pas obtenu la majorité, concentrées sur 31 séances.

```
2025: 3 séances conflictuelles
2024: 1 séances conflictuelles
2023: 1 séances conflictuelles
2022: 5 séances conflictuelles
2021: 3 séances conflictuelles
2020: 5 séances conflictuelles
2018: 2 séances conflictuelles
2017: 3 séances conflictuelles
2016: 4 séances conflictuelles
2015: 2 séances conflictuelles
2014: 2 séances conflictuelles
```

2020 et 2022 ont été les pires années.

Conflictuel est un mauvais terme: il identifie les délibérations n'ayant pas été votées à l'unanimité. Mais ces délibérations incluent également les sessions avec abstenus (qui n'ont pas voulu prendre part au vote étant donné un potentiel conflit d'intérêts).
