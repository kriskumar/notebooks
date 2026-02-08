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
Ai Capex Dynamics — Interactive Explorer

System dynamics model with inline Euler integration.
4 stocks, 6 flows, 10 parameters, 5 computed variables.

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
    base_capex_rate,
    base_hiring_rate,
    base_tech_workforce,
    deployment_lag,
    displacement_intensity,
    expected_roi,
    infrastructure_life,
    reference_valuation,
    revenue_per_capacity,
    valuation_sensitivity,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    deployment_pipeline = 400.0
    ai_infrastructure = 500.0
    market_cap = 15.0
    tech_employment = 6.0

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        new_capex = (base_capex_rate.value * market_cap / reference_valuation.value)
        capacity_deployed = (deployment_pipeline / deployment_lag.value)
        capacity_retired = (ai_infrastructure / infrastructure_life.value)
        tech_hiring = (tech_employment * base_hiring_rate.value)
        job_displacement = (ai_infrastructure * displacement_intensity.value)
        ai_revenue = (ai_infrastructure * revenue_per_capacity.value * tech_employment / base_tech_workforce.value)
        employment_ratio = (tech_employment / base_tech_workforce.value)
        actual_roi = (ai_revenue / max(ai_infrastructure, 1e-6))
        pe_ratio = (market_cap * 1000 / max(ai_revenue, 1e-6))
        returns_gap = (actual_roi - expected_roi.value)
        valuation_adjustment = (market_cap * valuation_sensitivity.value * returns_gap)

        rows.append(
            {
                "time": t,
                "deployment_pipeline": deployment_pipeline,
                "ai_infrastructure": ai_infrastructure,
                "market_cap": market_cap,
                "tech_employment": tech_employment,
                "new_capex": new_capex,
                "capacity_deployed": capacity_deployed,
                "capacity_retired": capacity_retired,
                "valuation_adjustment": valuation_adjustment,
                "tech_hiring": tech_hiring,
                "job_displacement": job_displacement,
                "ai_revenue": ai_revenue,
                "actual_roi": actual_roi,
                "returns_gap": returns_gap,
                "pe_ratio": pe_ratio,
                "employment_ratio": employment_ratio,
            }
        )

        # Euler integration
        deployment_pipeline += dt * (new_capex - capacity_deployed)
        deployment_pipeline = max(deployment_pipeline, 0)
        ai_infrastructure += dt * (capacity_deployed - capacity_retired)
        ai_infrastructure = max(ai_infrastructure, 0)
        market_cap += dt * valuation_adjustment
        market_cap = max(market_cap, 1)
        tech_employment += dt * (tech_hiring - job_displacement)
        tech_employment = max(tech_employment, 0)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Ai Capex Dynamics — Interactive Explorer

    **Stocks:** 4 | **Flows:** 6 | **Parameters:** 10 | **Computed:** 5

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
        value=0.5, start=0.1, stop=5.0, step=0.1, label="Time Step"
    )
    mo.hstack([final_time, time_step], justify="start", gap=1)
    return final_time, time_step


@app.cell
def parameter_controls(mo):
    base_capex_rate = mo.ui.slider(
        value=200.0, start=50.0, stop=500.0, step=4.5,
        label="Base Capex Rate (billion$/year)",
    )
    reference_valuation = mo.ui.slider(
        value=15.0, start=5.0, stop=30.0, step=0.25,
        label="Reference Valuation (trillion$)",
    )
    deployment_lag = mo.ui.slider(
        value=4.0, start=2.0, stop=7.0, step=0.05,
        label="Deployment Lag (years)",
    )
    infrastructure_life = mo.ui.slider(
        value=8.0, start=5.0, stop=15.0, step=0.1,
        label="Infrastructure Life (years)",
    )
    revenue_per_capacity = mo.ui.slider(
        value=0.15, start=0.05, stop=0.4, step=0.0035,
        label="Revenue Per Capacity (1/year)",
    )
    valuation_sensitivity = mo.ui.slider(
        value=0.3, start=0.05, stop=0.8, step=0.0075,
        label="Valuation Sensitivity (1/year)",
    )
    expected_roi = mo.ui.slider(
        value=0.2, start=0.05, stop=0.4, step=0.0035,
        label="Expected Roi (1/year)",
    )
    displacement_intensity = mo.ui.slider(
        value=0.001, start=0.0002, stop=0.003, step=2.8e-05,
        label="Displacement Intensity (million/billion$/year)",
    )
    base_hiring_rate = mo.ui.slider(
        value=0.05, start=0.01, stop=0.1, step=0.0009,
        label="Base Hiring Rate (1/year)",
    )
    base_tech_workforce = mo.ui.slider(
        value=6.0, start=4.0, stop=10.0, step=0.06,
        label="Base Tech Workforce (million)",
    )
    mo.vstack(
        [
        base_capex_rate,
        reference_valuation,
        deployment_lag,
        infrastructure_life,
        revenue_per_capacity,
        valuation_sensitivity,
        expected_roi,
        displacement_intensity,
        base_hiring_rate,
        base_tech_workforce,
        ]
    )
    return (
        base_capex_rate,
        base_hiring_rate,
        base_tech_workforce,
        deployment_lag,
        displacement_intensity,
        expected_roi,
        infrastructure_life,
        reference_valuation,
        revenue_per_capacity,
        valuation_sensitivity,
    )


