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
Carbon Price Dynamics — Interactive Explorer

System dynamics model with inline Euler integration.
3 stocks, 6 flows, 14 parameters, 6 computed variables.

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
    base_emissions,
    capacity_lifetime,
    cbam_rate,
    competitiveness_threshold,
    contraction_sensitivity,
    cost_sensitivity,
    emission_target,
    initial_output,
    investment_sensitivity,
    leakage_sensitivity,
    leakage_threshold,
    price_sensitivity,
    recovery_rate,
    total_energy_demand,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    renewable_capacity = 50.0
    industrial_output = 100.0
    carbon_price = 30.0
    renewable_fraction = 0  # Will be computed in loop
    carbon_emissions = 0  # Will be computed in loop
    emission_gap = 0  # Will be computed in loop
    production_cost_index = 0  # Will be computed in loop
    cbam_effectiveness = 0  # Will be computed in loop
    net_leakage_pressure = 0  # Will be computed in loop

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        capacity_addition = max(0, (carbon_price * investment_sensitivity.value))
        capacity_retirement = (renewable_capacity / capacity_lifetime.value)
        output_recovery = (max(0, (initial_output.value - industrial_output)) * recovery_rate.value)
        renewable_fraction = (renewable_capacity / total_energy_demand.value)
        production_cost_index = (1 + (carbon_price * cost_sensitivity.value))
        cbam_effectiveness = min(1, (cbam_rate.value / max(carbon_price, 1e-6)))
        carbon_emissions = (base_emissions.value * (industrial_output / initial_output.value) * (1 - renewable_fraction))
        output_contraction = (industrial_output * max(0, (production_cost_index - competitiveness_threshold.value)) * contraction_sensitivity.value)
        net_leakage_pressure = (max(0, (carbon_price - leakage_threshold.value)) * (1 - cbam_effectiveness))
        emission_gap = (carbon_emissions - emission_target.value)
        carbon_leakage_flow = (industrial_output * net_leakage_pressure * leakage_sensitivity.value)
        price_net_change = max((emission_gap * price_sensitivity.value), (1 - carbon_price))

        rows.append(
            {
                "time": t,
                "renewable_capacity": renewable_capacity,
                "industrial_output": industrial_output,
                "carbon_price": carbon_price,
                "capacity_addition": capacity_addition,
                "capacity_retirement": capacity_retirement,
                "output_recovery": output_recovery,
                "output_contraction": output_contraction,
                "carbon_leakage_flow": carbon_leakage_flow,
                "price_net_change": price_net_change,
                "renewable_fraction": renewable_fraction,
                "carbon_emissions": carbon_emissions,
                "emission_gap": emission_gap,
                "production_cost_index": production_cost_index,
                "cbam_effectiveness": cbam_effectiveness,
                "net_leakage_pressure": net_leakage_pressure,
            }
        )

        # Euler integration
        renewable_capacity += dt * (capacity_addition - capacity_retirement)
        renewable_capacity = max(renewable_capacity, 0)
        industrial_output += dt * (output_recovery - output_contraction - carbon_leakage_flow)
        industrial_output = max(industrial_output, 0)
        carbon_price += dt * price_net_change
        carbon_price = max(carbon_price, 1)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Carbon Price Dynamics — Interactive Explorer

    **Stocks:** 3 | **Flows:** 6 | **Parameters:** 14 | **Computed:** 6

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
    investment_sensitivity = mo.ui.slider(
        value=0.5, start=0.0, stop=3.0, step=0.03,
        label="Investment Sensitivity (GW/(USD/tonne*year))",
    )
    cost_sensitivity = mo.ui.slider(
        value=0.005, start=0.0, stop=0.02, step=0.0002,
        label="Cost Sensitivity (1/(USD/tonne))",
    )
    competitiveness_threshold = mo.ui.slider(
        value=1.2, start=1.0, stop=2.0, step=0.01,
        label="Competitiveness Threshold (index)",
    )
    contraction_sensitivity = mo.ui.slider(
        value=0.02, start=0.0, stop=0.1, step=0.001,
        label="Contraction Sensitivity (1/year)",
    )
    leakage_threshold = mo.ui.slider(
        value=60.0, start=20.0, stop=150.0, step=1.3,
        label="Leakage Threshold (USD/tonne)",
    )
    leakage_sensitivity = mo.ui.slider(
        value=0.003, start=0.0, stop=0.01, step=0.0001,
        label="Leakage Sensitivity (1/(USD/tonne*year))",
    )
    cbam_rate = mo.ui.slider(
        value=40.0, start=0.0, stop=120.0, step=1.2,
        label="Cbam Rate (USD/tonne)",
    )
    price_sensitivity = mo.ui.slider(
        value=0.5, start=0.1, stop=2.0, step=0.019,
        label="Price Sensitivity ((USD/tonne)/(Mt CO2/year))",
    )
    capacity_lifetime = mo.ui.slider(
        value=25.0, start=10.0, stop=40.0, step=0.3,
        label="Capacity Lifetime (year)",
    )
    recovery_rate = mo.ui.slider(
        value=0.05, start=0.01, stop=0.3, step=0.0029,
        label="Recovery Rate (1/year)",
    )
    total_energy_demand = mo.ui.slider(
        value=500.0, start=100.0, stop=1000.0, step=9.0,
        label="Total Energy Demand (GW)",
    )
    base_emissions = mo.ui.slider(
        value=80.0, start=20.0, stop=200.0, step=1.8,
        label="Base Emissions (Mt CO2/year)",
    )
    initial_output = mo.ui.slider(
        value=100.0, start=50.0, stop=200.0, step=1.5,
        label="Initial Output (index)",
    )
    emission_target = mo.ui.slider(
        value=50.0, start=10.0, stop=80.0, step=0.7,
        label="Emission Target (Mt CO2/year)",
    )
    mo.vstack(
        [
        investment_sensitivity,
        cost_sensitivity,
        competitiveness_threshold,
        contraction_sensitivity,
        leakage_threshold,
        leakage_sensitivity,
        cbam_rate,
        price_sensitivity,
        capacity_lifetime,
        recovery_rate,
        total_energy_demand,
        base_emissions,
        initial_output,
        emission_target,
        ]
    )
    return (
        base_emissions,
        capacity_lifetime,
        cbam_rate,
        competitiveness_threshold,
        contraction_sensitivity,
        cost_sensitivity,
        emission_target,
        initial_output,
        investment_sensitivity,
        leakage_sensitivity,
        leakage_threshold,
        price_sensitivity,
        recovery_rate,
        total_energy_demand,
    )


