# SNAP Adequacy Analyzer

**Does SNAP pay enough — and does the answer change by state?**

The federal government pays the same SNAP benefit in every state. A family of 4 in Mississippi receives the same $975/month as a family in New York City. But food costs are not the same. This project measures the adequacy gap and models what a geographic adjustment would cost.

**[Live Dashboard →](https://xmsq6runmevuki9slx2ixn.streamlit.app/)**

---

## The Policy Gap

SNAP's maximum benefit equals the USDA Thrifty Food Plan (TFP) — the estimated minimum cost of a nutritious diet. The TFP is set as a **flat national rate**, with two exceptions: Hawaii and Alaska already receive geographic adjustments.

The 48 contiguous states + DC get identical benefits despite food cost variations of up to 17% above or below the national average (BEA Regional Price Parities, 2022).

---

## Key Findings

| Finding | Result |
|---|---|
| States underfunded (gap > 0) | 21 states + DC |
| States overfunded (gap < 0) | 27 states |
| Most underfunded state | New York (+$107/mo for family of 4) |
| Most overfunded state | Mississippi (-$64/mo for family of 4) |
| Cost of 50% geographic adjustment | ~$2.0B/year |
| Cost of 100% geographic adjustment | ~$4.0B/year |

---

## Project Structure

```
snap_adequacy/
├── data/
│   ├── snap_allotments.csv     # USDA FY2025 SNAP maximum benefits by household size
│   └── state_data.csv          # BEA price parities, SNAP participation, poverty rates
├── analysis.sql                # SQL queries: gap analysis, top 10, regional, cost
├── snap_adequacy.db            # SQLite database (gitignored)
├── load_data.py                # Builds DB from CSVs — run once
├── run_queries.py              # Runs SQL queries, exports CSVs to exports/
├── app.py                      # Streamlit dashboard
├── requirements.txt
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
python3 load_data.py      # builds snap_adequacy.db
python3 run_queries.py    # exports analysis CSVs
streamlit run app.py      # launches dashboard
```

---

## Methodology

**Food Price Index:** BEA Regional Price Parities (Goods component), 2022. National average = 100.

**Gap formula:**
```
Adjusted benefit = Current SNAP benefit × (State Food Price Index / 100)
Gap              = Adjusted benefit − Current benefit
```

- **Positive gap** → state is underfunded (food costs more than the benefit covers)
- **Negative gap** → state is overfunded (benefit exceeds actual food cost)

**Policy proposal:** Apply a state-level multiplier to SNAP benefits based on BEA price parities. Benefits are only ever increased — no state's benefit is reduced.

---

## Data Sources

| Source | Data |
|---|---|
| USDA FNS | SNAP maximum allotments (FY2025) |
| BEA | Regional Price Parities — Goods component (2022) |
| Census ACS | State poverty rates (2022) |
| USDA FNS | SNAP participation by state (FY2022) |

---

*Built for research and education. Not financial or policy advice.*
