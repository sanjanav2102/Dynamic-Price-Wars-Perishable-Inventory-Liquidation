"""
Streamlit + Plotly dashboard for the price-wars simulation.

Run with:

    streamlit run dashboard.py
"""

from contextlib import redirect_stdout
from io import StringIO

import plotly.express as px
import streamlit as st

from integration.simulation import PriceWarSimulation


st.set_page_config(
    page_title="Dynamic Price Wars",
    layout="wide",
)

st.title(
    "🥛 Dynamic Price Wars & "
    "Perishable Inventory Liquidation"
)

st.caption(
    "Multi-agent negotiation simulation "
    "with optional Gemini AI strategies."
)


# =========================================================
# SETTINGS
# =========================================================

st.sidebar.header("Simulation settings")

st.sidebar.subheader("Product and inventory")

product_name = st.sidebar.text_input(
    "Product name",
    value="Fresh Milk",
)

initial_inventory = st.sidebar.number_input(
    "Initial inventory (units)",
    min_value=1,
    max_value=10000,
    value=500,
    step=50,
)

shelf_life_days = st.sidebar.number_input(
    "Shelf life (days)",
    min_value=1,
    max_value=30,
    value=5,
)

initial_reservation_price = st.sidebar.number_input(
    "Initial reservation price (₹/unit)",
    min_value=1.0,
    max_value=100000.0,
    value=100.0,
    step=5.0,
)

minimum_reservation_price = st.sidebar.number_input(
    "Minimum reservation price (₹/unit)",
    min_value=1.0,
    max_value=100000.0,
    value=60.0,
    step=5.0,
)

st.sidebar.subheader("Premium retailer")

premium_capacity = st.sidebar.number_input(
    "Premium storage capacity",
    min_value=1,
    max_value=10000,
    value=150,
    step=10,
)

premium_max_price = st.sidebar.number_input(
    "Premium maximum price (₹/unit)",
    min_value=1.0,
    max_value=100000.0,
    value=105.0,
    step=5.0,
)

premium_budget = st.sidebar.number_input(
    "Premium budget (₹)",
    min_value=0.0,
    max_value=100000000.0,
    value=15000.0,
    step=1000.0,
)

st.sidebar.subheader("Budget retailer")

budget_capacity = st.sidebar.number_input(
    "Budget storage capacity",
    min_value=1,
    max_value=10000,
    value=250,
    step=10,
)

budget_max_price = st.sidebar.number_input(
    "Budget maximum price (₹/unit)",
    min_value=1.0,
    max_value=100000.0,
    value=90.0,
    step=5.0,
)

budget_budget = st.sidebar.number_input(
    "Budget retailer budget (₹)",
    min_value=0.0,
    max_value=100000000.0,
    value=18000.0,
    step=1000.0,
)

st.sidebar.subheader("AI settings")

ai_enabled = st.sidebar.toggle(
    "Enable AI",
    value=True,
)

if ai_enabled:
    st.sidebar.success("AI mode enabled")
else:
    st.sidebar.info("Rule-based mode enabled")



# =========================================================
# RUN SIMULATION
# =========================================================


if st.button(
    "Run / reset simulation",
    type="primary",
):
    if minimum_reservation_price > initial_reservation_price:
        st.error(
            "Minimum reservation price cannot exceed "
            "the initial reservation price."
        )
        st.stop()

    sim = PriceWarSimulation(
        ai_enabled=ai_enabled,
        product_name=product_name,
        initial_inventory=int(initial_inventory),
        shelf_life_days=int(shelf_life_days),
        initial_reservation_price=initial_reservation_price,
        minimum_reservation_price=minimum_reservation_price,
        premium_capacity=int(premium_capacity),
        premium_max_price=premium_max_price,
        premium_budget=premium_budget,
        budget_capacity=int(budget_capacity),
        budget_max_price=budget_max_price,
        budget_budget=budget_budget,
    )

    output = StringIO()

    with redirect_stdout(output):
        sim.run()

    st.session_state["simulation"] = sim
    st.session_state["simulation_output"] = output.getvalue()
    st.session_state["simulation_ai_enabled"] = ai_enabled



sim = st.session_state.get(
    "simulation"
)

if sim is None:

    st.info(
        "Select AI mode and click "
        "**Run / reset simulation**."
    )

    st.stop()