@app.cell
def chart_controls(mo):
    stock_selector = mo.ui.multiselect(
        options={"Renewable Capacity (GW)": "renewable_capacity", "Industrial Output (index)": "industrial_output", "Carbon Price (USD/tonne)": "carbon_price"},
        value=["Renewable Capacity (GW)", "Industrial Output (index)", "Carbon Price (USD/tonne)"],
        label="Stock variables",
    )
    flow_selector = mo.ui.multiselect(
        options={"Capacity Addition (GW/year)": "capacity_addition", "Capacity Retirement (GW/year)": "capacity_retirement", "Output Recovery (index/year)": "output_recovery", "Output Contraction (index/year)": "output_contraction", "Carbon Leakage Flow (index/year)": "carbon_leakage_flow", "Price Net Change (USD/tonne/year)": "price_net_change"},
        value=["Capacity Addition (GW/year)", "Capacity Retirement (GW/year)", "Output Recovery (index/year)", "Output Contraction (index/year)", "Carbon Leakage Flow (index/year)", "Price Net Change (USD/tonne/year)"],
        label="Flow variables",
    )
    aux_selector = mo.ui.multiselect(
        options={"Renewable Fraction (fraction)": "renewable_fraction", "Carbon Emissions (Mt CO2/year)": "carbon_emissions", "Emission Gap (Mt CO2/year)": "emission_gap", "Production Cost Index (index)": "production_cost_index", "Cbam Effectiveness (fraction)": "cbam_effectiveness", "Net Leakage Pressure (USD/tonne)": "net_leakage_pressure"},
        value=["Renewable Fraction (fraction)", "Carbon Emissions (Mt CO2/year)", "Emission Gap (Mt CO2/year)", "Production Cost Index (index)", "Cbam Effectiveness (fraction)", "Net Leakage Pressure (USD/tonne)"],
        label="Auxiliary variables",
    )
    return stock_selector, flow_selector, aux_selector


