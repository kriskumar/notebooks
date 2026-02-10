"""
Marimo notebook for structural_oil_supply_shortage SD model.

Run with: marimo run <this_file>.py
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    import pysd
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    from pathlib import Path
    return mo, pysd, go, pd, np, Path

@app.cell
def load_model(Path):
    model_path = str(Path(__file__).parent / "structural_oil_supply_shortage.py")
    return (model_path,)

@app.cell
def run_simulation(pysd, model_path, final_time, time_step, natural_decline_fraction, base_ev_growth_rate, price_sensitivity, barrels_per_ev_per_day, displacement_efficiency, annual_demand_growth_fraction, reference_oil_price, price_elasticity, positive_incentive_filter, breakeven_price, investment_response_factor, vitol_peak_demand_projection, realistic_peak_demand_estimate):
    model = pysd.load(model_path)
    model.set_components({
        "natural_decline_fraction": natural_decline_fraction.value,
        "base_ev_growth_rate": base_ev_growth_rate.value,
        "price_sensitivity": price_sensitivity.value,
        "barrels_per_ev_per_day": barrels_per_ev_per_day.value,
        "displacement_efficiency": displacement_efficiency.value,
        "annual_demand_growth_fraction": annual_demand_growth_fraction.value,
        "reference_oil_price": reference_oil_price.value,
        "price_elasticity": price_elasticity.value,
        "positive_incentive_filter": positive_incentive_filter.value,
        "breakeven_price": breakeven_price.value,
        "investment_response_factor": investment_response_factor.value,
        "vitol_peak_demand_projection": vitol_peak_demand_projection.value,
        "realistic_peak_demand_estimate": realistic_peak_demand_estimate.value,
    })
    results = model.run(
        initial_condition="original",
        final_time=final_time.value,
        time_step=time_step.value,
    )
    return (results,)

@app.cell
def header(mo):
    mo.md(
        """
        # Structural Oil Supply Shortage - Interactive Explorer

        **Stocks:** 3 | **Flows:** 4 | **Parameters:** 13 | **Computed:** 10

        Adjust the sliders below to change parameters and see how the model responds in real time.
        """
    )
    return ()

@app.cell
def model_diagram(mo):
    mo.vstack([
        mo.md("## Model Structure"),
        mo.mermaid("""
graph TD
    classDef stock fill:#4a90d9,stroke:#2c5f8a,color:white,stroke-width:3px
    classDef flow fill:#e8a838,stroke:#b8842c,color:white,stroke-width:2px
    classDef constant fill:#7bc67e,stroke:#5a9d5c,color:white
    classDef computed fill:#c084fc,stroke:#9333ea,color:white

    oil_supply_capacity["Oil Supply Capacity"]:::stock
    cumulative_ev_fleet["Cumulative Ev Fleet"]:::stock
    base_oil_demand_growth["Base Oil Demand Growth"]:::stock
    new_capacity_investment(["New Capacity Investment"]):::flow
    field_decline_rate(["Field Decline Rate"]):::flow
    ev_adoption_rate(["Ev Adoption Rate"]):::flow
    demand_increase_rate(["Demand Increase Rate"]):::flow
    natural_decline_fraction{{"Natural Decline Fraction = 0.05"}}:::constant
    base_ev_growth_rate{{"Base Ev Growth Rate = 12.0"}}:::constant
    price_sensitivity{{"Price Sensitivity = 0.3"}}:::constant
    barrels_per_ev_per_day{{"Barrels Per Ev Per Day = 0.002"}}:::constant
    displacement_efficiency{{"Displacement Efficiency = 0.7"}}:::constant
    annual_demand_growth_fraction{{"Annual Demand Growth Fraction = 0.009"}}:::constant
    reference_oil_price{{"Reference Oil Price = 75.0"}}:::constant
    price_elasticity{{"Price Elasticity = 2.5"}}:::constant
    positive_incentive_filter{{"Positive Incentive Filter = 0.1"}}:::constant
    breakeven_price{{"Breakeven Price = 65.0"}}:::constant
    investment_response_factor{{"Investment Response Factor = 1.5"}}:::constant
    vitol_peak_demand_projection{{"Vitol Peak Demand Projection = 112.0"}}:::constant
    realistic_peak_demand_estimate{{"Realistic Peak Demand Estimate = 120.0"}}:::constant
    ev_adoption_multiplier[/"Ev Adoption Multiplier"/]:::computed
    oil_price_effect_on_evs[/"Oil Price Effect On Evs"/]:::computed
    oil_demand_displaced_by_evs[/"Oil Demand Displaced By Evs"/]:::computed
    actual_oil_demand[/"Actual Oil Demand"/]:::computed
    supply_demand_gap[/"Supply Demand Gap"/]:::computed
    gap_ratio[/"Gap Ratio"/]:::computed
    oil_price[/"Oil Price"/]:::computed
    price_above_breakeven[/"Price Above Breakeven"/]:::computed
    normalized_investment_signal[/"Normalized Investment Signal"/]:::computed
    investment_incentive[/"Investment Incentive"/]:::computed

    ev_adoption_rate ==>|"+"| cumulative_ev_fleet
    demand_increase_rate ==>|"+"| base_oil_demand_growth

        """),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])
    return ()

@app.cell
def model_info(mo):
    mo.accordion({
        "Stocks (3)": mo.md("""- **oil_supply_capacity** = 107.0 [million barrels per day]: Total oil production capacity available globally (starting at 107 million b/d in 2025)
