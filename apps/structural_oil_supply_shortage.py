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
Structural Oil Supply Shortage — Interactive Explorer

System dynamics model with inline Euler integration.
3 stocks, 4 flows, 13 parameters, 10 computed variables.

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
    annual_demand_growth_fraction,
    barrels_per_ev_per_day,
    base_ev_growth_rate,
    breakeven_price,
    displacement_efficiency,
    investment_response_factor,
    natural_decline_fraction,
    positive_incentive_filter,
    price_elasticity,
    price_sensitivity,
    realistic_peak_demand_estimate,
    reference_oil_price,
    vitol_peak_demand_projection,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    oil_supply_capacity = 107.0
    cumulative_ev_fleet = 22.0
    base_oil_demand_growth = 107.0

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    # Initialize computed variables for first iteration
    oil_price = reference_oil_price.value
    oil_price_effect_on_evs = 0.0

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        # Note: Parameters accessed via .value, stocks/flows use current variable values
        oil_demand_displaced_by_evs = cumulative_ev_fleet * barrels_per_ev_per_day.value * displacement_efficiency.value
        actual_oil_demand = base_oil_demand_growth - oil_demand_displaced_by_evs
        supply_demand_gap = actual_oil_demand - oil_supply_capacity
        gap_ratio = supply_demand_gap / oil_supply_capacity
        oil_price = reference_oil_price.value + gap_ratio * price_elasticity.value * reference_oil_price.value
        oil_price_effect_on_evs = (oil_price - reference_oil_price.value) / reference_oil_price.value * price_sensitivity.value
        ev_adoption_multiplier = 1 + oil_price_effect_on_evs
        price_above_breakeven = oil_price - breakeven_price.value
        normalized_investment_signal = price_above_breakeven / breakeven_price.value
        investment_incentive = (normalized_investment_signal + positive_incentive_filter.value) / 2
        new_capacity_investment = investment_incentive * investment_response_factor.value
        field_decline_rate = oil_supply_capacity * natural_decline_fraction.value
        ev_adoption_rate = base_ev_growth_rate.value * ev_adoption_multiplier
        demand_increase_rate = base_oil_demand_growth * annual_demand_growth_fraction.value

        rows.append(
            {
                "time": t,
                "oil_supply_capacity": oil_supply_capacity,
                "cumulative_ev_fleet": cumulative_ev_fleet,
                "base_oil_demand_growth": base_oil_demand_growth,
                "new_capacity_investment": new_capacity_investment,
                "field_decline_rate": field_decline_rate,
                "ev_adoption_rate": ev_adoption_rate,
                "demand_increase_rate": demand_increase_rate,
                "ev_adoption_multiplier": ev_adoption_multiplier,
                "oil_price_effect_on_evs": oil_price_effect_on_evs,
                "oil_demand_displaced_by_evs": oil_demand_displaced_by_evs,
                "actual_oil_demand": actual_oil_demand,
                "supply_demand_gap": supply_demand_gap,
                "gap_ratio": gap_ratio,
                "oil_price": oil_price,
                "price_above_breakeven": price_above_breakeven,
                "normalized_investment_signal": normalized_investment_signal,
                "investment_incentive": investment_incentive,
            }
        )

        # Euler integration
        oil_supply_capacity += dt * (new_capacity_investment - field_decline_rate)
        oil_supply_capacity = max(oil_supply_capacity, 0)
        cumulative_ev_fleet += dt * ev_adoption_rate
        cumulative_ev_fleet = max(cumulative_ev_fleet, 0)
        base_oil_demand_growth += dt * demand_increase_rate
        base_oil_demand_growth = max(base_oil_demand_growth, 0)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Structural Oil Supply Shortage — Interactive Explorer

    **Stocks:** 3 | **Flows:** 4 | **Parameters:** 13 | **Computed:** 10

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
    natural_decline_fraction = mo.ui.slider(
        value=0.05, start=0.0, stop=1.0, step=0.01,
        label="Natural Decline Fraction (1/year)",
    )
    base_ev_growth_rate = mo.ui.slider(
        value=12.0, start=0.0, stop=60.0, step=0.6,
        label="Base Ev Growth Rate (million vehicles per year)",
    )
    price_sensitivity = mo.ui.slider(
        value=0.3, start=0.0, stop=2.0, step=0.02,
        label="Price Sensitivity (dimensionless)",
    )
    barrels_per_ev_per_day = mo.ui.slider(
        value=0.002, start=0.0, stop=1, step=0.01,
        label="Barrels Per Ev Per Day (barrels per vehicle per day)",
    )
    displacement_efficiency = mo.ui.slider(
        value=0.7, start=0.0, stop=1.0, step=0.01,
        label="Displacement Efficiency (dimensionless)",
    )
    annual_demand_growth_fraction = mo.ui.slider(
        value=0.009, start=0.0, stop=0.05, step=0.0005,
        label="Annual Demand Growth Fraction (1/year)",
    )
    reference_oil_price = mo.ui.slider(
        value=75.0, start=0.0, stop=375.0, step=3.75,
        label="Reference Oil Price (dollars per barrel)",
    )
    price_elasticity = mo.ui.slider(
        value=2.5, start=0.0, stop=10.0, step=0.1,
        label="Price Elasticity (dimensionless)",
    )
    positive_incentive_filter = mo.ui.slider(
        value=0.1, start=0.0, stop=1, step=0.01,
        label="Positive Incentive Filter (dimensionless)",
    )
    breakeven_price = mo.ui.slider(
        value=65.0, start=0.0, stop=325.0, step=3.25,
        label="Breakeven Price (dollars per barrel)",
    )
    investment_response_factor = mo.ui.slider(
        value=1.5, start=0.0, stop=7.5, step=0.075,
        label="Investment Response Factor (million barrels per day per year)",
    )
    vitol_peak_demand_projection = mo.ui.slider(
        value=112.0, start=0.0, stop=560.0, step=5.6,
        label="Vitol Peak Demand Projection (million barrels per day)",
    )
    realistic_peak_demand_estimate = mo.ui.slider(
        value=120.0, start=0.0, stop=600.0, step=6.0,
        label="Realistic Peak Demand Estimate (million barrels per day)",
    )
    mo.vstack(
        [
        natural_decline_fraction,
        base_ev_growth_rate,
        price_sensitivity,
        barrels_per_ev_per_day,
        displacement_efficiency,
        annual_demand_growth_fraction,
        reference_oil_price,
        price_elasticity,
        positive_incentive_filter,
        breakeven_price,
        investment_response_factor,
        vitol_peak_demand_projection,
        realistic_peak_demand_estimate,
        ]
    )
    return (
        annual_demand_growth_fraction,
        barrels_per_ev_per_day,
        base_ev_growth_rate,
        breakeven_price,
        displacement_efficiency,
        investment_response_factor,
        natural_decline_fraction,
        positive_incentive_filter,
        price_elasticity,
        price_sensitivity,
        realistic_peak_demand_estimate,
        reference_oil_price,
        vitol_peak_demand_projection,
    )


