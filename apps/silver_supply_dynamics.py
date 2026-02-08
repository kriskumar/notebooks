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
Silver Supply Dynamics — Interactive Explorer

System dynamics model with inline Euler integration.
5 stocks, 7 flows, 12 parameters, 6 computed variables.

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
    base_industrial_demand,
    china_export_fraction,
    geopolitical_pressure,
    institutional_dampening,
    price_adjustment_speed,
    reference_inventory,
    restriction_rate,
    retail_buy_intensity,
    sentiment_decay_rate,
    social_media_amplifier,
    solar_demand_growth,
    western_supply_base,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values
    warehouse_inventory = 300.0
    retail_holdings = 200.0
    silver_price = 30.0
    chinese_export_capacity = 80.0
    retail_sentiment = 0.3

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        # Flows and computed variables (dependency order)
        western_supply = western_supply_base.value
        industrial_demand = (base_industrial_demand.value + solar_demand_growth.value)
        net_retail_flow = (retail_buy_intensity.value * retail_sentiment * warehouse_inventory)
        chinese_export_flow = (chinese_export_capacity * china_export_fraction.value)
        export_restriction = (chinese_export_capacity * restriction_rate.value * geopolitical_pressure.value)
        inventory_ratio = (warehouse_inventory / reference_inventory.value)
        effective_amplification = (social_media_amplifier.value - institutional_dampening.value)
        sentiment_decay = (retail_sentiment * sentiment_decay_rate.value)
        demand_supply_pressure = (1 - inventory_ratio)
        price_change = (silver_price * price_adjustment_speed.value * demand_supply_pressure)
        price_momentum = (price_change / max(silver_price, 1e-6))
        sentiment_change = (effective_amplification * price_momentum - sentiment_decay)
        institutional_edge = (demand_supply_pressure - price_momentum)

        rows.append(
            {
                "time": t,
                "warehouse_inventory": warehouse_inventory,
                "retail_holdings": retail_holdings,
                "silver_price": silver_price,
                "chinese_export_capacity": chinese_export_capacity,
                "retail_sentiment": retail_sentiment,
                "western_supply": western_supply,
                "industrial_demand": industrial_demand,
                "net_retail_flow": net_retail_flow,
                "chinese_export_flow": chinese_export_flow,
                "export_restriction": export_restriction,
                "price_change": price_change,
                "sentiment_change": sentiment_change,
                "inventory_ratio": inventory_ratio,
                "demand_supply_pressure": demand_supply_pressure,
                "price_momentum": price_momentum,
                "effective_amplification": effective_amplification,
                "sentiment_decay": sentiment_decay,
                "institutional_edge": institutional_edge,
            }
        )

        # Euler integration
        warehouse_inventory += dt * (western_supply + chinese_export_flow - industrial_demand - net_retail_flow)
        warehouse_inventory = max(warehouse_inventory, 10)
        retail_holdings += dt * net_retail_flow
        retail_holdings = max(retail_holdings, 0)
        silver_price += dt * price_change
        silver_price = max(silver_price, 5)
        chinese_export_capacity += dt * (0 - export_restriction)
        chinese_export_capacity = max(chinese_export_capacity, 0)
        retail_sentiment += dt * sentiment_change
        retail_sentiment = max(retail_sentiment, 0.01)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Silver Supply Dynamics — Interactive Explorer

    **Stocks:** 5 | **Flows:** 7 | **Parameters:** 12 | **Computed:** 6

    Adjust the sliders below to change parameters and see how the model responds in real time.
    """
    )
    return


@app.cell
def time_controls(mo):
    final_time = mo.ui.number(
        value=24, start=1, stop=240, step=1, label="Final Time"
    )
    time_step = mo.ui.number(
        value=0.25, start=0.1, stop=5.0, step=0.1, label="Time Step"
    )
    mo.hstack([final_time, time_step], justify="start", gap=1)
    return final_time, time_step


@app.cell
def parameter_controls(mo):
    western_supply_base = mo.ui.slider(
        value=640.0, start=500.0, stop=800.0, step=3.0,
        label="Western Supply Base (Moz/yr)",
    )
    base_industrial_demand = mo.ui.slider(
        value=500.0, start=400.0, stop=650.0, step=2.5,
        label="Base Industrial Demand (Moz/yr)",
    )
    solar_demand_growth = mo.ui.slider(
        value=200.0, start=100.0, stop=400.0, step=3.0,
        label="Solar Demand Growth (Moz/yr)",
    )
    retail_buy_intensity = mo.ui.slider(
        value=0.15, start=0.05, stop=0.4, step=0.0035,
        label="Retail Buy Intensity (1/yr)",
    )
    china_export_fraction = mo.ui.slider(
        value=0.8, start=0.2, stop=1.0, step=0.008,
        label="China Export Fraction (dimensionless)",
    )
    restriction_rate = mo.ui.slider(
        value=0.03, start=0.0, stop=0.15, step=0.0015,
        label="Restriction Rate (1/yr)",
    )
    geopolitical_pressure = mo.ui.slider(
        value=1.5, start=0.5, stop=3.0, step=0.025,
        label="Geopolitical Pressure (dimensionless)",
    )
    price_adjustment_speed = mo.ui.slider(
        value=0.5, start=0.1, stop=1.5, step=0.014,
        label="Price Adjustment Speed (1/yr)",
    )
    institutional_dampening = mo.ui.slider(
        value=1.0, start=0.0, stop=2.5, step=0.025,
        label="Institutional Dampening (dimensionless)",
    )
    social_media_amplifier = mo.ui.slider(
        value=3.0, start=1.0, stop=8.0, step=0.07,
        label="Social Media Amplifier (dimensionless)",
    )
    sentiment_decay_rate = mo.ui.slider(
        value=0.4, start=0.1, stop=1.0, step=0.009,
        label="Sentiment Decay Rate (1/yr)",
    )
    reference_inventory = mo.ui.slider(
        value=300.0, start=100.0, stop=500.0, step=4.0,
        label="Reference Inventory (Moz)",
    )
    mo.vstack(
        [
        western_supply_base,
        base_industrial_demand,
        solar_demand_growth,
        retail_buy_intensity,
        china_export_fraction,
        restriction_rate,
        geopolitical_pressure,
        price_adjustment_speed,
        institutional_dampening,
        social_media_amplifier,
        sentiment_decay_rate,
        reference_inventory,
        ]
    )
    return (
        base_industrial_demand,
        china_export_fraction,
        geopolitical_pressure,
        institutional_dampening,
        price_adjustment_speed,
        reference_inventory,
        restriction_rate,
        retail_buy_intensity,
        sentiment_decay_rate,
        social_media_amplifier,
        solar_demand_growth,
        western_supply_base,
    )


@app.cell
def tabbed_content(go, mo, results):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md("""
## Silver Supply Dynamics -- Analysis

