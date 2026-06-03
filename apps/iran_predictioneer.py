# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "mesa==3.5.1",
#     "networkx",
#     "plotly>=5.18.0",
#     "pandas>=2.0.0",
#     "numpy>=1.24.0",
# ]
# ///


import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium", app_title="iran_predictioneer")



@app.cell
def __():
    import marimo as mo
    import numpy as np
    import plotly.graph_objects as go
    return go, mo, np



@app.cell
def __():
    import sys, types
    try:
        import sqlite3  # present locally; often absent in Pyodide
    except ModuleNotFoundError:
        sys.modules["sqlite3"] = types.ModuleType("sqlite3")
    import mesa
    from abc import abstractmethod

    """
    BaseStepModel — abstract base class for step-based (non-RL) ABM models.

    All new Model Thinker model types inherit from this class and implement
    run_simulation(steps) returning a standard output dict.
    """



    class BaseStepModel(mesa.Model):
        """
        Base for step-driven ABM models that are observed, not policy-trained.

        Subclasses must implement:
            run_simulation(steps: int) -> dict

        The returned dict must contain at minimum:
            {
                "time_series": { metric_name: [v0, v1, ..., vT] },
                "final_state": { metric_name: value },
                "summary":    { key_stat: value },
            }
        """

        def __init__(self, seed: int | None = None, **kwargs):
            super().__init__(rng=seed, **kwargs)

        @property
        def num_agents(self) -> int:
            """Mesa 3.x compatibility: number of active agents."""
            return len(self.agents)

        @abstractmethod
        def run_simulation(self, steps: int) -> dict:
            """Run for `steps` ticks and return standard output dict."""

    """
    BdMPredictioneerModel — Bueno de Mesquita "Predictioneer" expected-weight
    bargaining, expressed as a step-based ABM.

    Each actor is an agent scored on three dials:
        power    in [0, 1]   — real leverage to move/block the outcome
        salience in [0, 1]   — how much the actor cares about THIS issue
        position in [0, 100] — desired endpoint (0 = peace, 100 = total war)

    Effective weight w_i = power_i * salience_i. The headline metric is the
    effective-weight-weighted mean position. Across rounds, each actor performs
    best-response: it shifts toward the current weighted mean, resisting in
    proportion to its own salience (high-salience actors dig in). The equilibrium
    emerges rather than being assumed.

    Two update mechanisms (select via `mechanism`):

      "best_response" (Level A) — each actor shifts toward the effective-weight mean,
        resisting in proportion to its own salience. Simple and explainable, but the
        (1−salience) weighting lets stubborn extremists anchor the outcome, so the
        equilibrium can drift past the weighted mean.

      "expected_utility" (Level B) — BdM's actual pairwise-challenge mechanism. For
        every ordered pair (i, j), the rest of the board "votes" with its effective
        weight for whichever of i or j it sits closer to, giving a probability P that
        i prevails. i's expected utility of challenging j is |x_i−x_j|·(2P−1); j is
        pressured toward every actor that holds a credible (EU>0) challenge against it,
        weighted by that EU. The fixed point is the effective-weight-weighted MEDIAN
        (median-voter theorem) — extremes get pulled in, the median actor is
        unbeatable, so no runaway.

    Optional `shocks` mutate an actor dial at a given step — e.g. an IRGC salience
    collapse as Bonyad funding dies — turning the article's "what breaks this"
    caveats into runnable experiments.
    """



    class ActorAgent(mesa.Agent):
        def __init__(self, model, name: str, power: float, salience: float, position: float):
            super().__init__(model)
            self.name = name
            self.power = power
            self.salience = salience
            self.position = position

        @property
        def weight(self) -> float:
            return self.power * self.salience


    class BdMPredictioneerModel(BaseStepModel):
        POSITION_RANGE = 100.0
        MECHANISMS = ("best_response", "expected_utility")

        def __init__(
            self,
            actors: list[dict],
            move_speed: float = 0.5,
            mechanism: str = "best_response",
            shocks: list[dict] | None = None,
            seed: int | None = 42,
        ):
            super().__init__(seed=seed)
            if mechanism not in self.MECHANISMS:
                raise ValueError(
                    f"Unknown mechanism '{mechanism}'. Choose one of {self.MECHANISMS}."
                )
            self.move_speed = move_speed
            self.mechanism = mechanism
            self.shocks = shocks or []
            self._tick = 0
            for a in actors:
                ActorAgent(self, a["name"], a["power"], a["salience"], a["position"])

        def _weighted_position(self) -> float:
            num = sum(a.weight * a.position for a in self.agents)
            den = sum(a.weight for a in self.agents)
            return num / den if den else 0.0

        def _position_spread(self) -> float:
            positions = [a.position for a in self.agents]
            return max(positions) - min(positions)

        def _apply_shocks(self):
            for s in self.shocks:
                if s["step"] != self._tick:
                    continue
                for a in self.agents:
                    if a.name == s["actor"]:
                        setattr(a, s["field"], s["value"])

        def _prevail_probability(self, focal: ActorAgent, rival: ActorAgent) -> float:
            """
            Probability that `focal` prevails over `rival`: the rest of the board votes
            with its effective weight for whichever contestant it sits closer to, and P
            is focal's share of the decisive (non-indifferent) weighted vote.
            Symmetric by construction: P(focal,rival) == 1 − P(rival,focal).
            """
            backing = 0.0
            decisive = 0.0
            for k in self.agents:
                vote = k.weight * (
                    abs(k.position - rival.position) - abs(k.position - focal.position)
                )
                decisive += abs(vote)
                if vote > 0:  # k sits closer to focal → backs focal
                    backing += vote
            return backing / decisive if decisive > 0 else 0.5

        def _best_response_step(self):
            target = self._weighted_position()
            for a in self.agents:
                a.position += (1 - a.salience) * self.move_speed * (target - a.position)

        def _expected_utility_step(self):
            agents = list(self.agents)
            pos = {a: a.position for a in agents}
            new = dict(pos)
            for j in agents:
                pull = 0.0
                weight = 0.0
                for i in agents:
                    if i is j:
                        continue
                    p_i = self._prevail_probability(i, j)
                    # i's expected utility of challenging j, normalised to [0,1] space
                    eu_i = abs(pos[i] - pos[j]) / self.POSITION_RANGE * (2 * p_i - 1)
                    if eu_i > 0:  # i holds a credible winning challenge → pressures j
                        pull += eu_i * (pos[i] - pos[j])
                        weight += eu_i
                if weight > 0:
                    target = pos[j] + pull / weight  # EU-weighted mean of credible challengers
                    new[j] = pos[j] + self.move_speed * (target - pos[j])
            for a in agents:
                a.position = max(0.0, min(self.POSITION_RANGE, new[a]))

        def step(self):
            self._tick += 1
            self._apply_shocks()
            if self.mechanism == "expected_utility":
                self._expected_utility_step()
            else:
                self._best_response_step()

        def run_simulation(self, steps: int = 50) -> dict:
            names = [a.name for a in self.agents]
            wp_ts = [self._weighted_position()]
            spread_ts = [self._position_spread()]
            actor_ts = {a.name: [a.position] for a in self.agents}

            for _ in range(steps):
                self.step()
                wp_ts.append(self._weighted_position())
                spread_ts.append(self._position_spread())
                for a in self.agents:
                    actor_ts[a.name].append(a.position)

            return {
                "time_series": {
                    "weighted_position": wp_ts,
                    "position_spread": spread_ts,
                    "actor_positions": actor_ts,
                },
                "final_state": {
                    "weighted_position": wp_ts[-1],
                    "actor_positions": {a.name: a.position for a in self.agents},
                    "actor_weights": {a.name: a.weight for a in self.agents},
                },
                "summary": {
                    "equilibrium_position": wp_ts[-1],
                    "initial_position": wp_ts[0],
                    "final_spread": spread_ts[-1],
                    "mechanism": self.mechanism,
                    "actors": names,
                },
            }
    return (BaseStepModel, ActorAgent, BdMPredictioneerModel)