@app.cell
def chart_controls(mo):
    stock_selector = mo.ui.multiselect(
        options={"Oil Supply Capacity (million barrels per day)": "oil_supply_capacity", "Cumulative Ev Fleet (million vehicles)": "cumulative_ev_fleet", "Base Oil Demand Growth (million barrels per day)": "base_oil_demand_growth"},
        value=["Oil Supply Capacity (million barrels per day)", "Cumulative Ev Fleet (million vehicles)", "Base Oil Demand Growth (million barrels per day)"],
        label="Stock variables",
    )
    flow_selector = mo.ui.multiselect(
        options={"New Capacity Investment (million barrels per day per year)": "new_capacity_investment", "Field Decline Rate (million barrels per day per year)": "field_decline_rate", "Ev Adoption Rate (million vehicles per year)": "ev_adoption_rate", "Demand Increase Rate (million barrels per day per year)": "demand_increase_rate"},
        value=["New Capacity Investment (million barrels per day per year)", "Field Decline Rate (million barrels per day per year)", "Ev Adoption Rate (million vehicles per year)", "Demand Increase Rate (million barrels per day per year)"],
        label="Flow variables",
    )
    aux_selector = mo.ui.multiselect(
        options={"Ev Adoption Multiplier (dimensionless)": "ev_adoption_multiplier", "Oil Price Effect On Evs (dimensionless)": "oil_price_effect_on_evs", "Oil Demand Displaced By Evs (million barrels per day)": "oil_demand_displaced_by_evs", "Actual Oil Demand (million barrels per day)": "actual_oil_demand", "Supply Demand Gap (million barrels per day)": "supply_demand_gap", "Gap Ratio (dimensionless)": "gap_ratio", "Oil Price (dollars per barrel)": "oil_price", "Price Above Breakeven (dollars per barrel)": "price_above_breakeven", "Normalized Investment Signal (dimensionless)": "normalized_investment_signal", "Investment Incentive (dimensionless)": "investment_incentive"},
        value=["Ev Adoption Multiplier (dimensionless)", "Oil Price Effect On Evs (dimensionless)", "Oil Demand Displaced By Evs (million barrels per day)", "Actual Oil Demand (million barrels per day)", "Supply Demand Gap (million barrels per day)", "Gap Ratio (dimensionless)", "Oil Price (dollars per barrel)", "Price Above Breakeven (dollars per barrel)", "Normalized Investment Signal (dimensionless)", "Investment Incentive (dimensionless)"],
        label="Auxiliary variables",
    )
    return stock_selector, flow_selector, aux_selector


