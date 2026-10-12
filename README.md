# Dynamic Price Wars & Perishable Inventory Liquidation

A Python multi-agent simulation of price negotiation for perishable inventory. A distributor negotiates with two retailers—`premium_grocery` and `budget_mart`—whose budgets, storage capacities, willingness to pay, and freshness requirements differ. The simulation tracks deals, revenue, sold and expired inventory, failed negotiations, and negotiation history.

The project supports optional local AI-assisted negotiation through Ollama. AI responses are parsed into structured decisions and validated; when a usable response is not available, the provider can use a deterministic fallback supplied by the agent. Business-rule checks and market validation remain important parts of the transaction flow.

## Features

- Three negotiating agents: distributor, premium retailer, and budget retailer.
- Shared market state for inventory, shelf life, reservation price, retailer state, and simulation rounds.
- Opening offers, counteroffers, acceptance, rejection, and walk-away actions.
- Deal validation and inventory updates through the market environment.
- Revenue, units sold, successful deals, failed negotiations, rejected offers, and expired-inventory metrics.
- Optional Ollama model support, configured by environment variables.
- Command-line simulation and a Streamlit dashboard with Plotly visualizations.
- Automated tests for agents, pricing, negotiation, inventory, market behavior, validation, and end-to-end behavior.

## Technology stack

- Python (the project was developed for Python 3.13)
- Pydantic for structured models and validation
- Ollama local HTTP API for optional AI decisions
- `python-dotenv` for loading environment variables
- Streamlit for the interactive dashboard
- Plotly for charts
- pytest for automated tests

The dependencies listed in `requirements.txt` are `pydantic`, `pytest`, `streamlit`, `plotly`, `openai`, `python-dotenv`, and `google-genai`. The active `ai_strategy/provider.py` in this project uses Ollama through Python's standard-library HTTP request utilities; the OpenAI and Google packages may be legacy or unused by this active provider.

## Project structure

```text
Dynamic-Price-Wars-Perishable-Inventory-Liquidation/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── distributor.py
│   ├── premium_retailer.py
│   └── budget_retailer.py
├── ai_strategy/
│   ├── __init__.py
│   ├── provider.py
│   ├── prompts.py
│   ├── provider_before_optimization.py
│   └── provider_gemini_backup.py
├── environment/
│   ├── __init__.py
│   ├── market.py
│   ├── inventory.py
│   ├── metrics.py
│   ├── pricing.py
│   └── validation.py
├── integration/
│   ├── __init__.py
│   └── simulation.py
├── models/
│   ├── __init__.py
│   └── schemas.py
├── negotiation/
│   ├── __init__.py
│   ├── manager.py
│   └── protocol.py
├── tests/
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_end_to_end.py
│   ├── test_gemini_provider.py
│   ├── test_inventory.py
│   ├── test_market.py
│   ├── test_negotiation.py
│   ├── test_pricing.py
│   └── test_validation.py
├── dashboard.py
├── main.py
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```

`agents/.backup` and Python/cache/Git metadata are omitted from this overview because they are not part of the normal runtime flow.

## How the components work

- **`agents/`** — Agent behavior for the distributor and both retailer types. Each agent evaluates offers according to its role and constraints.
- **`negotiation/manager.py`** — Coordinates retailer-distributor negotiation turns and records negotiation events and outcomes.
- **`negotiation/protocol.py`** — Defines negotiation protocol constants and shared protocol behavior.
- **`environment/market.py`** — Owns the shared market state, retailer states, deal execution, and round/day progression.
- **`environment/validation.py`** — Validates proposed deals against market and retailer constraints.
- **`environment/inventory.py`** — Tracks inventory availability and expiry-related state.
- **`environment/pricing.py`** — Calculates the distributor's reservation price as shelf life changes.
- **`environment/metrics.py`** — Tracks revenue, units sold, successful deals, failed negotiations, and rejected offers.
- **`models/schemas.py`** — Pydantic models and enums for market/retailer state, offers, decisions, deal results, and negotiation history events.
- **`ai_strategy/provider.py`** — Calls the local Ollama API, validates structured model responses, and uses the supplied fallback when necessary.
- **`ai_strategy/prompts.py`** — Prompt construction for AI-assisted strategy decisions.
- **`integration/simulation.py`** — Builds the default market and agents and runs the simulation.
- **`dashboard.py`** — Streamlit UI for configuring and running a simulation and viewing metrics, market status, successful deals, outcomes, decision-source counts, negotiation history, and console output.
- **`tests/`** — Automated tests for the main simulation components.

