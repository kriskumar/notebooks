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
Sodium Battery Energy — Interactive Explorer

System dynamics model with inline Euler integration.
5 stocks, 6 flows, 11 parameters, 6 computed variables.

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
    baseline_growth_rate,
    battery_lifetime,
    capacity_utilization,
    coal_base_price,
    coal_retirement_rate,
    cost_decline_rate,
    discharge_hours,
    gas_base_price,
    gas_retirement_rate,
    investment_budget,
    round_trip_efficiency,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    installed_capacity = 100.0
    unit_cost = 0.08
    total_demand = 5000.0
    gas_generation = 1500.0
    coal_generation = 2000.0

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        new_installations = (investment_budget.value / max(unit_cost, 1e-6))
        retirements = (installed_capacity / battery_lifetime.value)
        cost_reduction = (unit_cost * cost_decline_rate.value)
        demand_growth = (total_demand * baseline_growth_rate.value)
        dispatchable_power = (installed_capacity * round_trip_efficiency.value * capacity_utilization.value / discharge_hours.value)
        cost_per_kwh = (unit_cost * 1000)
        gas_price = (gas_base_price.value * gas_generation / 1500)
        coal_price = (coal_base_price.value * coal_generation / 2000)
        net_peak_demand = (total_demand - dispatchable_power)
        storage_penetration = (dispatchable_power / max(total_demand, 1e-6))
        gas_displaced = (gas_generation * storage_penetration * gas_retirement_rate.value)
        coal_displaced = (coal_generation * storage_penetration * coal_retirement_rate.value)

        rows.append(
            {
                "time": t,
                "installed_capacity": installed_capacity,
                "unit_cost": unit_cost,
                "total_demand": total_demand,
                "gas_generation": gas_generation,
                "coal_generation": coal_generation,
                "new_installations": new_installations,
                "retirements": retirements,
                "cost_reduction": cost_reduction,
                "demand_growth": demand_growth,
                "gas_displaced": gas_displaced,
                "coal_displaced": coal_displaced,
                "dispatchable_power": dispatchable_power,
                "net_peak_demand": net_peak_demand,
                "storage_penetration": storage_penetration,
                "cost_per_kwh": cost_per_kwh,
                "gas_price": gas_price,
                "coal_price": coal_price,
            }
        )

        # Euler integration
        installed_capacity += dt * (new_installations - retirements)
        installed_capacity = max(installed_capacity, 0)
        unit_cost += dt * (0 - cost_reduction)
        unit_cost = max(unit_cost, 0.001)
        total_demand += dt * demand_growth
        total_demand = max(total_demand, 0)
        gas_generation += dt * (0 - gas_displaced)
        gas_generation = max(gas_generation, 0)
        coal_generation += dt * (0 - coal_displaced)
        coal_generation = max(coal_generation, 0)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Sodium Battery Energy — Interactive Explorer

    **Stocks:** 5 | **Flows:** 6 | **Parameters:** 11 | **Computed:** 6

    Adjust the sliders below to change parameters and see how the model responds in real time.
    """
    )
    return


@app.cell
def time_controls(mo):
    final_time = mo.ui.number(
        value=50, start=1, stop=500, step=1, label="Final Time"
    )
    time_step = mo.ui.number(
        value=0.5, start=0.1, stop=5.0, step=0.1, label="Time Step"
    )
    mo.hstack([final_time, time_step], justify="start", gap=1)
    return final_time, time_step


@app.cell
def parameter_controls(mo):
    investment_budget = mo.ui.slider(
        value=50.0, start=5.0, stop=500.0, step=4.95,
        label="Investment Budget (billion$/year)",
    )
    battery_lifetime = mo.ui.slider(
        value=15.0, start=5.0, stop=30.0, step=0.25,
        label="Battery Lifetime (years)",
    )
    round_trip_efficiency = mo.ui.slider(
        value=0.85, start=0.5, stop=0.99, step=0.0049,
        label="Round Trip Efficiency (dimensionless)",
    )
    discharge_hours = mo.ui.slider(
        value=4.0, start=1.0, stop=12.0, step=0.11,
        label="Discharge Hours (hours)",
    )
    baseline_growth_rate = mo.ui.slider(
        value=0.02, start=0.0, stop=0.1, step=0.001,
        label="Baseline Growth Rate (1/year)",
    )
    cost_decline_rate = mo.ui.slider(
        value=0.08, start=0.0, stop=0.2, step=0.002,
        label="Cost Decline Rate (1/year)",
    )
    capacity_utilization = mo.ui.slider(
        value=0.7, start=0.3, stop=0.95, step=0.0065,
        label="Capacity Utilization (dimensionless)",
    )
    gas_retirement_rate = mo.ui.slider(
        value=0.05, start=0.01, stop=0.15, step=0.0014,
        label="Gas Retirement Rate (1/year)",
    )
    coal_retirement_rate = mo.ui.slider(
        value=0.03, start=0.01, stop=0.1, step=0.0009,
        label="Coal Retirement Rate (1/year)",
    )
    gas_base_price = mo.ui.slider(
        value=4.0, start=1.0, stop=15.0, step=0.14,
        label="Gas Base Price ($/MMBtu)",
    )
    coal_base_price = mo.ui.slider(
        value=60.0, start=20.0, stop=200.0, step=1.8,
        label="Coal Base Price ($/ton)",
    )
    mo.vstack(
        [
        investment_budget,
        battery_lifetime,
        round_trip_efficiency,
        discharge_hours,
        baseline_growth_rate,
        cost_decline_rate,
        capacity_utilization,
        gas_retirement_rate,
        coal_retirement_rate,
        gas_base_price,
        coal_base_price,
        ]
    )
    return (
        baseline_growth_rate,
        battery_lifetime,
        capacity_utilization,
        coal_base_price,
        coal_retirement_rate,
        cost_decline_rate,
        discharge_hours,
        gas_base_price,
        gas_retirement_rate,
        investment_budget,
        round_trip_efficiency,
    )


@app.cell
def tabbed_content(go, mo, results):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
### Overview
Models the full energy transition chain: sodium-ion battery cost decline -> storage deployment -> fossil fuel displacement -> gas & coal price collapse. Key loops: (R1) lower costs -> more installations -> more production -> lower costs; (B1) capacity retirements; (B2) growing demand vs. storage; (B3) storage penetration drives gas displacement; (B4) storage penetration drives coal displacement. Solar+storage becomes the cheapest source as battery costs fall exponentially, making gas peakers and coal baseload uneconomic.

### Learning Objectives
- Understand exponential cost decline dynamics
- Explore feedback between investment, cost, and deployment
- Analyze peak demand displacement by storage
- Compare conservative vs aggressive technology scenarios
- Learn stock-flow modeling of technology adoption
- See how cheap storage drives fossil fuel demand and price decline
- Explore the dynamics of energy transition tipping points

### Scenarios
**Conservative Scenario** -- Lower investment, slower cost decline, modest demand growth — gas and coal decline slowly  
Parameters: `investment_budget=20`, `cost_decline_rate=0.04`, `baseline_growth_rate=0.01`

**Aggressive Deployment** -- Massive investment, fast learning, long-duration storage — rapid fossil displacement  
Parameters: `investment_budget=150`, `cost_decline_rate=0.12`, `discharge_hours=8`

**Coal Phase-Out Policy** -- Policy-driven coal retirement with moderate gas transition  
Parameters: `coal_retirement_rate=0.08`, `gas_retirement_rate=0.03`, `investment_budget=80`

### Customization Tips
- Adjust investment_budget (default $50B/yr) to model different policy scenarios
- Change cost_decline_rate (default 8%/yr) for optimistic vs conservative technology learning
- Modify battery_lifetime (default 15yr) for different chemistries
- Vary discharge_hours (1-12) to compare short-duration vs long-duration storage
- Set baseline_growth_rate to 0 for a flat-demand scenario
- Increase gas_retirement_rate to model faster gas peaker displacement
- Raise coal_retirement_rate to simulate policy-driven coal phase-out
- Adjust gas_base_price and coal_base_price for regional price differences

### Related Concepts
- Wright's law / learning curves
- Grid-scale energy storage
- Peak demand shaving
- Renewable energy integration
- Sodium-ion vs lithium-ion chemistry
- Fossil fuel stranded assets
- Merit order effect
- Solar + storage levelized cost
"""),
    ])

    # --- Model Structure tab ---
    mermaid_diagram = mo.vstack([
        mo.md("## Model Structure"),
        mo.mermaid(
            """
    graph TD
        classDef stock fill:#4a90d9,stroke:#2c5f8a,color:white,stroke-width:3px
        classDef flow fill:#e8a838,stroke:#b8842c,color:white,stroke-width:2px
        classDef constant fill:#7bc67e,stroke:#5a9d5c,color:white
        classDef computed fill:#c084fc,stroke:#9333ea,color:white
    
        installed_capacity["Installed Capacity"]:::stock
        unit_cost["Unit Cost"]:::stock
        total_demand["Total Demand"]:::stock
        gas_generation["Gas Generation"]:::stock
        coal_generation["Coal Generation"]:::stock
        new_installations(["New Installations"]):::flow
        retirements(["Retirements"]):::flow
        cost_reduction(["Cost Reduction"]):::flow
        demand_growth(["Demand Growth"]):::flow
        gas_displaced(["Gas Displaced"]):::flow
        coal_displaced(["Coal Displaced"]):::flow
        investment_budget{{"Investment Budget = 50.0"}}:::constant
        battery_lifetime{{"Battery Lifetime = 15.0"}}:::constant
        round_trip_efficiency{{"Round Trip Efficiency = 0.85"}}:::constant
        discharge_hours{{"Discharge Hours = 4.0"}}:::constant
        baseline_growth_rate{{"Baseline Growth Rate = 0.02"}}:::constant
        cost_decline_rate{{"Cost Decline Rate = 0.08"}}:::constant
        capacity_utilization{{"Capacity Utilization = 0.7"}}:::constant
        gas_retirement_rate{{"Gas Retirement Rate = 0.05"}}:::constant
        coal_retirement_rate{{"Coal Retirement Rate = 0.03"}}:::constant
        gas_base_price{{"Gas Base Price = 4.0"}}:::constant
        coal_base_price{{"Coal Base Price = 60.0"}}:::constant
        dispatchable_power[/"Dispatchable Power"/]:::computed
        net_peak_demand[/"Net Peak Demand"/]:::computed
        storage_penetration[/"Storage Penetration"/]:::computed
        cost_per_kwh[/"Cost Per Kwh"/]:::computed
        gas_price[/"Gas Price"/]:::computed
        coal_price[/"Coal Price"/]:::computed
    
        new_installations ==>|"+"| installed_capacity
        installed_capacity ==>|"-"| retirements
        unit_cost ==>|"-"| cost_reduction
        demand_growth ==>|"+"| total_demand
        gas_generation ==>|"-"| gas_displaced
        coal_generation ==>|"-"| coal_displaced
    
        unit_cost -.-> new_installations
        investment_budget -.-> new_installations
        battery_lifetime -.-> retirements
        cost_decline_rate -.-> cost_reduction
        baseline_growth_rate -.-> demand_growth
        storage_penetration -.-> gas_displaced
        gas_retirement_rate -.-> gas_displaced
        storage_penetration -.-> coal_displaced
        coal_retirement_rate -.-> coal_displaced
        round_trip_efficiency -.-> dispatchable_power
        installed_capacity -.-> dispatchable_power
        discharge_hours -.-> dispatchable_power
        capacity_utilization -.-> dispatchable_power
        dispatchable_power -.-> net_peak_demand
        total_demand -.-> net_peak_demand
        dispatchable_power -.-> storage_penetration
        total_demand -.-> storage_penetration
        unit_cost -.-> cost_per_kwh
        gas_generation -.-> gas_price
        gas_base_price -.-> gas_price
        coal_generation -.-> coal_price
        coal_base_price -.-> coal_price
        """
        ),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    fig_stocks = go.Figure()
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["installed_capacity"], mode="lines", name="Installed Capacity (GWh)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["unit_cost"], mode="lines", name="Unit Cost (billion$/GWh)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["total_demand"], mode="lines", name="Total Demand (GW)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["gas_generation"], mode="lines", name="Gas Generation (GW)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["coal_generation"], mode="lines", name="Coal Generation (GW)"))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    fig_flows = go.Figure()
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["new_installations"], mode="lines", name="New Installations (GWh/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["retirements"], mode="lines", name="Retirements (GWh/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["cost_reduction"], mode="lines", name="Cost Reduction (billion$/GWh/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["demand_growth"], mode="lines", name="Demand Growth (GW/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["gas_displaced"], mode="lines", name="Gas Displaced (GW/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["coal_displaced"], mode="lines", name="Coal Displaced (GW/year)"))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    fig_aux = go.Figure()
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["dispatchable_power"], mode="lines", name="Dispatchable Power (GW)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["net_peak_demand"], mode="lines", name="Net Peak Demand (GW)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["storage_penetration"], mode="lines", name="Storage Penetration (dimensionless)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["cost_per_kwh"], mode="lines", name="Cost Per Kwh ($/kWh)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["gas_price"], mode="lines", name="Gas Price ($/MMBtu)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["coal_price"], mode="lines", name="Coal Price ($/ton)"))
    fig_aux.update_layout(title="Computed Auxiliary Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    simulation_content = mo.vstack([
        mo.ui.plotly(fig_stocks),
        mo.ui.plotly(fig_flows),
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
