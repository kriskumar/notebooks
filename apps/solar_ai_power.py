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
Solar Ai Power — Interactive Explorer

System dynamics model with inline Euler integration.
5 stocks, 7 flows, 11 parameters, 5 computed variables.

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
    battery_efficiency,
    battery_lifetime,
    capacity_factor,
    connection_rate,
    cost_learning_rate,
    demand_growth_rate,
    discharge_hours,
    panel_lifetime,
    solar_investment,
    storage_investment,
    storage_unit_cost,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    solar_capacity = 2300.0
    data_center_demand = 50.0
    solar_cost = 1.0
    battery_storage = 200.0
    grid_queue = 1100.0

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        project_submissions = (solar_investment.value / max(solar_cost, 1e-6))
        grid_connections = (grid_queue * connection_rate.value)
        panel_retirements = (solar_capacity / panel_lifetime.value)
        demand_increase = (data_center_demand * demand_growth_rate.value)
        cost_reduction = (solar_cost * cost_learning_rate.value)
        storage_deployed = (storage_investment.value / storage_unit_cost.value)
        storage_retired = (battery_storage / battery_lifetime.value)
        solar_power_output = (solar_capacity * capacity_factor.value)
        dispatchable_storage = (battery_storage * battery_efficiency.value / discharge_hours.value)
        queue_pressure = (grid_queue / max(solar_capacity, 1e-6))
        total_clean_power = (solar_power_output + dispatchable_storage)
        clean_to_demand_ratio = (total_clean_power / max(data_center_demand, 1e-6))

        rows.append(
            {
                "time": t,
                "solar_capacity": solar_capacity,
                "data_center_demand": data_center_demand,
                "solar_cost": solar_cost,
                "battery_storage": battery_storage,
                "grid_queue": grid_queue,
                "project_submissions": project_submissions,
                "grid_connections": grid_connections,
                "panel_retirements": panel_retirements,
                "demand_increase": demand_increase,
                "cost_reduction": cost_reduction,
                "storage_deployed": storage_deployed,
                "storage_retired": storage_retired,
                "solar_power_output": solar_power_output,
                "dispatchable_storage": dispatchable_storage,
                "total_clean_power": total_clean_power,
                "clean_to_demand_ratio": clean_to_demand_ratio,
                "queue_pressure": queue_pressure,
            }
        )

        # Euler integration
        solar_capacity += dt * (grid_connections - panel_retirements)
        solar_capacity = max(solar_capacity, 0)
        data_center_demand += dt * demand_increase
        data_center_demand = max(data_center_demand, 0)
        solar_cost += dt * (0 - cost_reduction)
        solar_cost = max(solar_cost, 0.01)
        battery_storage += dt * (storage_deployed - storage_retired)
        battery_storage = max(battery_storage, 0)
        grid_queue += dt * (project_submissions - grid_connections)
        grid_queue = max(grid_queue, 0)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Solar Ai Power — Interactive Explorer

    **Stocks:** 5 | **Flows:** 7 | **Parameters:** 11 | **Computed:** 5

    Adjust the sliders below to change parameters and see how the model responds in real time.
    """
    )
    return


@app.cell
def time_controls(mo):
    final_time = mo.ui.number(
        value=30, start=1, stop=300, step=1, label="Final Time"
    )
    time_step = mo.ui.number(
        value=0.5, start=0.1, stop=5.0, step=0.1, label="Time Step"
    )
    mo.hstack([final_time, time_step], justify="start", gap=1)
    return final_time, time_step


@app.cell
def parameter_controls(mo):
    solar_investment = mo.ui.slider(
        value=400.0, start=50.0, stop=2000.0, step=19.5,
        label="Solar Investment (billion$/year)",
    )
    panel_lifetime = mo.ui.slider(
        value=30.0, start=15.0, stop=40.0, step=0.25,
        label="Panel Lifetime (years)",
    )
    demand_growth_rate = mo.ui.slider(
        value=0.22, start=0.05, stop=0.5, step=0.0045,
        label="Demand Growth Rate (1/year)",
    )
    cost_learning_rate = mo.ui.slider(
        value=0.1, start=0.02, stop=0.2, step=0.0018,
        label="Cost Learning Rate (1/year)",
    )
    storage_investment = mo.ui.slider(
        value=50.0, start=5.0, stop=500.0, step=4.95,
        label="Storage Investment (billion$/year)",
    )
    storage_unit_cost = mo.ui.slider(
        value=0.15, start=0.05, stop=0.5, step=0.0045,
        label="Storage Unit Cost (billion$/GWh)",
    )
    connection_rate = mo.ui.slider(
        value=0.5, start=0.1, stop=0.8, step=0.007,
        label="Connection Rate (1/year)",
    )
    capacity_factor = mo.ui.slider(
        value=0.25, start=0.1, stop=0.4, step=0.003,
        label="Capacity Factor (dimensionless)",
    )
    battery_lifetime = mo.ui.slider(
        value=15.0, start=8.0, stop=25.0, step=0.17,
        label="Battery Lifetime (years)",
    )
    discharge_hours = mo.ui.slider(
        value=4.0, start=1.0, stop=12.0, step=0.11,
        label="Discharge Hours (hours)",
    )
    battery_efficiency = mo.ui.slider(
        value=0.9, start=0.8, stop=0.95, step=0.0015,
        label="Battery Efficiency (dimensionless)",
    )
    mo.vstack(
        [
        solar_investment,
        panel_lifetime,
        demand_growth_rate,
        cost_learning_rate,
        storage_investment,
        storage_unit_cost,
        connection_rate,
        capacity_factor,
        battery_lifetime,
        discharge_hours,
        battery_efficiency,
        ]
    )
    return (
        battery_efficiency,
        battery_lifetime,
        capacity_factor,
        connection_rate,
        cost_learning_rate,
        demand_growth_rate,
        discharge_hours,
        panel_lifetime,
        solar_investment,
        storage_investment,
        storage_unit_cost,
    )


@app.cell
def tabbed_content(go, mo, results):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
### Overview
Models the race between solar+storage deployment and AI-driven electricity demand growth. Key feedback loops: (R1) solar cost learning — cheaper panels attract more investment, driving more deployment, further reducing costs; (B1) grid interconnection bottleneck — falling costs flood the queue with projects, but connection_rate limits how fast they go online; (B2) panel retirements balance capacity growth. The critical metric is clean_to_demand_ratio: when it drops below 1, fossil fuels must fill the AI power gap. With default parameters, solar starts 12x ahead but AI demand's 22%/yr exponential growth steadily closes the gap.

### Learning Objectives
- Understand the exponential dynamics of both solar cost decline and AI demand growth
- Explore how grid interconnection bottlenecks constrain clean energy deployment
- Analyze the role of battery storage in making solar viable for 24/7 data center loads
- Compare scenarios where solar wins vs where fossil fuels must fill the gap
- Learn how investment levels and policy choices affect the energy transition timeline

### Scenarios
**US Grid Bottleneck** -- US-only scenario with severe interconnection delays (14% approval rate) and aggressive AI demand  
Parameters: `connection_rate=0.14`, `solar_investment=100`, `demand_growth_rate=0.25`

**Global Fast Transition** -- Doubled investment with fast learning — can solar outrun AI demand?  
Parameters: `solar_investment=800`, `storage_investment=200`, `cost_learning_rate=0.15`

**AI Slowdown** -- AI demand grows at 10%/yr instead of 22% — efficiency gains and market saturation  
Parameters: `demand_growth_rate=0.1`

### Customization Tips
- Adjust demand_growth_rate (default 22%/yr) to explore AI boom vs slowdown scenarios
- Lower connection_rate to 0.14 to model US-only grid bottleneck dynamics
- Increase solar_investment above $400B to simulate policy-driven deployment push
- Change cost_learning_rate to see impact of faster/slower technology improvement
- Set discharge_hours to 8-12 for long-duration storage scenarios
- Increase storage_investment to model aggressive battery buildout alongside solar
- Adjust capacity_factor (0.10-0.40) to compare cloudy vs sunny regions

### Related Concepts
- Wright's Law / Swanson's Law for solar
- Grid interconnection queue bottleneck
- AI data center power density (100+ kW/rack)
- Solar capacity factor and intermittency
- Battery storage for solar firming
- Levelized cost of energy (LCOE)
- Hyperscaler energy procurement (PPAs)
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
    
        solar_capacity["Solar Capacity"]:::stock
        data_center_demand["Data Center Demand"]:::stock
        solar_cost["Solar Cost"]:::stock
        battery_storage["Battery Storage"]:::stock
        grid_queue["Grid Queue"]:::stock
        project_submissions(["Project Submissions"]):::flow
        grid_connections(["Grid Connections"]):::flow
        panel_retirements(["Panel Retirements"]):::flow
        demand_increase(["Demand Increase"]):::flow
        cost_reduction(["Cost Reduction"]):::flow
        storage_deployed(["Storage Deployed"]):::flow
        storage_retired(["Storage Retired"]):::flow
        solar_investment{{"Solar Investment = 400.0"}}:::constant
        panel_lifetime{{"Panel Lifetime = 30.0"}}:::constant
        demand_growth_rate{{"Demand Growth Rate = 0.22"}}:::constant
        cost_learning_rate{{"Cost Learning Rate = 0.1"}}:::constant
        storage_investment{{"Storage Investment = 50.0"}}:::constant
        storage_unit_cost{{"Storage Unit Cost = 0.15"}}:::constant
        connection_rate{{"Connection Rate = 0.5"}}:::constant
        capacity_factor{{"Capacity Factor = 0.25"}}:::constant
        battery_lifetime{{"Battery Lifetime = 15.0"}}:::constant
        discharge_hours{{"Discharge Hours = 4.0"}}:::constant
        battery_efficiency{{"Battery Efficiency = 0.9"}}:::constant
        solar_power_output[/"Solar Power Output"/]:::computed
        dispatchable_storage[/"Dispatchable Storage"/]:::computed
        total_clean_power[/"Total Clean Power"/]:::computed
        clean_to_demand_ratio[/"Clean To Demand Ratio"/]:::computed
        queue_pressure[/"Queue Pressure"/]:::computed
    
        grid_connections ==>|"+"| solar_capacity
        solar_capacity ==>|"-"| panel_retirements
        demand_increase ==>|"+"| data_center_demand
        solar_cost ==>|"-"| cost_reduction
        storage_deployed ==>|"+"| battery_storage
        battery_storage ==>|"-"| storage_retired
        project_submissions ==>|"+"| grid_queue
        grid_queue ==>|"-"| grid_connections
    
        solar_cost -.-> project_submissions
        solar_investment -.-> project_submissions
        connection_rate -.-> grid_connections
        panel_lifetime -.-> panel_retirements
        demand_growth_rate -.-> demand_increase
        cost_learning_rate -.-> cost_reduction
        storage_unit_cost -.-> storage_deployed
        storage_investment -.-> storage_deployed
        battery_lifetime -.-> storage_retired
        solar_capacity -.-> solar_power_output
        capacity_factor -.-> solar_power_output
        battery_storage -.-> dispatchable_storage
        battery_efficiency -.-> dispatchable_storage
        discharge_hours -.-> dispatchable_storage
        dispatchable_storage -.-> total_clean_power
        solar_power_output -.-> total_clean_power
        total_clean_power -.-> clean_to_demand_ratio
        data_center_demand -.-> clean_to_demand_ratio
        grid_queue -.-> queue_pressure
        solar_capacity -.-> queue_pressure
        """
        ),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    fig_stocks = go.Figure()
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["solar_capacity"], mode="lines", name="Solar Capacity (GW)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["data_center_demand"], mode="lines", name="Data Center Demand (GW)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["solar_cost"], mode="lines", name="Solar Cost ($/W)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["battery_storage"], mode="lines", name="Battery Storage (GWh)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["grid_queue"], mode="lines", name="Grid Queue (GW)"))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    fig_flows = go.Figure()
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["project_submissions"], mode="lines", name="Project Submissions (GW/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["grid_connections"], mode="lines", name="Grid Connections (GW/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["panel_retirements"], mode="lines", name="Panel Retirements (GW/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["demand_increase"], mode="lines", name="Demand Increase (GW/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["cost_reduction"], mode="lines", name="Cost Reduction ($/W/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["storage_deployed"], mode="lines", name="Storage Deployed (GWh/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["storage_retired"], mode="lines", name="Storage Retired (GWh/year)"))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    fig_aux = go.Figure()
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["solar_power_output"], mode="lines", name="Solar Power Output (GW)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["dispatchable_storage"], mode="lines", name="Dispatchable Storage (GW)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["total_clean_power"], mode="lines", name="Total Clean Power (GW)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["clean_to_demand_ratio"], mode="lines", name="Clean To Demand Ratio (dimensionless)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["queue_pressure"], mode="lines", name="Queue Pressure (dimensionless)"))
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