@app.cell
def __(mo):
    mechanism_sl = mo.ui.text(value="expected_utility", label="mechanism", disabled=True)
    move_speed_sl = mo.ui.slider(0.0, 1.0, value=0.5, step=0.01, label="move_speed")
    actors_sl = mo.ui.text(value="[{'name': 'Larijani', 'power': 0.9, 'salience': 0.8, 'position': 40.0}, {'name': 'IRGC', 'power': 0.7, 'salience': 0.6, 'position': 85.0}, {'name': 'Trump', 'power': 1.0, 'salience': 0.7, 'position': 58.0}, {'name': 'Israel', 'power': 0.6, 'salience': 0.9, 'position': 95.0}]", label="actors", disabled=True)
    shocks_sl = mo.ui.text(value="[{'actor': 'IRGC', 'step': 5, 'field': 'salience', 'value': 0.1}]", label="shocks", disabled=True)
    steps_sl = mo.ui.slider(10, 180, value=60, step=10, label="steps")
    mo.vstack([mechanism_sl, move_speed_sl, actors_sl, shocks_sl, steps_sl])
    return (mechanism_sl, move_speed_sl, actors_sl, shocks_sl, steps_sl,)



@app.cell
def __(BdMPredictioneerModel, steps_sl, mechanism_sl, move_speed_sl, actors_sl, shocks_sl):
    model = BdMPredictioneerModel(mechanism=mechanism_sl.value, move_speed=move_speed_sl.value, actors=actors_sl.value, shocks=shocks_sl.value, seed=42)
    out = model.run_simulation(steps=steps_sl.value)
    return model, out



@app.cell
def __(go, mo, out):
    ts = out.get("time_series", {})
    figs = []
    for metric_name, series in ts.items():
        fig = go.Figure()
        if series and isinstance(series[0], (list, tuple)):
            ncols = len(series[0])
            for j in range(ncols):
                fig.add_scatter(y=[row[j] for row in series], mode="lines",
                                name=f"{metric_name}[{j}]")
        else:
            fig.add_scatter(y=series, mode="lines", name=metric_name)
        fig.update_layout(title=metric_name, xaxis_title="step",
                          margin=dict(l=40, r=20, t=40, b=40), height=320)
        figs.append(fig)
    mo.vstack(figs) if figs else mo.md("_no time_series in result_")
    return



@app.cell
def __(mo, out):
    summary = out.get("summary", {})
    _rows = "\n".join(f"| {k} | {v} |" for k, v in summary.items())
    mo.md(f"### Summary\n\n| metric | value |\n|---|---|\n{_rows}") if summary \
        else mo.md("_no summary in result_")
    return



@app.cell
def __(mo):
    return mo.md("""# Iran Conflict — BdM Predictioneer
Expected-utility bargaining over a peace(0)–war(100) continuum. Equilibrium = effective-weight-weighted median. IRGC salience collapse (Bonyad funding) fires at step 5.""")



if __name__ == '__main__':
    app.run()