## Default simulation setup

Unless changed through the dashboard or constructor arguments, `PriceWarSimulation` uses these starting values:

| Setting | Default |
|---|---:|
| Product | Fresh Milk |
| Initial inventory | 500 units |
| Total shelf life | 5 days |
| Initial distributor reservation price | ₹100 per unit |
| Minimum distributor reservation price | ₹60 per unit |
| Premium retailer capacity | 150 units |
| Premium retailer maximum willingness to pay | ₹105 per unit |
| Premium retailer budget | ₹15,000 |
| Premium retailer minimum shelf life | 2 days |
| Premium retailer sales velocity | 50 units/day |
| Budget retailer capacity | 250 units |
| Budget retailer maximum willingness to pay | ₹90 per unit |
| Budget retailer budget | ₹18,000 |
| Budget retailer minimum shelf life | 1 day |
| Budget retailer sales velocity | 70 units/day |

The dashboard allows several of these values to be changed before running a simulation. Results depend on the selected settings and, when enabled, the AI model's responses.

## Business constraints and decision flow

The project models the following business considerations:

- The distributor considers its current reservation price and remaining shelf life.
- Retailers consider their budgets, available capacity, maximum willingness to pay, and minimum required shelf life.
- Offers must be feasible for the buyer and seller and are checked by the market before a deal is committed.
- The negotiation manager coordinates offer/counteroffer turns and records decisions.
- Negotiations can succeed or end without a deal when the agents cannot agree.
- The simulation tracks inventory and expiry as time advances.

The current project constraint for a completed deal is a maximum quantity of **100 units per deal**. The deal validator and negotiation flow should be used as the source of truth for whether an offer is accepted by the environment.

At a high level, the flow is:

1. Initialize the market, distributor, and retailer agents.
2. Read the current market and retailer state.
3. A retailer proposes an opening offer.
4. The distributor evaluates it and accepts, counters, or ends the negotiation.
5. The retailer responds to a counteroffer.
6. The negotiation manager and market validation determine whether a deal can be committed.
7. A successful deal updates the shared state and metrics; otherwise the negotiation is recorded as unsuccessful.
8. The simulation advances time and tracks remaining inventory and shelf life.

## Requirements

- Python 3.13 recommended for reproducing the development setup.
- `pip`.
- Ollama installed and running if AI-assisted negotiation is enabled.
- The model configured in `OLLAMA_MODEL` pulled into Ollama.

## Installation

Run commands from the project root—the directory containing `main.py`, `dashboard.py`, and `requirements.txt`.

### 1. Create and activate a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Configure Ollama

Install Ollama from its official distribution and ensure the Ollama service is running. Pull the configured model:

```bash
ollama pull qwen2.5:3b
```

Check that Ollama is reachable locally at `http://localhost:11434` and that the model is available before running with AI enabled.

### 4. Configure environment variables

Create a `.env` file in the project root. The active Ollama provider reads these variables:

```dotenv
AI_ENABLED=true
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://localhost:11434
```

To use deterministic fallback/rule-based behavior without requesting AI decisions, set:

```dotenv
AI_ENABLED=false
```

The provider defaults to AI disabled if `AI_ENABLED` is not set. The dashboard also has an Enable AI toggle and passes its selected value to the simulation.

