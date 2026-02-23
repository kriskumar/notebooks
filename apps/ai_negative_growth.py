# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "plotly>=5.18.0",
#     "pandas>=2.0.0",
#     "numpy>=1.24.0",
# ]
# ///
"""
Ai Negative Growth — Interactive Explorer

System dynamics model with inline Euler integration.
3 stocks, 4 flows, 14 parameters, 13 computed variables.

No PySD required — runs in WASM/Pyodide.
"""

import marimo

app = marimo.App(width="medium")


@app.cell
def imports():
    import marimo as mo
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np

    return go, mo, np, pd


@app.cell
def run_simulation(
    ai_growth_rate,
    ai_productivity_gain,
    ai_productivity_max,
    base_consumption,
    consumption_gain,
    depreciation_fraction,
    displacement_speed,
    min_labor_share,
    mpc_owners,
    mpc_spread,
    mpc_workers,
    owner_reinvestment_rate,
    ubi_rate,
    worker_savings_rate,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    ai_adoption = 0.01
    labor_share = 0.6
    capital_stock = 100.0
    effective_mpc = 0  # Will be computed in loop
    ubi_boost = 0  # Will be computed in loop
    effective_mpc_with_ubi = 0  # Will be computed in loop
    multiplier_denom = 0  # Will be computed in loop
    keynesian_multiplier = 0  # Will be computed in loop
    autonomous_consumption = 0  # Will be computed in loop
    gdp = 0  # Will be computed in loop
    effective_savings_rate = 0  # Will be computed in loop
    worker_income = 0  # Will be computed in loop
    owner_income = 0  # Will be computed in loop
    ubi_transfer = 0  # Will be computed in loop
    real_gdp = 0  # Will be computed in loop
    supply_side_capacity = 0  # Will be computed in loop

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        ai_adoption_growth = (ai_growth_rate.value * ai_adoption * (1 - ai_adoption))
        labor_displacement_flow = (displacement_speed.value * ai_adoption * (labor_share - min_labor_share.value))
        capital_depreciation = (depreciation_fraction.value * capital_stock)
        effective_mpc = ((mpc_workers.value * labor_share) + (mpc_owners.value * (1 - labor_share)))
        ubi_boost = (mpc_spread.value * ubi_rate.value * (1 - labor_share))
        autonomous_consumption = (base_consumption.value + (consumption_gain.value * ai_adoption))
        effective_savings_rate = ((worker_savings_rate.value * labor_share) + (owner_reinvestment_rate.value * (1 - labor_share)))
        supply_side_capacity = (capital_stock * (1 + (ai_productivity_max.value * ai_adoption)))
        effective_mpc_with_ubi = (effective_mpc + ubi_boost)
        multiplier_denom = max(0.05, (1 - effective_mpc_with_ubi))
        keynesian_multiplier = (1 / max(multiplier_denom, 1e-6))
        gdp = (autonomous_consumption * keynesian_multiplier)
        gross_investment = (effective_savings_rate * gdp)
        worker_income = (gdp * labor_share)
        owner_income = (gdp * (1 - labor_share))
        real_gdp = (gdp * (1 + (ai_productivity_gain.value * ai_adoption)))
        ubi_transfer = (ubi_rate.value * owner_income)

        rows.append(
            {
                "time": t,
                "ai_adoption": ai_adoption,
                "labor_share": labor_share,
                "capital_stock": capital_stock,
                "ai_adoption_growth": ai_adoption_growth,
                "labor_displacement_flow": labor_displacement_flow,
                "gross_investment": gross_investment,
                "capital_depreciation": capital_depreciation,
                "effective_mpc": effective_mpc,
                "ubi_boost": ubi_boost,
                "effective_mpc_with_ubi": effective_mpc_with_ubi,
                "multiplier_denom": multiplier_denom,
                "keynesian_multiplier": keynesian_multiplier,
                "autonomous_consumption": autonomous_consumption,
                "gdp": gdp,
                "effective_savings_rate": effective_savings_rate,
                "worker_income": worker_income,
                "owner_income": owner_income,
                "ubi_transfer": ubi_transfer,
                "real_gdp": real_gdp,
                "supply_side_capacity": supply_side_capacity,
            }
        )

        # Euler integration
        ai_adoption += dt * ai_adoption_growth
        ai_adoption = max(ai_adoption, 0)
        labor_share += dt * (0 - labor_displacement_flow)
        labor_share = max(labor_share, 0)
        capital_stock += dt * (gross_investment - capital_depreciation)
        capital_stock = max(capital_stock, 0)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Ai Negative Growth — Interactive Explorer

    **Stocks:** 3 | **Flows:** 4 | **Parameters:** 14 | **Computed:** 13

    Adjust the sliders below to change parameters and see how the model responds in real time.
    """
    )
    return


@app.cell
def time_controls(mo):
    final_time = mo.ui.number(
        value=60, start=1, stop=600, step=1, label="Final Time"
    )
    time_step = mo.ui.number(
        value=0.25, start=0.1, stop=5.0, step=0.1, label="Time Step"
    )
    mo.hstack([final_time, time_step], justify="start", gap=1)
    return final_time, time_step


@app.cell
def parameter_controls(mo):
    mpc_workers = mo.ui.slider(
        value=0.9, start=0.0, stop=1.0, step=0.01,
        label="Mpc Workers (fraction)",
    )
    mpc_owners = mo.ui.slider(
        value=0.2, start=0.0, stop=1.0, step=0.01,
        label="Mpc Owners (fraction)",
    )
    mpc_spread = mo.ui.slider(
        value=0.7, start=0.0, stop=1.0, step=0.01,
        label="Mpc Spread (fraction)",
    )
    base_consumption = mo.ui.slider(
        value=38.0, start=0.0, stop=190.0, step=1.9,
        label="Base Consumption (index)",
    )
    consumption_gain = mo.ui.slider(
        value=2.0, start=0.0, stop=10.0, step=0.1,
        label="Consumption Gain (index)",
    )
    ai_growth_rate = mo.ui.slider(
        value=0.4, start=0.1, stop=2.0, step=0.019,
        label="Ai Growth Rate (1/year)",
    )
    min_labor_share = mo.ui.slider(
        value=0.05, start=0.0, stop=0.3, step=0.003,
        label="Min Labor Share (fraction)",
    )
    displacement_speed = mo.ui.slider(
        value=0.1, start=0.01, stop=0.5, step=0.0049,
        label="Displacement Speed (1/year)",
    )
    worker_savings_rate = mo.ui.slider(
        value=0.07, start=0.0, stop=0.5, step=0.005,
        label="Worker Savings Rate (fraction)",
    )
    owner_reinvestment_rate = mo.ui.slider(
        value=0.03, start=0.0, stop=0.5, step=0.005,
        label="Owner Reinvestment Rate (fraction)",
    )
    depreciation_fraction = mo.ui.slider(
        value=0.05, start=0.01, stop=0.2, step=0.0019,
        label="Depreciation Fraction (1/year)",
    )
    ai_productivity_gain = mo.ui.slider(
        value=0.8, start=0.0, stop=5.0, step=0.05,
        label="Ai Productivity Gain (dimensionless)",
    )
    ai_productivity_max = mo.ui.slider(
        value=3.0, start=0.5, stop=10.0, step=0.095,
        label="Ai Productivity Max (dimensionless)",
    )
    ubi_rate = mo.ui.slider(
        value=0.0, start=0.0, stop=0.9, step=0.009,
        label="Ubi Rate (fraction)",
    )
    mo.vstack(
        [
        mpc_workers,
        mpc_owners,
        mpc_spread,
        base_consumption,
        consumption_gain,
        ai_growth_rate,
        min_labor_share,
        displacement_speed,
        worker_savings_rate,
        owner_reinvestment_rate,
        depreciation_fraction,
        ai_productivity_gain,
        ai_productivity_max,
        ubi_rate,
        ]
    )
    return (
        ai_growth_rate,
        ai_productivity_gain,
        ai_productivity_max,
        base_consumption,
        consumption_gain,
        depreciation_fraction,
        displacement_speed,
        min_labor_share,
        mpc_owners,
        mpc_spread,
        mpc_workers,
        owner_reinvestment_rate,
        ubi_rate,
        worker_savings_rate,
    )


@app.cell
def chart_controls(mo):
    stock_selector = mo.ui.multiselect(
        options={"Ai Adoption (fraction)": "ai_adoption", "Labor Share (fraction)": "labor_share", "Capital Stock (index)": "capital_stock"},
        value=["Ai Adoption (fraction)", "Labor Share (fraction)", "Capital Stock (index)"],
        label="Stock variables",
    )
    flow_selector = mo.ui.multiselect(
        options={"Ai Adoption Growth (fraction/year)": "ai_adoption_growth", "Labor Displacement Flow (fraction/year)": "labor_displacement_flow", "Gross Investment (index/year)": "gross_investment", "Capital Depreciation (index/year)": "capital_depreciation"},
        value=["Ai Adoption Growth (fraction/year)", "Labor Displacement Flow (fraction/year)", "Gross Investment (index/year)", "Capital Depreciation (index/year)"],
        label="Flow variables",
    )
    aux_selector = mo.ui.multiselect(
        options={"Effective Mpc (fraction)": "effective_mpc", "Ubi Boost (fraction)": "ubi_boost", "Effective Mpc With Ubi (fraction)": "effective_mpc_with_ubi", "Multiplier Denom (fraction)": "multiplier_denom", "Keynesian Multiplier (dimensionless)": "keynesian_multiplier", "Autonomous Consumption (index)": "autonomous_consumption", "Gdp (index)": "gdp", "Effective Savings Rate (fraction)": "effective_savings_rate", "Worker Income (index)": "worker_income", "Owner Income (index)": "owner_income", "Ubi Transfer (index)": "ubi_transfer", "Real Gdp (index)": "real_gdp", "Supply Side Capacity (index)": "supply_side_capacity"},
        value=["Effective Mpc (fraction)", "Ubi Boost (fraction)", "Effective Mpc With Ubi (fraction)", "Multiplier Denom (fraction)", "Keynesian Multiplier (dimensionless)", "Autonomous Consumption (index)", "Gdp (index)", "Effective Savings Rate (fraction)", "Worker Income (index)", "Owner Income (index)", "Ubi Transfer (index)", "Real Gdp (index)", "Supply Side Capacity (index)"],
        label="Auxiliary variables",
    )
    return stock_selector, flow_selector, aux_selector


@app.cell
def tabbed_content(aux_selector, flow_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
### Overview
Replicates and extends the two mechanisms from 'Will Advanced AI Lead to Negative Economic Growth?' (Aleximas, 2025). Mechanism 1 (Demand Collapse): calibrated to match GDP falling from 100 to 52.3 as labor_share drops from 0.60 to 0.05. Mechanism 2 (Capital Decumulation): calibrated for ~65% capital stock decline. Policy lever ubi_rate tests the sovereign wealth fund recommendation. Real GDP shows the initial inverted-U (rises ~5% before falling ~6%) matching the OLG model's +7.8%/-4.2% trajectory.

### Learning Objectives
- Understand how income redistribution between high-MPC and low-MPC agents collapses aggregate demand
- See how the Keynesian multiplier changes from 2.63 to 1.31 as labor share falls 0.60→0.05
- Trace the OLG capital decumulation: lower wages → less savings → capital falls 65%
- Explore why supply capacity (AI × capital) stays far above actual output (demand-constrained idle capacity)
- Test policy: how much redistribution via UBI is needed to prevent negative growth

### Customization Tips
- ubi_rate=0.5: near-full demand recovery (GDP~92.5); ubi_rate=0.75: GDP exceeds baseline
- min_labor_share=0.30 for partial automation (augmentation not full replacement)
- ai_growth_rate=0.8 for rapid AGI scenario; =0.2 for slow/gradual transition
- displacement_speed=0.3 for fast structural unemployment; =0.05 for slow adjustment
- mpc_owners=0.40 to test moderate owner consumption (less severe demand collapse)
"""),
    ])

    # --- Model Structure tab ---
    mermaid_diagram = mo.vstack([
        mo.md("## Model Structure"),
        mo.Html("""
            <style>
                .mermaid-container {
                    width: 100%;
                    height: 1200px;
                    overflow: auto;
                }
                .mermaid-container svg {
                    min-width: 1400px !important;
                    min-height: 1200px !important;
                }
            </style>
        """),
        mo.Html("<div class='mermaid-container'>"),
        mo.mermaid(
            """
    graph LR
        classDef stock fill:#4a90d9,stroke:#2c5f8a,color:white,stroke-width:3px
        classDef flow fill:#e8a838,stroke:#b8842c,color:white,stroke-width:2px
        classDef constant fill:#7bc67e,stroke:#5a9d5c,color:white
        classDef computed fill:#c084fc,stroke:#9333ea,color:white
    
        ai_adoption["Ai Adoption"]:::stock
        labor_share["Labor Share"]:::stock
        capital_stock["Capital Stock"]:::stock
        ai_adoption_growth(["Ai Adoption Growth"]):::flow
        labor_displacement_flow(["Labor Displacement Flow"]):::flow
        gross_investment(["Gross Investment"]):::flow
        capital_depreciation(["Capital Depreciation"]):::flow
        mpc_workers{{"Mpc Workers = 0.9"}}:::constant
        mpc_owners{{"Mpc Owners = 0.2"}}:::constant
        mpc_spread{{"Mpc Spread = 0.7"}}:::constant
        base_consumption{{"Base Consumption = 38.0"}}:::constant
        consumption_gain{{"Consumption Gain = 2.0"}}:::constant
        ai_growth_rate{{"Ai Growth Rate = 0.4"}}:::constant
        min_labor_share{{"Min Labor Share = 0.05"}}:::constant
        displacement_speed{{"Displacement Speed = 0.1"}}:::constant
        worker_savings_rate{{"Worker Savings Rate = 0.07"}}:::constant
        owner_reinvestment_rate{{"Owner Reinvestment Rate = 0.03"}}:::constant
        depreciation_fraction{{"Depreciation Fraction = 0.05"}}:::constant
        ai_productivity_gain{{"Ai Productivity Gain = 0.8"}}:::constant
        ai_productivity_max{{"Ai Productivity Max = 3.0"}}:::constant
        ubi_rate{{"Ubi Rate = 0.0"}}:::constant
        effective_mpc[/"Effective Mpc"/]:::computed
        ubi_boost[/"Ubi Boost"/]:::computed
        effective_mpc_with_ubi[/"Effective Mpc With Ubi"/]:::computed
        multiplier_denom[/"Multiplier Denom"/]:::computed
        keynesian_multiplier[/"Keynesian Multiplier"/]:::computed
        autonomous_consumption[/"Autonomous Consumption"/]:::computed
        gdp[/"Gdp"/]:::computed
        effective_savings_rate[/"Effective Savings Rate"/]:::computed
        worker_income[/"Worker Income"/]:::computed
        owner_income[/"Owner Income"/]:::computed
        ubi_transfer[/"Ubi Transfer"/]:::computed
        real_gdp[/"Real Gdp"/]:::computed
        supply_side_capacity[/"Supply Side Capacity"/]:::computed
    
        ai_adoption_growth ==>|"+"| ai_adoption
        labor_share ==>|"-"| labor_displacement_flow
        gross_investment ==>|"+"| capital_stock
        capital_stock ==>|"-"| capital_depreciation
    
        ai_growth_rate -.-> ai_adoption_growth
        ai_adoption -.-> labor_displacement_flow
        min_labor_share -.-> labor_displacement_flow
        displacement_speed -.-> labor_displacement_flow
        effective_savings_rate -.-> gross_investment
        gdp -.-> gross_investment
        depreciation_fraction -.-> capital_depreciation
        labor_share -.-> effective_mpc
        mpc_workers -.-> effective_mpc
        mpc_owners -.-> effective_mpc
        mpc_spread -.-> ubi_boost
        ubi_rate -.-> ubi_boost
        labor_share -.-> ubi_boost
        effective_mpc -.-> effective_mpc_with_ubi
        ubi_boost -.-> effective_mpc_with_ubi
        effective_mpc_with_ubi -.-> multiplier_denom
        multiplier_denom -.-> keynesian_multiplier
        ai_adoption -.-> autonomous_consumption
        consumption_gain -.-> autonomous_consumption
        base_consumption -.-> autonomous_consumption
        autonomous_consumption -.-> gdp
        keynesian_multiplier -.-> gdp
        worker_savings_rate -.-> effective_savings_rate
        labor_share -.-> effective_savings_rate
        owner_reinvestment_rate -.-> effective_savings_rate
        labor_share -.-> worker_income
        gdp -.-> worker_income
        labor_share -.-> owner_income
        gdp -.-> owner_income
        owner_income -.-> ubi_transfer
        ubi_rate -.-> ubi_transfer
        ai_adoption -.-> real_gdp
        ai_productivity_gain -.-> real_gdp
        gdp -.-> real_gdp
        ai_productivity_max -.-> supply_side_capacity
        ai_adoption -.-> supply_side_capacity
        capital_stock -.-> supply_side_capacity
        """
        ),
        mo.Html("</div>"),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'ai_adoption': 'Ai Adoption (fraction)', 'labor_share': 'Labor Share (fraction)', 'capital_stock': 'Capital Stock (index)'}
    _CAPITAL_RIGHT = {'capital_stock'}
    fig_stocks = go.Figure()
    _has_left_s = _has_right_s = False
    for _key in stock_selector.value:
        if _key in _CAPITAL_RIGHT:
            fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key), yaxis="y2"))
            _has_right_s = True
        else:
            fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
            _has_left_s = True
    _stocks_layout = dict(title="Stock Variables Over Time", xaxis_title="Time", template="plotly_white", legend=dict(x=0.01, y=0.99))
    if _has_left_s:
        _stocks_layout["yaxis"] = dict(title="Fraction (0–1)")
    if _has_right_s:
        _stocks_layout["yaxis2"] = dict(title="Capital Stock (index)", overlaying="y", side="right", showgrid=False)
    fig_stocks.update_layout(**_stocks_layout)

    _flow_labels = {'ai_adoption_growth': 'Ai Adoption Growth (fraction/year)', 'labor_displacement_flow': 'Labor Displacement Flow (fraction/year)', 'gross_investment': 'Gross Investment (index/year)', 'capital_depreciation': 'Capital Depreciation (index/year)'}
    _LEFT_FLOWS = {'ai_adoption_growth', 'labor_displacement_flow'}
    _RIGHT_FLOWS = {'gross_investment', 'capital_depreciation'}
    fig_flows = go.Figure()
    _has_left_f = _has_right_f = False
    for _key in flow_selector.value:
        if _key in _RIGHT_FLOWS:
            fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key), yaxis="y2"))
            _has_right_f = True
        else:
            fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key)))
            _has_left_f = True
    _flows_layout = dict(title="Flow Variables Over Time", xaxis_title="Time", template="plotly_white", legend=dict(x=0.01, y=0.99))
    if _has_left_f:
        _flows_layout["yaxis"] = dict(title="Rate — adoption/displacement (fraction/year)")
    if _has_right_f:
        _flows_layout["yaxis2"] = dict(title="Rate — investment/depreciation (index/year)", overlaying="y", side="right", showgrid=False)
    fig_flows.update_layout(**_flows_layout)

    _aux_labels = {'effective_mpc': 'Effective Mpc (fraction)', 'ubi_boost': 'Ubi Boost (fraction)', 'effective_mpc_with_ubi': 'Effective Mpc With Ubi (fraction)', 'multiplier_denom': 'Multiplier Denom (fraction)', 'keynesian_multiplier': 'Keynesian Multiplier (dimensionless)', 'autonomous_consumption': 'Autonomous Consumption (index)', 'gdp': 'Gdp (index)', 'effective_savings_rate': 'Effective Savings Rate (fraction)', 'worker_income': 'Worker Income (index)', 'owner_income': 'Owner Income (index)', 'ubi_transfer': 'Ubi Transfer (index)', 'real_gdp': 'Real Gdp (index)', 'supply_side_capacity': 'Supply Side Capacity (index)'}
    fig_aux = go.Figure()
    for _key in aux_selector.value:
        fig_aux.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_aux_labels.get(_key, _key)))
    fig_aux.update_layout(title="Computed Auxiliary Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    simulation_content = mo.vstack([
        stock_selector,
        mo.ui.plotly(fig_stocks),
        flow_selector,
        mo.ui.plotly(fig_flows),
        aux_selector,
        mo.ui.plotly(fig_aux),
        mo.ui.table(results.reset_index().rename(columns={"time": "Time"})),
    ])

    mo.ui.tabs({
        "Simulation": simulation_content,
        "Analysis": analysis_content,
        "Model Structure": mermaid_diagram,
    })
    return


if __name__ == "__main__":
    app.run()
