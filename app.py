"""
SNAP Adequacy Analyzer — Streamlit Dashboard
Usage: streamlit run app.py
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SNAP Adequacy Analyzer",
    page_icon="🥗",
    layout="wide",
)

DB_PATH = Path(__file__).parent / "snap_adequacy.db"

# ── Colors ────────────────────────────────────────────────────────────────────
RED    = "#EF4444"
GREEN  = "#22C55E"
BLUE   = "#3B82F6"
ORANGE = "#F97316"
YELLOW = "#FACC15"
GRAY   = "#6B7280"
LIGHT  = "#F3F4F6"
DARK   = "#111827"

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df        = pd.read_sql("SELECT * FROM gap_analysis", conn)
    allotments = pd.read_sql("SELECT * FROM snap_allotments", conn)
    conn.close()
    return df, allotments

df, allotments = load_data()
df_48 = df[df["snap_adjusted"] == "No"].copy()

BENEFIT_MAP = dict(zip(allotments["household_size"], allotments["monthly_benefit"]))

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🥗 SNAP Adequacy")
    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "SNAP pays a **flat national benefit** to every state. But food costs vary "
        "significantly by location. This tool measures the adequacy gap and models "
        "the cost of a geographic adjustment."
    )
    st.markdown("---")
    st.markdown("### Methodology")
    st.markdown(
        "**Food Price Index:** BEA Regional Price Parities (Goods component), "
        "2022. National average = 100.\n\n"
        "**Gap formula:**\n"
        "```\n"
        "Adjusted benefit = Current benefit\n"
        "                 × (Food Price Index / 100)\n\n"
        "Gap = Adjusted benefit − Current benefit\n"
        "```\n"
        "Positive gap → underfunded  \n"
        "Negative gap → overfunded"
    )
    st.markdown("---")
    st.markdown("### Data Sources")
    st.markdown(
        "- USDA FNS — SNAP allotments (FY2025)\n"
        "- BEA — Regional Price Parities\n"
        "- Census ACS — State poverty rates\n"
        "- USDA FNS — SNAP participation by state"
    )
    st.markdown("---")
    st.caption("Built for research and education. Not financial or policy advice.")

# ── Page Title ────────────────────────────────────────────────────────────────
st.title("🥗 SNAP Adequacy Analyzer")
st.markdown(
    "**The federal government pays the same SNAP benefit in every state.** "
    "A family of 4 in Mississippi gets exactly the same $975/month as a family in New York City. "
    "But food costs are not the same. This dashboard measures the gap — and proposes a fix."
)
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 National Overview",
    "🗺️ Gap Map",
    "🏆 Top 10 Analysis",
    "⚙️ Policy Simulator",
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — NATIONAL OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    underfunded = df_48[df_48["gap_4"] > 0]
    overfunded  = df_48[df_48["gap_4"] < 0]
    near_adeq   = df_48[df_48["gap_4"] == 0]

    total_cost   = underfunded["annual_cost_billions"].sum()
    affected_k   = underfunded["snap_participants_thousands"].sum()
    avg_gap_under = underfunded["gap_4"].mean()
    avg_gap_over  = overfunded["gap_4"].mean()

    # ── KPI tiles ─────────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("States Underfunded",    f"{len(underfunded)}")
    k2.metric("States Overfunded",     f"{len(overfunded)}")
    k3.metric("Avg Monthly Gap (Under)", f"${avg_gap_under:+.0f}")
    k4.metric("Avg Monthly Gap (Over)",  f"${avg_gap_over:+.0f}")
    k5.metric("Cost of Full Adequacy", f"${total_cost:.1f}B / yr")

    st.markdown("---")

    # ── Adequacy status breakdown ──────────────────────────────────────────────
    col_a, col_b = st.columns([1.2, 1])

    with col_a:
        st.subheader("Monthly Adequacy Gap — All States")
        st.caption("Sorted by gap: most underfunded (top) to most overfunded (bottom). "
                   "Hawaii and Alaska already receive geographic adjustments from USDA.")

        display_cols = ["state", "region", "food_price_index",
                        "benefit_4", "adjusted_benefit_4", "gap_4", "adequacy_status"]
        labels = {
            "state": "State", "region": "Region",
            "food_price_index": "Food Price Index",
            "benefit_4": "Current Benefit ($)",
            "adjusted_benefit_4": "Benefit Needed ($)",
            "gap_4": "Monthly Gap ($)",
            "adequacy_status": "Status",
        }

        styled = df_48[display_cols].sort_values("gap_4", ascending=False).rename(columns=labels)

        def color_gap(val):
            if val > 30:
                return f"background-color: #FEE2E2; color: {DARK}"
            elif val > 0:
                return f"background-color: #FEF3C7; color: {DARK}"
            elif val > -30:
                return f"background-color: #F0FDF4; color: {DARK}"
            else:
                return f"background-color: #DCFCE7; color: {DARK}"

        st.dataframe(
            styled.style.map(color_gap, subset=["Monthly Gap ($)"]),
            height=480,
            use_container_width=True,
        )

    with col_b:
        st.subheader("Status Breakdown")
        status_counts = df["adequacy_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        color_map = {
            "Severely Underfunded": RED,
            "Underfunded": ORANGE,
            "Near Adequate": YELLOW,
            "Overfunded": GREEN,
            "Already Adjusted": BLUE,
        }
        fig_pie = px.pie(
            status_counts,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map=color_map,
            hole=0.45,
        )
        fig_pie.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(font=dict(size=11)),
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Regional Average Gap")
        reg = df_48.groupby("region").agg(
            avg_gap=("gap_4", "mean"),
            states=("state", "count"),
        ).reset_index().sort_values("avg_gap", ascending=False)

        fig_reg = px.bar(
            reg, x="region", y="avg_gap", color="avg_gap",
            color_continuous_scale=[[0, GREEN], [0.5, YELLOW], [1, RED]],
            color_continuous_midpoint=0,
            labels={"avg_gap": "Avg Monthly Gap ($)", "region": "Region"},
            text=reg["avg_gap"].apply(lambda x: f"${x:+.0f}"),
        )
        fig_reg.update_traces(textposition="outside")
        fig_reg.update_layout(
            coloraxis_showscale=False,
            margin=dict(t=10, b=10),
            xaxis_title=None,
        )
        st.plotly_chart(fig_reg, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — GAP MAP
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Monthly Adequacy Gap by State — Family of 4")
    st.caption(
        "**Red** = SNAP benefit falls short of actual food costs (underfunded). "
        "**Green** = benefit exceeds food costs (overfunded). "
        "Gray states (HI, AK) already receive SNAP geographic adjustments."
    )

    max_abs = max(abs(df_48["gap_4"].min()), abs(df_48["gap_4"].max()))

    fig_map = px.choropleth(
        df,
        locations="state_code",
        locationmode="USA-states",
        color="gap_4",
        color_continuous_scale=[[0, GREEN], [0.5, "#F9FAFB"], [1, RED]],
        color_continuous_midpoint=0,
        range_color=[-max_abs, max_abs],
        scope="usa",
        hover_name="state",
        hover_data={
            "state_code": False,
            "gap_4": ":.0f",
            "food_price_index": ":.1f",
            "adjusted_benefit_4": ":.0f",
            "snap_participants_thousands": ":.0f",
            "adequacy_status": True,
        },
        labels={
            "gap_4": "Monthly Gap ($)",
            "food_price_index": "Food Price Index",
            "adjusted_benefit_4": "Benefit Needed ($)",
            "snap_participants_thousands": "Participants (000s)",
            "adequacy_status": "Status",
        },
    )
    fig_map.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        coloraxis_colorbar=dict(
            title="Monthly Gap ($)",
            tickprefix="$",
            len=0.6,
        ),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        height=500,
    )
    st.plotly_chart(fig_map, use_container_width=True)

    # ── Food price index map ──────────────────────────────────────────────────
    st.subheader("Food Price Index by State (BEA Regional Price Parities)")
    st.caption("National average = 100. States above 100 have above-average food costs.")

    fig_idx = px.choropleth(
        df,
        locations="state_code",
        locationmode="USA-states",
        color="food_price_index",
        color_continuous_scale="Blues",
        range_color=[90, 115],
        scope="usa",
        hover_name="state",
        hover_data={"state_code": False, "food_price_index": ":.1f", "region": True},
        labels={"food_price_index": "Food Price Index"},
    )
    fig_idx.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        coloraxis_colorbar=dict(title="Price Index", len=0.6),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
        height=480,
    )
    st.plotly_chart(fig_idx, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — TOP 10 ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    top_under = df_48.nlargest(10, "gap_4")
    top_over  = df_48.nsmallest(10, "gap_4")

    st.subheader("10 Most Underfunded States — SNAP Buys the Least Here")
    st.caption(
        "These states have above-average food costs but receive the same flat national benefit. "
        "A family of 4 in these states cannot buy the Thrifty Food Plan with their current SNAP benefit."
    )

    col1, col2 = st.columns(2)

    with col1:
        fig_under = go.Figure(go.Bar(
            x=top_under["gap_4"],
            y=top_under["state"],
            orientation="h",
            marker_color=RED,
            text=top_under["gap_4"].apply(lambda x: f"+${x:.0f}/mo"),
            textposition="outside",
        ))
        fig_under.update_layout(
            title="Monthly Underfunding Gap (Family of 4)",
            xaxis_title="Monthly Gap ($)",
            yaxis=dict(autorange="reversed"),
            margin=dict(t=40, b=20, l=10, r=60),
            height=360,
            xaxis=dict(tickprefix="$"),
        )
        st.plotly_chart(fig_under, use_container_width=True)

    with col2:
        under_display = top_under[[
            "state", "food_price_index", "benefit_4",
            "adjusted_benefit_4", "gap_4", "snap_participants_thousands", "poverty_rate"
        ]].rename(columns={
            "state": "State",
            "food_price_index": "Price Index",
            "benefit_4": "Current ($)",
            "adjusted_benefit_4": "Needed ($)",
            "gap_4": "Gap ($)",
            "snap_participants_thousands": "Participants (K)",
            "poverty_rate": "Poverty %",
        })
        st.dataframe(under_display, hide_index=True, use_container_width=True)

    st.markdown("---")

    st.subheader("10 Most Overfunded States — SNAP Buys More Than Needed Here")
    st.caption(
        "These states have below-average food costs. Their residents receive more purchasing "
        "power per dollar of SNAP than the national Thrifty Food Plan assumes."
    )

    col3, col4 = st.columns(2)

    with col3:
        fig_over = go.Figure(go.Bar(
            x=top_over["gap_4"],
            y=top_over["state"],
            orientation="h",
            marker_color=GREEN,
            text=top_over["gap_4"].apply(lambda x: f"${x:.0f}/mo"),
            textposition="outside",
        ))
        fig_over.update_layout(
            title="Monthly Overfunding (Family of 4)",
            xaxis_title="Monthly Gap ($)",
            yaxis=dict(autorange="reversed"),
            margin=dict(t=40, b=20, l=10, r=60),
            height=360,
            xaxis=dict(tickprefix="$"),
        )
        st.plotly_chart(fig_over, use_container_width=True)

    with col4:
        over_display = top_over[[
            "state", "food_price_index", "benefit_4",
            "adjusted_benefit_4", "gap_4", "snap_participants_thousands", "poverty_rate"
        ]].rename(columns={
            "state": "State",
            "food_price_index": "Price Index",
            "benefit_4": "Current ($)",
            "adjusted_benefit_4": "Needed ($)",
            "gap_4": "Gap ($)",
            "snap_participants_thousands": "Participants (K)",
            "poverty_rate": "Poverty %",
        })
        st.dataframe(over_display, hide_index=True, use_container_width=True)

    # ── Scatter: food price index vs poverty rate ────────────────────────────
    st.markdown("---")
    st.subheader("Food Price Index vs Poverty Rate")
    st.caption(
        "Each dot is a state. High-cost states (right) are not necessarily high-poverty states — "
        "showing why a flat benefit is a poor fit. Some of the most vulnerable populations "
        "live in low-cost states with low SNAP adequacy gaps (their problem is income, not prices)."
    )

    fig_scatter = px.scatter(
        df_48,
        x="food_price_index",
        y="poverty_rate",
        color="gap_4",
        color_continuous_scale=[[0, GREEN], [0.5, YELLOW], [1, RED]],
        color_continuous_midpoint=0,
        size="snap_participants_thousands",
        size_max=30,
        hover_name="state",
        hover_data={"state_code": True, "gap_4": ":.0f"},
        labels={
            "food_price_index": "Food Price Index (100 = national avg)",
            "poverty_rate": "Poverty Rate (%)",
            "gap_4": "Monthly Gap ($)",
            "snap_participants_thousands": "Participants (K)",
        },
        text="state_code",
    )
    fig_scatter.update_traces(textposition="top center", textfont_size=9)
    fig_scatter.add_vline(x=100, line_dash="dash", line_color=GRAY,
                          annotation_text="National avg", annotation_position="top right")
    fig_scatter.update_layout(
        height=480,
        margin=dict(t=20, b=20),
        coloraxis_colorbar=dict(title="Gap ($)", tickprefix="$"),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — POLICY SIMULATOR
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Geographic Adjustment Policy Simulator")
    st.markdown(
        "**What if SNAP adopted a state-level food price multiplier?** "
        "Move the slider to apply a partial or full geographic adjustment to all 48 contiguous states + DC. "
        "Benefits are only ever increased — no state's benefit is reduced."
    )

    # ── Controls ──────────────────────────────────────────────────────────────
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        adj_pct = st.slider(
            "Geographic Adjustment Factor",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
            format="%d%%",
            help="0% = no change. 100% = full adjustment to state food prices. "
                 "Overfunded states are never reduced.",
        )
    with col_ctrl2:
        hh_size = st.selectbox(
            "Household Size",
            options=[1, 2, 3, 4, 5, 6],
            index=3,
            help="Changes the base benefit level used in the simulation.",
        )

    base_benefit = BENEFIT_MAP.get(hh_size, 975)

    # ── Simulation ────────────────────────────────────────────────────────────
    sim = df_48.copy()
    sim["adjusted_benefit_sim"] = base_benefit * (sim["food_price_index"] / 100.0)
    sim["gap_sim"]              = sim["adjusted_benefit_sim"] - base_benefit
    # Only increase benefits, never reduce
    sim["new_benefit"]          = base_benefit + np.maximum(sim["gap_sim"], 0) * (adj_pct / 100.0)
    sim["benefit_change"]       = sim["new_benefit"] - base_benefit
    # Annual cost of this adjustment (positive gaps only, scaled by adjustment %)
    sim["annual_cost_sim"] = np.where(
        sim["gap_sim"] > 0,
        sim["gap_sim"] * (adj_pct / 100.0) / hh_size
        * sim["snap_participants_thousands"] * 1000 * 12 / 1e9,
        0,
    )
    sim["fully_funded"] = sim["new_benefit"] >= sim["adjusted_benefit_sim"] - 0.01

    total_cost_sim   = sim["annual_cost_sim"].sum()
    states_helped    = (sim["benefit_change"] > 0).sum()
    states_full      = sim[sim["gap_sim"] > 0]["fully_funded"].sum()
    participants_helped = sim[sim["benefit_change"] > 0]["snap_participants_thousands"].sum()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Additional Annual Federal Cost", f"${total_cost_sim:.2f}B")
    k2.metric("States Receiving More",          f"{states_helped}")
    k3.metric("States Fully Funded",            f"{states_full} / {len(sim[sim['gap_sim'] > 0])}")
    k4.metric("Participants Helped (000s)",     f"{participants_helped:,.0f}K")

    st.markdown("---")

    # ── Proposed benefit chart ─────────────────────────────────────────────────
    top_sim = sim[sim["gap_sim"] > 0].nlargest(10, "gap_sim")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.markdown("**Benefit Change — Top 10 Underfunded States**")
        fig_sim = go.Figure()
        fig_sim.add_trace(go.Bar(
            name="Current Benefit",
            y=top_sim["state"],
            x=[base_benefit] * len(top_sim),
            orientation="h",
            marker_color=GRAY,
        ))
        fig_sim.add_trace(go.Bar(
            name="Proposed Increase",
            y=top_sim["state"],
            x=top_sim["benefit_change"],
            orientation="h",
            marker_color=BLUE,
            text=top_sim["benefit_change"].apply(lambda x: f"+${x:.0f}"),
            textposition="outside",
        ))
        fig_sim.update_layout(
            barmode="stack",
            xaxis_title=f"Monthly Benefit — HH of {hh_size} ($)",
            yaxis=dict(autorange="reversed"),
            margin=dict(t=10, b=10, l=10, r=60),
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(tickprefix="$"),
        )
        st.plotly_chart(fig_sim, use_container_width=True)

    with col_s2:
        st.markdown("**Simulated Benefits — All States**")
        sim_display = sim[["state", "state_code", "food_price_index",
                            "new_benefit", "benefit_change", "annual_cost_sim",
                            "adequacy_status"]].sort_values("benefit_change", ascending=False)
        sim_display = sim_display.rename(columns={
            "state": "State",
            "state_code": "Code",
            "food_price_index": "Price Index",
            "new_benefit": f"New Benefit ($)",
            "benefit_change": "Increase ($)",
            "annual_cost_sim": "Annual Cost ($B)",
            "adequacy_status": "Status",
        })
        sim_display["New Benefit ($)"]  = sim_display["New Benefit ($)"].round(0).astype(int)
        sim_display["Increase ($)"]     = sim_display["Increase ($)"].round(0).astype(int)
        sim_display["Annual Cost ($B)"] = sim_display["Annual Cost ($B)"].round(3)
        st.dataframe(sim_display, hide_index=True, use_container_width=True, height=380)

    # ── Cost curve ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Cost vs. Adjustment Level")
    st.caption("How does the federal cost grow as we increase the adjustment factor from 0% to 100%?")

    pcts   = list(range(0, 101, 5))
    costs  = []
    helped = []
    for p in pcts:
        c = np.where(
            sim["gap_sim"] > 0,
            sim["gap_sim"] * (p / 100.0) / hh_size
            * sim["snap_participants_thousands"] * 1000 * 12 / 1e9,
            0,
        ).sum()
        h = int((np.maximum(sim["gap_sim"], 0) * (p / 100.0) > 0).sum()
                if p > 0 else 0)
        costs.append(round(c, 3))
        helped.append(h)

    cost_df = pd.DataFrame({"Adjustment %": pcts, "Annual Cost ($B)": costs})

    fig_curve = px.area(
        cost_df, x="Adjustment %", y="Annual Cost ($B)",
        color_discrete_sequence=[BLUE],
        labels={"Annual Cost ($B)": "Additional Annual Federal Cost ($B)"},
    )
    fig_curve.add_vline(
        x=adj_pct, line_dash="dash", line_color=RED,
        annotation_text=f"Current slider: {adj_pct}%",
        annotation_position="top right",
    )
    fig_curve.update_layout(
        height=300, margin=dict(t=10, b=10),
        xaxis=dict(ticksuffix="%"),
        yaxis=dict(tickprefix="$", ticksuffix="B"),
    )
    st.plotly_chart(fig_curve, use_container_width=True)

    # ── Policy proposal text ──────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("📋 Policy Proposal Summary")

    under_states = sim[sim["gap_sim"] > 0].nlargest(3, "gap_sim")["state"].tolist()
    worst_state  = under_states[0]
    worst_gap    = sim[sim["state"] == worst_state]["gap_sim"].values[0]
    worst_new    = sim[sim["state"] == worst_state]["new_benefit"].values[0]

    st.info(
        f"**Proposed Reform:** Apply a {adj_pct}% geographic adjustment to SNAP benefits "
        f"based on BEA Regional Price Parities.\n\n"
        f"- A family of {hh_size} in **{worst_state}** would receive **${worst_new:,.0f}/month** "
        f"instead of ${base_benefit:,} — closing ${worst_gap * adj_pct / 100:.0f} of the "
        f"${worst_gap:.0f}/month adequacy gap.\n"
        f"- **{states_helped} states** would receive higher benefits.\n"
        f"- An estimated **{participants_helped:,}K SNAP participants** would see increased benefits.\n"
        f"- **Total additional federal cost: ${total_cost_sim:.2f} billion per year** — "
        f"approximately {total_cost_sim / 115:.1f}% of the current annual SNAP budget (~$115B)."
    )
