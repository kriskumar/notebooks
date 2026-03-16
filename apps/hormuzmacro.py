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
Hormuzmacro — Interactive Explorer

System dynamics model with inline Euler integration.
6 stocks, 9 flows, 26 parameters, 17 computed variables.

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
    anxiety_price_sensitivity,
    base_inflation,
    consumer_exposure_param,
    credit_mean_reversion_rate,
    credit_sensitivity_param,
    credit_transmission_lag,
    demand_price_elasticity,
    destocking_rate_param,
    fiscal_sensitivity_param,
    gdp_credit_sensitivity_param,
    hoarding_propensity,
    hormuz_disruption_mbd,
    jic_demand_factor,
    jic_max_increment,
    jic_ratchet_speed,
    mena_supply_share,
    oil_gdp_sensitivity,
    oil_inflation_passthrough,
    political_sensitivity_param,
    price_adjustment_speed,
    relief_decay_rate,
    spr_activation_coeff,
    spr_max_rate,
    spr_trigger_price,
    strait_total_recovery_time,
    world_demand_base,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    global_oil_supply = 84.5
    oil_price = 90.0
    precautionary_inventory = 0.0
    western_credit_index = 100.0
    supply_chain_buffer = 1.0
    political_pressure = 0.0
    security_anxiety = 0  # Will be computed in loop
    net_hoarding_demand = 0  # Will be computed in loop
    base_demand_adjusted = 0  # Will be computed in loop
    effective_supply = 0  # Will be computed in loop
    effective_demand = 0  # Will be computed in loop
    supply_demand_gap = 0  # Will be computed in loop
    spr_release_rate = 0  # Will be computed in loop
    jic_demand = 0  # Will be computed in loop
    jic_target = 0  # Will be computed in loop
    supply_insecurity_level = 0  # Will be computed in loop
    mena_revenue_signal = 0  # Will be computed in loop
    de_dollarization_pressure = 0  # Will be computed in loop
    inflation_rate = 0  # Will be computed in loop
    crowding_out_pressure = 0  # Will be computed in loop
    tightening_pressure_combined = 0  # Will be computed in loop
    consumer_pain = 0  # Will be computed in loop
    gdp_impact_index = 0  # Will be computed in loop

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        supply_restoration_rate = max(0, ((world_demand_base.value - global_oil_supply) / strait_total_recovery_time.value))
        pressure_relief_rate = (political_pressure * relief_decay_rate.value)
        credit_tightening_rate = 0
        credit_recovery_rate = (max(0, (100 - western_credit_index)) * credit_mean_reversion_rate.value)
        security_anxiety = min(1, max(0, (((oil_price - 90) / 90) * anxiety_price_sensitivity.value)))
        base_demand_adjusted = (world_demand_base.value * max(0.85, (1 + (demand_price_elasticity.value * ((oil_price / 90) - 1)))))
        spr_release_rate = min(spr_max_rate.value, max(0, ((oil_price - spr_trigger_price.value) * spr_activation_coeff.value)))
        jic_demand = (((supply_chain_buffer - 1) * world_demand_base.value) * jic_demand_factor.value)
        mena_revenue_signal = max(0, ((oil_price - 70) * mena_supply_share.value))
        inflation_rate = ((((oil_price / 90) - 1) * oil_inflation_passthrough.value) + base_inflation.value)
        consumer_pain = (max(0, ((oil_price / 90) - 1)) * consumer_exposure_param.value)
        gdp_impact_index = max(0.5, ((1 - (((100 - western_credit_index) / 100) * gdp_credit_sensitivity_param.value)) - (max(0, ((oil_price / 90) - 1)) * oil_gdp_sensitivity.value)))
        hoarding_rate = ((security_anxiety * hoarding_propensity.value) * world_demand_base.value)
        destocking_rate = ((precautionary_inventory * (1 - security_anxiety)) * destocking_rate_param.value)
        effective_supply = (global_oil_supply + spr_release_rate)
        de_dollarization_pressure = (mena_revenue_signal * credit_sensitivity_param.value)
        crowding_out_pressure = max(0, ((inflation_rate - base_inflation.value) * fiscal_sensitivity_param.value))
        pressure_buildup_rate = (consumer_pain * political_sensitivity_param.value)
        net_hoarding_demand = (hoarding_rate - destocking_rate)
        tightening_pressure_combined = (de_dollarization_pressure + crowding_out_pressure)
        effective_demand = ((base_demand_adjusted + net_hoarding_demand) + jic_demand)
        supply_demand_gap = (effective_demand - effective_supply)
        price_change_rate = ((price_adjustment_speed.value * (supply_demand_gap / world_demand_base.value)) * oil_price)
        supply_insecurity_level = min(1, max(0, (supply_demand_gap / (world_demand_base.value * 0.05))))
        jic_target = (1 + min(jic_max_increment.value, (supply_insecurity_level * jic_max_increment.value)))
        jic_ratchet_rate = max(0, ((jic_target - supply_chain_buffer) * jic_ratchet_speed.value))

        rows.append(
            {
                "time": t,
                "global_oil_supply": global_oil_supply,
                "oil_price": oil_price,
                "precautionary_inventory": precautionary_inventory,
                "western_credit_index": western_credit_index,
                "supply_chain_buffer": supply_chain_buffer,
                "political_pressure": political_pressure,
                "supply_restoration_rate": supply_restoration_rate,
                "price_change_rate": price_change_rate,
                "hoarding_rate": hoarding_rate,
                "destocking_rate": destocking_rate,
                "jic_ratchet_rate": jic_ratchet_rate,
                "pressure_buildup_rate": pressure_buildup_rate,
                "pressure_relief_rate": pressure_relief_rate,
                "credit_tightening_rate": credit_tightening_rate,
                "credit_recovery_rate": credit_recovery_rate,
                "security_anxiety": security_anxiety,
                "net_hoarding_demand": net_hoarding_demand,
                "base_demand_adjusted": base_demand_adjusted,
                "effective_supply": effective_supply,
                "effective_demand": effective_demand,
                "supply_demand_gap": supply_demand_gap,
                "spr_release_rate": spr_release_rate,
                "jic_demand": jic_demand,
                "jic_target": jic_target,
                "supply_insecurity_level": supply_insecurity_level,
                "mena_revenue_signal": mena_revenue_signal,
                "de_dollarization_pressure": de_dollarization_pressure,
                "inflation_rate": inflation_rate,
                "crowding_out_pressure": crowding_out_pressure,
                "tightening_pressure_combined": tightening_pressure_combined,
                "consumer_pain": consumer_pain,
                "gdp_impact_index": gdp_impact_index,
            }
        )

        # Euler integration
        global_oil_supply += dt * supply_restoration_rate
        oil_price += dt * price_change_rate
        precautionary_inventory += dt * (hoarding_rate - destocking_rate)
        western_credit_index += dt * (credit_recovery_rate - credit_tightening_rate)
        supply_chain_buffer += dt * jic_ratchet_rate
        political_pressure += dt * (pressure_buildup_rate - pressure_relief_rate)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Hormuzmacro — Interactive Explorer

    **Stocks:** 6 | **Flows:** 9 | **Parameters:** 26 | **Computed:** 17

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
    world_demand_base = mo.ui.slider(
        value=103.0, start=0, stop=515.0, step=1.03,
        label="World Demand Base (Mb/d)",
    )
    strait_total_recovery_time = mo.ui.slider(
        value=6.0, start=0, stop=30.0, step=0.06,
        label="Strait Total Recovery Time (months)",
    )
    price_adjustment_speed = mo.ui.slider(
        value=0.3, start=0, stop=1, step=0.01,
        label="Price Adjustment Speed (1/month)",
    )
    anxiety_price_sensitivity = mo.ui.slider(
        value=1.5, start=0, stop=7.5, step=0.015,
        label="Anxiety Price Sensitivity (dimensionless)",
    )
    hoarding_propensity = mo.ui.slider(
        value=0.025, start=0, stop=1, step=0.01,
        label="Hoarding Propensity (dimensionless)",
    )
    destocking_rate_param = mo.ui.slider(
        value=0.15, start=0, stop=1, step=0.01,
        label="Destocking Rate Param (1/month)",
    )
    spr_max_rate = mo.ui.slider(
        value=4.4, start=0, stop=22.0, step=0.044,
        label="Spr Max Rate (Mb/d)",
    )
    spr_trigger_price = mo.ui.slider(
        value=100.0, start=0, stop=500.0, step=1.0,
        label="Spr Trigger Price (USD/bbl)",
    )
    spr_activation_coeff = mo.ui.slider(
        value=0.04, start=0, stop=1, step=0.01,
        label="Spr Activation Coeff (Mb/d per USD)",
    )
    demand_price_elasticity = mo.ui.slider(
        value=-0.02, start=0, stop=-0.1, step=-0.0002,
        label="Demand Price Elasticity (dimensionless)",
    )
    credit_transmission_lag = mo.ui.slider(
        value=6.0, start=0, stop=30.0, step=0.06,
        label="Credit Transmission Lag (months)",
    )
    credit_sensitivity_param = mo.ui.slider(
        value=0.3, start=0, stop=1, step=0.01,
        label="Credit Sensitivity Param (dimensionless)",
    )
    fiscal_sensitivity_param = mo.ui.slider(
        value=0.2, start=0, stop=1, step=0.01,
        label="Fiscal Sensitivity Param (dimensionless)",
    )
    gdp_credit_sensitivity_param = mo.ui.slider(
        value=0.4, start=0, stop=1, step=0.01,
        label="Gdp Credit Sensitivity Param (dimensionless)",
    )
    oil_gdp_sensitivity = mo.ui.slider(
        value=0.15, start=0, stop=1, step=0.01,
        label="Oil Gdp Sensitivity (dimensionless)",
    )
    credit_mean_reversion_rate = mo.ui.slider(
        value=0.05, start=0, stop=1, step=0.01,
        label="Credit Mean Reversion Rate (1/month)",
    )
    jic_ratchet_speed = mo.ui.slider(
        value=0.08, start=0, stop=1, step=0.01,
        label="Jic Ratchet Speed (1/month)",
    )
    jic_max_increment = mo.ui.slider(
        value=0.04, start=0, stop=1, step=0.01,
        label="Jic Max Increment (dimensionless)",
    )
    jic_demand_factor = mo.ui.slider(
        value=0.03, start=0, stop=1, step=0.01,
        label="Jic Demand Factor (dimensionless)",
    )
    political_sensitivity_param = mo.ui.slider(
        value=0.5, start=0, stop=1, step=0.01,
        label="Political Sensitivity Param (1/month)",
    )
    relief_decay_rate = mo.ui.slider(
        value=0.1, start=0, stop=1, step=0.01,
        label="Relief Decay Rate (1/month)",
    )
    consumer_exposure_param = mo.ui.slider(
        value=1.0, start=0, stop=1, step=0.01,
        label="Consumer Exposure Param (dimensionless)",
    )
    mena_supply_share = mo.ui.slider(
        value=0.3, start=0, stop=1, step=0.01,
        label="Mena Supply Share (dimensionless)",
    )
    oil_inflation_passthrough = mo.ui.slider(
        value=0.3, start=0, stop=1, step=0.01,
        label="Oil Inflation Passthrough (dimensionless)",
    )
    base_inflation = mo.ui.slider(
        value=0.03, start=0, stop=1, step=0.01,
        label="Base Inflation (fraction)",
    )
    hormuz_disruption_mbd = mo.ui.slider(
        value=18.5, start=0, stop=92.5, step=0.185,
        label="Hormuz Disruption Mbd (Mb/d)",
    )
    mo.vstack(
        [
        world_demand_base,
        strait_total_recovery_time,
        price_adjustment_speed,
        anxiety_price_sensitivity,
        hoarding_propensity,
        destocking_rate_param,
        spr_max_rate,
        spr_trigger_price,
        spr_activation_coeff,
        demand_price_elasticity,
        credit_transmission_lag,
        credit_sensitivity_param,
        fiscal_sensitivity_param,
        gdp_credit_sensitivity_param,
        oil_gdp_sensitivity,
        credit_mean_reversion_rate,
        jic_ratchet_speed,
        jic_max_increment,
        jic_demand_factor,
        political_sensitivity_param,
        relief_decay_rate,
        consumer_exposure_param,
        mena_supply_share,
        oil_inflation_passthrough,
        base_inflation,
        hormuz_disruption_mbd,
        ]
    )
    return (
        anxiety_price_sensitivity,
        base_inflation,
        consumer_exposure_param,
        credit_mean_reversion_rate,
        credit_sensitivity_param,
        credit_transmission_lag,
        demand_price_elasticity,
        destocking_rate_param,
        fiscal_sensitivity_param,
        gdp_credit_sensitivity_param,
        hoarding_propensity,
        hormuz_disruption_mbd,
        jic_demand_factor,
        jic_max_increment,
        jic_ratchet_speed,
        mena_supply_share,
        oil_gdp_sensitivity,
        oil_inflation_passthrough,
        political_sensitivity_param,
        price_adjustment_speed,
        relief_decay_rate,
        spr_activation_coeff,
        spr_max_rate,
        spr_trigger_price,
        strait_total_recovery_time,
        world_demand_base,
    )