@app.cell
def tabbed_content(aux_selector, flow_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
# Carbon Price Dynamics: Two-Loop System Dynamics Model

## Model Overview

This model captures how carbon pricing interacts with two fundamental economic responses over a 15-year horizon, producing very different outcomes depending on which loop dominates.

## Feedback Loops

### B1 — Green Transition (Balancing)
**Carbon Price → Renewable Investment → Renewable Capacity → Renewable Fraction → Carbon Emissions ↓ → Emission Gap ↓ → Carbon Price ↓**

High carbon price makes renewable energy investment attractive. As capacity builds, it displaces fossil fuels, reducing emissions below the policy target, which causes the market to lower the price. A self-correcting loop that works best when `investment_sensitivity` is high.

### B2a — Industrial Cost Contraction (Balancing)
**Carbon Price → Production Cost Index → exceeds Competitiveness Threshold → Output Contraction → Industrial Output ↓ → Carbon Emissions ↓ → Carbon Price ↓**

When carbon costs push the production cost index above 1.2 (a 20% premium), domestic industry contracts. Less production means fewer emissions, eventually pulling the price down. The economy pays a real cost to achieve the emission reduction.

### B2b — Carbon Leakage (Balancing, with CBAM interaction)
**Carbon Price → (above $60 threshold) → Net Leakage Pressure → Carbon Leakage Flow → Industrial Output ↓ → Emissions ↓ → Carbon Price ↓**

Above $60/tonne, production starts relocating to unregulated jurisdictions. **CBAM neutralizes this** by equalizing the carbon cost on imports: `cbam_effectiveness = MIN(1, cbam_rate / carbon_price)`. Without CBAM, leakage is the dominant driver of industrial collapse — 5× larger than cost contraction alone at peak.

## Scenario Presets

| Parameter | Baseline | S1: Solar Glut | S2: Industrial Collapse |
|---|---|---|---|
| `investment_sensitivity` | 0.5 | **1.5** | 0.2 |
| `cost_sensitivity` | 0.005 | 0.002 | **0.01** |
| `cbam_rate` | 40 | 40 | **0** |

## Simulation Results Summary

### Baseline (investment_sensitivity=0.5, cost_sensitivity=0.005, cbam_rate=$40)
- Carbon price peaks at **$68** (year 6), then falls to **$6.5** by year 15
- Renewables grow 50 → 296 GW (59% share); small industrial dip to 96
- Emissions fall 72 → 32 Mt. CBAM fully neutralises leakage throughout.

### S1: Solar Glut (investment_sensitivity=1.5, cost_sensitivity=0.002, cbam_rate=$40)
- Renewables explode 50 → **361 GW** by year 7 (72% share)
- Carbon price peaks at only **$46** then **crashes to $1** — the investment signal collapses
- Industrial output untouched (100 throughout). Emissions reach 22 Mt by year 7.
- **Risk**: Once price floors at $1, new additions stop and retirements erode capacity. Emissions slowly creep back up (22 → 35 Mt by year 15).

### S2: Industrial Collapse (investment_sensitivity=0.2, cost_sensitivity=0.01, cbam_rate=$0)
- Carbon price climbs to **$82** peak (year 7–8) — slow renewables cannot pull it down
- Industry contracts immediately: PCI = 1.30 at $30 (already above 1.20 threshold at t=0)
- **Leakage** (B2b, no CBAM) peaks at **5.4 index units/year** — 5× larger than cost contraction
- Industrial output bottoms at **67.6** (year 12): a **32% collapse**
- Slow recovery as price falls; emissions reach 37 Mt — barely better than solar glut scenario
- **Policy lesson**: Without CBAM, most industrial damage comes from leakage, not the carbon price itself

## Key Policy Insights
1. **CBAM is the difference between manageable and catastrophic**: In S2, removing CBAM caused leakage to dominate over cost contraction 5:1 at peak
2. **Solar glut creates its own trap**: Fast buildout crashes the price signal, removing the incentive for further investment — emissions slowly recover as capacity ages
3. **Both loops achieve similar emission outcomes** (~35–37 Mt at year 15) through radically different paths: clean growth vs. industrial destruction
4. **The `leakage_threshold` ($60) is a critical tipping point**: Once crossed without CBAM, leakage accelerates rapidly and recovery is slow (5%/year)

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
    
        renewable_capacity["Renewable Capacity"]:::stock
        industrial_output["Industrial Output"]:::stock
        carbon_price["Carbon Price"]:::stock
        capacity_addition(["Capacity Addition"]):::flow
        capacity_retirement(["Capacity Retirement"]):::flow
        output_recovery(["Output Recovery"]):::flow
        output_contraction(["Output Contraction"]):::flow
        carbon_leakage_flow(["Carbon Leakage Flow"]):::flow
        price_net_change(["Price Net Change"]):::flow
        investment_sensitivity{{"Investment Sensitivity = 0.5"}}:::constant
        cost_sensitivity{{"Cost Sensitivity = 0.005"}}:::constant
        competitiveness_threshold{{"Competitiveness Threshold = 1.2"}}:::constant
        contraction_sensitivity{{"Contraction Sensitivity = 0.02"}}:::constant
        leakage_threshold{{"Leakage Threshold = 60.0"}}:::constant
        leakage_sensitivity{{"Leakage Sensitivity = 0.003"}}:::constant
        cbam_rate{{"Cbam Rate = 40.0"}}:::constant
        price_sensitivity{{"Price Sensitivity = 0.5"}}:::constant
        capacity_lifetime{{"Capacity Lifetime = 25.0"}}:::constant
        recovery_rate{{"Recovery Rate = 0.05"}}:::constant
        total_energy_demand{{"Total Energy Demand = 500.0"}}:::constant
        base_emissions{{"Base Emissions = 80.0"}}:::constant
        initial_output{{"Initial Output = 100.0"}}:::constant
        emission_target{{"Emission Target = 50.0"}}:::constant
        renewable_fraction[/"Renewable Fraction"/]:::computed
        carbon_emissions[/"Carbon Emissions"/]:::computed
        emission_gap[/"Emission Gap"/]:::computed
        production_cost_index[/"Production Cost Index"/]:::computed
        cbam_effectiveness[/"Cbam Effectiveness"/]:::computed
        net_leakage_pressure[/"Net Leakage Pressure"/]:::computed
    
        capacity_addition ==>|"+"| renewable_capacity
        renewable_capacity ==>|"-"| capacity_retirement
        output_recovery ==>|"+"| industrial_output
        industrial_output ==>|"-"| output_contraction
        industrial_output ==>|"-"| carbon_leakage_flow
        price_net_change ==>|"+"| carbon_price
    
        investment_sensitivity -.-> capacity_addition
        carbon_price -.-> capacity_addition
        capacity_lifetime -.-> capacity_retirement
        recovery_rate -.-> output_recovery
        initial_output -.-> output_recovery
        contraction_sensitivity -.-> output_contraction
        competitiveness_threshold -.-> output_contraction
        production_cost_index -.-> output_contraction
        leakage_sensitivity -.-> carbon_leakage_flow
        net_leakage_pressure -.-> carbon_leakage_flow
        price_sensitivity -.-> price_net_change
        emission_gap -.-> price_net_change
        total_energy_demand -.-> renewable_fraction
        renewable_capacity -.-> renewable_fraction
        industrial_output -.-> carbon_emissions
        base_emissions -.-> carbon_emissions
        renewable_fraction -.-> carbon_emissions
        initial_output -.-> carbon_emissions
        emission_target -.-> emission_gap
        carbon_emissions -.-> emission_gap
        cost_sensitivity -.-> production_cost_index
        carbon_price -.-> production_cost_index
        carbon_price -.-> cbam_effectiveness
        cbam_rate -.-> cbam_effectiveness
        leakage_threshold -.-> net_leakage_pressure
        carbon_price -.-> net_leakage_pressure
        cbam_effectiveness -.-> net_leakage_pressure
        """
        ),
        mo.Html("</div>"),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'renewable_capacity': 'Renewable Capacity (GW)', 'industrial_output': 'Industrial Output (index)', 'carbon_price': 'Carbon Price (USD/tonne)'}
    fig_stocks = go.Figure()
    for _key in stock_selector.value:
        fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    _flow_labels = {'capacity_addition': 'Capacity Addition (GW/year)', 'capacity_retirement': 'Capacity Retirement (GW/year)', 'output_recovery': 'Output Recovery (index/year)', 'output_contraction': 'Output Contraction (index/year)', 'carbon_leakage_flow': 'Carbon Leakage Flow (index/year)', 'price_net_change': 'Price Net Change (USD/tonne/year)'}
    fig_flows = go.Figure()
    for _key in flow_selector.value:
        fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key)))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    _aux_labels = {'renewable_fraction': 'Renewable Fraction (fraction)', 'carbon_emissions': 'Carbon Emissions (Mt CO2/year)', 'emission_gap': 'Emission Gap (Mt CO2/year)', 'production_cost_index': 'Production Cost Index (index)', 'cbam_effectiveness': 'Cbam Effectiveness (fraction)', 'net_leakage_pressure': 'Net Leakage Pressure (USD/tonne)'}
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
