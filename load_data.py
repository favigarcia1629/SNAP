"""
SNAP Adequacy Analyzer — Data Loader
Run once to build snap_adequacy.db from source CSVs.
Usage: python3 load_data.py
"""
import os
import sqlite3
import pandas as pd

BASE    = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "snap_adequacy.db")
DATA    = os.path.join(BASE, "data")


def load():
    conn = sqlite3.connect(DB_PATH)

    # ── snap_allotments ───────────────────────────────────────────────────────
    df_allot = pd.read_csv(os.path.join(DATA, "snap_allotments.csv"))
    df_allot.to_sql("snap_allotments", conn, if_exists="replace", index=False)
    print(f"  snap_allotments : {len(df_allot)} rows")

    # ── state_data ────────────────────────────────────────────────────────────
    df_state = pd.read_csv(os.path.join(DATA, "state_data.csv"))
    df_state.to_sql("state_data", conn, if_exists="replace", index=False)
    print(f"  state_data      : {len(df_state)} rows")

    # ── gap_analysis view ─────────────────────────────────────────────────────
    # The core calculation:
    #   adjusted_benefit = current_benefit × (food_price_index / 100)
    #   gap              = adjusted_benefit - current_benefit
    #
    # Positive gap  → underfunded  (food costs MORE than the flat benefit covers)
    # Negative gap  → overfunded   (benefit exceeds actual food cost in that state)
    conn.execute("DROP VIEW IF EXISTS gap_analysis")
    conn.execute("""
        CREATE VIEW gap_analysis AS
        SELECT
            s.state,
            s.state_code,
            s.food_price_index,
            s.snap_participants_thousands,
            s.poverty_rate,
            s.region,
            s.snap_adjusted,

            -- ── Household of 1 ──────────────────────────────────────────────
            292.0                                                           AS benefit_1,
            ROUND(292.0 * (s.food_price_index / 100.0), 2)                 AS adjusted_benefit_1,
            ROUND(292.0 * (s.food_price_index / 100.0) - 292.0, 2)        AS gap_1,

            -- ── Household of 4 (primary benchmark) ─────────────────────────
            975.0                                                           AS benefit_4,
            ROUND(975.0 * (s.food_price_index / 100.0), 2)                 AS adjusted_benefit_4,
            ROUND(975.0 * (s.food_price_index / 100.0) - 975.0, 2)        AS gap_4,

            -- ── Per-person monthly gap ──────────────────────────────────────
            ROUND((975.0 * (s.food_price_index / 100.0) - 975.0) / 4.0, 2) AS gap_per_person,

            -- ── Annual additional federal cost (billions) ───────────────────
            -- Only positive gaps cost money — we never reduce existing benefits
            ROUND(
                CASE WHEN (975.0 * (s.food_price_index / 100.0) - 975.0) > 0
                     THEN (975.0 * (s.food_price_index / 100.0) - 975.0) / 4.0
                          * s.snap_participants_thousands * 1000.0 * 12.0 / 1e9
                     ELSE 0.0 END,
                3
            ) AS annual_cost_billions,

            -- ── Adequacy label ──────────────────────────────────────────────
            CASE
                WHEN s.snap_adjusted = 'Yes'                                   THEN 'Already Adjusted'
                WHEN (975.0 * (s.food_price_index / 100.0) - 975.0) >  50     THEN 'Severely Underfunded'
                WHEN (975.0 * (s.food_price_index / 100.0) - 975.0) >   0     THEN 'Underfunded'
                WHEN (975.0 * (s.food_price_index / 100.0) - 975.0) > -30     THEN 'Near Adequate'
                ELSE                                                                 'Overfunded'
            END AS adequacy_status

        FROM state_data s
    """)

    conn.commit()
    conn.close()
    print("  gap_analysis view created")
    print(f"\nDatabase saved → {DB_PATH}")


if __name__ == "__main__":
    print("Loading data...")
    load()