- **cumulative_ev_fleet** = 22.0 [million vehicles]: Global EV fleet (22 million in 2025)
- **base_oil_demand_growth** = 107.0 [million barrels per day]: Oil demand before EV displacement (107M in 2025)"""),
        "Flows (4)": mo.md("""- **new_capacity_investment** [million barrels per day per year]: New production capacity coming online
- **field_decline_rate** [million barrels per day per year]: Natural decline of existing oil fields (from IEA report)
- **ev_adoption_rate** [million vehicles per year]: Annual rate of new EV adoption
- **demand_increase_rate** [million barrels per day per year]: Demand growth from economic expansion"""),
        "Parameters (13)": mo.md("""- **natural_decline_fraction** = 0.05 [1/year]: Annual decline rate of oil fields (5%)
- **base_ev_growth_rate** = 12.0 [million vehicles per year]: Baseline EV sales rate (conservative per BloombergNEF)
- **price_sensitivity** = 0.3 [dimensionless]: EV adoption sensitivity to oil prices
- **barrels_per_ev_per_day** = 0.002 [barrels per vehicle per day]: Oil per conventional vehicle displaced
- **displacement_efficiency** = 0.7 [dimensionless]: Not all EVs replace high-mileage vehicles
- **annual_demand_growth_fraction** = 0.009 [1/year]: 0.9% annual growth to reach ~120M by mid-2030s
- **reference_oil_price** = 75.0 [dollars per barrel]: Baseline price in balanced market
- **price_elasticity** = 2.5 [dimensionless]: Price responsiveness to imbalance
- **positive_incentive_filter** = 0.1 [dimensionless]: Minimum positive investment level
- **breakeven_price** = 65.0 [dollars per barrel]: Price needed for new production
- **investment_response_factor** = 1.5 [million barrels per day per year]: Maximum investment rate
- **vitol_peak_demand_projection** = 112.0 [million barrels per day]: Vitol's projection for mid-2030s
- **realistic_peak_demand_estimate** = 120.0 [million barrels per day]: Author's revised estimate (25% of Vitol's EV assumptions)"""),
        "Computed Auxiliaries (10)": mo.md("""- **ev_adoption_multiplier** [dimensionless]: Price effect on EV adoption