### Original Question
*How do information asymmetries between commodity trading desks and retail investors shape silver price dynamics during supply squeezes? What structural factors (Chinese export controls, solar demand growth) interact with social media-driven speculation, and who actually captures value?*

### Key Feedback Loops

| Loop | Type | Mechanism |
|------|------|-----------|
| **R1 -- Retail FOMO** | Reinforcing | Price rises -> momentum -> social media amplification -> sentiment -> more buying -> inventory drain -> price rises |
| **R2 -- Chinese Supply Squeeze** | Reinforcing | Geopolitical pressure -> export restrictions -> less Chinese silver -> inventory falls -> price rises |
| **B1 -- Institutional Dampening** | Balancing | Institutions counter-trade -> reduces effective amplification -> slows sentiment growth -> limits R1 |
| **B2 -- Physical Exhaustion** | Balancing | Inventory drops -> retail buying = sentiment x intensity x inventory -> self-limits as inventory depletes |
| **B3 -- Sentiment Decay** | Balancing | Without sustained momentum, attention fades -> buying slows |

### Information Asymmetry
The **institutional edge** metric = demand_supply_pressure - price_momentum quantifies the gap between what commodity desks see (inventory movements, daily) and what retail sees (price charts, lagged). When positive, desks are positioning ahead of retail. When negative, price has overshot fundamentals and desks are distributing to retail.

Institutional dampening operates on the **sentiment channel**, not price directly: effective_amplification = social_media_amplifier - institutional_dampening. At defaults (3.0 - 1.0 = 2.0), retail receives 2/3 of the momentum signal because desk counter-trading compresses observable price moves.

### Critical Insight
Retail can temporarily drive prices through FOMO (R1), but institutional dampening (B1) and physical constraints (B2) usually limit the squeeze. The **exception**: when genuine structural deficit (Chinese export ban + solar demand growth) depletes inventory -- then even dampened signals eventually break through because the fundamental tightness is real.

"""),
            mo.md("""
### Overview
Models silver market supply squeezes and the information asymmetry between commodity desks and retail traders.

Supply-demand balance at t=0: western_supply (640) + chinese_exports (64) - industrial_demand (700) - retail_buying (13.5) = -9.5 Moz/yr structural deficit. This deficit accelerates as Chinese exports decline from geopolitical restrictions.