@app.cell
def tabbed_content(go, mo, results):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
### Overview
Models the core contradiction in Big Tech AI investment: massive capex driven by high valuations encounters time-delayed returns realization (3-5 years), while simultaneously displacing the workforce that drives consumer/enterprise demand for AI services.

Key feedback loops:
- (R1) Valuation-Capex Reinforcing: high market_cap → more new_capex → bigger deployment_pipeline → more ai_infrastructure → expected future returns → higher market_cap
- (B1) Returns Reality Balancing: actual_roi < expected_roi → negative returns_gap → valuation declines → reduced capex
- (B2) Labor Displacement: ai_infrastructure → job_displacement → falling tech_employment → reduced ai_revenue → lower actual_roi → valuation correction
- (B3) Pipeline Inertia: capex committed years ago continues deploying even as market corrects, maintaining displacement pressure

The critical insight: revenue PEAKS then DECLINES despite growing infrastructure, because employment drag overcomes capacity gains. Watch pe_ratio and employment_ratio for early warning signals.

### Learning Objectives
- Understand how time delays between investment and returns create valuation instability
- Explore the contradiction between AI capex and labor market deterioration
- See how reinforcing loops (valuation→capex) interact with balancing loops (returns reality)
- Analyze pipeline inertia — why committed investments continue despite market corrections
- Compare scenarios where AI investment succeeds vs creates a bubble
- Learn how employment-demand feedback can undermine technology adoption returns
- Identify early warning indicators (PE ratio, employment ratio) for market corrections

### Scenarios
**Current Trajectory** -- Default parameters — $200B/yr capex, 4-year deployment lag, 20% expected ROI vs 15% actual. Watch valuation erode while pipeline keeps deploying.

**Capex Arms Race** -- Doubled investment, higher expectations, slow market correction — maximum bubble dynamics before inevitable crash  
Parameters: `base_capex_rate=400`, `expected_roi=0.3`, `valuation_sensitivity=0.15`

**Rapid Displacement** -- Aggressive automation with hiring freeze — employment collapses, revenue follows, severe valuation correction  
Parameters: `displacement_intensity=0.002`, `base_hiring_rate=0.03`

**Soft Landing** -- Higher revenue yield, faster deployment, mild displacement — can AI investment actually work out?  
Parameters: `revenue_per_capacity=0.25`, `deployment_lag=3`, `displacement_intensity=0.0005`

### Customization Tips
- Increase deployment_lag (4→6) to see more extreme returns gap from longer delays
- Raise displacement_intensity (0.001→0.002) for aggressive automation scenarios
- Lower expected_roi (0.20→0.10) to model market repricing of AI expectations
- Increase base_capex_rate (200→400) to simulate the current capex arms race
- Set valuation_sensitivity to 0.6+ for faster market corrections (flash crash dynamics)
- Reduce base_hiring_rate (0.05→0.02) to model hiring freezes alongside AI deployment
- Increase infrastructure_life (8→12) if GPU depreciation slows with better hardware

