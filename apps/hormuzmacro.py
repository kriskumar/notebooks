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
9 stocks, 12 flows, 38 parameters, 27 computed variables.

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
    agri_adjustment_speed,
    agri_direct_impact,
    anxiety_price_sensitivity,
    base_inflation,
    consumer_exposure_param,
    credit_mean_reversion_rate,
    credit_sensitivity_param,
    credit_transmission_lag,
    crop_cycle_lag,
    demand_price_elasticity,
    destocking_rate_param,
    fertilizer_adjustment_speed,
    fertilizer_agri_passthrough,
    fiscal_sensitivity_param,
    food_weight_in_cpi,
    gas_ammonia_cost_share,
    gas_oil_passthrough,
    gdp_credit_sensitivity_param,
    hoarding_propensity,
    hormuz_disruption_mbd,
    hormuz_fertilizer_impact,
    hormuz_gas_share,
    jic_demand_factor,
    jic_max_increment,
    jic_ratchet_speed,
    mena_supply_share,
    naphtha_adjustment_speed,
    naphtha_crack_ratio,
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
    fertilizer_price_index = 1.0
    naphtha_price_index = 1.0
    agri_price_index = 1.0
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
    gas_price_index = 0  # Will be computed in loop
    ammonia_cost_index = 0  # Will be computed in loop
    fertilizer_supply_factor = 0  # Will be computed in loop
    fertilizer_target = 0  # Will be computed in loop
    naphtha_target = 0  # Will be computed in loop
    delayed_fertilizer_signal = 0  # Will be computed in loop
    agri_supply_disruption = 0  # Will be computed in loop
    agri_target = 0  # Will be computed in loop
    food_inflation_contribution = 0  # Will be computed in loop
    commodity_cascade_index = 0  # Will be computed in loop

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
        consumer_pain = (max(0, ((oil_price / 90) - 1)) * consumer_exposure_param.value)
        gdp_impact_index = max(0.5, ((1 - (((100 - western_credit_index) / 100) * gdp_credit_sensitivity_param.value)) - (max(0, ((oil_price / 90) - 1)) * oil_gdp_sensitivity.value)))
        gas_price_index = ((1 + (gas_oil_passthrough.value * ((oil_price / 90) - 1))) + max(0, ((1 - (global_oil_supply / world_demand_base.value)) * hormuz_gas_share.value)))
        fertilizer_supply_factor = (1 + max(0, ((1 - (global_oil_supply / world_demand_base.value)) * hormuz_fertilizer_impact.value)))
        naphtha_target = max(0.5, (oil_price / 90))
        delayed_fertilizer_signal = 0
        agri_supply_disruption = max(0, ((1 - (global_oil_supply / world_demand_base.value)) * agri_direct_impact.value))
        food_inflation_contribution = ((agri_price_index - 1) * food_weight_in_cpi.value)
        commodity_cascade_index = (((fertilizer_price_index + naphtha_price_index) + agri_price_index) / 3)
        hoarding_rate = ((security_anxiety * hoarding_propensity.value) * world_demand_base.value)
        destocking_rate = ((precautionary_inventory * (1 - security_anxiety)) * destocking_rate_param.value)
        effective_supply = (global_oil_supply + spr_release_rate)
        de_dollarization_pressure = (mena_revenue_signal * credit_sensitivity_param.value)
        pressure_buildup_rate = (consumer_pain * political_sensitivity_param.value)
        ammonia_cost_index = ((gas_ammonia_cost_share.value * gas_price_index) + (1 - gas_ammonia_cost_share.value))
        naphtha_price_change = ((naphtha_target - naphtha_price_index) * naphtha_adjustment_speed.value)
        agri_target = max(1, ((1 + ((delayed_fertilizer_signal - 1) * fertilizer_agri_passthrough.value)) + agri_supply_disruption))
        inflation_rate = (((((oil_price / 90) - 1) * oil_inflation_passthrough.value) + base_inflation.value) + food_inflation_contribution)
        net_hoarding_demand = (hoarding_rate - destocking_rate)
        fertilizer_target = max(1, (ammonia_cost_index * fertilizer_supply_factor))
        agri_price_change = ((agri_target - agri_price_index) * agri_adjustment_speed.value)
        crowding_out_pressure = max(0, ((inflation_rate - base_inflation.value) * fiscal_sensitivity_param.value))
        effective_demand = ((base_demand_adjusted + net_hoarding_demand) + jic_demand)
        fertilizer_price_change = ((fertilizer_target - fertilizer_price_index) * fertilizer_adjustment_speed.value)
        tightening_pressure_combined = (de_dollarization_pressure + crowding_out_pressure)
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
                "fertilizer_price_index": fertilizer_price_index,
                "naphtha_price_index": naphtha_price_index,
                "agri_price_index": agri_price_index,
                "supply_restoration_rate": supply_restoration_rate,
                "price_change_rate": price_change_rate,
                "hoarding_rate": hoarding_rate,
                "destocking_rate": destocking_rate,
                "jic_ratchet_rate": jic_ratchet_rate,
                "pressure_buildup_rate": pressure_buildup_rate,
                "pressure_relief_rate": pressure_relief_rate,
                "credit_tightening_rate": credit_tightening_rate,
                "credit_recovery_rate": credit_recovery_rate,
                "fertilizer_price_change": fertilizer_price_change,
                "naphtha_price_change": naphtha_price_change,
                "agri_price_change": agri_price_change,
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
                "gas_price_index": gas_price_index,
                "ammonia_cost_index": ammonia_cost_index,
                "fertilizer_supply_factor": fertilizer_supply_factor,
                "fertilizer_target": fertilizer_target,
                "naphtha_target": naphtha_target,
                "delayed_fertilizer_signal": delayed_fertilizer_signal,
                "agri_supply_disruption": agri_supply_disruption,
                "agri_target": agri_target,
                "food_inflation_contribution": food_inflation_contribution,
                "commodity_cascade_index": commodity_cascade_index,
            }
        )

        # Euler integration
        global_oil_supply += dt * supply_restoration_rate
        oil_price += dt * price_change_rate
        precautionary_inventory += dt * (hoarding_rate - destocking_rate)
        western_credit_index += dt * (credit_recovery_rate - credit_tightening_rate)
        supply_chain_buffer += dt * jic_ratchet_rate
        political_pressure += dt * (pressure_buildup_rate - pressure_relief_rate)
        fertilizer_price_index += dt * fertilizer_price_change
        naphtha_price_index += dt * naphtha_price_change
        agri_price_index += dt * agri_price_change
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Hormuzmacro — Interactive Explorer

    **Stocks:** 9 | **Flows:** 12 | **Parameters:** 38 | **Computed:** 27

    Adjust the sliders below to change parameters and see how the model responds in real time.
    """
    )
    return


@app.cell
def time_controls(mo):
    final_time = mo.ui.number(
        value=18, start=1, stop=180, step=1, label="Final Time"
    )
    time_step = mo.ui.number(
        value=0.0625, start=0.1, stop=5.0, step=0.1, label="Time Step"
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
        value=-0.02, start=-0.1, stop=0, step=0.001,
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
    gas_oil_passthrough = mo.ui.slider(
        value=0.7, start=0, stop=1, step=0.01,
        label="Gas Oil Passthrough (dimensionless)",
    )
    gas_ammonia_cost_share = mo.ui.slider(
        value=0.8, start=0, stop=1, step=0.01,
        label="Gas Ammonia Cost Share (dimensionless)",
    )
    hormuz_gas_share = mo.ui.slider(
        value=0.3, start=0, stop=1, step=0.01,
        label="Hormuz Gas Share (dimensionless)",
    )
    hormuz_fertilizer_impact = mo.ui.slider(
        value=0.5, start=0, stop=1, step=0.01,
        label="Hormuz Fertilizer Impact (dimensionless)",
    )
    fertilizer_adjustment_speed = mo.ui.slider(
        value=0.3, start=0, stop=1, step=0.01,
        label="Fertilizer Adjustment Speed (1/month)",
    )
    naphtha_crack_ratio = mo.ui.slider(
        value=0.85, start=0, stop=1, step=0.01,
        label="Naphtha Crack Ratio (dimensionless)",
    )
    naphtha_adjustment_speed = mo.ui.slider(
        value=0.6, start=0, stop=1, step=0.01,
        label="Naphtha Adjustment Speed (1/month)",
    )
    crop_cycle_lag = mo.ui.slider(
        value=4.0, start=0, stop=20.0, step=0.04,
        label="Crop Cycle Lag (months)",
    )
    fertilizer_agri_passthrough = mo.ui.slider(
        value=0.35, start=0, stop=1, step=0.01,
        label="Fertilizer Agri Passthrough (dimensionless)",
    )
    agri_adjustment_speed = mo.ui.slider(
        value=0.15, start=0, stop=1, step=0.01,
        label="Agri Adjustment Speed (1/month)",
    )
    agri_direct_impact = mo.ui.slider(
        value=0.2, start=0, stop=1, step=0.01,
        label="Agri Direct Impact (dimensionless)",
    )
    food_weight_in_cpi = mo.ui.slider(
        value=0.15, start=0, stop=1, step=0.01,
        label="Food Weight In Cpi (dimensionless)",
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
        gas_oil_passthrough,
        gas_ammonia_cost_share,
        hormuz_gas_share,
        hormuz_fertilizer_impact,
        fertilizer_adjustment_speed,
        naphtha_crack_ratio,
        naphtha_adjustment_speed,
        crop_cycle_lag,
        fertilizer_agri_passthrough,
        agri_adjustment_speed,
        agri_direct_impact,
        food_weight_in_cpi,
        ]
    )
    return (
        agri_adjustment_speed,
        agri_direct_impact,
        anxiety_price_sensitivity,
        base_inflation,
        consumer_exposure_param,
        credit_mean_reversion_rate,
        credit_sensitivity_param,
        credit_transmission_lag,
        crop_cycle_lag,
        demand_price_elasticity,
        destocking_rate_param,
        fertilizer_adjustment_speed,
        fertilizer_agri_passthrough,
        fiscal_sensitivity_param,
        food_weight_in_cpi,
        gas_ammonia_cost_share,
        gas_oil_passthrough,
        gdp_credit_sensitivity_param,
        hoarding_propensity,
        hormuz_disruption_mbd,
        hormuz_fertilizer_impact,
        hormuz_gas_share,
        jic_demand_factor,
        jic_max_increment,
        jic_ratchet_speed,
        mena_supply_share,
        naphtha_adjustment_speed,
        naphtha_crack_ratio,
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
        options={"Global Oil Supply (Mb/d)": "global_oil_supply", "Oil Price (USD/bbl)": "oil_price", "Precautionary Inventory (Mb/d)": "precautionary_inventory", "Western Credit Index (index)": "western_credit_index", "Supply Chain Buffer (dimensionless)": "supply_chain_buffer", "Political Pressure (index)": "political_pressure", "Fertilizer Price Index (index)": "fertilizer_price_index", "Naphtha Price Index (index)": "naphtha_price_index", "Agri Price Index (index)": "agri_price_index"},
        value=["Global Oil Supply (Mb/d)", "Oil Price (USD/bbl)", "Precautionary Inventory (Mb/d)", "Western Credit Index (index)", "Supply Chain Buffer (dimensionless)", "Political Pressure (index)", "Fertilizer Price Index (index)", "Naphtha Price Index (index)", "Agri Price Index (index)"],
        label="Stock variables",
    )
    flow_selector = mo.ui.multiselect(
        options={"Supply Restoration Rate (Mb/d/month)": "supply_restoration_rate", "Price Change Rate (USD/bbl/month)": "price_change_rate", "Hoarding Rate (Mb/d)": "hoarding_rate", "Destocking Rate (Mb/d)": "destocking_rate", "Jic Ratchet Rate (dimensionless/month)": "jic_ratchet_rate", "Pressure Buildup Rate (index/month)": "pressure_buildup_rate", "Pressure Relief Rate (index/month)": "pressure_relief_rate", "Credit Tightening Rate (index/month)": "credit_tightening_rate", "Credit Recovery Rate (index/month)": "credit_recovery_rate", "Fertilizer Price Change (index/month)": "fertilizer_price_change", "Naphtha Price Change (index/month)": "naphtha_price_change", "Agri Price Change (index/month)": "agri_price_change"},
        value=["Supply Restoration Rate (Mb/d/month)", "Price Change Rate (USD/bbl/month)", "Hoarding Rate (Mb/d)", "Destocking Rate (Mb/d)", "Jic Ratchet Rate (dimensionless/month)", "Pressure Buildup Rate (index/month)", "Pressure Relief Rate (index/month)", "Credit Tightening Rate (index/month)", "Credit Recovery Rate (index/month)", "Fertilizer Price Change (index/month)", "Naphtha Price Change (index/month)", "Agri Price Change (index/month)"],
        label="Flow variables",
    )
    aux_selector = mo.ui.multiselect(
        options={"Security Anxiety (dimensionless)": "security_anxiety", "Net Hoarding Demand (Mb/d)": "net_hoarding_demand", "Base Demand Adjusted (Mb/d)": "base_demand_adjusted", "Effective Supply (Mb/d)": "effective_supply", "Effective Demand (Mb/d)": "effective_demand", "Supply Demand Gap (Mb/d)": "supply_demand_gap", "Spr Release Rate (Mb/d)": "spr_release_rate", "Jic Demand (Mb/d)": "jic_demand", "Jic Target (dimensionless)": "jic_target", "Supply Insecurity Level (dimensionless)": "supply_insecurity_level", "Mena Revenue Signal (USD/bbl * fraction)": "mena_revenue_signal", "De Dollarization Pressure (index/month)": "de_dollarization_pressure", "Inflation Rate (fraction)": "inflation_rate", "Crowding Out Pressure (index/month)": "crowding_out_pressure", "Tightening Pressure Combined (index/month)": "tightening_pressure_combined", "Consumer Pain (dimensionless)": "consumer_pain", "Gdp Impact Index (dimensionless)": "gdp_impact_index", "Gas Price Index (index)": "gas_price_index", "Ammonia Cost Index (index)": "ammonia_cost_index", "Fertilizer Supply Factor (dimensionless)": "fertilizer_supply_factor", "Fertilizer Target (index)": "fertilizer_target", "Naphtha Target (index)": "naphtha_target", "Delayed Fertilizer Signal (index)": "delayed_fertilizer_signal", "Agri Supply Disruption (dimensionless)": "agri_supply_disruption", "Agri Target (index)": "agri_target", "Food Inflation Contribution (fraction)": "food_inflation_contribution", "Commodity Cascade Index (index)": "commodity_cascade_index"},
        value=["Security Anxiety (dimensionless)", "Net Hoarding Demand (Mb/d)", "Base Demand Adjusted (Mb/d)", "Effective Supply (Mb/d)", "Effective Demand (Mb/d)", "Supply Demand Gap (Mb/d)", "Spr Release Rate (Mb/d)", "Jic Demand (Mb/d)", "Jic Target (dimensionless)", "Supply Insecurity Level (dimensionless)", "Mena Revenue Signal (USD/bbl * fraction)", "De Dollarization Pressure (index/month)", "Inflation Rate (fraction)", "Crowding Out Pressure (index/month)", "Tightening Pressure Combined (index/month)", "Consumer Pain (dimensionless)", "Gdp Impact Index (dimensionless)", "Gas Price Index (index)", "Ammonia Cost Index (index)", "Fertilizer Supply Factor (dimensionless)", "Fertilizer Target (index)", "Naphtha Target (index)", "Delayed Fertilizer Signal (index)", "Agri Supply Disruption (dimensionless)", "Agri Target (index)", "Food Inflation Contribution (fraction)", "Commodity Cascade Index (index)"],
        label="Auxiliary variables",
    )
    return stock_selector, flow_selector, aux_selector


@app.cell
def tabbed_content(aux_selector, flow_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
## Hormuz Strait Closure — Macro + Commodity Cascade

*Based on Carlyle "A Crude Awakening" (March 2026)*

> "Oil feeds gas, gas feeds ammonia, ammonia feeds urea, naphtha feeds crackers, crackers feed polymers."

### Four Oil-Layer Feedback Loops
**R1 — Hoarding Multiplier**: price → anxiety → 2–3 Mb/d precautionary demand surge  
**B1 — Infrastructure Recovery Lag**: first-order supply restoration; `strait_total_recovery_time` is the key dial  
**B2 — Reversed Credit Channel**: DELAY3(6mo) de-dollarization + fiscal crowding-out, amplified by food inflation  
**R2 — JIT→JIC Ratchet**: permanent structural demand step-up as every importer secures simultaneously  
**B3 — SPR Release**: capped at 4.4 Mb/d (<25% of disruption)

### Commodity Cascade (with lags)
- **Gas** → oil passthrough (70%) + direct Hormuz LNG disruption (Qatar = 20% global LNG)
- **Fertilizer/Urea** → gas is 80% of ammonia cost; Qatar + Iran supply cut; ~1–2 month lag
- **Naphtha** → direct petroleum distillate; tracks crude with ~0.5–1 month lag; feedstock for plastics
- **Agricultural Commodities** → fertilizer shortage via **4-month crop-cycle lag** + direct MENA agri disruption
- **Feedback**: agri prices → food CPI (15%) → inflation → crowding-out → tighter credit (amplifies B2)

### Baseline Results (6-month recovery)
| Month | Oil | Gas idx | Fertilizer | Naphtha | Agri | Inflation | Credit | GDP |
|-------|-----|---------|------------|---------|------|-----------|--------|-----|
| t=0 | $90 | 1.054 | 1.000 | 1.000 | 1.000 | 3.0% | 100 | 1.00 |
| t=6 | $110 | 1.179 | 1.140 | 1.178 | 1.018 | 10.1% | 97.1 | 0.954 |
| t=12 | $118 | 1.227 | 1.184 | 1.296 | 1.038 | 13.0% | 84.2 | 0.890 |
| t=18 | $120 | 1.235 | 1.193 | 1.330 | 1.054 | 13.8% | 67.9 | 0.822 |

The **4-month agri lag** is key: food pain arrives just as markets think the crisis has passed.

### Key Dial: `strait_total_recovery_time`
- 3 months (quick): oil ~$105, credit holds, agri barely moves
- 6 months (baseline): oil ~$120, fertilizer +19%, credit −32%
- 12 months (mined): oil >$147 rising, credit collapses

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
        fertilizer_price_index["Fertilizer Price Index"]:::stock
        naphtha_price_index["Naphtha Price Index"]:::stock
        agri_price_index["Agri Price Index"]:::stock
        supply_restoration_rate(["Supply Restoration Rate"]):::flow
        price_change_rate(["Price Change Rate"]):::flow
        hoarding_rate(["Hoarding Rate"]):::flow
        destocking_rate(["Destocking Rate"]):::flow
        jic_ratchet_rate(["Jic Ratchet Rate"]):::flow
        pressure_buildup_rate(["Pressure Buildup Rate"]):::flow
        pressure_relief_rate(["Pressure Relief Rate"]):::flow
        credit_tightening_rate(["Credit Tightening Rate"]):::flow
        credit_recovery_rate(["Credit Recovery Rate"]):::flow
        fertilizer_price_change(["Fertilizer Price Change"]):::flow
        naphtha_price_change(["Naphtha Price Change"]):::flow
        agri_price_change(["Agri Price Change"]):::flow
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
        gas_oil_passthrough{{"Gas Oil Passthrough = 0.7"}}:::constant
        gas_ammonia_cost_share{{"Gas Ammonia Cost Share = 0.8"}}:::constant
        hormuz_gas_share{{"Hormuz Gas Share = 0.3"}}:::constant
        hormuz_fertilizer_impact{{"Hormuz Fertilizer Impact = 0.5"}}:::constant
        fertilizer_adjustment_speed{{"Fertilizer Adjustment Speed = 0.3"}}:::constant
        naphtha_crack_ratio{{"Naphtha Crack Ratio = 0.85"}}:::constant
        naphtha_adjustment_speed{{"Naphtha Adjustment Speed = 0.6"}}:::constant
        crop_cycle_lag{{"Crop Cycle Lag = 4.0"}}:::constant
        fertilizer_agri_passthrough{{"Fertilizer Agri Passthrough = 0.35"}}:::constant
        agri_adjustment_speed{{"Agri Adjustment Speed = 0.15"}}:::constant
        agri_direct_impact{{"Agri Direct Impact = 0.2"}}:::constant
        food_weight_in_cpi{{"Food Weight In Cpi = 0.15"}}:::constant
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
        gas_price_index[/"Gas Price Index"/]:::computed
        ammonia_cost_index[/"Ammonia Cost Index"/]:::computed
        fertilizer_supply_factor[/"Fertilizer Supply Factor"/]:::computed
        fertilizer_target[/"Fertilizer Target"/]:::computed
        naphtha_target[/"Naphtha Target"/]:::computed
        delayed_fertilizer_signal[/"Delayed Fertilizer Signal"/]:::computed
        agri_supply_disruption[/"Agri Supply Disruption"/]:::computed
        agri_target[/"Agri Target"/]:::computed
        food_inflation_contribution[/"Food Inflation Contribution"/]:::computed
        commodity_cascade_index[/"Commodity Cascade Index"/]:::computed
    
        supply_restoration_rate ==>|"+"| global_oil_supply
        price_change_rate ==>|"+"| oil_price
        hoarding_rate ==>|"+"| precautionary_inventory
        precautionary_inventory ==>|"-"| destocking_rate
        credit_recovery_rate ==>|"+"| western_credit_index
        western_credit_index ==>|"-"| credit_tightening_rate
        jic_ratchet_rate ==>|"+"| supply_chain_buffer
        pressure_buildup_rate ==>|"+"| political_pressure
        political_pressure ==>|"-"| pressure_relief_rate
        fertilizer_price_change ==>|"+"| fertilizer_price_index
        naphtha_price_change ==>|"+"| naphtha_price_index
        agri_price_change ==>|"+"| agri_price_index
    
        strait_total_recovery_time -.-> supply_restoration_rate
        world_demand_base -.-> supply_restoration_rate
        price_adjustment_speed -.-> price_change_rate
        supply_demand_gap -.-> price_change_rate
        world_demand_base -.-> price_change_rate
        hoarding_propensity -.-> hoarding_rate
        security_anxiety -.-> hoarding_rate
        world_demand_base -.-> hoarding_rate
        security_anxiety -.-> destocking_rate
        destocking_rate_param -.-> destocking_rate
        jic_target -.-> jic_ratchet_rate
        jic_ratchet_speed -.-> jic_ratchet_rate
        consumer_pain -.-> pressure_buildup_rate
        political_sensitivity_param -.-> pressure_buildup_rate
        relief_decay_rate -.-> pressure_relief_rate
        credit_mean_reversion_rate -.-> credit_recovery_rate
        fertilizer_target -.-> fertilizer_price_change
        fertilizer_adjustment_speed -.-> fertilizer_price_change
        naphtha_adjustment_speed -.-> naphtha_price_change
        naphtha_target -.-> naphtha_price_change
        agri_adjustment_speed -.-> agri_price_change
        agri_target -.-> agri_price_change
        oil_price -.-> security_anxiety
        anxiety_price_sensitivity -.-> security_anxiety
        destocking_rate -.-> net_hoarding_demand
        hoarding_rate -.-> net_hoarding_demand
        demand_price_elasticity -.-> base_demand_adjusted
        oil_price -.-> base_demand_adjusted
        world_demand_base -.-> base_demand_adjusted
        global_oil_supply -.-> effective_supply
        spr_release_rate -.-> effective_supply
        base_demand_adjusted -.-> effective_demand
        net_hoarding_demand -.-> effective_demand
        jic_demand -.-> effective_demand
        effective_supply -.-> supply_demand_gap
        effective_demand -.-> supply_demand_gap
        spr_trigger_price -.-> spr_release_rate
        oil_price -.-> spr_release_rate
        spr_activation_coeff -.-> spr_release_rate
        spr_max_rate -.-> spr_release_rate
        supply_chain_buffer -.-> jic_demand
        jic_demand_factor -.-> jic_demand
        world_demand_base -.-> jic_demand
        supply_insecurity_level -.-> jic_target
        jic_max_increment -.-> jic_target
        supply_demand_gap -.-> supply_insecurity_level
        world_demand_base -.-> supply_insecurity_level
        oil_price -.-> mena_revenue_signal
        mena_supply_share -.-> mena_revenue_signal
        mena_revenue_signal -.-> de_dollarization_pressure
        credit_sensitivity_param -.-> de_dollarization_pressure
        oil_price -.-> inflation_rate
        food_inflation_contribution -.-> inflation_rate
        base_inflation -.-> inflation_rate
        oil_inflation_passthrough -.-> inflation_rate
        fiscal_sensitivity_param -.-> crowding_out_pressure
        base_inflation -.-> crowding_out_pressure
        inflation_rate -.-> crowding_out_pressure
        de_dollarization_pressure -.-> tightening_pressure_combined
        crowding_out_pressure -.-> tightening_pressure_combined
        oil_price -.-> consumer_pain
        consumer_exposure_param -.-> consumer_pain
        western_credit_index -.-> gdp_impact_index
        oil_gdp_sensitivity -.-> gdp_impact_index
        oil_price -.-> gdp_impact_index
        gdp_credit_sensitivity_param -.-> gdp_impact_index
        hormuz_gas_share -.-> gas_price_index
        oil_price -.-> gas_price_index
        gas_oil_passthrough -.-> gas_price_index
        global_oil_supply -.-> gas_price_index
        world_demand_base -.-> gas_price_index
        gas_ammonia_cost_share -.-> ammonia_cost_index
        gas_price_index -.-> ammonia_cost_index
        global_oil_supply -.-> fertilizer_supply_factor
        hormuz_fertilizer_impact -.-> fertilizer_supply_factor
        world_demand_base -.-> fertilizer_supply_factor
        ammonia_cost_index -.-> fertilizer_target
        fertilizer_supply_factor -.-> fertilizer_target
        oil_price -.-> naphtha_target
        global_oil_supply -.-> agri_supply_disruption
        agri_direct_impact -.-> agri_supply_disruption
        world_demand_base -.-> agri_supply_disruption
        fertilizer_agri_passthrough -.-> agri_target
        delayed_fertilizer_signal -.-> agri_target
        agri_supply_disruption -.-> agri_target
        food_weight_in_cpi -.-> food_inflation_contribution
        agri_price_index -.-> food_inflation_contribution
        fertilizer_price_index -.-> commodity_cascade_index
        naphtha_price_index -.-> commodity_cascade_index
        agri_price_index -.-> commodity_cascade_index
        """
        ),
        mo.Html("</div>"),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'global_oil_supply': 'Global Oil Supply (Mb/d)', 'oil_price': 'Oil Price (USD/bbl)', 'precautionary_inventory': 'Precautionary Inventory (Mb/d)', 'western_credit_index': 'Western Credit Index (index)', 'supply_chain_buffer': 'Supply Chain Buffer (dimensionless)', 'political_pressure': 'Political Pressure (index)', 'fertilizer_price_index': 'Fertilizer Price Index (index)', 'naphtha_price_index': 'Naphtha Price Index (index)', 'agri_price_index': 'Agri Price Index (index)'}
    fig_stocks = go.Figure()
    for _key in stock_selector.value:
        fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    _flow_labels = {'supply_restoration_rate': 'Supply Restoration Rate (Mb/d/month)', 'price_change_rate': 'Price Change Rate (USD/bbl/month)', 'hoarding_rate': 'Hoarding Rate (Mb/d)', 'destocking_rate': 'Destocking Rate (Mb/d)', 'jic_ratchet_rate': 'Jic Ratchet Rate (dimensionless/month)', 'pressure_buildup_rate': 'Pressure Buildup Rate (index/month)', 'pressure_relief_rate': 'Pressure Relief Rate (index/month)', 'credit_tightening_rate': 'Credit Tightening Rate (index/month)', 'credit_recovery_rate': 'Credit Recovery Rate (index/month)', 'fertilizer_price_change': 'Fertilizer Price Change (index/month)', 'naphtha_price_change': 'Naphtha Price Change (index/month)', 'agri_price_change': 'Agri Price Change (index/month)'}
    fig_flows = go.Figure()
    for _key in flow_selector.value:
        fig_flows.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_flow_labels.get(_key, _key)))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    _aux_labels = {'security_anxiety': 'Security Anxiety (dimensionless)', 'net_hoarding_demand': 'Net Hoarding Demand (Mb/d)', 'base_demand_adjusted': 'Base Demand Adjusted (Mb/d)', 'effective_supply': 'Effective Supply (Mb/d)', 'effective_demand': 'Effective Demand (Mb/d)', 'supply_demand_gap': 'Supply Demand Gap (Mb/d)', 'spr_release_rate': 'Spr Release Rate (Mb/d)', 'jic_demand': 'Jic Demand (Mb/d)', 'jic_target': 'Jic Target (dimensionless)', 'supply_insecurity_level': 'Supply Insecurity Level (dimensionless)', 'mena_revenue_signal': 'Mena Revenue Signal (USD/bbl * fraction)', 'de_dollarization_pressure': 'De Dollarization Pressure (index/month)', 'inflation_rate': 'Inflation Rate (fraction)', 'crowding_out_pressure': 'Crowding Out Pressure (index/month)', 'tightening_pressure_combined': 'Tightening Pressure Combined (index/month)', 'consumer_pain': 'Consumer Pain (dimensionless)', 'gdp_impact_index': 'Gdp Impact Index (dimensionless)', 'gas_price_index': 'Gas Price Index (index)', 'ammonia_cost_index': 'Ammonia Cost Index (index)', 'fertilizer_supply_factor': 'Fertilizer Supply Factor (dimensionless)', 'fertilizer_target': 'Fertilizer Target (index)', 'naphtha_target': 'Naphtha Target (index)', 'delayed_fertilizer_signal': 'Delayed Fertilizer Signal (index)', 'agri_supply_disruption': 'Agri Supply Disruption (dimensionless)', 'agri_target': 'Agri Target (index)', 'food_inflation_contribution': 'Food Inflation Contribution (fraction)', 'commodity_cascade_index': 'Commodity Cascade Index (index)'}
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