Key feedback loops:
- (R1) Retail FOMO: price rises → momentum → amplified by social media → sentiment rises → more retail buying → inventory drain → more price rise
- (R2) Chinese Supply Squeeze: geopolitical pressure → export restrictions → less Chinese silver → inventory falls → price rises
- (B1) Institutional Dampening: institutions counter-trade against retail momentum → reduces effective amplification of price signal → slows sentiment growth → limits R1 loop strength
- (B2) Physical Exhaustion: inventory drops → net_retail_flow = sentiment * intensity * inventory → buying self-limits as inventory depletes
- (B3) Sentiment Decay: without sustained momentum, attention fades → buying slows

Information asymmetry mechanism:
- institutional_dampening reduces social_media_amplifier (effective_amplification = social_media - dampening)
- Desks see inventory (leading indicator), retail sees price (lagging)
- institutional_edge metric = demand_supply_pressure - price_momentum quantifies the gap
- When edge > 0: desks are buying ahead of retail; when < 0: desks are selling to retail

Critical insight: retail can temporarily drive prices through FOMO (R1), but institutional dampening (B1) and physical constraints (B2) usually limit the squeeze. The EXCEPTION: when genuine structural deficit (Chinese export ban + solar demand growth) depletes inventory — then even dampened signals eventually break through.

### Learning Objectives
- Understand how information asymmetry shapes price dynamics and value transfer
- Explore Chinese export controls creating delayed-visibility supply deficits
- See how social media creates predictable retail behavior institutions can front-run
- Analyze the effective_amplification = social_media - institutional_dampening dynamic
- Learn why retail can temporarily move markets but institutions usually dampen the signal
- Identify conditions (genuine physical deficit) where retail can overcome dampening
- Compare scenarios: full amplification vs institutional suppression

### Scenarios
**Current Trajectory** -- Default — mild structural deficit, gradual Chinese restriction, moderate institutional dampening. Watch slow inventory decline transition to price breakout.

**Chinese Export Ban** -- Acute Chinese restriction (rare earth 2010 / germanium 2023 playbook). Rapid supply deficit forces price revaluation.  
Parameters: `geopolitical_pressure=3.0`, `restriction_rate=0.12`, `china_export_fraction=0.3`

**Silver Squeeze 2.0** -- Viral social media campaign with reduced institutional resistance. Tests coordinated retail vs institutional dampening.  
Parameters: `social_media_amplifier=7.0`, `retail_buy_intensity=0.35`, `sentiment_decay_rate=0.2`, `institutional_dampening=0.5`

**No Institutional Resistance** -- Full social media amplification without desk counter-trading. Reveals the price signal hidden by institutional dampening.  
Parameters: `institutional_dampening=0.0`, `geopolitical_pressure=2.0`

### Customization Tips
- Set institutional_dampening to 0 to remove commodity desk resistance (full social media amplification)
- Increase geopolitical_pressure to 2.5-3.0 for acute Chinese export ban
- Raise social_media_amplifier to 6-8 for viral silver squeeze campaign
- Lower reference_inventory to 100-150 to reflect actual COMEX registered levels (~30 Moz)
- Increase solar_demand_growth to 300-400 for accelerating energy transition demand
- Set china_export_fraction to 0.3 for sudden export control announcement
- Lower western_supply_base to 580-600 for larger structural deficit
- Set institutional_dampening > social_media_amplifier to model full market suppression