### Related Concepts
- Accelerator-multiplier model (Samuelson)
- Hype cycle and trough of disillusionment
- Jevons paradox (efficiency gains increase total consumption)
- Creative destruction (Schumpeter)
- Pipeline delay / material delay in SD
- Minsky moment (stability breeds instability)
- Goodhart's Law applied to AI metrics
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
    
        deployment_pipeline["Deployment Pipeline"]:::stock
        ai_infrastructure["Ai Infrastructure"]:::stock
        market_cap["Market Cap"]:::stock
        tech_employment["Tech Employment"]:::stock
        new_capex(["New Capex"]):::flow
        capacity_deployed(["Capacity Deployed"]):::flow
        capacity_retired(["Capacity Retired"]):::flow
        valuation_adjustment(["Valuation Adjustment"]):::flow
        tech_hiring(["Tech Hiring"]):::flow
        job_displacement(["Job Displacement"]):::flow
        base_capex_rate{{"Base Capex Rate = 200.0"}}:::constant
        reference_valuation{{"Reference Valuation = 15.0"}}:::constant
        deployment_lag{{"Deployment Lag = 4.0"}}:::constant
        infrastructure_life{{"Infrastructure Life = 8.0"}}:::constant
        revenue_per_capacity{{"Revenue Per Capacity = 0.15"}}:::constant
        valuation_sensitivity{{"Valuation Sensitivity = 0.3"}}:::constant
        expected_roi{{"Expected Roi = 0.2"}}:::constant
        displacement_intensity{{"Displacement Intensity = 0.001"}}:::constant
        base_hiring_rate{{"Base Hiring Rate = 0.05"}}:::constant
        base_tech_workforce{{"Base Tech Workforce = 6.0"}}:::constant
        ai_revenue[/"Ai Revenue"/]:::computed
        actual_roi[/"Actual Roi"/]:::computed
        returns_gap[/"Returns Gap"/]:::computed
        pe_ratio[/"Pe Ratio"/]:::computed
        employment_ratio[/"Employment Ratio"/]:::computed
    
        new_capex ==>|"+"| deployment_pipeline
        deployment_pipeline ==>|"-"| capacity_deployed
        capacity_deployed ==>|"+"| ai_infrastructure
        ai_infrastructure ==>|"-"| capacity_retired
        valuation_adjustment ==>|"+"| market_cap
        tech_hiring ==>|"+"| tech_employment
        tech_employment ==>|"-"| job_displacement
    
        reference_valuation -.-> new_capex
        base_capex_rate -.-> new_capex
        market_cap -.-> new_capex
        deployment_lag -.-> capacity_deployed
        infrastructure_life -.-> capacity_retired
        valuation_sensitivity -.-> valuation_adjustment
        returns_gap -.-> valuation_adjustment
        base_hiring_rate -.-> tech_hiring
        ai_infrastructure -.-> job_displacement
        displacement_intensity -.-> job_displacement
        base_tech_workforce -.-> ai_revenue
        tech_employment -.-> ai_revenue
        ai_infrastructure -.-> ai_revenue
        revenue_per_capacity -.-> ai_revenue
        ai_revenue -.-> actual_roi
        ai_infrastructure -.-> actual_roi
        expected_roi -.-> returns_gap
        actual_roi -.-> returns_gap
        ai_revenue -.-> pe_ratio
        market_cap -.-> pe_ratio
        base_tech_workforce -.-> employment_ratio
        tech_employment -.-> employment_ratio
        """
        ),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    fig_stocks = go.Figure()
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["deployment_pipeline"], mode="lines", name="Deployment Pipeline (billion$)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["ai_infrastructure"], mode="lines", name="Ai Infrastructure (billion$)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["market_cap"], mode="lines", name="Market Cap (trillion$)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["tech_employment"], mode="lines", name="Tech Employment (million)"))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    fig_flows = go.Figure()
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["new_capex"], mode="lines", name="New Capex (billion$/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["capacity_deployed"], mode="lines", name="Capacity Deployed (billion$/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["capacity_retired"], mode="lines", name="Capacity Retired (billion$/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["valuation_adjustment"], mode="lines", name="Valuation Adjustment (trillion$/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["tech_hiring"], mode="lines", name="Tech Hiring (million/year)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["job_displacement"], mode="lines", name="Job Displacement (million/year)"))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    fig_aux = go.Figure()
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["ai_revenue"], mode="lines", name="Ai Revenue (billion$/year)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["actual_roi"], mode="lines", name="Actual Roi (1/year)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["returns_gap"], mode="lines", name="Returns Gap (1/year)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["pe_ratio"], mode="lines", name="Pe Ratio (dimensionless)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["employment_ratio"], mode="lines", name="Employment Ratio (dimensionless)"))
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
