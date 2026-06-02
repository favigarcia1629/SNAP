"""
SNAP Adequacy Analyzer — Query Runner
Runs all SQL queries and exports results as CSVs to exports/
Usage: python3 run_queries.py
"""
import os
import sqlite3
import pandas as pd

BASE    = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE, "snap_adequacy.db")
OUT_DIR = os.path.join(BASE, "exports")
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)


def save(df, filename, label):
    path = os.path.join(OUT_DIR, filename)
    df.to_csv(path, index=False)
    print(f"  {label:<40} → {filename}  ({len(df)} rows)")


print("Running SNAP adequacy queries...\n")

# Q1: National overview
save(pd.read_sql_query("""
    SELECT
        COUNT(*) AS total_states_dc,
        SUM(CASE WHEN gap_4 > 0  AND snap_adjusted = 'No' THEN 1 ELSE 0 END) AS underfunded_states,
        SUM(CASE WHEN gap_4 <= 0 AND snap_adjusted = 'No' THEN 1 ELSE 0 END) AS adequate_or_overfunded,
        SUM(CASE WHEN snap_adjusted = 'Yes' THEN 1 ELSE 0 END)               AS already_adjusted,
        ROUND(AVG(CASE WHEN snap_adjusted = 'No' THEN food_price_index END), 1) AS avg_food_price_index,
        ROUND(SUM(annual_cost_billions), 2) AS total_extra_cost_billions
    FROM gap_analysis
""", conn), "q1_national_overview.csv", "Q1  National overview")

# Q2: Full gap analysis
save(pd.read_sql_query("""
    SELECT state, state_code, region, food_price_index,
           benefit_4 AS current_benefit, adjusted_benefit_4 AS benefit_needed,
           gap_4 AS monthly_gap, gap_per_person AS gap_per_person_monthly,
           snap_participants_thousands, poverty_rate, adequacy_status
    FROM gap_analysis
    WHERE snap_adjusted = 'No'
    ORDER BY gap_4 DESC
""", conn), "q2_full_gap_analysis.csv", "Q2  Full gap analysis (48+DC)")

# Q3: Top 10 underfunded
save(pd.read_sql_query("""
    SELECT state, state_code, region, food_price_index,
           benefit_4 AS current_benefit, adjusted_benefit_4 AS benefit_needed,
           gap_4 AS monthly_gap, snap_participants_thousands, poverty_rate,
           annual_cost_billions
    FROM gap_analysis
    WHERE snap_adjusted = 'No' AND gap_4 > 0
    ORDER BY gap_4 DESC
    LIMIT 10
""", conn), "q3_top10_underfunded.csv", "Q3  Top 10 most underfunded")

# Q4: Top 10 overfunded
save(pd.read_sql_query("""
    SELECT state, state_code, region, food_price_index,
           benefit_4 AS current_benefit, adjusted_benefit_4 AS benefit_needed,
           gap_4 AS monthly_gap, snap_participants_thousands, poverty_rate
    FROM gap_analysis
    WHERE snap_adjusted = 'No' AND gap_4 < 0
    ORDER BY gap_4 ASC
    LIMIT 10
""", conn), "q4_top10_overfunded.csv", "Q4  Top 10 most overfunded")

# Q5: Regional summary
save(pd.read_sql_query("""
    SELECT region, COUNT(*) AS states,
           ROUND(AVG(food_price_index), 1) AS avg_food_index,
           ROUND(AVG(gap_4), 2) AS avg_monthly_gap,
           SUM(snap_participants_thousands) AS total_participants_k,
           ROUND(AVG(poverty_rate), 1) AS avg_poverty_rate,
           ROUND(SUM(annual_cost_billions), 3) AS extra_cost_billions
    FROM gap_analysis
    WHERE snap_adjusted = 'No'
    GROUP BY region
    ORDER BY avg_monthly_gap DESC
""", conn), "q5_regional_summary.csv", "Q5  Regional summary")

# Q6: Adequacy status breakdown
save(pd.read_sql_query("""
    SELECT adequacy_status, COUNT(*) AS states,
           SUM(snap_participants_thousands) AS participants_thousands,
           ROUND(AVG(gap_4), 2) AS avg_monthly_gap,
           ROUND(SUM(annual_cost_billions), 3) AS extra_cost_billions
    FROM gap_analysis
    GROUP BY adequacy_status
    ORDER BY avg_monthly_gap DESC
""", conn), "q6_adequacy_status.csv", "Q6  Adequacy status breakdown")

# Q7: Cost of full adequacy
save(pd.read_sql_query("""
    SELECT
        ROUND(SUM(annual_cost_billions), 2) AS total_extra_cost_billions,
        SUM(CASE WHEN gap_4 > 0 THEN snap_participants_thousands ELSE 0 END) AS affected_participants_thousands,
        COUNT(CASE WHEN gap_4 > 0 THEN 1 END) AS underfunded_state_count
    FROM gap_analysis
    WHERE snap_adjusted = 'No'
""", conn), "q7_cost_of_full_adequacy.csv", "Q7  Cost of full adequacy")

# Q8: Proposed vs current benefit (top 10)
save(pd.read_sql_query("""
    SELECT state, state_code,
           benefit_4 AS current_monthly_benefit,
           adjusted_benefit_4 AS proposed_monthly_benefit,
           gap_4 AS monthly_increase,
           ROUND(gap_4 * 12, 2) AS annual_increase_per_hh,
           snap_participants_thousands, annual_cost_billions
    FROM gap_analysis
    WHERE snap_adjusted = 'No' AND gap_4 > 0
    ORDER BY gap_4 DESC
    LIMIT 10
""", conn), "q8_proposed_benefits.csv", "Q8  Proposed vs current (top 10)")

conn.close()
print("\nAll exports saved to exports/")
