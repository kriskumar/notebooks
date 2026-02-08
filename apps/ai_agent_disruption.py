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
Ai Agent Disruption — Interactive Explorer

System dynamics model with inline Euler integration.
4 stocks, 5 flows, 12 parameters, 6 computed variables.

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
    base_capability_growth,
    base_compute_growth,
    capability_threshold,
    compute_cost_per_unit,
    compute_per_user,
    depreciation_rate,
    displacement_rate,
    imitation_rate,
    innovation_rate,
    potential_market,
    reinvestment_fraction,
    revenue_per_user,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    task_horizon = 1.0
    agent_users = 50.0
    saas_revenue = 300.0
    gpu_compute = 100.0

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        capability_growth = (task_horizon * base_capability_growth.value * gpu_compute / 100)
        compute_depreciation = (gpu_compute * depreciation_rate.value)
        adoption_fraction = (agent_users / potential_market.value)
        remaining_market = (potential_market.value - agent_users)
        ai_revenue = (agent_users * revenue_per_user.value / 1000)
        capability_readiness = (task_horizon / (task_horizon + capability_threshold.value))
        compute_demand = (agent_users * compute_per_user.value)
        compute_investment = (base_compute_growth.value + (ai_revenue * reinvestment_fraction.value / compute_cost_per_unit.value))
        revenue_displacement = (saas_revenue * displacement_rate.value * adoption_fraction * capability_readiness)
        compute_availability = (gpu_compute / (compute_demand + gpu_compute))
        new_adoptions = ((innovation_rate.value + (imitation_rate.value * adoption_fraction)) * remaining_market * capability_readiness * compute_availability)

        rows.append(
            {
                "time": t,
                "task_horizon": task_horizon,
                "agent_users": agent_users,
                "saas_revenue": saas_revenue,
                "gpu_compute": gpu_compute,
                "capability_growth": capability_growth,
                "new_adoptions": new_adoptions,
                "revenue_displacement": revenue_displacement,
                "compute_investment": compute_investment,
                "compute_depreciation": compute_depreciation,
                "adoption_fraction": adoption_fraction,
                "remaining_market": remaining_market,
                "ai_revenue": ai_revenue,
                "capability_readiness": capability_readiness,
                "compute_demand": compute_demand,
                "compute_availability": compute_availability,
            }
        )

        # Euler integration
        task_horizon += dt * capability_growth
        task_horizon = max(task_horizon, 0)
        agent_users += dt * new_adoptions
        agent_users = max(agent_users, 0)
        saas_revenue += dt * (0 - revenue_displacement)
        saas_revenue = max(saas_revenue, 0)
        gpu_compute += dt * (compute_investment - compute_depreciation)
        gpu_compute = max(gpu_compute, 0)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Ai Agent Disruption — Interactive Explorer

    **Stocks:** 4 | **Flows:** 5 | **Parameters:** 12 | **Computed:** 6

    Adjust the sliders below to change parameters and see how the model responds in real time.
    """
    )
    return


@app.cell
def time_controls(mo):
    final_time = mo.ui.number(
        value=20, start=1, stop=200, step=1, label="Final Time"
    )
    time_step = mo.ui.number(
        value=0.25, start=0.1, stop=5.0, step=0.1, label="Time Step"
    )
    mo.hstack([final_time, time_step], justify="start", gap=1)
    return final_time, time_step


@app.cell
def parameter_controls(mo):
    base_capability_growth = mo.ui.slider(
        value=1.2, start=0.3, stop=3.0, step=0.027,
        label="Base Capability Growth (1/yr)",
    )
    innovation_rate = mo.ui.slider(
        value=0.01, start=0.001, stop=0.05, step=0.00049,
        label="Innovation Rate (1/yr)",
    )
    imitation_rate = mo.ui.slider(
        value=0.25, start=0.05, stop=0.6, step=0.0055,
        label="Imitation Rate (1/yr)",
    )
    potential_market = mo.ui.slider(
        value=500.0, start=100.0, stop=1000.0, step=9.0,
        label="Potential Market (million)",
    )
    capability_threshold = mo.ui.slider(
        value=4.0, start=1.0, stop=16.0, step=0.15,
        label="Capability Threshold (hours)",
    )
    displacement_rate = mo.ui.slider(
        value=0.08, start=0.01, stop=0.25, step=0.0024,
        label="Displacement Rate (1/yr)",
    )
    revenue_per_user = mo.ui.slider(
        value=200.0, start=50.0, stop=600.0, step=5.5,
        label="Revenue Per User ($/yr)",
    )
    reinvestment_fraction = mo.ui.slider(
        value=0.5, start=0.1, stop=0.9, step=0.008,
        label="Reinvestment Fraction (dimensionless)",
    )
    compute_per_user = mo.ui.slider(
        value=0.5, start=0.1, stop=3.0, step=0.029,
        label="Compute Per User (units/million)",
    )
    depreciation_rate = mo.ui.slider(
        value=0.15, start=0.05, stop=0.3, step=0.0025,
        label="Depreciation Rate (1/yr)",
    )
    compute_cost_per_unit = mo.ui.slider(
        value=0.5, start=0.1, stop=2.0, step=0.019,
        label="Compute Cost Per Unit ($B)",
    )
    base_compute_growth = mo.ui.slider(
        value=10.0, start=0.0, stop=40.0, step=0.4,
        label="Base Compute Growth (units/yr)",
    )
    mo.vstack(
        [
        base_capability_growth,
        innovation_rate,
        imitation_rate,
        potential_market,
        capability_threshold,
        displacement_rate,
        revenue_per_user,
        reinvestment_fraction,
        compute_per_user,
        depreciation_rate,
        compute_cost_per_unit,
        base_compute_growth,
        ]
    )
    return (
        base_capability_growth,
        base_compute_growth,
        capability_threshold,
        compute_cost_per_unit,
        compute_per_user,
        depreciation_rate,
        displacement_rate,
        imitation_rate,
        innovation_rate,
        potential_market,
        reinvestment_fraction,
        revenue_per_user,
    )


@app.cell
def chart_controls(mo):
    stock_selector = mo.ui.multiselect(
        options={"Task Horizon (hours)": "task_horizon", "Agent Users (million)": "agent_users", "Saas Revenue ($B/yr)": "saas_revenue", "Gpu Compute (units)": "gpu_compute"},
        value=["Task Horizon (hours)", "Agent Users (million)", "Saas Revenue ($B/yr)", "Gpu Compute (units)"],
        label="Stock variables",
    )
    flow_selector = mo.ui.multiselect(
        options={"Capability Growth (hours/yr)": "capability_growth", "New Adoptions (million/yr)": "new_adoptions", "Revenue Displacement ($B/yr/yr)": "revenue_displacement", "Compute Investment (units/yr)": "compute_investment", "Compute Depreciation (units/yr)": "compute_depreciation"},
        value=["Capability Growth (hours/yr)", "New Adoptions (million/yr)", "Revenue Displacement ($B/yr/yr)", "Compute Investment (units/yr)", "Compute Depreciation (units/yr)"],
        label="Flow variables",
    )
    aux_selector = mo.ui.multiselect(
        options={"Adoption Fraction (dimensionless)": "adoption_fraction", "Remaining Market (million)": "remaining_market", "Ai Revenue ($B/yr)": "ai_revenue", "Capability Readiness (dimensionless)": "capability_readiness", "Compute Demand (units)": "compute_demand", "Compute Availability (dimensionless)": "compute_availability"},
        value=["Adoption Fraction (dimensionless)", "Remaining Market (million)", "Ai Revenue ($B/yr)", "Capability Readiness (dimensionless)", "Compute Demand (units)", "Compute Availability (dimensionless)"],
        label="Auxiliary variables",
    )
    return stock_selector, flow_selector, aux_selector


@app.cell
def tabbed_content(aux_selector, flow_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
### Overview
Models the disruption dynamics of AI coding agents displacing traditional SaaS software and information work. Captures five key feedback loops: the Capability Flywheel (R1) where AI revenue funds compute that improves capability, Word-of-Mouth adoption (R2), Compute Constraints (B1) that govern adoption speed, Market Saturation (B2), and the Capability Gate (B3) that delays adoption until agents can handle complex tasks.

At t=0: 50M agent users (10% of 500M knowledge workers), task horizon of 1 hour (simple code completions), $300B traditional SaaS revenue, and $10B AI agent revenue. The central tension: capability doubles every ~7 months but compute investment must keep pace to sustain growth.

Key feedback loops:
- (R1) Capability Flywheel: AI revenue → compute investment → GPU capacity → capability growth → longer task horizon → more adoption → more AI revenue
- (R2) Word of Mouth: More agent users → higher adoption fraction → stronger imitation effect → more new adoptions → more agent users
- (B1) Compute Constraint: More agent users → higher compute demand → lower compute availability → slower adoption. Anthropic's growth being 'constrained by compute' is this loop in action.
- (B2) Market Saturation: More agent users → smaller remaining market → fewer new adoptions
- (B3) Capability Gate: Low task horizon → low capability readiness → slow adoption (releases as capability grows past threshold)

### Learning Objectives
- Understand how exponential capability growth (7-month doubling) creates S-curve adoption dynamics with a tipping point
- Explore the compute constraint as a natural governor on AI disruption speed — and what happens when it relaxes
- Analyze the disruption tipping point where capability_readiness × adoption_fraction accelerates SaaS displacement nonlinearly
- See how the Capability Flywheel (R1) creates winner-take-all dynamics — revenue funds compute that funds capability
- Compare disruption timelines: when does SaaS revenue decline by 50%? How sensitive is this to the capability threshold?
- Understand the Azure vs Copilot dilemma: compute used for inference can't be sold as cloud capacity

### Scenarios
**Current Trajectory** -- Default parameters — watch the capability readiness inflection around year 2-3 as task horizon crosses the 4-hour threshold, triggering acceleration in both adoption and SaaS displacement.

**Compute Constrained** -- Reduced infrastructure investment. Adoption stalls as compute can't keep pace with demand — the Anthropic bottleneck scenario.  
Parameters: `base_compute_growth=3`, `reinvestment_fraction=0.3`, `compute_per_user=1.0`

**Rapid Disruption** -- Breakthrough capability growth + viral adoption + aggressive displacement. Compresses the disruption timeline by 5+ years.  
Parameters: `base_capability_growth=2.0`, `imitation_rate=0.4`, `displacement_rate=0.15`

**SaaS Resilience** -- Incumbents are stickier than expected — enterprise switching costs, compliance requirements, and agents needing much longer task horizons to displace complex workflows.  
Parameters: `displacement_rate=0.03`, `capability_threshold=10`, `innovation_rate=0.005`

### Customization Tips
- Increase base_capability_growth to 2.0-2.5 for architecture breakthroughs (e.g., o3-like reasoning improvements)
- Lower capability_threshold to 2 hours to model developer-only disruption (coding is easier than general knowledge work)
- Raise compute_per_user to 1.5-2.0 for compute-intensive agentic workflows (multi-step reasoning, tool use chains)
- Set base_compute_growth to 0 to see how dependent disruption is on the R1 flywheel alone
- Increase imitation_rate to 0.4-0.5 for viral team-level adoption (entire engineering orgs switching at once)
- Lower compute_cost_per_unit to 0.2 to model hardware efficiency gains (smaller models, better inference chips)
- Raise revenue_per_user to 400-500 to model premium enterprise agent pricing
- Set displacement_rate to 0.15-0.20 for aggressive 'agents replace entire tool categories' scenarios

### Related Concepts
- Bass diffusion model — S-curve adoption with innovation (p) and imitation (q) coefficients
- Christensen's disruption theory — AI agents as low-end disruption that moves upmarket
- METR AI agent benchmarks — empirical measurement of task horizon expansion
- SaaS unit economics — how ~75% gross margins compress when agents bypass UI-based workflows
- Azure vs Copilot capacity allocation — Microsoft's GPU compute as zero-sum between cloud and AI
- Wright's Law / experience curves — declining cost of intelligence per unit of useful work
- Jevons paradox — cheaper AI could increase total compute demand rather than reduce it
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
    
        task_horizon["Task Horizon"]:::stock
        agent_users["Agent Users"]:::stock
        saas_revenue["Saas Revenue"]:::stock
        gpu_compute["Gpu Compute"]:::stock
        capability_growth(["Capability Growth"]):::flow
        new_adoptions(["New Adoptions"]):::flow
        revenue_displacement(["Revenue Displacement"]):::flow
        compute_investment(["Compute Investment"]):::flow
        compute_depreciation(["Compute Depreciation"]):::flow
        base_capability_growth{{"Base Capability Growth = 1.2"}}:::constant
        innovation_rate{{"Innovation Rate = 0.01"}}:::constant
        imitation_rate{{"Imitation Rate = 0.25"}}:::constant
        potential_market{{"Potential Market = 500.0"}}:::constant
        capability_threshold{{"Capability Threshold = 4.0"}}:::constant
        displacement_rate{{"Displacement Rate = 0.08"}}:::constant
        revenue_per_user{{"Revenue Per User = 200.0"}}:::constant
        reinvestment_fraction{{"Reinvestment Fraction = 0.5"}}:::constant
        compute_per_user{{"Compute Per User = 0.5"}}:::constant
        depreciation_rate{{"Depreciation Rate = 0.15"}}:::constant
        compute_cost_per_unit{{"Compute Cost Per Unit = 0.5"}}:::constant
        base_compute_growth{{"Base Compute Growth = 10.0"}}:::constant
        adoption_fraction[/"Adoption Fraction"/]:::computed
        remaining_market[/"Remaining Market"/]:::computed
        ai_revenue[/"Ai Revenue"/]:::computed
        capability_readiness[/"Capability Readiness"/]:::computed
        compute_demand[/"Compute Demand"/]:::computed
        compute_availability[/"Compute Availability"/]:::computed
    
        capability_growth ==>|"+"| task_horizon
        new_adoptions ==>|"+"| agent_users
        saas_revenue ==>|"-"| revenue_displacement
        compute_investment ==>|"+"| gpu_compute
        gpu_compute ==>|"-"| compute_depreciation
    
        base_capability_growth -.-> capability_growth
        gpu_compute -.-> capability_growth
        remaining_market -.-> new_adoptions
        adoption_fraction -.-> new_adoptions
        imitation_rate -.-> new_adoptions
        innovation_rate -.-> new_adoptions
        capability_readiness -.-> new_adoptions
        compute_availability -.-> new_adoptions
        capability_readiness -.-> revenue_displacement
        adoption_fraction -.-> revenue_displacement
        displacement_rate -.-> revenue_displacement
        reinvestment_fraction -.-> compute_investment
        compute_cost_per_unit -.-> compute_investment
        base_compute_growth -.-> compute_investment
        ai_revenue -.-> compute_investment
        depreciation_rate -.-> compute_depreciation
        agent_users -.-> adoption_fraction
        potential_market -.-> adoption_fraction
        agent_users -.-> remaining_market
        potential_market -.-> remaining_market
        revenue_per_user -.-> ai_revenue
        agent_users -.-> ai_revenue
        capability_threshold -.-> capability_readiness
        task_horizon -.-> capability_readiness
        agent_users -.-> compute_demand
        compute_per_user -.-> compute_demand
        gpu_compute -.-> compute_availability
        compute_demand -.-> compute_availability
        """
        ),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'task_horizon': 'Task Horizon (hours)', 'agent_users': 'Agent Users (million)', 'saas_revenue': 'Saas Revenue ($B/yr)', 'gpu_compute': 'Gpu Compute (units)'}
    fig_stocks = go.Figure()
    for _key in stock_selector.value:
        fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    _flow_labels = {'capability_growth': 'Capability Growth (hours/yr)', 'new_adoptions': 'New Adoptions (million/yr)', 'revenue_displacement': 'Revenue Displacement ($B/yr/yr)', 'compute_investment': 'Compute Investment (units/yr)', 'compute_depreciation': 'Compute Depreciation (units/yr)'}
    fig_flows = go.Figure()
    for _key in flow_selector.value:
        fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key)))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    _aux_labels = {'adoption_fraction': 'Adoption Fraction (dimensionless)', 'remaining_market': 'Remaining Market (million)', 'ai_revenue': 'Ai Revenue ($B/yr)', 'capability_readiness': 'Capability Readiness (dimensionless)', 'compute_demand': 'Compute Demand (units)', 'compute_availability': 'Compute Availability (dimensionless)'}
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
