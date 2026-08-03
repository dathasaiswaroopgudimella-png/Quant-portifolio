<div align="center">

<br />

<img src="https://img.shields.io/badge/FRAGMENT-Adversarial%20Model%20Risk%20Platform-8083ff?style=for-the-badge&logo=python&logoColor=white" alt="FRAGMENT Banner" />

<br /><br />

# FRAGMENT — Adversarial Quantitative Model Risk Platform

### *Find the smallest market shift that breaks your pricing model. Before the market does.*

<br />

[![Python](https://img.shields.io/badge/Python-3.10.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![QuantLib](https://img.shields.io/badge/QuantLib-1.43-ff6b6b?style=flat-square)](https://www.quantlib.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Node.js](https://img.shields.io/badge/Node.js-24.14.0-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)
[![SciPy](https://img.shields.io/badge/SciPy-1.15.3-8CAAE6?style=flat-square&logo=scipy&logoColor=white)](https://scipy.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![SR 11-7](https://img.shields.io/badge/Federal%20Reserve-SR%2011--7%20Compliant-c0c1ff?style=flat-square)](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm)

</div>

---

## 🎯 What is FRAGMENT?

**FRAGMENT** is a **production-grade quantitative model risk validation platform** built for quantitative analysts, risk managers, and financial engineers. It answers one critical question that existing tools fail to ask:

> *"What is the **smallest realistic market shift** that causes your Black-Scholes pricing model to produce unacceptably large errors relative to QuantLib's analytical ground truth?"*

This is the central question behind **Federal Reserve SR 11-7** (Model Risk Management) guidance — and FRAGMENT answers it with rigorous, reproducible adversarial mathematics.

---

## 🔴 The Problem FRAGMENT Solves

Standard backtests validate models against historical data. They miss **silent failure modes** — parameter combinations that look fine in backtesting but cause catastrophic mispricing under real market stress.

Consider this real scenario:
- A Black-Scholes call option model prices correctly at σ = 20%, S = $100
- At σ = 38%, S = $87, the same model diverges from QuantLib by **$2.14** — a 12.7% error
- A $10M options desk running this model without FRAGMENT would lose **$1.27M** in mispriced hedges during a single volatility event

FRAGMENT finds that exact breaking point **before you deploy**.

---

## ✨ Platform Features

### 🔬 Four-Mode Model Ingestion
| Mode | Description |
|------|-------------|
| **Direct Python Code** | Paste or write any `(S, K, T, r, sigma)` → float pricing function |
| **Natural Language / Formula Prompt** | Describe the model in plain English or LaTeX. OpenRouter AI synthesizes executable Python code automatically |
| **File Upload** | Drag-and-drop `.py`, `.txt`, or `.json` pricing model files |
| **Quant Model Preset Library** | One-click selection from 5 pre-built quant models (BSM Call, BSM Put, Garman-Kohlhagen FX, Skew-Vulnerable, Short Tenor) |

### 🧪 Adversarial Validation Engine (SciPy + QuantLib)
- **SciPy Differential Evolution** — Non-convex global optimizer searches a 49-combination (7×7) Spot × Volatility grid to find the exact minimal parameter perturbation that maximizes QuantLib divergence
- **QuantLib 1.43 Analytical Ground Truth** — Industry-reference C++ pricing engine used as the validation baseline
- **AST Security Sandbox** — Python Abstract Syntax Tree inspection ensures only `math`, `scipy.stats`, and `numpy` can execute inside user-submitted code

### 📊 6-Axis Hexagonal Radar Chart
Every validated model receives a **6-dimensional health assessment**, rendered as an interactive SVG Hexagonal Radar Chart:

| Axis | What It Measures |
|------|-----------------|
| Conceptual Soundness | Mathematical formulation alignment with physical market dynamics |
| Numerical Stability | Floating-point precision under extreme exponent and short-tenor calculations |
| Parameter Robustness | Pricing sensitivity to simultaneous multi-parameter perturbations |
| Boundary Condition Safety | Behaviour at extreme limits (σ → 0%, S → crash scenarios) |
| Greek Fidelity | Partial derivative (Δ, Γ, Vega, Θ, ρ) accuracy vs QuantLib exact greeks |
| Benchmark Alignment | Direct dollar-for-dollar pricing agreement with QuantLib |

### 🏛️ Federal Reserve SR 11-7 Regulatory Audit
- Full compliance checklist auto-generated for every validation run
- Conceptual Soundness → PASS / WARNING classification
- Out-of-sample stress test evidence documentation
- Ongoing monitoring threshold configuration

### 🤖 OpenRouter AI Executive Reports
- **Model Synthesis**: Converts natural language model descriptions into sandboxed Python code
- **Governance Narratives**: AI synthesizes human-readable SR 11-7 executive reports with mathematical assumption breakdowns
- Powered by **Google Gemini 2.5 Flash** via OpenRouter

### 📈 Live Market Data Integration
- **Yahoo Finance (yfinance)** integration: real-time spot prices, 21-day historical volatility, risk-free rate
- Market Monitor dashboard with live vol regime tracking

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRAGMENT Platform                             │
│                                                                  │
│  ┌─────────────────────┐        ┌──────────────────────────┐   │
│  │   Next.js Frontend  │  HTTP  │   FastAPI Backend         │   │
│  │   (Port 3000)       │◄──────►│   (Port 8000)             │   │
│  │                     │        │                           │   │
│  │  ○ Landing Page     │        │  ○ /api/v1/models         │   │
│  │  ○ Dashboard        │        │  ○ /api/v1/validations    │   │
│  │  ○ Editor Sandbox   │        │  ○ /api/v1/market-data    │   │
│  │  ○ Validation Reports│        │  ○ /api/v1/reports        │   │
│  │  ○ Market Monitor   │        │                           │   │
│  └─────────────────────┘        └──────────┬───────────────┘   │
│                                             │                    │
│                              ┌──────────────▼───────────────┐   │
│                              │        Engine Layer           │   │
│                              │                               │   │
│                              │  QuantLib 1.43 Pricer        │   │
│                              │  SciPy Differential Evolution│   │
│                              │  AST Security Sandbox        │   │
│                              │  SymPy Assumption Extractor  │   │
│                              │  Fragility Scorer (0-100)    │   │
│                              │  Hexagonal Radar Scorer      │   │
│                              └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Pricing Engine** | QuantLib | 1.43 | Analytical option pricing ground truth |
| **Optimization** | SciPy | 1.15.3 | Differential Evolution adversarial search |
| **Math / Assumptions** | SymPy | ≥1.12 | Symbolic assumption extraction |
| **Market Data** | yfinance | 1.5.2 | Live spot prices, volatility, rates |
| **Backend API** | FastAPI | 0.139.0 | Async REST API with Pydantic validation |
| **ASGI Server** | Uvicorn | 0.49.0 | Production async server |
| **Database** | SQLite (aiosqlite) | — | Model registry and run history |
| **AI / NLP** | OpenRouter (Gemini 2.5 Flash) | — | Model synthesis + SR 11-7 reports |
| **Frontend** | Next.js 14 | 14.2.35 | Server-side rendered React application |
| **Runtime** | Python | 3.10.11 | Backend runtime |
| **Runtime** | Node.js | 24.14.0 | Frontend runtime |

---

## 🚀 Getting Started

### Prerequisites

Ensure the following are installed on your system:

| Requirement | Version | Install Link |
|-------------|---------|-------------|
| **Python** | 3.10.x or 3.11.x | [python.org/downloads](https://www.python.org/downloads/) |
| **Node.js** | 20.x, 22.x, or 24.x | [nodejs.org](https://nodejs.org/en/download) |
| **npm** | 9.x or higher | Bundled with Node.js |
| **Git** | Any modern version | [git-scm.com](https://git-scm.com/) |

> **⚠️ QuantLib Note**: QuantLib Python bindings require a C++ compiler. On Windows, use the pre-compiled wheel:
> ```
> pip install QuantLib
> ```
> On Ubuntu/Debian: `sudo apt-get install libquantlib0-dev` then `pip install QuantLib`

---

### 1. Clone the Repository

```bash
git clone https://github.com/dathasaiswaroopgudimella-png/Quant-portifolio.git
cd Quant-portifolio
```

---

### 2. Backend Setup

```bash
cd backend

# Install all Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key (optional — platform works without it, OpenRouter enables AI model synthesis and executive report generation):

```env
OPENROUTER_API_KEY="your-openrouter-api-key-here"
OPENROUTER_MODEL="google/gemini-2.5-flash"
```

Start the backend API server:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Verify it's running:** Open http://127.0.0.1:8000/health — you should see:
```json
{
  "status": "healthy",
  "service": "FRAGMENT Engine",
  "quantlib_version": "1.43",
  "sandbox_isolation": "ACTIVE"
}
```

---

### 3. Frontend Setup

```bash
# Open a new terminal window
cd frontend

# Install Node.js dependencies
npm install

# Start the Next.js development server
npm run dev
```

**Open in browser:** http://localhost:3000

---

### 4. Environment Configuration Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Optional | Enables AI model synthesis from text prompts + SR 11-7 governance report generation |
| `OPENROUTER_MODEL` | Optional | AI model to use (default: `google/gemini-2.5-flash`) |
| `DATABASE_URL` | Optional | PostgreSQL URL for production (SQLite used by default) |

---

## 💡 Usage Guide

### Running Your First Adversarial Validation

1. **Navigate to the Editor Sandbox** → `localhost:3000/editor`

2. **Choose an ingestion mode:**
   - **Code Tab**: Paste your pricing function (must accept `S, K, T, r, sigma` and return a `float`)
   - **Prompt Tab**: Describe your model: *"European call with continuous dividend yield q"*
   - **Upload Tab**: Drag-and-drop your `.py` model file
   - **Presets Tab**: Select from 5 pre-built quant models

3. **Set market parameters**: Spot (S), Strike (K), Maturity (T), Rate (r), Volatility (σ)

4. **Click "Run Adversarial Validation"**: SciPy Differential Evolution executes a 49-point grid search over the Spot × Volatility space, finding the worst-case parameter combination that maximizes divergence from QuantLib ground truth.

5. **View your Deep-Dive Report** (`/validations/[id]`):
   - **6-Axis Hexagonal Radar Chart** — Model health across 6 quantitative dimensions
   - **7×7 Fragility Surface Heatmap** — Dollar-level pricing error at every grid point
   - **Analytical Greek Drifts** — Δ, Γ, Vega, Θ, ρ vs QuantLib exact partial derivatives
   - **SR 11-7 Regulatory Audit** — Federal Reserve compliance checklist
   - **AI Executive Narrative** — OpenRouter-synthesized governance report

---

## 📐 Fragility Score Classification

| Score Range | Classification | Meaning |
|-------------|---------------|---------|
| 0 – 15 | 🟢 **ROBUST** | Passes all boundary and stress conditions. Approved for production. |
| 16 – 40 | 🟡 **MODERATE** | Minor sensitivity under extreme vol skew. Acceptable with monitoring. |
| 41 – 70 | 🟠 **FRAGILE** | Significant pricing drift under vol regime shifts. Bounds required. |
| 71 – 100 | 🔴 **CRITICAL** | Severe breakdown under market stress. Action required before deployment. |

---

## 📁 Project Structure

```
Quant-portifolio/
├── backend/                        # FastAPI Python Backend
│   ├── app/
│   │   ├── api/v1/                 # REST API Route Handlers
│   │   │   ├── models.py           # Model registry & synthesis endpoints
│   │   │   ├── validations.py      # Adversarial validation engine endpoints
│   │   │   ├── market.py           # Live market data (Yahoo Finance)
│   │   │   └── reports.py          # AI executive report endpoints
│   │   ├── engine/                 # Core Quantitative Engine Layer
│   │   │   ├── adversarial_engine.py   # SciPy Differential Evolution search
│   │   │   ├── quantlib_pricer.py      # QuantLib 1.43 analytical pricer
│   │   │   ├── sandbox.py              # AST security inspection & execution
│   │   │   ├── assumption_engine.py    # SymPy assumption extractor
│   │   │   ├── fragility_scorer.py     # 0-100 Fragility Index calculator
│   │   │   └── expectations.py         # Quantitative expectation suite
│   │   ├── services/
│   │   │   └── report_ai.py        # OpenRouter AI model synthesis & reports
│   │   ├── models/domain.py        # SQLAlchemy ORM models
│   │   ├── schemas/schemas.py      # Pydantic request/response schemas
│   │   └── core/config.py          # Environment configuration
│   ├── requirements.txt            # Python package dependencies
│   └── .env.example                # Environment variable template
│
├── frontend/                       # Next.js 14 Frontend Application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Landing page (world-class narrative)
│   │   │   ├── dashboard/          # Model inventory & governance dashboard
│   │   │   ├── editor/             # Multi-format model ingestion sandbox
│   │   │   ├── validations/
│   │   │   │   ├── page.tsx        # Validation runs list & search
│   │   │   │   └── [id]/page.tsx   # Deep-dive single report (Hex Radar + Heatmap)
│   │   │   └── market/             # Live market monitor dashboard
│   │   ├── components/
│   │   │   ├── TopNav.tsx          # Glassmorphic navigation bar
│   │   │   └── HexagonalRadarChart.tsx  # Interactive 6-axis SVG radar chart
│   │   └── lib/api.ts              # Typed API client with TypeScript interfaces
│   └── package.json                # Node.js dependencies
│
└── docker-compose.yml              # Docker deployment configuration
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Platform health check with QuantLib version |
| `POST` | `/api/v1/models/upload` | Register Python pricing model (AST validated) |
| `POST` | `/api/v1/models/synthesize` | Synthesize Python model from text prompt via OpenRouter AI |
| `GET` | `/api/v1/models` | List all registered financial models |
| `POST` | `/api/v1/validations` | Execute SciPy adversarial search + QuantLib validation |
| `GET` | `/api/v1/validations` | List all validation runs with hexagonal scores |
| `GET` | `/api/v1/validations/{id}` | Get single validation run with full metrics |
| `GET` | `/api/v1/validations/{id}/report` | Get AI executive SR 11-7 governance report |
| `GET` | `/api/v1/market-data/{ticker}` | Live spot price, volatility, rate from Yahoo Finance |

> Full interactive API documentation: **http://127.0.0.1:8000/docs**

---

## 🎓 Financial Background

### Why Black-Scholes Models Fail Silently

The Black-Scholes model makes several strong mathematical assumptions:
- Constant volatility: **∂σ/∂t = 0** (violated in every real market regime shift)
- Constant risk-free rate: **∂r/∂t = 0** (violated during rate cycles)
- Log-normal price distribution (violated with fat tails)
- Zero transaction costs and continuous hedging

FRAGMENT's adversarial engine **exploits these assumptions** — it finds the exact parameter combination where these approximations produce unacceptable mispricing. This is the core of SR 11-7 model risk management.

### The SciPy Differential Evolution Approach

Rather than exhaustive grid search, FRAGMENT uses **Differential Evolution (DE)** — a non-convex global optimization algorithm — to search the (Spot × Volatility × Rate) parameter space:

```python
# Objective function: maximize |user_model_price - quantlib_price|
result = differential_evolution(
    func=adversarial_objective,
    bounds=[(S_min, S_max), (vol_min, vol_max), (rate_min, rate_max)],
    strategy='best1bin',
    maxiter=100,
    popsize=10,
    seed=42  # Deterministic & reproducible
)
```

This is **orders of magnitude** more efficient than exhaustive grid search and finds global optima that simple sensitivity analysis misses.

---

## 🤝 Contributing

Contributions from quantitative analysts, risk engineers, and full-stack developers are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improved-heston-model`)
3. Commit your changes (`git commit -m 'Add Heston stochastic vol model support'`)
4. Push to the branch (`git push origin feature/improved-heston-model`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👤 Author

**Datha Sai Swaroop Gudimella**

Quantitative Finance Platform Developer — Building production-grade tools at the intersection of derivatives pricing, model risk governance, and modern software engineering.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=flat-square&logo=linkedin)](https://linkedin.com/in/dathasaiswaroopgudimella)
[![GitHub](https://img.shields.io/badge/GitHub-dathasaiswaroopgudimella--png-181717?style=flat-square&logo=github)](https://github.com/dathasaiswaroopgudimella-png)

---

<div align="center">

**Built with mathematical rigor. Powered by QuantLib. Validated by SciPy.**

*FRAGMENT — Because your derivatives model should survive the next volatility regime before it has to.*

</div>