### Related Concepts
- Hunt Brothers silver squeeze (1980)
- COMEX registered vs eligible inventory
- Paper-to-physical silver ratio and delivery risk
- Chinese critical minerals export control playbook
- SLV ETF creation/redemption as institutional tool
- Lease rate as physical tightness indicator
- Contango vs backwardation in futures
- Order flow toxicity and informed trading
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
    
        warehouse_inventory["Warehouse Inventory"]:::stock
        retail_holdings["Retail Holdings"]:::stock
        silver_price["Silver Price"]:::stock
        chinese_export_capacity["Chinese Export Capacity"]:::stock
        retail_sentiment["Retail Sentiment"]:::stock
        western_supply(["Western Supply"]):::flow
        industrial_demand(["Industrial Demand"]):::flow
        net_retail_flow(["Net Retail Flow"]):::flow
        chinese_export_flow(["Chinese Export Flow"]):::flow
        export_restriction(["Export Restriction"]):::flow
        price_change(["Price Change"]):::flow
        sentiment_change(["Sentiment Change"]):::flow
        western_supply_base{{"Western Supply Base = 640.0"}}:::constant
        base_industrial_demand{{"Base Industrial Demand = 500.0"}}:::constant
        solar_demand_growth{{"Solar Demand Growth = 200.0"}}:::constant
        retail_buy_intensity{{"Retail Buy Intensity = 0.15"}}:::constant
        china_export_fraction{{"China Export Fraction = 0.8"}}:::constant
        restriction_rate{{"Restriction Rate = 0.03"}}:::constant
        geopolitical_pressure{{"Geopolitical Pressure = 1.5"}}:::constant
        price_adjustment_speed{{"Price Adjustment Speed = 0.5"}}:::constant
        institutional_dampening{{"Institutional Dampening = 1.0"}}:::constant
        social_media_amplifier{{"Social Media Amplifier = 3.0"}}:::constant
        sentiment_decay_rate{{"Sentiment Decay Rate = 0.4"}}:::constant
        reference_inventory{{"Reference Inventory = 300.0"}}:::constant
        inventory_ratio[/"Inventory Ratio"/]:::computed
        demand_supply_pressure[/"Demand Supply Pressure"/]:::computed
        price_momentum[/"Price Momentum"/]:::computed
        effective_amplification[/"Effective Amplification"/]:::computed
        sentiment_decay[/"Sentiment Decay"/]:::computed
        institutional_edge[/"Institutional Edge"/]:::computed
    
        western_supply ==>|"+"| warehouse_inventory
        chinese_export_flow ==>|"+"| warehouse_inventory
        warehouse_inventory ==>|"-"| industrial_demand
        warehouse_inventory ==>|"-"| net_retail_flow
        net_retail_flow ==>|"+"| retail_holdings
        price_change ==>|"+"| silver_price
        chinese_export_capacity ==>|"-"| export_restriction
        sentiment_change ==>|"+"| retail_sentiment
    
        western_supply_base -.-> western_supply
        solar_demand_growth -.-> industrial_demand
        base_industrial_demand -.-> industrial_demand
        retail_buy_intensity -.-> net_retail_flow
        retail_sentiment -.-> net_retail_flow
        chinese_export_capacity -.-> chinese_export_flow
        china_export_fraction -.-> chinese_export_flow
        restriction_rate -.-> export_restriction
        geopolitical_pressure -.-> export_restriction
        demand_supply_pressure -.-> price_change
        price_adjustment_speed -.-> price_change
        price_momentum -.-> sentiment_change
        sentiment_decay -.-> sentiment_change
        effective_amplification -.-> sentiment_change
        warehouse_inventory -.-> inventory_ratio
        reference_inventory -.-> inventory_ratio
        inventory_ratio -.-> demand_supply_pressure
        price_change -.-> price_momentum
        silver_price -.-> price_momentum
        social_media_amplifier -.-> effective_amplification
        institutional_dampening -.-> effective_amplification
        sentiment_decay_rate -.-> sentiment_decay
        retail_sentiment -.-> sentiment_decay
        demand_supply_pressure -.-> institutional_edge
        price_momentum -.-> institutional_edge
        """
        ),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    fig_stocks = go.Figure()
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["warehouse_inventory"], mode="lines", name="Warehouse Inventory (Moz)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["retail_holdings"], mode="lines", name="Retail Holdings (Moz)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["silver_price"], mode="lines", name="Silver Price ($/oz)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["chinese_export_capacity"], mode="lines", name="Chinese Export Capacity (Moz/yr)"))
    fig_stocks.add_trace(go.Scatter(x=results.index, y=results["retail_sentiment"], mode="lines", name="Retail Sentiment (dimensionless)"))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    fig_flows = go.Figure()
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["western_supply"], mode="lines", name="Western Supply (Moz/yr)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["industrial_demand"], mode="lines", name="Industrial Demand (Moz/yr)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["net_retail_flow"], mode="lines", name="Net Retail Flow (Moz/yr)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["chinese_export_flow"], mode="lines", name="Chinese Export Flow (Moz/yr)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["export_restriction"], mode="lines", name="Export Restriction (Moz/yr/yr)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["price_change"], mode="lines", name="Price Change ($/oz/yr)"))
    fig_flows.add_trace(go.Scatter(x=results.index, y=results["sentiment_change"], mode="lines", name="Sentiment Change (1/yr)"))
    fig_flows.update_layout(title="Flow Variables Over Time", xaxis_title="Time", yaxis_title="Rate", template="plotly_white")

    fig_aux = go.Figure()
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["inventory_ratio"], mode="lines", name="Inventory Ratio (dimensionless)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["demand_supply_pressure"], mode="lines", name="Demand Supply Pressure (dimensionless)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["price_momentum"], mode="lines", name="Price Momentum (1/yr)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["effective_amplification"], mode="lines", name="Effective Amplification (dimensionless)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["sentiment_decay"], mode="lines", name="Sentiment Decay (1/yr)"))
    fig_aux.add_trace(go.Scatter(x=results.index, y=results["institutional_edge"], mode="lines", name="Institutional Edge (dimensionless)"))
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