@app.cell
def chart_controls(mo):
    stock_selector = mo.ui.multiselect(
        options={"Global Oil Supply (Mb/d)": "global_oil_supply", "Oil Price (USD/bbl)": "oil_price", "Precautionary Inventory (Mb/d)": "precautionary_inventory", "Western Credit Index (index)": "western_credit_index", "Supply Chain Buffer (dimensionless)": "supply_chain_buffer", "Political Pressure (index)": "political_pressure"},
        value=["Global Oil Supply (Mb/d)", "Oil Price (USD/bbl)", "Precautionary Inventory (Mb/d)", "Western Credit Index (index)", "Supply Chain Buffer (dimensionless)", "Political Pressure (index)"],
        label="Stock variables",
    )
    flow_selector = mo.ui.multiselect(
        options={"Supply Restoration Rate (Mb/d/month)": "supply_restoration_rate", "Price Change Rate (USD/bbl/month)": "price_change_rate", "Hoarding Rate (Mb/d)": "hoarding_rate", "Destocking Rate (Mb/d)": "destocking_rate", "Jic Ratchet Rate (dimensionless/month)": "jic_ratchet_rate", "Pressure Buildup Rate (index/month)": "pressure_buildup_rate", "Pressure Relief Rate (index/month)": "pressure_relief_rate", "Credit Tightening Rate (index/month)": "credit_tightening_rate", "Credit Recovery Rate (index/month)": "credit_recovery_rate"},
        value=["Supply Restoration Rate (Mb/d/month)", "Price Change Rate (USD/bbl/month)", "Hoarding Rate (Mb/d)", "Destocking Rate (Mb/d)", "Jic Ratchet Rate (dimensionless/month)", "Pressure Buildup Rate (index/month)", "Pressure Relief Rate (index/month)", "Credit Tightening Rate (index/month)", "Credit Recovery Rate (index/month)"],
        label="Flow variables",
    )
    aux_selector = mo.ui.multiselect(
        options={"Security Anxiety (dimensionless)": "security_anxiety", "Net Hoarding Demand (Mb/d)": "net_hoarding_demand", "Base Demand Adjusted (Mb/d)": "base_demand_adjusted", "Effective Supply (Mb/d)": "effective_supply", "Effective Demand (Mb/d)": "effective_demand", "Supply Demand Gap (Mb/d)": "supply_demand_gap", "Spr Release Rate (Mb/d)": "spr_release_rate", "Jic Demand (Mb/d)": "jic_demand", "Jic Target (dimensionless)": "jic_target", "Supply Insecurity Level (dimensionless)": "supply_insecurity_level", "Mena Revenue Signal (USD/bbl * fraction)": "mena_revenue_signal", "De Dollarization Pressure (index/month)": "de_dollarization_pressure", "Inflation Rate (fraction)": "inflation_rate", "Crowding Out Pressure (index/month)": "crowding_out_pressure", "Tightening Pressure Combined (index/month)": "tightening_pressure_combined", "Consumer Pain (dimensionless)": "consumer_pain", "Gdp Impact Index (dimensionless)": "gdp_impact_index"},
        value=["Security Anxiety (dimensionless)", "Net Hoarding Demand (Mb/d)", "Base Demand Adjusted (Mb/d)", "Effective Supply (Mb/d)", "Effective Demand (Mb/d)", "Supply Demand Gap (Mb/d)", "Spr Release Rate (Mb/d)", "Jic Demand (Mb/d)", "Jic Target (dimensionless)", "Supply Insecurity Level (dimensionless)", "Mena Revenue Signal (USD/bbl * fraction)", "De Dollarization Pressure (index/month)", "Inflation Rate (fraction)", "Crowding Out Pressure (index/month)", "Tightening Pressure Combined (index/month)", "Consumer Pain (dimensionless)", "Gdp Impact Index (dimensionless)"],
        label="Auxiliary variables",
    )
    return stock_selector, flow_selector, aux_selector


