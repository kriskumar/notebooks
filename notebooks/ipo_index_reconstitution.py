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
Ipo Index Reconstitution — Interactive Explorer

System dynamics model with inline Euler integration.
5 stocks, 0 flows, 6 parameters, 7 computed variables.

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
    inclusion_rate,
    ipo_target_weight,
    flow_multiplier,
    arbitrage_dampening,
    passive_aum_trillions,
    final_time,
    np,
    pd,
    time_step,
):
    # Initial stock values (float-adjusted weights in QQQ, ~end-2025 snapshot)
    new_entrants_weight = 0.0
    nvda_weight = 0.09
    msft_weight = 0.08
    aapl_weight = 0.07
    other_weight = 0.76

    # Effective per-$ price impact after arbitrage dampening
    # Wurgler-Zhuravskaya (2002): arbs offset a fraction of mechanical demand
    effective_multiplier = flow_multiplier.value * (1.0 - arbitrage_dampening.value)
    aum_usd = passive_aum_trillions.value * 1e12  # convert $T -> $

    rows = []
    t = 0.0
    dt = time_step.value
    t_end = final_time.value

    while t <= t_end + dt / 2:
        weight_gap = ipo_target_weight.value - new_entrants_weight
        existing_pool = nvda_weight + msft_weight + aapl_weight + other_weight
        inclusion_flow = inclusion_rate.value * weight_gap
        nvda_outflow = inclusion_flow * (nvda_weight / max(existing_pool, 1e-6))
        msft_outflow = inclusion_flow * (msft_weight / max(existing_pool, 1e-6))
        aapl_outflow = inclusion_flow * (aapl_weight / max(existing_pool, 1e-6))
        other_outflow = inclusion_flow * (other_weight / max(existing_pool, 1e-6))

        # Price impact = mechanical $ outflow × Gabaix-Koijen multiplier,
        # net of arbitrage dampening.  Output in % of name's own market cap.
        # outflow is fraction-of-AUM per month; convert to % price impact
        # per name using the name's current weight as size proxy.
        nvda_price_impact_pct = (
            -100.0 * nvda_outflow * effective_multiplier / max(nvda_weight, 1e-6)
        )
        msft_price_impact_pct = (
            -100.0 * msft_outflow * effective_multiplier / max(msft_weight, 1e-6)
        )
        aapl_price_impact_pct = (
            -100.0 * aapl_outflow * effective_multiplier / max(aapl_weight, 1e-6)
        )
        # Dollar-flow magnitude for the largest name
        nvda_dollar_outflow_b = nvda_outflow * aum_usd / 1e9  # $B / month

        rows.append(
            {
                "time": t,
                "new_entrants_weight": new_entrants_weight,
                "nvda_weight": nvda_weight,
                "msft_weight": msft_weight,
                "aapl_weight": aapl_weight,
                "other_weight": other_weight,
                "weight_gap": weight_gap,
                "inclusion_flow": inclusion_flow,
                "existing_pool": existing_pool,
                "nvda_outflow": nvda_outflow,
                "msft_outflow": msft_outflow,
                "aapl_outflow": aapl_outflow,
                "other_outflow": other_outflow,
                "nvda_price_impact_pct": nvda_price_impact_pct,
                "msft_price_impact_pct": msft_price_impact_pct,
                "aapl_price_impact_pct": aapl_price_impact_pct,
                "nvda_dollar_outflow_b": nvda_dollar_outflow_b,
            }
        )

        new_entrants_weight += dt * inclusion_flow
        nvda_weight += dt * (0 - nvda_outflow)
        msft_weight += dt * (0 - msft_outflow)
        aapl_weight += dt * (0 - aapl_outflow)
        other_weight += dt * (0 - other_outflow)
        t += dt

    results = pd.DataFrame(rows).set_index("time")
    return (results,)