# =========================================================
# STATUS
# =========================================================

summary = (
    sim.environment.metrics
    .get_summary()
)

status = (
    sim.environment
    .get_status()
)


run_used_ai = st.session_state.get(
    "simulation_ai_enabled",
    ai_enabled,
)

st.success(
    "Simulation completed in "
    + (
        "AI mode."
        if run_used_ai
        else "rule-based mode."
    )
)


# =========================================================
# METRICS
# =========================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total revenue",
    f"₹{summary['total_revenue']:,.2f}",
)

c2.metric(
    "Units sold",
    f"{summary['units_sold']:,}",
)

c3.metric(
    "Successful deals",
    summary["successful_deals"],
)

c4.metric(
    "Expired inventory",
    status.get(
        "expired_inventory",
        0,
    ),
)


# =========================================================
# MARKET STATUS
# =========================================================

st.subheader(
    "Market status"
)

st.json(status)


# =========================================================
# NEGOTIATION DATA
# =========================================================

results = sim.results

deal_rows = []
event_rows = []

for result in results:

    deal = result.deal_result

    if deal and deal.success:

        deal_rows.append(
            {
                "Retailer": result.buyer_id,
                "Quantity": deal.quantity,
                "Unit price (₹)": (
                    deal.unit_price
                ),
                "Deal value (₹)": (
                    deal.total_value
                ),
            }
        )

    for event in result.events:

        reason = event.reason or ""

        source = "RULE"

        if "[AI]" in reason:
            source = "AI"

        elif "[FALLBACK]" in reason:
            source = "FALLBACK"

        event_rows.append(
            {
                "Round": (
                    event.round_number
                ),
                "Turn": (
                    event.turn_number
                ),
                "Actor": event.actor,
                "Source": source,
                "Action": (
                    event.action.value
                ),
                "Price (₹)": (
                    event.price_per_unit
                ),
                "Quantity": event.quantity,
                "Reason": reason,
            }
        )


# =========================================================
# DEALS / OUTCOMES
# =========================================================

left, right = st.columns(2)


with left:

    st.subheader(
        "Successful deals"
    )

    if deal_rows:

        st.dataframe(
            deal_rows,
            use_container_width=True,
            hide_index=True,
        )

        st.plotly_chart(
            px.bar(
                deal_rows,
                x="Retailer",
                y="Quantity",
                title=(
                    "Units sold by retailer"
                ),
            ),
            use_container_width=True,
        )

    else:

        st.warning(
            "No successful deals."
        )


with right:

    st.subheader(
        "Negotiation outcomes"
    )

    outcomes = [
        {
            "Outcome": "Successful",
            "Count": (
                summary[
                    "successful_deals"
                ]
            ),
        },
        {
            "Outcome": "Failed",
            "Count": (
                summary[
                    "failed_negotiations"
                ]
            ),
        },
        {
            "Outcome": "Rejected",
            "Count": (
                summary[
                    "rejected_offers"
                ]
            ),
        },
    ]

    st.plotly_chart(
        px.bar(
            outcomes,
            x="Outcome",
            y="Count",
        ),
        use_container_width=True,
    )


# =========================================================
# AI DECISION SUMMARY
# =========================================================

st.subheader(
    "Decision source"
)

if event_rows:

    ai_count = sum(
        row["Source"] == "AI"
        for row in event_rows
    )

    fallback_count = sum(
        row["Source"] == "FALLBACK"
        for row in event_rows
    )

    rule_count = sum(
        row["Source"] == "RULE"
        for row in event_rows
    )

    source_rows = [
        {
            "Source": "AI",
            "Count": ai_count,
        },
        {
            "Source": "Fallback",
            "Count": fallback_count,
        },
        {
            "Source": "Rule",
            "Count": rule_count,
        },
    ]

    st.dataframe(
        source_rows,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# NEGOTIATION HISTORY
# =========================================================

st.subheader(
    "Negotiation history"
)

if event_rows:

    st.dataframe(
        event_rows,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "No negotiation events were recorded."
    )


# =========================================================
# TERMINAL OUTPUT
# =========================================================

with st.expander(
    "Simulation console output"
):

    st.code(
        st.session_state.get(
            "simulation_output",
            "",
        )
    )