@app.cell
def tabbed_content(aux_selector, flow_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
## Hormuz Strait Closure — Macro Shock Model

*Based on Carlyle "A Crude Awakening" (March 2026), by Jeff Currie & James Gutman*

> "The physical shortfall is the trigger; the behavioral response is the multiplier."

### The Disruption

The Strait of Hormuz carries **18.5 million barrels/day** — 18% of global oil supply — plus LNG, fertilizer, and metals. A closure is without precedent. As of March 2026, Polymarket puts the probability still closed on March 31 at 85%.

### Four Feedback Loops

**R1 — Hoarding Multiplier (Reinforcing)**
Rising prices trigger security anxiety → precautionary inventory buildup → effective demand surges 2–3 Mb/d on top of physical disruption. In 1979, a 4–5% physical shortfall doubled the effective demand impact. *The behavioral response is the multiplier.*

**B1 — Infrastructure Recovery Lag (Balancing, delayed)**
Even after political resolution, supply does not snap back. Damaged infrastructure at Kharg Island and Ras Tanura, scattered fleets, repriced war-risk insurance, and renegotiated contracts mean 3–6 months before flows normalize. Modeled as first-order recovery with `strait_total_recovery_time` as the key scenario variable.

**B2 — Reversed Credit Channel (Balancing, 6-month lag)**
In the 1970s, OPEC surpluses were recycled through Western banks → QE-like credit expansion → lower rates. Today the transmission runs in reverse: MENA invests domestically, de-dollarizes. Federal debt at 120% GDP (vs 32% in 1974) means inflation-indexed transfer payments auto-expand deficits, forcing Treasury issuance at the worst moment, crowding out private credit. Captured via DELAY3 with 6-month transmission lag.

**R2 — JIT→JIC Ratchet (Reinforcing, permanent)**
Every major importer securing supply simultaneously. China suspended petroleum product exports. The shift from just-in-time to just-in-case is irreversible — modeled as a one-way ratchet adding up to ~4 Mb/d structural demand.

**B3 — SPR Release (Balancing, capped)**
Political pressure from consumer pain triggers SPR releases — but the US SPR maximum drawdown of 4.4 Mb/d covers less than 25% of the 18.5 Mb/d Hormuz disruption.

### Scenario Results (18-month simulation)

| Scenario | Peak Oil Price | GDP Loss @ 12mo | Credit @ 18mo |
|----------|---------------|-----------------|---------------|
| Quick resolution (3 months) | ~$105/bbl | −8% | ~74/100 |
| Baseline (6 months) | ~$119/bbl | −24% | ~27/100 |
| High hoarding (propensity ×2) | ~$124/bbl | −12% | ~67/100 |
| No SPR release | ~$124/bbl | −11% | ~67/100 |
| Mined strait (12 months) | >$147/bbl, rising | −37% | collapsed |

### Key Policy Insight

The SPR is nearly irrelevant to price (S1 vs S5 differ by only ~$1/bbl). The dominant variable is `strait_total_recovery_time` — doubling it from 6→12 months adds $28/bbl and causes credit collapse. **Oil is the rare earth of the macro system**: remaining uses (petrochemicals, aviation, fertilizers, grid balancing) have no substitutes. Price shocks cause production shutdowns, not demand destruction.
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
    
        global_oil_supply["Global Oil Supply"]:::stock
        oil_price["Oil Price"]:::stock
        precautionary_inventory["Precautionary Inventory"]:::stock
        western_credit_index["Western Credit Index"]:::stock
        supply_chain_buffer["Supply Chain Buffer"]:::stock
        political_pressure["Political Pressure"]:::stock
        supply_restoration_rate(["Supply Restoration Rate"]):::flow
        price_change_rate(["Price Change Rate"]):::flow
        hoarding_rate(["Hoarding Rate"]):::flow
        destocking_rate(["Destocking Rate"]):::flow
        jic_ratchet_rate(["Jic Ratchet Rate"]):::flow
        pressure_buildup_rate(["Pressure Buildup Rate"]):::flow
        pressure_relief_rate(["Pressure Relief Rate"]):::flow
        credit_tightening_rate(["Credit Tightening Rate"]):::flow
        credit_recovery_rate(["Credit Recovery Rate"]):::flow
        world_demand_base{{"World Demand Base = 103.0"}}:::constant
        strait_total_recovery_time{{"Strait Total Recovery Time = 6.0"}}:::constant
        price_adjustment_speed{{"Price Adjustment Speed = 0.3"}}:::constant
        anxiety_price_sensitivity{{"Anxiety Price Sensitivity = 1.5"}}:::constant
        hoarding_propensity{{"Hoarding Propensity = 0.025"}}:::constant
        destocking_rate_param{{"Destocking Rate Param = 0.15"}}:::constant
        spr_max_rate{{"Spr Max Rate = 4.4"}}:::constant
        spr_trigger_price{{"Spr Trigger Price = 100.0"}}:::constant
        spr_activation_coeff{{"Spr Activation Coeff = 0.04"}}:::constant
        demand_price_elasticity{{"Demand Price Elasticity = -0.02"}}:::constant
        credit_transmission_lag{{"Credit Transmission Lag = 6.0"}}:::constant
        credit_sensitivity_param{{"Credit Sensitivity Param = 0.3"}}:::constant
        fiscal_sensitivity_param{{"Fiscal Sensitivity Param = 0.2"}}:::constant
        gdp_credit_sensitivity_param{{"Gdp Credit Sensitivity Param = 0.4"}}:::constant
        oil_gdp_sensitivity{{"Oil Gdp Sensitivity = 0.15"}}:::constant
        credit_mean_reversion_rate{{"Credit Mean Reversion Rate = 0.05"}}:::constant
        jic_ratchet_speed{{"Jic Ratchet Speed = 0.08"}}:::constant
        jic_max_increment{{"Jic Max Increment = 0.04"}}:::constant
        jic_demand_factor{{"Jic Demand Factor = 0.03"}}:::constant
        political_sensitivity_param{{"Political Sensitivity Param = 0.5"}}:::constant
        relief_decay_rate{{"Relief Decay Rate = 0.1"}}:::constant
        consumer_exposure_param{{"Consumer Exposure Param = 1.0"}}:::constant
        mena_supply_share{{"Mena Supply Share = 0.3"}}:::constant
        oil_inflation_passthrough{{"Oil Inflation Passthrough = 0.3"}}:::constant
        base_inflation{{"Base Inflation = 0.03"}}:::constant
        hormuz_disruption_mbd{{"Hormuz Disruption Mbd = 18.5"}}:::constant
        security_anxiety[/"Security Anxiety"/]:::computed
        net_hoarding_demand[/"Net Hoarding Demand"/]:::computed
        base_demand_adjusted[/"Base Demand Adjusted"/]:::computed
        effective_supply[/"Effective Supply"/]:::computed
        effective_demand[/"Effective Demand"/]:::computed
        supply_demand_gap[/"Supply Demand Gap"/]:::computed
        spr_release_rate[/"Spr Release Rate"/]:::computed
        jic_demand[/"Jic Demand"/]:::computed
        jic_target[/"Jic Target"/]:::computed
        supply_insecurity_level[/"Supply Insecurity Level"/]:::computed
        mena_revenue_signal[/"Mena Revenue Signal"/]:::computed
        de_dollarization_pressure[/"De Dollarization Pressure"/]:::computed
        inflation_rate[/"Inflation Rate"/]:::computed
        crowding_out_pressure[/"Crowding Out Pressure"/]:::computed
        tightening_pressure_combined[/"Tightening Pressure Combined"/]:::computed
        consumer_pain[/"Consumer Pain"/]:::computed
        gdp_impact_index[/"Gdp Impact Index"/]:::computed
    
        supply_restoration_rate ==>|"+"| global_oil_supply
        price_change_rate ==>|"+"| oil_price
        hoarding_rate ==>|"+"| precautionary_inventory
        precautionary_inventory ==>|"-"| destocking_rate
        credit_recovery_rate ==>|"+"| western_credit_index
        western_credit_index ==>|"-"| credit_tightening_rate
        jic_ratchet_rate ==>|"+"| supply_chain_buffer
        pressure_buildup_rate ==>|"+"| political_pressure
        political_pressure ==>|"-"| pressure_relief_rate
    
        strait_total_recovery_time -.-> supply_restoration_rate
        world_demand_base -.-> supply_restoration_rate
        price_adjustment_speed -.-> price_change_rate
        supply_demand_gap -.-> price_change_rate
        world_demand_base -.-> price_change_rate
        hoarding_propensity -.-> hoarding_rate
        world_demand_base -.-> hoarding_rate
        security_anxiety -.-> hoarding_rate
        destocking_rate_param -.-> destocking_rate
        security_anxiety -.-> destocking_rate
        jic_ratchet_speed -.-> jic_ratchet_rate
        jic_target -.-> jic_ratchet_rate
        political_sensitivity_param -.-> pressure_buildup_rate
        consumer_pain -.-> pressure_buildup_rate
        relief_decay_rate -.-> pressure_relief_rate
        credit_mean_reversion_rate -.-> credit_recovery_rate
        anxiety_price_sensitivity -.-> security_anxiety
        oil_price -.-> security_anxiety
        hoarding_rate -.-> net_hoarding_demand
        destocking_rate -.-> net_hoarding_demand
        demand_price_elasticity -.-> base_demand_adjusted
        world_demand_base -.-> base_demand_adjusted
        oil_price -.-> base_demand_adjusted
        spr_release_rate -.-> effective_supply
        global_oil_supply -.-> effective_supply
        net_hoarding_demand -.-> effective_demand
        jic_demand -.-> effective_demand
        base_demand_adjusted -.-> effective_demand
        effective_demand -.-> supply_demand_gap
        effective_supply -.-> supply_demand_gap
        spr_activation_coeff -.-> spr_release_rate
        spr_max_rate -.-> spr_release_rate
        spr_trigger_price -.-> spr_release_rate
        oil_price -.-> spr_release_rate
        supply_chain_buffer -.-> jic_demand
        jic_demand_factor -.-> jic_demand
        world_demand_base -.-> jic_demand
        jic_max_increment -.-> jic_target
        supply_insecurity_level -.-> jic_target
        supply_demand_gap -.-> supply_insecurity_level
        world_demand_base -.-> supply_insecurity_level
        mena_supply_share -.-> mena_revenue_signal
        oil_price -.-> mena_revenue_signal
        mena_revenue_signal -.-> de_dollarization_pressure
        credit_sensitivity_param -.-> de_dollarization_pressure
        oil_inflation_passthrough -.-> inflation_rate
        base_inflation -.-> inflation_rate
        oil_price -.-> inflation_rate
        inflation_rate -.-> crowding_out_pressure
        base_inflation -.-> crowding_out_pressure
        fiscal_sensitivity_param -.-> crowding_out_pressure
        de_dollarization_pressure -.-> tightening_pressure_combined
        crowding_out_pressure -.-> tightening_pressure_combined
        consumer_exposure_param -.-> consumer_pain
        oil_price -.-> consumer_pain
        gdp_credit_sensitivity_param -.-> gdp_impact_index
        western_credit_index -.-> gdp_impact_index
        oil_gdp_sensitivity -.-> gdp_impact_index
        oil_price -.-> gdp_impact_index
        """
        ),
        mo.Html("</div>"),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'global_oil_supply': 'Global Oil Supply (Mb/d)', 'oil_price': 'Oil Price (USD/bbl)', 'precautionary_inventory': 'Precautionary Inventory (Mb/d)', 'western_credit_index': 'Western Credit Index (index)', 'supply_chain_buffer': 'Supply Chain Buffer (dimensionless)', 'political_pressure': 'Political Pressure (index)'}
    fig_stocks = go.Figure()
    for _key in stock_selector.value:
        fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    _flow_labels = {'supply_restoration_rate': 'Supply Restoration Rate (Mb/d/month)', 'price_change_rate': 'Price Change Rate (USD/bbl/month)', 'hoarding_rate': 'Hoarding Rate (Mb/d)', 'destocking_rate': 'Destocking Rate (Mb/d)', 'jic_ratchet_rate': 'Jic Ratchet Rate (dimensionless/month)', 'pressure_buildup_rate': 'Pressure Buildup Rate (index/month)', 'pressure_relief_rate': 'Pressure Relief Rate (index/month)', 'credit_tightening_rate': 'Credit Tightening Rate (index/month)', 'credit_recovery_rate': 'Credit Recovery Rate (index/month)'}
    fig_flows = go.Figure()
    for _key in flow_selector.value:
        fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key)))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    _aux_labels = {'security_anxiety': 'Security Anxiety (dimensionless)', 'net_hoarding_demand': 'Net Hoarding Demand (Mb/d)', 'base_demand_adjusted': 'Base Demand Adjusted (Mb/d)', 'effective_supply': 'Effective Supply (Mb/d)', 'effective_demand': 'Effective Demand (Mb/d)', 'supply_demand_gap': 'Supply Demand Gap (Mb/d)', 'spr_release_rate': 'Spr Release Rate (Mb/d)', 'jic_demand': 'Jic Demand (Mb/d)', 'jic_target': 'Jic Target (dimensionless)', 'supply_insecurity_level': 'Supply Insecurity Level (dimensionless)', 'mena_revenue_signal': 'Mena Revenue Signal (USD/bbl * fraction)', 'de_dollarization_pressure': 'De Dollarization Pressure (index/month)', 'inflation_rate': 'Inflation Rate (fraction)', 'crowding_out_pressure': 'Crowding Out Pressure (index/month)', 'tightening_pressure_combined': 'Tightening Pressure Combined (index/month)', 'consumer_pain': 'Consumer Pain (dimensionless)', 'gdp_impact_index': 'Gdp Impact Index (dimensionless)'}
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