@app.cell
def header(mo):
    mo.md(
        """
    # Ipo Index Reconstitution — Interactive Explorer

    **Stocks:** 5 | **Flows:** 0 | **Parameters:** 6 | **Computed:** 7

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
    # --- Reconstitution sizing ---
    # Base case ≈ 0.033 (float-adj. combined cap of OpenAI+SpaceX+Anthropic+Cerebras
    # vs QQQ).  Stress ≈ 0.15 for full mega-cap inclusion across multiple indices.
    ipo_target_weight = mo.ui.slider(
        value=0.033, start=0, stop=0.20, step=0.005,
        label="IPO target weight in index (float-adj.)",
    )
    # Inclusion-rate calibration (S&P / QQQ rebalance dynamics):
    # Russell / S&P rebalances are ~quarterly with most flow at the event date.
    # Continuous-time half-life of ~3 months → r = ln(2)/3 ≈ 0.23/month.
    inclusion_rate = mo.ui.slider(
        value=0.23, start=0.02, stop=1.0, step=0.01,
        label="Inclusion rate (1/month) — Russell/QQQ schedule ≈ 0.23",
    )

    # --- Price-impact handicaps grounded in the literature ---
    # Gabaix & Koijen (2021) "Inelastic Markets Hypothesis": $1 net flow into
    # the equity market raises aggregate value by ≈ $5.  Single-name flows
    # are noisier but the multiplier is the right order of magnitude.
    flow_multiplier = mo.ui.slider(
        value=5.0, start=0.0, stop=10.0, step=0.25,
        label="Flow multiplier M (Gabaix–Koijen 2021, ≈ 5)",
    )
    # Wurgler & Zhuravskaya (2002): arbitrageurs partially flatten demand
    # curves; offset is smaller for stocks without close substitutes.
    # Modern decay (Patel–Welch 2017, Greenwood–Sammon 2025) is consistent
    # with a high dampening regime.
    arbitrage_dampening = mo.ui.slider(
        value=0.4, start=0.0, stop=0.95, step=0.05,
        label="Arbitrage dampening 1-α (Wurgler–Zhuravskaya 2002, ≈ 0.4)",
    )
    # QQQ-tracking passive AUM, scaled up to include closet indexers
    passive_aum_trillions = mo.ui.slider(
        value=0.35, start=0.05, stop=2.0, step=0.05,
        label="Tracked passive AUM ($T) — Invesco QQQ + close trackers",
    )

    mo.vstack(
        [
            mo.md("**Reconstitution sizing**"),
            ipo_target_weight,
            inclusion_rate,
            mo.md("**Price-impact handicaps (literature-anchored)**"),
            flow_multiplier,
            arbitrage_dampening,
            passive_aum_trillions,
        ]
    )
    return (
        inclusion_rate,
        ipo_target_weight,
        flow_multiplier,
        arbitrage_dampening,
        passive_aum_trillions,
    )


@app.cell
def chart_controls(mo):
    stock_selector = mo.ui.multiselect(
        options={"New Entrants Weight (fraction)": "new_entrants_weight", "Nvda Weight (fraction)": "nvda_weight", "Msft Weight (fraction)": "msft_weight", "Aapl Weight (fraction)": "aapl_weight", "Other Weight (fraction)": "other_weight"},
        value=["New Entrants Weight (fraction)", "Nvda Weight (fraction)", "Msft Weight (fraction)", "Aapl Weight (fraction)", "Other Weight (fraction)"],
        label="Stock variables",
    )
    aux_selector = mo.ui.multiselect(
        options={
            "Weight Gap (fraction)": "weight_gap",
            "Inclusion Flow (fraction/month)": "inclusion_flow",
            "NVDA Outflow (fraction/month)": "nvda_outflow",
            "MSFT Outflow (fraction/month)": "msft_outflow",
            "AAPL Outflow (fraction/month)": "aapl_outflow",
            "Other Outflow (fraction/month)": "other_outflow",
        },
        value=[
            "Weight Gap (fraction)",
            "Inclusion Flow (fraction/month)",
            "NVDA Outflow (fraction/month)",
            "Other Outflow (fraction/month)",
        ],
        label="Mechanical flow variables",
    )
    impact_selector = mo.ui.multiselect(
        options={
            "NVDA price impact (% / month)": "nvda_price_impact_pct",
            "MSFT price impact (% / month)": "msft_price_impact_pct",
            "AAPL price impact (% / month)": "aapl_price_impact_pct",
            "NVDA dollar outflow ($B / month)": "nvda_dollar_outflow_b",
        },
        value=[
            "NVDA price impact (% / month)",
            "MSFT price impact (% / month)",
            "AAPL price impact (% / month)",
        ],
        label="Calibrated price impact (Gabaix–Koijen × (1 − W-Z dampening))",
    )
    return stock_selector, aux_selector, impact_selector


@app.cell
def tabbed_content(aux_selector, impact_selector, go, mo, results, stock_selector):
    # --- Analysis tab ---
    analysis_content = mo.vstack([
            mo.md(r"""
# Origin

**Channel:** BBG / markets
**Model type:** ABM
**Structural question:** When a cluster of large IPOs forces index reconstitution, how do coupled index funds reallocate finite capital — and which existing index members absorb the largest proportional outflow shock?

**Original question:**
> Mega-IPO liquidity drain risk: When Cerebras, SpaceX, Anthropic, and OpenAI all IPO in close succession, what is the estimated float/index reconstitution capital displacement, and which current index members (SOXX, QQQ) face the largest outflow risk?

## Model logic

Each existing index member is an agent holding a fraction of total passive AUM. A reconstitution event opens a target weight for the new mega-IPO entrants. The inclusion flow drains existing members **proportional to their current weight share** — the same logic real index funds use to fund mechanical buys. Under this proportional rule every existing member loses the **same percentage** of its weight, but the **largest absolute outflow** lands on the largest holder: NVDA among named agents, and the aggregated "other" pool overall.

## Coefficient calibration (literature anchors)

| Parameter | Default | Source |
|---|---|---|
| `ipo_target_weight` | 0.033 | Float-adj. cap of OpenAI (~$300B) + SpaceX (~$350B) + Anthropic (~$150B) + Cerebras (~$25B) ÷ QQQ (~$25T). Stress case 0.10–0.15. |
| `inclusion_rate` | 0.23 / month | Russell / S&P quarterly rebalance: ≈ half-life of 3 months in continuous time (ln 2 / 3). Chen (2006) shows most flow concentrates around the event window. |
| `flow_multiplier` | 5.0 | Gabaix & Koijen (2021) *Inelastic Markets Hypothesis*: $1 of equity net flow ⇒ ≈ $5 aggregate value impact (NBER w28967). |
| `arbitrage_dampening` | 0.40 | Wurgler & Zhuravskaya (2002) *Does Arbitrage Flatten Demand Curves?* (JoB): arbitrageurs offset ~30–50% of mechanical pressure for index inclusions, more for names with close substitutes. |
| `passive_aum_trillions` | 0.35 | Invesco QQQ AUM + close trackers; widen to capture closet indexers. |

**Important regime caveats:**

- **Historical inclusion effect (Shleifer 1986; Harris–Gurel 1986):** S&P additions earned +3% to +9% abnormal returns over a few weeks. Use low dampening (≈ 0.1–0.3) to replicate that regime.
- **Modern decay (Patel–Welch 2017; Greenwood–Sammon 2025):** Post-2010 the inclusion premium has effectively gone to zero on average. Use high dampening (≈ 0.7–0.9) to replicate.
- **Russell-specific (Chen 2006):** Front-loaded, mean-reverting within ~1 quarter — increase `inclusion_rate` to 0.5+ to model that schedule.

## What to watch

- `nvda_price_impact_pct`: % price drag per month on the largest single holder, calibrated end-to-end. This is the headline number — the SOXX/QQQ name with the biggest forced-sell shock in % terms.
- `nvda_dollar_outflow_b`: $B/month of mechanical sells in NVDA — handy for comparing to ADV and gauging whether arbitrage capital can absorb it (~$40–80B ADV in NVDA today).
- `inclusion_flow`: should be heavily front-loaded under default settings; flattens out as `weight_gap` closes.

## Sensitivity bands worth sweeping

1. **Bear / "no effect"** — `flow_multiplier=5`, `arbitrage_dampening=0.85`. Recreates Greenwood–Sammon (2025).
2. **Base** — defaults as shipped. Roughly the 2000–2015 inclusion-effect regime.
3. **Stress** — `ipo_target_weight=0.10`, `arbitrage_dampening=0.15`, `flow_multiplier=7`. Cluster-IPO event with thin arbitrage capital (post-2020 quant-deleveraging analog).
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
    
        new_entrants_weight["New Entrants Weight"]:::stock
        nvda_weight["Nvda Weight"]:::stock
        msft_weight["Msft Weight"]:::stock
        aapl_weight["Aapl Weight"]:::stock
        other_weight["Other Weight"]:::stock
        initial_time{{"Initial Time = 0.0"}}:::constant
        final_time{{"Final Time = 24.0"}}:::constant
        time_step{{"Time Step = 0.25"}}:::constant
        saveper{{"Saveper = 1.0"}}:::constant
        ipo_target_weight{{"Ipo Target Weight = 0.15"}}:::constant
        inclusion_rate{{"Inclusion Rate = 0.12"}}:::constant
        weight_gap[/"Weight Gap"/]:::computed
        inclusion_flow[/"Inclusion Flow"/]:::computed
        existing_pool[/"Existing Pool"/]:::computed
        nvda_outflow[/"Nvda Outflow"/]:::computed
        msft_outflow[/"Msft Outflow"/]:::computed
        aapl_outflow[/"Aapl Outflow"/]:::computed
        other_outflow[/"Other Outflow"/]:::computed
    
        inclusion_flow ==>|"+"| new_entrants_weight
        nvda_weight ==>|"-"| nvda_outflow
        msft_weight ==>|"-"| msft_outflow
        aapl_weight ==>|"-"| aapl_outflow
        other_weight ==>|"-"| other_outflow
    
        ipo_target_weight -.-> weight_gap
        new_entrants_weight -.-> weight_gap
        weight_gap -.-> inclusion_flow
        inclusion_rate -.-> inclusion_flow
        msft_weight -.-> existing_pool
        nvda_weight -.-> existing_pool
        other_weight -.-> existing_pool
        aapl_weight -.-> existing_pool
        existing_pool -.-> nvda_outflow
        inclusion_flow -.-> nvda_outflow
        existing_pool -.-> msft_outflow
        inclusion_flow -.-> msft_outflow
        existing_pool -.-> aapl_outflow
        inclusion_flow -.-> aapl_outflow
        existing_pool -.-> other_outflow
        inclusion_flow -.-> other_outflow
        """
        ),
        mo.Html("</div>"),
        mo.md("*Boxes: stocks | Rounded: flows | Hexagons: parameters | Slanted: computed*"),
    ])

    # --- Simulation tab ---
    _stock_labels = {'new_entrants_weight': 'New Entrants Weight (fraction)', 'nvda_weight': 'Nvda Weight (fraction)', 'msft_weight': 'Msft Weight (fraction)', 'aapl_weight': 'Aapl Weight (fraction)', 'other_weight': 'Other Weight (fraction)'}
    fig_stocks = go.Figure()
    for _key in stock_selector.value:
        fig_stocks.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_stock_labels.get(_key, _key)))
    fig_stocks.update_layout(title="Stock Variables Over Time", xaxis_title="Time", yaxis_title="Value", template="plotly_white")

    _aux_labels = {'weight_gap': 'Weight Gap (fraction)', 'inclusion_flow': 'Inclusion Flow (fraction/month)', 'existing_pool': 'Existing Pool (fraction)', 'nvda_outflow': 'NVDA Outflow (fraction/month)', 'msft_outflow': 'MSFT Outflow (fraction/month)', 'aapl_outflow': 'AAPL Outflow (fraction/month)', 'other_outflow': 'Other Outflow (fraction/month)'}
    fig_aux = go.Figure()
    for _key in aux_selector.value:
        fig_aux.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_aux_labels.get(_key, _key)))
    fig_aux.update_layout(title="Mechanical Flows", xaxis_title="Time (months)", yaxis_title="Value", template="plotly_white")

    _impact_labels = {
        'nvda_price_impact_pct': 'NVDA price impact (%/mo)',
        'msft_price_impact_pct': 'MSFT price impact (%/mo)',
        'aapl_price_impact_pct': 'AAPL price impact (%/mo)',
        'nvda_dollar_outflow_b': 'NVDA $ outflow ($B/mo)',
    }
    fig_impact = go.Figure()
    for _key in impact_selector.value:
        fig_impact.add_trace(go.Scatter(x=results.index, y=results[_key], mode="lines", name=_impact_labels.get(_key, _key)))
    fig_impact.update_layout(title="Calibrated Price Impact (Gabaix–Koijen × (1 − Wurgler–Zhuravskaya dampening))", xaxis_title="Time (months)", yaxis_title="% / month or $B / month", template="plotly_white")

    simulation_content = mo.vstack([
        stock_selector,
        mo.ui.plotly(fig_stocks),
        aux_selector,
        mo.ui.plotly(fig_aux),
        impact_selector,
        mo.ui.plotly(fig_impact),
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
