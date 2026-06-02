-- ─────────────────────────────────────────────────────────────────────────────
-- SNAP Adequacy Analyzer — SQL Analysis
-- SQLite compatible — run with: python3 run_queries.py
--
-- Core concept:
--   SNAP pays a flat national benefit. Food costs vary by state.
--   food_price_index = BEA Regional Price Parities (Goods), national avg = 100
--   gap_4 = what a family of 4 needs vs what they get ($)
--     positive = underfunded, negative = overfunded
-- ─────────────────────────────────────────────────────────────────────────────


-- Q1: National Overview
-- How many states are underfunded, and what's the total cost to fix it?
SELECT
    COUNT(*)                                                                AS total_states_dc,
    SUM(CASE WHEN gap_4 > 0  AND snap_adjusted = 'No' THEN 1 ELSE 0 END)  AS underfunded_states,
    SUM(CASE WHEN gap_4 <= 0 AND snap_adjusted = 'No' THEN 1 ELSE 0 END)  AS adequate_or_overfunded,
    SUM(CASE WHEN snap_adjusted = 'Yes'               THEN 1 ELSE 0 END)  AS already_adjusted,
    ROUND(AVG(CASE WHEN snap_adjusted = 'No' THEN food_price_index END), 1) AS avg_food_price_index,
    ROUND(SUM(annual_cost_billions), 2)                                    AS total_extra_cost_billions
FROM gap_analysis;


-- Q2: Full gap analysis — all 48 contiguous states + DC
-- Shows every state's food price index, current benefit, what it should be, and the gap
SELECT
    state,
    state_code,
    region,
    food_price_index,
    benefit_4                                                    AS current_benefit,
    adjusted_benefit_4                                           AS benefit_needed,
    gap_4                                                        AS monthly_gap,
    gap_per_person                                               AS gap_per_person_monthly,
    snap_participants_thousands,
    poverty_rate,
    adequacy_status
FROM gap_analysis
WHERE snap_adjusted = 'No'
ORDER BY gap_4 DESC;


-- Q3: Top 10 most underfunded states
-- These are the states where SNAP buys the least food relative to actual prices
SELECT
    state,
    state_code,
    region,
    food_price_index,
    benefit_4                  AS current_benefit,
    adjusted_benefit_4         AS benefit_needed,
    gap_4                      AS monthly_gap,
    snap_participants_thousands,
    poverty_rate,
    annual_cost_billions
FROM gap_analysis
WHERE snap_adjusted = 'No'
  AND gap_4 > 0
ORDER BY gap_4 DESC
LIMIT 10;


-- Q4: Top 10 most overfunded states
-- States where the flat benefit exceeds the local cost of the Thrifty Food Plan
SELECT
    state,
    state_code,
    region,
    food_price_index,
    benefit_4           AS current_benefit,
    adjusted_benefit_4  AS benefit_needed,
    gap_4               AS monthly_gap,
    snap_participants_thousands,
    poverty_rate
FROM gap_analysis
WHERE snap_adjusted = 'No'
  AND gap_4 < 0
ORDER BY gap_4 ASC
LIMIT 10;


-- Q5: Regional summary
-- Which regions have the worst adequacy problem on average?
SELECT
    region,
    COUNT(*)                                                     AS states,
    ROUND(AVG(food_price_index), 1)                              AS avg_food_index,
    ROUND(AVG(gap_4), 2)                                         AS avg_monthly_gap,
    SUM(snap_participants_thousands)                             AS total_participants_k,
    ROUND(AVG(poverty_rate), 1)                                  AS avg_poverty_rate,
    ROUND(SUM(annual_cost_billions), 3)                          AS extra_cost_billions
FROM gap_analysis
WHERE snap_adjusted = 'No'
GROUP BY region
ORDER BY avg_monthly_gap DESC;


-- Q6: Adequacy status breakdown
-- How many states fall into each category?
SELECT
    adequacy_status,
    COUNT(*)                             AS states,
    SUM(snap_participants_thousands)     AS participants_thousands,
    ROUND(AVG(gap_4), 2)                 AS avg_monthly_gap,
    ROUND(SUM(annual_cost_billions), 3)  AS extra_cost_billions
FROM gap_analysis
GROUP BY adequacy_status
ORDER BY avg_monthly_gap DESC;


-- Q7: Cost of full adequacy
-- If we closed 100% of the gap for all underfunded states, what would it cost?
SELECT
    ROUND(SUM(annual_cost_billions), 2)          AS total_extra_cost_billions,
    SUM(CASE WHEN gap_4 > 0
             THEN snap_participants_thousands
             ELSE 0 END)                          AS affected_participants_thousands,
    COUNT(CASE WHEN gap_4 > 0 THEN 1 END)         AS underfunded_state_count
FROM gap_analysis
WHERE snap_adjusted = 'No';


-- Q8: Proposed benefit vs current benefit (top 10 underfunded)
-- Shows the concrete dollar change this policy would produce
SELECT
    state,
    state_code,
    benefit_4                                          AS current_monthly_benefit,
    adjusted_benefit_4                                 AS proposed_monthly_benefit,
    gap_4                                              AS monthly_increase,
    ROUND(gap_4 * 12, 2)                               AS annual_increase_per_hh,
    snap_participants_thousands,
    annual_cost_billions
FROM gap_analysis
WHERE snap_adjusted = 'No'
  AND gap_4 > 0
ORDER BY gap_4 DESC
LIMIT 10;
