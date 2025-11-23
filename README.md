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
OK: presence.csv écrit (42 élus × 93 séances).
Légende: présent = 1, absent = 0

--- Recap présence (93 séances) ---
Elu                               Total   Pct M1   Pct M2   Pct M3
----------------------------------------------------------------------
BRACHET                         90/ 93 (96.8%)  100.0%  100.0%   94.5%
JULLIAN                         90/ 93 (96.8%)  100.0%   97.2%   96.4%
OUTREBON                        89/ 93 (95.7%)  100.0%  100.0%   92.7%
TAMISIER                        89/ 93 (95.7%)    0.0%  100.0%   96.4%
SICHECHOL                       88/ 93 (94.6%)    0.0%  100.0%   94.5%
COURBON                         87/ 93 (93.5%)  100.0%   91.7%   94.5%
MIOTTO                          85/ 93 (91.4%)  100.0%   91.7%   90.9%
CUBLIER                         67/ 93 (72.0%)   50.0%   80.6%   67.3%
FONS                            65/ 93 (69.9%)  100.0%  100.0%   49.1%
MICHALLET                       65/ 93 (69.9%)    0.0%   41.7%   90.9%
BERTHOUD                        51/ 93 (54.8%)    0.0%    0.0%   92.7%
NAULIN                          51/ 93 (54.8%)    0.0%    0.0%   92.7%
ROUAND                          51/ 93 (54.8%)    0.0%    0.0%   92.7%
RAVET                           50/ 93 (53.8%)    0.0%    0.0%   90.9%
GUITTET                         45/ 93 (48.4%)    0.0%    0.0%   81.8%
NAVARRO                         45/ 93 (48.4%)    0.0%    0.0%   81.8%
VIOLLET                         44/ 93 (47.3%)    0.0%    0.0%   80.0%
CASCHETTA                       41/ 93 (44.1%)    0.0%    0.0%   74.5%
GRAU                            39/ 93 (41.9%)    0.0%    0.0%   70.9%
MONTCEL                         39/ 93 (41.9%)    0.0%    0.0%   70.9%
TREVISANI                       39/ 93 (41.9%)  100.0%  100.0%    1.8%
DANIEL                          38/ 93 (40.9%)  100.0%  100.0%    0.0%
PETIT                           37/ 93 (39.8%)    0.0%   97.2%    3.6%
ROMANCLAVELLOUX                 37/ 93 (39.8%)  100.0%   91.7%    3.6%
SICARD                          36/ 93 (38.7%)    0.0%   94.4%    3.6%
GOUTTENOIRE                     33/ 93 (35.5%)    0.0%   86.1%    3.6%
SEGURA                          27/ 93 (29.0%)    0.0%   75.0%    0.0%
MARCONNET                       25/ 93 (26.9%)    0.0%   69.4%    0.0%
FORISSIER                       13/ 93 (14.0%)    0.0%   36.1%    0.0%
JOUFFRE                         12/ 93 (12.9%)    0.0%    0.0%   21.8%
LEMARCHAND                       8/ 93 ( 8.6%)    0.0%    0.0%   14.5%
SAYERCORTAZZI                    8/ 93 ( 8.6%)    0.0%    0.0%   14.5%
PATRIER                          6/ 93 ( 6.5%)    0.0%    0.0%   10.9%
CHAPUT                           2/ 93 ( 2.2%)  100.0%    0.0%    0.0%
CHOLLET                          2/ 93 ( 2.2%)  100.0%    0.0%    0.0%
MARY                             2/ 93 ( 2.2%)  100.0%    0.0%    0.0%
MICHAUDON                        2/ 93 ( 2.2%)  100.0%    0.0%    0.0%
ROUXLAFORIE                      2/ 93 ( 2.2%)  100.0%    0.0%    0.0%
CHAIZE                           1/ 93 ( 1.1%)    0.0%    0.0%    1.8%
FERRARI                          0/ 93 ( 0.0%)    0.0%    0.0%    0.0%
LAMOUILLE                        0/ 93 ( 0.0%)    0.0%    0.0%    0.0%
VERPILLIEUX                      0/ 93 ( 0.0%)    0.0%    0.0%    0.0%
```

Donc la palme de la présence revient à Odile Brachet et Charles Jullian. Bravo!

Pour une visualisation amélioré, il y a aussi [ce Google Spreadsheet](https://docs.google.com/spreadsheets/d/1ROild1SIDdJA6udKDhdlJ6ol0SaCYrStdaPG_rscMss/edit?usp=sharing).

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
