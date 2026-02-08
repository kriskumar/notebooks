# Macro Models — Interactive System Dynamics

Interactive models that explore macro questions using [PySD](https://pysd.readthedocs.io/) for system dynamics and [Marimo](https://marimo.io) for browser-based notebooks. Each model runs entirely in your browser — no server, no installs.

## Models

### Silver Supply Dynamics
*How do information asymmetries between commodity desks and retail investors shape silver price dynamics during supply squeezes?*

Explores Chinese export controls, warehouse inventory drawdowns, social media-amplified retail speculation, and institutional counter-trading. Watch how structural deficits interact with FOMO feedback loops.

### AI Capex Dynamics
*What happens when $400B in AI infrastructure spending meets declining returns — and who gets hurt?*

Models the reinforcing loop between AI valuations and capital expenditure, balanced by reality checks on actual ROI, labor displacement, and pipeline inertia. Revenue peaks then declines despite growing infrastructure.

### Sodium Battery Energy
*How fast can sodium-ion batteries displace fossil fuel generation, and what happens to gas and coal prices along the way?*

Tracks battery adoption and cost decline curves alongside gas and coal displacement driven by storage penetration. Simple supply-demand pricing shows how energy transition reshapes the generation mix.

### Solar AI Power
*Can solar deployment keep pace with AI datacenter electricity demand?*

Models the feedback between solar capacity growth, AI compute buildout, grid constraints, and electricity pricing as two exponential curves compete for the same infrastructure.

## How it works

Each model is defined as an [abstractModel](https://pysd.readthedocs.io/) JSON spec. The notebooks use inline Euler integration (numpy/pandas only) so they run in WASM/Pyodide without any Python server. Parameter sliders let you adjust assumptions and see results in real time.

Models are exported via `marimo export html-wasm --sandbox` and deployed to GitHub Pages automatically on push.

## Running locally

```bash
# Run any model
marimo run apps/silver_supply_dynamics.py

# Build the static site
uv run .github/scripts/build.py

# Serve locally
python -m http.server -d _site
```

## License

MIT