**Configuration note:** The `.env.example` included in the ZIP currently documents `OPENAI_API_KEY` and `OPENAI_MODEL`, while the active `ai_strategy/provider.py` uses `OLLAMA_MODEL` and `OLLAMA_BASE_URL`. Follow the Ollama configuration above for the active provider. Updating `.env.example` to match the Ollama provider would prevent confusion.

Do not commit `.env` or API keys/secrets. The supplied `.gitignore` already excludes `.env`.

## Run the simulation

### Command-line mode

Run the simulation using the entry point:

```bash
python main.py
```

This creates a `PriceWarSimulation` with its default settings and runs it in the terminal. The simulation prints round information, negotiation results, and summary metrics.

### Interactive dashboard

Run the Streamlit dashboard:

```bash
python -m streamlit run dashboard.py
```

In the dashboard:

1. Configure the product, inventory, shelf life, reservation prices, retailer capacities, willingness-to-pay limits, and budgets in the sidebar.
2. Enable or disable AI.
3. Click **Run / reset simulation**.
4. Review the revenue, units sold, successful deals, expired inventory, market status, successful-deal table, outcome chart, decision-source summary, negotiation history, and console output.

The dashboard's AI toggle defaults to enabled in the current code. Make sure Ollama is running and the configured model is available when using this setting.

## Run tests

From the project root with the virtual environment activated:

```bash
python -m pytest -v
```

The repository includes tests covering agents, end-to-end simulation behavior, inventory, market behavior, negotiation, pricing, and validation. It also includes `test_gemini_provider.py`; that test relates to a Gemini provider path and may require review because the active provider in this project is Ollama. The `pytest.ini` file defines an `integration` marker for tests that make real external API calls.

Run the tests and use the current terminal output as the authoritative pass/fail result. Do not assume every test passes without executing the suite in the environment where the project will be submitted.

## Results and metrics

The application reports metrics such as:

- **Total revenue** — sum of successful deal values.
- **Units sold** — total quantity sold in successful deals.
- **Successful deals** — count of completed transactions.
- **Failed negotiations** — count of negotiations that end without a successful deal.
- **Rejected offers** — count of offers recorded as rejected.
- **Expired inventory** — inventory that expires during the simulation.
- **Negotiation history** — round, turn, actor, action, price, quantity, reason, and inferred source label.

The dashboard's AI/Rule/Fallback summary is derived from source tags in each event's reason text. It represents event labels, not necessarily the number of raw model requests or proof that every AI response determined the final action.

Simulation results can vary with configuration and AI responses. Use the values displayed by the current run rather than treating any single run as a guaranteed outcome.

## Troubleshooting

- **Ollama connection error:** Ensure Ollama is running and `OLLAMA_BASE_URL` points to the local service.
- **Model not found:** Run `ollama pull qwen2.5:3b` or pull the model named in `OLLAMA_MODEL`.
- **AI responses fall back:** Inspect the terminal/dashboard console output. Invalid model JSON, a timeout, connection failure, or schema validation failure can cause fallback behavior.
- **Import errors:** Ensure the virtual environment is activated and `requirements.txt` has been installed from the project root.
- **Dashboard does not show a result:** Click **Run / reset simulation** after changing settings.
- **Tests involving external providers:** Check the test marker and provider-specific test setup; the active AI provider is Ollama.

## Limitations and possible extensions

- AI output can vary, and one simulation run is not sufficient to establish that AI improves performance.
- The current dashboard summarizes source labels from negotiation-event reasons rather than reporting a complete AI-request telemetry breakdown.
- The test suite contains a Gemini-named provider test while the active provider is Ollama; align or explicitly separate provider-specific tests as the project evolves.
- Useful extensions include repeatable multi-run experiments, AI-versus-rule-only comparisons, richer telemetry, and additional retailer strategies.

## License

No license file was included in the supplied project archive. Add a `LICENSE` file if you intend to publish or redistribute the project under a specific license.
