"""Streamlit + Plotly dashboard for the price-wars simulation.

Run with: streamlit run dashboard.py
"""
from contextlib import redirect_stdout
from io import StringIO

import plotly.express as px
import streamlit as st

from integration.simulation import PriceWarSimulation


st.set_page_config(page_title="Dynamic Price Wars", layout="wide")
st.title("🥛 Dynamic Price Wars & Perishable Inventory Liquidation")
st.caption("Run the existing deterministic multi-agent simulation and inspect its outcomes.")

if st.button("Run / reset simulation", type="primary"):
    sim = PriceWarSimulation()
    with redirect_stdout(StringIO()):
        sim.run()
    st.session_state["simulation"] = sim

sim = st.session_state.get("simulation")
if sim is None:
    st.info("Click **Run / reset simulation** to generate a fresh run.")
    st.stop()

summary = sim.environment.metrics.get_summary()
status = sim.environment.get_status()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total revenue", f"₹{summary['total_revenue']:,.2f}")
c2.metric("Units sold", f"{summary['units_sold']:,}")
c3.metric("Successful deals", summary["successful_deals"])
c4.metric("Expired inventory", status.get("expired_inventory", "See status"))

st.subheader("Market status")
st.json(status)

results = sim.results
deal_rows = []
event_rows = []
for result in results:
    deal = result.deal_result
    if deal and deal.success:
        deal_rows.append({
            "Retailer": result.buyer_id,
            "Quantity": deal.quantity,
            "Unit price (₹)": deal.unit_price,
            "Deal value (₹)": deal.total_value,
        })
    for event in result.events:
        event_rows.append({
            "Round": event.round_number,
            "Turn": event.turn_number,
            "Actor": event.actor,
            "Action": event.action.value,
            "Price (₹)": event.price_per_unit,
            "Quantity": event.quantity,
            "Reason": event.reason,
        })

left, right = st.columns(2)
with left:
    st.subheader("Successful deals")
    if deal_rows:
        st.dataframe(deal_rows, use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(
            deal_rows, x="Retailer", y="Quantity",
            title="Units sold by retailer"
        ), use_container_width=True)
    else:
        st.warning("No successful deals in this run.")
with right:
    st.subheader("Negotiation outcomes")
    outcomes = [
        {"Outcome": "Successful", "Count": summary["successful_deals"]},
        {"Outcome": "Failed", "Count": summary["failed_negotiations"]},
        {"Outcome": "Rejected offers", "Count": summary["rejected_offers"]},
    ]
    st.plotly_chart(px.bar(outcomes, x="Outcome", y="Count"),
                    use_container_width=True)

st.subheader("Negotiation history")
if event_rows:
    st.dataframe(event_rows, use_container_width=True, hide_index=True)
else:
    st.info("No negotiation events were recorded.")