- **oil_price_effect_on_evs** [dimensionless]: Normalized price impact on EV adoption
- **oil_demand_displaced_by_evs** [million barrels per day]: Oil demand displaced by EV fleet
- **actual_oil_demand** [million barrels per day]: Net demand after EV displacement
- **supply_demand_gap** [million barrels per day]: Structural shortage (positive) or surplus (negative)
- **gap_ratio** [dimensionless]: Imbalance as fraction of capacity
- **oil_price** [dollars per barrel]: Price responding to supply-demand balance
- **price_above_breakeven** [dollars per barrel]: Profitability signal for investment
- **normalized_investment_signal** [dimensionless]: Normalized profitability
- **investment_incentive** [dimensionless]: Investment attractiveness"""),
    })
    return ()

@app.cell
def time_controls(mo):
    initial_time = mo.ui.number(
        value=0,
        start=0,
        stop=1000,
        step=1,
        label="Initial Time",
    )
    final_time = mo.ui.number(
        value=100,
        start=1,
        stop=1000,
        step=1,
        label="Final Time",
    )
    time_step = mo.ui.number(
        value=1,
        start=0.01,
        stop=100,
        step=0.1,
        label="Time Step",
    )
    mo.hstack([initial_time, final_time, time_step], justify="start", gap=1)
    return initial_time, final_time, time_step

@app.cell
def parameter_controls(mo):
    natural_decline_fraction = mo.ui.slider(value=0.05, start=0.0, stop=1.0, step=0.01, label="Natural Decline Fraction (1/year)")
    base_ev_growth_rate = mo.ui.slider(value=12.0, start=0.0, stop=60.0, step=0.6, label="Base Ev Growth Rate (million vehicles per year)")
    price_sensitivity = mo.ui.slider(value=0.3, start=0.0, stop=2.0, step=0.02, label="Price Sensitivity (dimensionless)")
    barrels_per_ev_per_day = mo.ui.slider(value=0.002, start=0.0, stop=1, step=0.01, label="Barrels Per Ev Per Day (barrels per vehicle per day)")
    displacement_efficiency = mo.ui.slider(value=0.7, start=0.0, stop=1.0, step=0.01, label="Displacement Efficiency (dimensionless)")
    annual_demand_growth_fraction = mo.ui.slider(value=0.009, start=0.0, stop=0.05, step=0.0005, label="Annual Demand Growth Fraction (1/year)")
    reference_oil_price = mo.ui.slider(value=75.0, start=0.0, stop=375.0, step=3.75, label="Reference Oil Price (dollars per barrel)")
    price_elasticity = mo.ui.slider(value=2.5, start=0.0, stop=10.0, step=0.1, label="Price Elasticity (dimensionless)")
    positive_incentive_filter = mo.ui.slider(value=0.1, start=0.0, stop=1, step=0.01, label="Positive Incentive Filter (dimensionless)")
    breakeven_price = mo.ui.slider(value=65.0, start=0.0, stop=325.0, step=3.25, label="Breakeven Price (dollars per barrel)")
    investment_response_factor = mo.ui.slider(value=1.5, start=0.0, stop=7.5, step=0.075, label="Investment Response Factor (million barrels per day per year)")
    vitol_peak_demand_projection = mo.ui.slider(value=112.0, start=0.0, stop=560.0, step=5.6, label="Vitol Peak Demand Projection (million barrels per day)")
    realistic_peak_demand_estimate = mo.ui.slider(value=120.0, start=0.0, stop=600.0, step=6.0, label="Realistic Peak Demand Estimate (million barrels per day)")
    mo.vstack([natural_decline_fraction, base_ev_growth_rate, price_sensitivity, barrels_per_ev_per_day, displacement_efficiency, annual_demand_growth_fraction, reference_oil_price, price_elasticity, positive_incentive_filter, breakeven_price, investment_response_factor, vitol_peak_demand_projection, realistic_peak_demand_estimate])
    return natural_decline_fraction, base_ev_growth_rate, price_sensitivity, barrels_per_ev_per_day, displacement_efficiency, annual_demand_growth_fraction, reference_oil_price, price_elasticity, positive_incentive_filter, breakeven_price, investment_response_factor, vitol_peak_demand_projection, realistic_peak_demand_estimate

@app.cell
def stock_charts(mo, go, results):
    fig_stocks = go.Figure()
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["oil_supply_capacity"], mode="lines", name="Oil Supply Capacity"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["cumulative_ev_fleet"], mode="lines", name="Cumulative Ev Fleet"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["base_oil_demand_growth"], mode="lines", name="Base Oil Demand Growth"))
    fig_stocks.update_layout(
        title="Stock Variables Over Time",
        xaxis_title="Time",
        yaxis_title="Value",
        template="plotly_white",
    )
    mo.ui.plotly(fig_stocks)
    return ()

@app.cell
def flow_charts(mo, go, results):
    fig_flows = go.Figure()
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["new_capacity_investment"], mode="lines", name="New Capacity Investment"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["field_decline_rate"], mode="lines", name="Field Decline Rate"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["ev_adoption_rate"], mode="lines", name="Ev Adoption Rate"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["demand_increase_rate"], mode="lines", name="Demand Increase Rate"))
    fig_flows.update_layout(
        title="Flow Variables Over Time",
        xaxis_title="Time",
        yaxis_title="Rate",
        template="plotly_white",
    )
    mo.ui.plotly(fig_flows)
    return ()

@app.cell
def auxiliary_charts(mo, go, results):
    fig_aux = go.Figure()
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["ev_adoption_multiplier"], mode="lines", name="Ev Adoption Multiplier"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["oil_price_effect_on_evs"], mode="lines", name="Oil Price Effect On Evs"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["oil_demand_displaced_by_evs"], mode="lines", name="Oil Demand Displaced By Evs"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["actual_oil_demand"], mode="lines", name="Actual Oil Demand"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["supply_demand_gap"], mode="lines", name="Supply Demand Gap"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["gap_ratio"], mode="lines", name="Gap Ratio"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["oil_price"], mode="lines", name="Oil Price"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["price_above_breakeven"], mode="lines", name="Price Above Breakeven"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["normalized_investment_signal"], mode="lines", name="Normalized Investment Signal"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["investment_incentive"], mode="lines", name="Investment Incentive"))
    fig_aux.update_layout(
        title="Computed Auxiliary Variables Over Time",
        xaxis_title="Time",
        yaxis_title="Value",
        template="plotly_white",
    )
    mo.ui.plotly(fig_aux)
    return ()

@app.cell
def data_table(mo, results):
    mo.ui.table(results.reset_index().rename(columns={"index": "Time"}))
    return ()

if __name__ == "__main__":
    app.run()