@app.cell
def tabbed_content(aux_selector, flow_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
# Structural Oil Supply Shortage Analysis

## Original Article
**Source**: [HFI Research - What Does a Structural Oil Supply Shortage Mean?](https://www.hfir.com/p/wctw-what-does-a-structural-oil-supply)

## The Core Thesis

This model captures the dynamics described in the HFI Research article analyzing whether a structural oil supply deficit is emerging. The analysis challenges conventional assumptions about oil demand peak and EV displacement.

### Key Insights from the Article

**1. Optimistic EV Assumptions**
- Vitol (world's largest oil trader) projects global demand peak at ~112 million b/d by mid-2030s
- Assumes new energy vehicles (NEV) will displace ~11 million b/d by 2040
- **Problem**: This requires European EV sales to double and US sales to triple current trajectories
- BloombergNEF expresses skepticism about achieving these penetration rates

**2. Realistic Demand Projection**
- If Vitol is only "25% right" on NEV penetration (more realistic assumption)
- Peak demand would be closer to **120 million b/d** instead of 112 million b/d
- This 8 million b/d difference is significant for structural supply balance

**3. Supply-Side Constraints**
- IEA report (September 2025) highlights concerning oil field decline rates
- Natural depletion of existing fields creates persistent downward pressure on capacity
- Investment must overcome ~5% annual decline just to maintain current capacity

## Model Structure

### Reinforcing Feedback Loop: The Structural Shortage
1. **Field decline** reduces oil supply capacity
2. Lower supply vs. growing demand creates a **supply-demand gap**
3. Gap drives **oil prices higher**
4. Higher prices incentivize **new capacity investment**
5. BUT: Investment rate cannot overcome the natural decline rate + demand growth
6. **Result**: Gap continues widening, prices keep rising

### Balancing Feedback Loop: EV Response
1. **High oil prices** make EVs more economically attractive
2. **Accelerated EV adoption** occurs
3. EVs **displace oil demand**
4. Reduced demand helps moderate the supply-demand gap
5. BUT: EV adoption is slower than many forecasts assume

## Key Findings

### Baseline Scenario (15-year projection)
- **Supply capacity declines**: 107 → 64 million b/d (40% reduction)
- **Demand grows**: 107 → 122 million b/d (14% increase)
- **Supply-demand gap**: 0 → 58 million b/d shortage
- **Oil price**: $75 → $245/barrel (227% increase)
- **EV fleet**: 22 → 264 million vehicles (12x growth)
- **Oil displaced by EVs**: Only 0.37 million b/d by year 15

### Why the Shortage is "Structural"
Even with:
- Significant oil price increases ($75 → $245/barrel)
- Strong investment response to high prices
- 12x growth in EV fleet

The structural dynamics create an unavoidable supply shortage because:
1. **Natural field decline rate (5%/year) is relentless**
2. **New capacity investment has long lead times** (5-10 years)
3. **EV displacement effect is slower than optimistic forecasts**
4. **Base demand continues growing** with economic expansion

## Scenario Analysis

Try adjusting these parameters to explore different futures:

**Aggressive EV Adoption**
- Increase `base_ev_growth_rate` to 18-20 million/year
- Increase `price_sensitivity` to 0.5-0.8
- See if EV displacement can prevent the shortage

**Higher Investment Response**
- Increase `investment_response_factor` to 2.5-3.0
- Reduce `breakeven_price` to $55-60/barrel
- Test if supply can keep pace with demand

**Slower Demand Growth**
- Reduce `annual_demand_growth_fraction` to 0.005 (0.5%)
- Models scenario with economic slowdown or efficiency gains

**Lower Field Decline**
- Reduce `natural_decline_fraction` to 0.03-0.04
- Tests impact of improved recovery techniques or new discoveries

## Implications

1. **Oil may not peak due to demand destruction, but supply constraints**
2. **Energy transition timeline matters** - too slow = high oil prices
3. **Investment in oil production remains critical** even during energy transition
4. **Price volatility likely** as market oscillates between shortage fears and recession risks
5. **Geopolitical implications** of structural supply tightness
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
    
        new_capacity_investment ==>|"+"| oil_supply_capacity
        field_decline_rate ==>|"-"| oil_supply_capacity
        ev_adoption_rate ==>|"+"| cumulative_ev_fleet
        demand_increase_rate ==>|"+"| base_oil_demand_growth

        oil_supply_capacity -.-> field_decline_rate
        natural_decline_fraction -.-> field_decline_rate
        cumulative_ev_fleet -.-> oil_demand_displaced_by_evs
        barrels_per_ev_per_day -.-> oil_demand_displaced_by_evs
        displacement_efficiency -.-> oil_demand_displaced_by_evs
        base_oil_demand_growth -.-> actual_oil_demand
        oil_demand_displaced_by_evs -.-> actual_oil_demand
        actual_oil_demand -.-> supply_demand_gap
        oil_supply_capacity -.-> supply_demand_gap
        supply_demand_gap -.-> gap_ratio
        oil_supply_capacity -.-> gap_ratio
        reference_oil_price -.-> oil_price
        gap_ratio -.-> oil_price
        price_elasticity -.-> oil_price
        oil_price -.-> oil_price_effect_on_evs
        reference_oil_price -.-> oil_price_effect_on_evs
        price_sensitivity -.-> oil_price_effect_on_evs
        oil_price_effect_on_evs -.-> ev_adoption_multiplier
        base_ev_growth_rate -.-> ev_adoption_rate
        ev_adoption_multiplier -.-> ev_adoption_rate
        oil_price -.-> price_above_breakeven
        breakeven_price -.-> price_above_breakeven
        price_above_breakeven -.-> normalized_investment_signal
        breakeven_price -.-> normalized_investment_signal
        normalized_investment_signal -.-> investment_incentive
        positive_incentive_filter -.-> investment_incentive
        investment_incentive -.-> new_capacity_investment
        investment_response_factor -.-> new_capacity_investment
        base_oil_demand_growth -.-> demand_increase_rate
        annual_demand_growth_fraction -.-> demand_increase_rate

        """
        ),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'oil_supply_capacity': 'Oil Supply Capacity (million barrels per day)', 'cumulative_ev_fleet': 'Cumulative Ev Fleet (million vehicles)', 'base_oil_demand_growth': 'Base Oil Demand Growth (million barrels per day)'}
    fig_stocks = go.Figure()
    for _key in stock_selector.value:
        fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    _flow_labels = {'new_capacity_investment': 'New Capacity Investment (million barrels per day per year)', 'field_decline_rate': 'Field Decline Rate (million barrels per day per year)', 'ev_adoption_rate': 'Ev Adoption Rate (million vehicles per year)', 'demand_increase_rate': 'Demand Increase Rate (million barrels per day per year)'}
    fig_flows = go.Figure()
    for _key in flow_selector.value:
        fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key)))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    _aux_labels = {'ev_adoption_multiplier': 'Ev Adoption Multiplier (dimensionless)', 'oil_price_effect_on_evs': 'Oil Price Effect On Evs (dimensionless)', 'oil_demand_displaced_by_evs': 'Oil Demand Displaced By Evs (million barrels per day)', 'actual_oil_demand': 'Actual Oil Demand (million barrels per day)', 'supply_demand_gap': 'Supply Demand Gap (million barrels per day)', 'gap_ratio': 'Gap Ratio (dimensionless)', 'oil_price': 'Oil Price (dollars per barrel)', 'price_above_breakeven': 'Price Above Breakeven (dollars per barrel)', 'normalized_investment_signal': 'Normalized Investment Signal (dimensionless)', 'investment_incentive': 'Investment Incentive (dimensionless)'}
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
