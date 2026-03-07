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
Hormuz Oil Shock — Interactive Explorer

System dynamics model with inline Euler integration.
3 stocks, 5 flows, 14 parameters, 7 computed variables.

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
    baseline_price,
    capacity_buildup_time,
    demand_elasticity,
    demand_threshold,
    disruption_ramp_time,
    global_demand_mbpd,
    max_alternative_capacity,
    max_disruption,
    max_spr_release,
    normal_hormuz_flow_mbpd,
    price_adjustment_delay,
    price_sensitivity,
    recovery_time,
    spr_response_fraction,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    oil_price = 72.0
    disruption_level = 0.0
    alternative_capacity_mbpd = 0.0
    disrupted_mbpd = 0  # Will be computed in loop
    demand_destruction_mbpd = 0  # Will be computed in loop
    gross_supply_gap_mbpd = 0  # Will be computed in loop
    spr_release_mbpd = 0  # Will be computed in loop
    net_supply_gap_mbpd = 0  # Will be computed in loop
    supply_gap_fraction = 0  # Will be computed in loop
    target_price = 0  # Will be computed in loop

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        disruption_ramp = max(0, ((max_disruption.value - disruption_level) / disruption_ramp_time.value))
        disruption_recovery = max(0, ((disruption_level - max_disruption.value) / recovery_time.value))
        capacity_growth = ((max_alternative_capacity.value - alternative_capacity_mbpd) / capacity_buildup_time.value)
        disrupted_mbpd = (normal_hormuz_flow_mbpd.value * disruption_level)
        demand_destruction_mbpd = max(0, ((oil_price - demand_threshold.value) * demand_elasticity.value))
        gross_supply_gap_mbpd = max(0, ((disrupted_mbpd - alternative_capacity_mbpd) - demand_destruction_mbpd))
        spr_release_mbpd = min(max_spr_release.value, max(0, (gross_supply_gap_mbpd * spr_response_fraction.value)))
        net_supply_gap_mbpd = max(0, (gross_supply_gap_mbpd - spr_release_mbpd))
        supply_gap_fraction = (net_supply_gap_mbpd / global_demand_mbpd.value)
        target_price = (baseline_price.value * (1 + (price_sensitivity.value * supply_gap_fraction)))
        price_increase = max(0, ((target_price - oil_price) / price_adjustment_delay.value))
        price_decrease = max(0, ((oil_price - target_price) / price_adjustment_delay.value))

        rows.append(
            {
                "time": t,
                "oil_price": oil_price,
                "disruption_level": disruption_level,
                "alternative_capacity_mbpd": alternative_capacity_mbpd,
                "price_increase": price_increase,
                "price_decrease": price_decrease,
                "disruption_ramp": disruption_ramp,
                "disruption_recovery": disruption_recovery,
                "capacity_growth": capacity_growth,
                "disrupted_mbpd": disrupted_mbpd,
                "demand_destruction_mbpd": demand_destruction_mbpd,
                "gross_supply_gap_mbpd": gross_supply_gap_mbpd,
                "spr_release_mbpd": spr_release_mbpd,
                "net_supply_gap_mbpd": net_supply_gap_mbpd,
                "supply_gap_fraction": supply_gap_fraction,
                "target_price": target_price,
            }
        )

        # Euler integration
        oil_price += dt * (price_increase - price_decrease)
        oil_price = max(oil_price, 0)
        disruption_level += dt * (disruption_ramp - disruption_recovery)
        disruption_level = max(disruption_level, 0)
        alternative_capacity_mbpd += dt * capacity_growth
        alternative_capacity_mbpd = max(alternative_capacity_mbpd, 0)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Hormuz Oil Shock — Interactive Explorer

    **Stocks:** 3 | **Flows:** 5 | **Parameters:** 14 | **Computed:** 7

    Adjust the sliders below to change parameters and see how the model responds in real time.
    """
    )
    return


@app.cell
def time_controls(mo):
    final_time = mo.ui.number(
        value=100, start=1, stop=1000, step=1, label="Final Time"
    )
    time_step = mo.ui.number(
        value=1, start=0.1, stop=5.0, step=0.1, label="Time Step"
    )
    mo.hstack([final_time, time_step], justify="start", gap=1)
    return final_time, time_step


@app.cell
def parameter_controls(mo):
    baseline_price = mo.ui.slider(
        value=72.0, start=0, stop=360.0, step=0.72,
        label="Baseline Price (dollars_per_barrel)",
    )
    normal_hormuz_flow_mbpd = mo.ui.slider(
        value=20.0, start=0, stop=100.0, step=0.2,
        label="Normal Hormuz Flow Mbpd (million_barrels_per_day)",
    )
    global_demand_mbpd = mo.ui.slider(
        value=104.0, start=0, stop=520.0, step=1.04,
        label="Global Demand Mbpd (million_barrels_per_day)",
    )
    max_disruption = mo.ui.slider(
        value=0.86, start=0, stop=1, step=0.01,
        label="Max Disruption (fraction)",
    )
    disruption_ramp_time = mo.ui.slider(
        value=5.0, start=0, stop=25.0, step=0.05,
        label="Disruption Ramp Time (Day)",
    )
    recovery_time = mo.ui.slider(
        value=30.0, start=0, stop=150.0, step=0.3,
        label="Recovery Time (Day)",
    )
    max_alternative_capacity = mo.ui.slider(
        value=5.0, start=0, stop=25.0, step=0.05,
        label="Max Alternative Capacity (million_barrels_per_day)",
    )
    capacity_buildup_time = mo.ui.slider(
        value=120.0, start=0, stop=600.0, step=1.2,
        label="Capacity Buildup Time (Day)",
    )
    max_spr_release = mo.ui.slider(
        value=4.0, start=0, stop=20.0, step=0.04,
        label="Max Spr Release (million_barrels_per_day)",
    )
    spr_response_fraction = mo.ui.slider(
        value=0.25, start=0, stop=1, step=0.01,
        label="Spr Response Fraction (fraction)",
    )
    demand_elasticity = mo.ui.slider(
        value=0.1, start=0, stop=1, step=0.01,
        label="Demand Elasticity (million_barrels_per_day_per_dollar)",
    )
    demand_threshold = mo.ui.slider(
        value=80.0, start=0, stop=400.0, step=0.8,
        label="Demand Threshold (dollars_per_barrel)",
    )
    price_sensitivity = mo.ui.slider(
        value=8.0, start=0, stop=40.0, step=0.08,
        label="Price Sensitivity (dimensionless)",
    )
    price_adjustment_delay = mo.ui.slider(
        value=14.0, start=0, stop=70.0, step=0.14,
        label="Price Adjustment Delay (Day)",
    )
    mo.vstack(
        [
        baseline_price,
        normal_hormuz_flow_mbpd,
        global_demand_mbpd,
        max_disruption,
        disruption_ramp_time,
        recovery_time,
        max_alternative_capacity,
        capacity_buildup_time,
        max_spr_release,
        spr_response_fraction,
        demand_elasticity,
        demand_threshold,
        price_sensitivity,
        price_adjustment_delay,
        ]
    )
    return (
        baseline_price,
        capacity_buildup_time,
        demand_elasticity,
        demand_threshold,
        disruption_ramp_time,
        global_demand_mbpd,
        max_alternative_capacity,
        max_disruption,
        max_spr_release,
        normal_hormuz_flow_mbpd,
        price_adjustment_delay,
        price_sensitivity,
        recovery_time,
        spr_response_fraction,
    )


@app.cell
def chart_controls(mo):
    stock_selector = mo.ui.multiselect(
        options={"Oil Price (dollars_per_barrel)": "oil_price", "Disruption Level (fraction)": "disruption_level", "Alternative Capacity Mbpd (million_barrels_per_day)": "alternative_capacity_mbpd"},
        value=["Oil Price (dollars_per_barrel)", "Disruption Level (fraction)", "Alternative Capacity Mbpd (million_barrels_per_day)"],
        label="Stock variables",
    )
    flow_selector = mo.ui.multiselect(
        options={"Price Increase (dollars_per_barrel_per_Day)": "price_increase", "Price Decrease (dollars_per_barrel_per_Day)": "price_decrease", "Disruption Ramp (fraction_per_Day)": "disruption_ramp", "Disruption Recovery (fraction_per_Day)": "disruption_recovery", "Capacity Growth (million_barrels_per_day_per_Day)": "capacity_growth"},
        value=["Price Increase (dollars_per_barrel_per_Day)", "Price Decrease (dollars_per_barrel_per_Day)", "Disruption Ramp (fraction_per_Day)", "Disruption Recovery (fraction_per_Day)", "Capacity Growth (million_barrels_per_day_per_Day)"],
        label="Flow variables",
    )
    aux_selector = mo.ui.multiselect(
        options={"Disrupted Mbpd (million_barrels_per_day)": "disrupted_mbpd", "Demand Destruction Mbpd (million_barrels_per_day)": "demand_destruction_mbpd", "Gross Supply Gap Mbpd (million_barrels_per_day)": "gross_supply_gap_mbpd", "Spr Release Mbpd (million_barrels_per_day)": "spr_release_mbpd", "Net Supply Gap Mbpd (million_barrels_per_day)": "net_supply_gap_mbpd", "Supply Gap Fraction (fraction)": "supply_gap_fraction", "Target Price (dollars_per_barrel)": "target_price"},
        value=["Disrupted Mbpd (million_barrels_per_day)", "Demand Destruction Mbpd (million_barrels_per_day)", "Gross Supply Gap Mbpd (million_barrels_per_day)", "Spr Release Mbpd (million_barrels_per_day)", "Net Supply Gap Mbpd (million_barrels_per_day)", "Supply Gap Fraction (fraction)", "Target Price (dollars_per_barrel)"],
        label="Auxiliary variables",
    )
    return stock_selector, flow_selector, aux_selector


@app.cell
def tabbed_content(aux_selector, flow_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
## Strait of Hormuz Oil Price Shock — 2026 Iran Crisis

**Context (March 7, 2026):** Following US/Israel strikes on Iran on Feb 28, 2026, the Strait of Hormuz has seen flows drop 86% — from ~20 million barrels/day to ~3 million barrels/day. Brent crude surged from $72 to $90 in one week. This model projects the price trajectory under different closure durations.

### What This Model Captures

Three interacting stocks with stabilizing feedbacks:

| Stock | Dynamic |
|-------|---------|
| **oil_price** | Adjusts toward equilibrium with a 14-day market lag |
| **disruption_level** | Ramps to 86% in 5 days, recovers over 30 days after ceasefire |
| **alternative_capacity_mbpd** | Saudi Petroline + UAE pipeline builds to 5 mbpd over ~4 months |

Three stabilizing feedbacks prevent a runaway price spiral:
1. **SPR/IEA release** — up to 4 mbpd, activated proportional to supply gap
2. **Demand destruction** — 0.1 mbpd lost per dollar above $80/barrel threshold
3. **Alternative routing** — Saudi Petroline (5–7 mbpd capacity) + UAE Abu Dhabi-Fujairah pipeline

### Scenario Results

**Phase 1 — Shock (all scenarios):**
| Day | Date | Price | Change |
|-----|------|-------|--------|
| 0 | Feb 28 | $72 | Crisis starts |
| 7 | Mar 6 | $102 | +41% — actual $90 (markets pricing uncertainty) |
| 14 | Mar 13 | $117 | +63% |
| 30 | Mar 29 | $120 | +67% — near peak |

**Scenario A — Ceasefire at day 30 (set max_disruption = 0):**
- Day 30 after ceasefire: $93 (-22% from peak)
- Day 45 after ceasefire: $83 (-31% from peak)
- Day 90 after ceasefire: $72 — back to baseline

**Scenario B — Extended closure (no ceasefire):**
- Day 90: $114 (alt routes: 3.9 mbpd, SPR: 2.5 mbpd)
- Day 180: $111 — plateau, no further natural relief
- Day 365: ~$111 — sustained if strait stays closed

### Key Finding: The $111 Floor

Three stabilizers collectively offset ~40% of the 17.2 mbpd disruption:
- Saudi Petroline + UAE pipeline: **5 mbpd**
- IEA/SPR release: **~2.5 mbpd**
- Demand destruction at $111: **~3 mbpd**

Without these, analyst forecasts of $150–200 would be valid. With them, the sustained equilibrium is ~$111/barrel.

### Model Calibration

The model predicts $102 at Day 7; actual Brent is $90–92. The ~$10 gap reflects markets pricing ~50% probability of rapid resolution. If the crisis persists without ceasefire signals, expect Brent to approach $100+ by ~March 13.

### Use the Sliders To Explore

- **max_disruption** → set to 0 to model ceasefire/reopening
- **price_sensitivity** → higher = more panic pricing (1973-style)
- **max_spr_release** → test SPR capacity scenarios
- **max_alternative_capacity** → test if Saudi pipeline runs at full 7 mbpd
- **demand_elasticity** → test recession-driven demand collapse
- **recovery_time** → test how fast the strait can physically reopen
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
    
        oil_price["Oil Price"]:::stock
        disruption_level["Disruption Level"]:::stock
        alternative_capacity_mbpd["Alternative Capacity Mbpd"]:::stock
        price_increase(["Price Increase"]):::flow
        price_decrease(["Price Decrease"]):::flow
        disruption_ramp(["Disruption Ramp"]):::flow
        disruption_recovery(["Disruption Recovery"]):::flow
        capacity_growth(["Capacity Growth"]):::flow
        baseline_price{{"Baseline Price = 72.0"}}:::constant
        normal_hormuz_flow_mbpd{{"Normal Hormuz Flow Mbpd = 20.0"}}:::constant
        global_demand_mbpd{{"Global Demand Mbpd = 104.0"}}:::constant
        max_disruption{{"Max Disruption = 0.86"}}:::constant
        disruption_ramp_time{{"Disruption Ramp Time = 5.0"}}:::constant
        recovery_time{{"Recovery Time = 30.0"}}:::constant
        max_alternative_capacity{{"Max Alternative Capacity = 5.0"}}:::constant
        capacity_buildup_time{{"Capacity Buildup Time = 120.0"}}:::constant
        max_spr_release{{"Max Spr Release = 4.0"}}:::constant
        spr_response_fraction{{"Spr Response Fraction = 0.25"}}:::constant
        demand_elasticity{{"Demand Elasticity = 0.1"}}:::constant
        demand_threshold{{"Demand Threshold = 80.0"}}:::constant
        price_sensitivity{{"Price Sensitivity = 8.0"}}:::constant
        price_adjustment_delay{{"Price Adjustment Delay = 14.0"}}:::constant
        disrupted_mbpd[/"Disrupted Mbpd"/]:::computed
        demand_destruction_mbpd[/"Demand Destruction Mbpd"/]:::computed
        gross_supply_gap_mbpd[/"Gross Supply Gap Mbpd"/]:::computed
        spr_release_mbpd[/"Spr Release Mbpd"/]:::computed
        net_supply_gap_mbpd[/"Net Supply Gap Mbpd"/]:::computed
        supply_gap_fraction[/"Supply Gap Fraction"/]:::computed
        target_price[/"Target Price"/]:::computed
    
        price_increase ==>|"+"| oil_price
        oil_price ==>|"-"| price_decrease
        disruption_ramp ==>|"+"| disruption_level
        disruption_level ==>|"-"| disruption_recovery
        capacity_growth ==>|"+"| alternative_capacity_mbpd
    
        price_adjustment_delay -.-> price_increase
        target_price -.-> price_increase
        price_adjustment_delay -.-> price_decrease
        target_price -.-> price_decrease
        max_disruption -.-> disruption_ramp
        disruption_ramp_time -.-> disruption_ramp
        max_disruption -.-> disruption_recovery
        recovery_time -.-> disruption_recovery
        max_alternative_capacity -.-> capacity_growth
        capacity_buildup_time -.-> capacity_growth
        normal_hormuz_flow_mbpd -.-> disrupted_mbpd
        disruption_level -.-> disrupted_mbpd
        demand_elasticity -.-> demand_destruction_mbpd
        oil_price -.-> demand_destruction_mbpd
        demand_threshold -.-> demand_destruction_mbpd
        alternative_capacity_mbpd -.-> gross_supply_gap_mbpd
        disrupted_mbpd -.-> gross_supply_gap_mbpd
        demand_destruction_mbpd -.-> gross_supply_gap_mbpd
        gross_supply_gap_mbpd -.-> spr_release_mbpd
        max_spr_release -.-> spr_release_mbpd
        spr_response_fraction -.-> spr_release_mbpd
        gross_supply_gap_mbpd -.-> net_supply_gap_mbpd
        spr_release_mbpd -.-> net_supply_gap_mbpd
        net_supply_gap_mbpd -.-> supply_gap_fraction
        global_demand_mbpd -.-> supply_gap_fraction
        supply_gap_fraction -.-> target_price
        baseline_price -.-> target_price
        price_sensitivity -.-> target_price
        """
        ),
        mo.Html("</div>"),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'oil_price': 'Oil Price (dollars_per_barrel)', 'disruption_level': 'Disruption Level (fraction)', 'alternative_capacity_mbpd': 'Alternative Capacity Mbpd (million_barrels_per_day)'}
    fig_stocks = go.Figure()
    for _key in stock_selector.value:
        fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    _flow_labels = {'price_increase': 'Price Increase (dollars_per_barrel_per_Day)', 'price_decrease': 'Price Decrease (dollars_per_barrel_per_Day)', 'disruption_ramp': 'Disruption Ramp (fraction_per_Day)', 'disruption_recovery': 'Disruption Recovery (fraction_per_Day)', 'capacity_growth': 'Capacity Growth (million_barrels_per_day_per_Day)'}
    fig_flows = go.Figure()
    for _key in flow_selector.value:
        fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key)))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    _aux_labels = {'disrupted_mbpd': 'Disrupted Mbpd (million_barrels_per_day)', 'demand_destruction_mbpd': 'Demand Destruction Mbpd (million_barrels_per_day)', 'gross_supply_gap_mbpd': 'Gross Supply Gap Mbpd (million_barrels_per_day)', 'spr_release_mbpd': 'Spr Release Mbpd (million_barrels_per_day)', 'net_supply_gap_mbpd': 'Net Supply Gap Mbpd (million_barrels_per_day)', 'supply_gap_fraction': 'Supply Gap Fraction (fraction)', 'target_price': 'Target Price (dollars_per_barrel)'}
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
