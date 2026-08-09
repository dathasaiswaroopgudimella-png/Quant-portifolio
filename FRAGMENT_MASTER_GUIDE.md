# FRAGMENT — Master Project Guide

> **One document to understand everything.** This guide is written so that someone who has never seen a line of this codebase — and does not know what quantitative finance, FastAPI, Next.js, or option pricing even mean — can read it top to bottom and walk away ready to confidently explain, extend, debug, or demo every part of this system.

---

## Table of Contents

1. [What Is FRAGMENT?](#1-what-is-fragment)
2. [The Real-World Problem Being Solved](#2-the-real-world-problem-being-solved)
3. [The Core Idea — In Plain English](#3-the-core-idea--in-plain-english)
4. [High-Level System Architecture](#4-high-level-system-architecture)
5. [Technology Stack — Every Choice Explained](#5-technology-stack--every-choice-explained)
6. [Repository File Structure](#6-repository-file-structure)
7. [Backend — How It Is Built](#7-backend--how-it-is-built)
8. [The Reasoning Engines — The Heart of the Project](#8-the-reasoning-engines--the-heart-of-the-project)
9. [AI Services](#9-ai-services)
10. [Market Data Service](#10-market-data-service)
11. [Complete Validation Data Flow — Step by Step](#11-complete-validation-data-flow--step-by-step)
12. [Frontend — How It Is Built](#12-frontend--how-it-is-built)
13. [3D Visual Components](#13-3d-visual-components)
14. [API Keys — What They Are, Where to Get Them, Where to Put Them](#14-api-keys--what-they-are-where-to-get-them-where-to-put-them)
15. [Local Development Setup — Start to Finish](#15-local-development-setup--start-to-finish)
16. [Docker Deployment](#16-docker-deployment)
17. [Test Suite](#17-test-suite)
18. [Frequently Asked Questions](#18-frequently-asked-questions)

---

## 1. What Is FRAGMENT?

FRAGMENT is a **quantitative model risk validation platform** built as a professional portfolio project. The name stands for **Fragility, Robustness, and Adversarial Gradient Measurement Engine for Numerical Trajectories**.

In simple terms: it is a web application where a user can upload their own Python-based financial pricing model — the kind used on trading desks to price stock options — and the system automatically finds the exact market conditions under which that model breaks down. It then produces a full audit report with a risk score, visual charts, regulatory compliance analysis, and an AI-generated executive summary.

This is not a toy. The techniques used — SciPy Differential Evolution, QuantLib C++ analytical pricing, AST security inspection, Federal Reserve SR 11-7 governance alignment — are the same approaches used in real bank model risk management teams.

---

## 2. The Real-World Problem Being Solved

### What is a financial model?

A financial model, in this context, is a mathematical formula that estimates the fair price of a financial contract called an **option**. An option gives its buyer the right — but not the obligation — to buy or sell a stock at a pre-agreed price on a future date.

The most famous pricing formula in history is the **Black-Scholes-Merton (BSM) model**, which won the 1997 Nobel Prize in Economics. It takes five inputs:

| Parameter | Symbol | Meaning |
|-----------|--------|---------|
| Spot Price | S | Current price of the underlying stock |
| Strike Price | K | The pre-agreed future purchase price |
| Time to Maturity | T | How many years until the option expires |
| Risk-Free Rate | r | The yield on a government bond |
| Volatility | σ | How wildly the stock price fluctuates |

And it outputs a single number: the fair value of the option today.

### What goes wrong?

The BSM formula makes strong simplifying assumptions:

- **Constant volatility**: assumes σ never changes. In reality, volatility shifts dramatically during market crises.
- **Constant interest rates**: central banks raise and lower rates continuously.
- **Log-normal returns**: assumes stock prices follow a smooth bell-curve. Real markets have "fat tails" — extreme events happen far more often than the formula expects.

When quants (quantitative analysts) build custom pricing models, they often introduce subtle bugs or make simplifying assumptions that look fine under normal conditions but collapse under stress.

### The regulatory context

The U.S. Federal Reserve issued guidance called **SR 11-7** — *Guidance on Model Risk Management* — which requires banks and financial institutions to rigorously validate their models. This means:

- Documenting all model assumptions
- Testing models under adversarial market scenarios
- Maintaining ongoing monitoring
- Generating executive governance reports for audit committees

Most small-to-mid-size firms cannot afford the quant teams to do this properly. FRAGMENT automates the entire process.

---

## 3. The Core Idea — In Plain English

Imagine you have built a calculator that you claim correctly prices stock options. FRAGMENT's job is to be a relentless adversary — to methodically try every possible combination of market conditions and find the specific combination where your calculator gives the most wrong answer compared to a mathematically perfect reference implementation.

That search is not random guessing. It uses **Differential Evolution** — a global non-convex optimizer from evolutionary computing — to efficiently explore a 4-dimensional search space and converge on the exact "breaking point" of your model.

Once found, the system:

1. Measures exactly how wrong the model is at that breaking point (in dollar terms and percentage terms)
2. Computes a **Fragility Index** from 0 to 100 — zero means perfectly robust, 100 means severely broken
3. Classifies the model as ROBUST, MODERATE, FRAGILE, or CRITICAL
4. Breaks down which market factor (volatility, spot price, interest rate) drove the most damage
5. Runs a formal expectation suite of 6 mathematical assertions about correct pricing behavior
6. Renders a 3D surface mesh of the error landscape across all spot-volatility combinations
7. Generates a regulatory-grade written audit report via AI, aligned to Federal Reserve SR 11-7 standards

---

## 4. High-Level System Architecture

The system is split into two completely independent processes that communicate over HTTP:

```
USER BROWSER
    |
    v
Next.js 14 Frontend  (Port 3000)
    Landing Page -> Dashboard -> Editor -> Market -> Audit Report
    Three.js WebGL 3D | Chart.js Charts | Monaco Code Editor
    |
    | HTTP REST API (JSON)
    | CORS: localhost:3000 <-> localhost:8000
    v
FastAPI Backend  (Port 8000)
    /api/v1/auth          JWT Authentication
    /api/v1/models        CRUD for Financial Models
    /api/v1/validations   Run adversarial search, get results
    /api/v1/market        Live market data (yfinance)
    /api/v1/reports       Retrieve audit reports

    ── REASONING ENGINE LAYER ──────────────────────
    AST Parser -> Sandbox Evaluator -> QuantLib Pricer
         |
         v
    Adversarial Engine (SciPy Differential Evolution — 4D)
         |
         v
    Fragility Scorer -> Assumption Extractor -> Expectation Suite
         |
         v
    OpenRouter AI  (Executive Narrative + Model Synthesis)
    ────────────────────────────────────────────────

    SQLite Database (fragment.db)
    via SQLAlchemy 2.0 async + aiosqlite
```

The frontend serves the user interface and handles all visualization. The backend contains all business logic, mathematical computation, and data storage. You could replace the frontend with a mobile app, CLI tool, or Jupyter notebook and the backend would not need to change at all.

---

## 5. Technology Stack — Every Choice Explained

### Backend Technologies

**Python 3.10+**
The lingua franca of quantitative finance. NumPy, SciPy, and QuantLib all have first-class Python bindings. Every major quant library exists in Python first.

**FastAPI ≥ 0.115**
High-performance async web framework. Provides automatic OpenAPI/Swagger documentation from type hints alone. Dramatically faster than Django or Flask for API-only services because it is built on Starlette and uses Python's async/await natively.

**Uvicorn ≥ 0.30**
ASGI (Asynchronous Server Gateway Interface) server. Allows FastAPI to handle thousands of concurrent connections without blocking. When the adversarial engine is running a 30-second computation, the server still responds to health checks and other requests.

**QuantLib ≥ 1.43**
The industry-standard open-source library for quantitative finance. Written in C++ with Python bindings via SWIG (Simplified Wrapper and Interface Generator). Implements hundreds of pricing models used by banks worldwide. Used as the mathematically exact "ground truth" comparator against which user models are measured. Has been in production use at financial institutions for over two decades.

**SciPy ≥ 1.13**
Scientific computing library. The `scipy.optimize.differential_evolution` function is the core of the adversarial search engine — a global non-convex optimizer that efficiently explores high-dimensional parameter spaces.

**NumPy ≥ 1.26**
Fundamental array computation library. Used in fragility surface generation, statistical calculations (mean, std across seeds), and log-return computation in the market data service.

**SQLAlchemy ≥ 2.0 (async)**
The de-facto Python ORM (Object-Relational Mapper) for database operations. The async version allows non-blocking database queries — database reads do not freeze other operations.

**aiosqlite ≥ 0.20**
Async SQLite driver. SQLite is used as the database in local development, meaning no database setup is required. Just install Python dependencies and start the server.

**Pydantic v2 ≥ 2.7**
Data validation library. Every API request body and response body is defined as a Pydantic model, providing automatic type checking, serialization, and OpenAPI schema generation from type hints.

**pydantic-settings ≥ 2.2**
Loads configuration from `.env` files into typed Pydantic Settings objects. Makes environment configuration safe, typed, and self-documenting.

**yfinance ≥ 0.2.40**
Yahoo Finance API wrapper. Fetches live (15-minute delayed) stock prices and option chain implied volatility for any publicly traded ticker.

**httpx ≥ 0.27**
Async HTTP client for Python. Used to make non-blocking HTTP calls to the OpenRouter AI API when generating executive reports.

**PyJWT ≥ 2.8**
JSON Web Token library for generating and verifying authentication tokens.

**passlib[bcrypt] ≥ 1.7**
Password hashing library using the industry-standard bcrypt algorithm. Passwords are never stored in plain text; bcrypt applies a unique salt and multiple hashing rounds.

**pytest ≥ 8.0**
Test runner. 19 tests across 5 test files covering all reasoning engines without network calls or database setup.

### Frontend Technologies

**Next.js ≥ 14.2**
React meta-framework with the App Router — file-system-based routing where every folder with a `page.tsx` becomes a URL. Provides server-side rendering, automatic code splitting, and production optimization out of the box.

**React ≥ 18.3**
Component-based UI library. The entire frontend is built as a tree of reusable components, each managing its own state and rendering logic.

**TypeScript ≥ 5.7**
Typed superset of JavaScript. Every component prop, API response, and state variable has a type annotation. The TypeScript compiler catches errors at build time rather than at runtime in production.

**Three.js ≥ 0.185**
The most powerful WebGL 3D graphics library for the web. Used for the hero GBM particle field (HeroScene3D) and the interactive 3D fragility surface mesh (FragilitySurface3D).

**@monaco-editor/react ≥ 4.6**
The exact same editor engine that powers VS Code, embedded in the browser as a React component. Powers the Python code editor in the model sandbox with full syntax highlighting, bracket matching, and error indicators.

**Chart.js + react-chartjs-2 ≥ 4.4**
2D charting library. Used specifically for the hexagonal radar chart on the audit report page.

**Tailwind CSS ≥ 3.4**
Utility-first CSS framework. Provides consistent spacing, typography, colors, and responsive layout without writing custom CSS files for every component.

**lucide-react ≥ 0.469**
Clean, consistent icon library with tree-shaking — only icons actually used are bundled into the final build.

---

## 6. Repository File Structure

```
Quant portifolio/
|
+-- FRAGMENT_MASTER_GUIDE.md           <- This file — complete knowledge base
+-- README.md                          <- GitHub-facing project overview
+-- docker-compose.yml                 <- Multi-container Docker orchestration
+-- LICENSE                            <- MIT License
|
+-- backend/
|   +-- .env.example                   <- Template for environment variables
|   +-- requirements.txt               <- All Python dependencies pinned
|   +-- Dockerfile                     <- Container definition for backend
|   +-- fragment.db                    <- SQLite database file (auto-created on first run)
|   |
|   +-- app/
|       +-- main.py                    <- FastAPI app entry point, CORS config, health endpoint
|       |
|       +-- core/
|       |   +-- config.py              <- Pydantic Settings (reads .env file)
|       |   +-- security.py            <- JWT token creation and verification, bcrypt utilities
|       |
|       +-- db/
|       |   +-- session.py             <- SQLAlchemy async engine and session factory
|       |
|       +-- models/
|       |   +-- domain.py              <- SQLAlchemy ORM table definitions (5 tables)
|       |
|       +-- schemas/
|       |   +-- schemas.py             <- Pydantic request and response shape definitions
|       |
|       +-- api/
|       |   +-- deps.py                <- FastAPI dependency injection (auth guard)
|       |   +-- v1/
|       |       +-- router.py          <- Master API router — combines all sub-routers
|       |       +-- auth.py            <- /auth endpoints (login, register, me)
|       |       +-- models.py          <- /models endpoints (CRUD + synthesize + assumptions)
|       |       +-- validations.py     <- /validations endpoints — THE CORE ENGINE CALL
|       |       +-- market.py          <- /market endpoint (yfinance live data)
|       |       +-- reports.py         <- /reports endpoint (audit report retrieval)
|       |
|       +-- engine/                    <- THE REASONING ENGINES — all quantitative intelligence
|       |   +-- ast_parser.py          <- Static AST security inspection before any execution
|       |   +-- sandbox.py             <- Thread-isolated restricted execution environment
|       |   +-- quantlib_pricer.py     <- QuantLib C++ analytical ground truth engine
|       |   +-- adversarial_engine.py  <- SciPy DE 4D adversarial parameter search
|       |   +-- fragility_scorer.py    <- Fragility index + risk attribution computation
|       |   +-- assumption_engine.py   <- AST-driven mathematical assumption extraction
|       |   +-- expectations.py        <- Formal verification 6-assertion expectation suite
|       |
|       +-- services/
|           +-- report_ai.py           <- OpenRouter AI executive reports + model synthesis
|           +-- yfinance_provider.py   <- Yahoo Finance live market data provider
|
+-- frontend/
    +-- package.json                   <- NPM dependencies and build scripts
    +-- next.config.js                 <- Next.js configuration
    +-- tailwind.config.ts             <- Custom Tailwind CSS theme tokens
    +-- tsconfig.json                  <- TypeScript compiler options
    +-- Dockerfile                     <- Container definition for frontend
    |
    +-- src/
        +-- app/                       <- Next.js App Router (file path = URL route)
        |   +-- layout.tsx             <- Root HTML shell, font imports, metadata
        |   +-- globals.css            <- Global CSS design tokens and base styles
        |   +-- page.tsx               <- Landing page route: /
        |   +-- dashboard/
        |   |   +-- page.tsx           <- Model inventory route: /dashboard
        |   +-- editor/
        |   |   +-- page.tsx           <- Sandbox editor route: /editor
        |   +-- market/
        |   |   +-- page.tsx           <- Market monitor route: /market
        |   +-- validations/
        |       +-- [id]/
        |           +-- page.tsx       <- Audit report route: /validations/:id
        |
        +-- components/
        |   +-- FragilitySurface3D.tsx <- WebGL 3D error surface mesh (Three.js)
        |   +-- HeroScene3D.tsx        <- WebGL GBM stochastic path particle field
        |   +-- HexagonalRadarChart.tsx <- 6-axis risk radar chart (Chart.js)
        |   +-- Navbar.tsx             <- Landing page top navigation bar
        |   +-- TopNav.tsx             <- App-wide inner navigation (dashboard onwards)
        |
        +-- lib/
            +-- api.ts                 <- Typed fetch wrapper — all API calls go through here
```

---

## 7. Backend — How It Is Built

### 7.1 Entry Point and Server Boot

**File:** `backend/app/main.py`

When you run `uvicorn app.main:app --reload --port 8000`, Python imports this file, discovers the `app` FastAPI object, and starts the ASGI server.

The `lifespan` async context manager runs exactly once at startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FRAGMENT backend database tables...")
    await init_db()   # Runs CREATE TABLE IF NOT EXISTS for all 5 tables
    logger.info("FRAGMENT core engine ready.")
    yield
    logger.info("Shutting down FRAGMENT backend.")
```

This means zero manual database setup — the SQLite file and all tables are created automatically on first run.

**CORS middleware** is configured to allow requests from localhost ports 3000, 3001, and 8000. Without this, browsers would block requests from the frontend (localhost:3000) to the backend (localhost:8000) as a cross-origin security policy violation.

**The `/health` endpoint** is a liveness probe — it returns a simple JSON object confirming the server is running and which versions of QuantLib, the sandbox, and the engine are active.

### 7.2 Configuration and Environment Variables

**File:** `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "FRAGMENT - Adversarial Validation Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "..."              # Used to sign JWT tokens — change in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    DATABASE_URL: str = "sqlite+aiosqlite:///./fragment.db"  # Default
    REDIS_URL: str = "redis://localhost:6379/0"              # Optional
    OPENROUTER_API_KEY: Optional[str] = None                 # Optional AI features
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"

    class Config:
        env_file = ".env"
```

The same codebase reads from `.env` in development, real environment variables in production, and the `environment:` block in docker-compose.yml in Docker — without any code changes.

### 7.3 Database Layer

The database session is managed by SQLAlchemy's async engine. Every API endpoint receives a fresh database session via FastAPI dependency injection:

```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
```

This is the "unit of work" pattern — each request gets a fresh session, transactions are committed or rolled back atomically, and sessions are closed automatically when the request completes.

### 7.4 Domain Models — Database Tables

**File:** `backend/app/models/domain.py`

Five SQLAlchemy ORM classes map Python objects to database rows:

**User** — Registered user accounts. Relationships: one user owns many FinancialModels.

**FinancialModel** — A pricing model with its Python source code. Relationships: belongs to one User, has many Assumptions, has many ValidationRuns.

**Assumption** — One mathematical assumption extracted from a model's code (e.g., "Constant Volatility Assumption — dσ/dt = 0"). Relationships: belongs to one FinancialModel.

**ValidationRun** — One execution of the adversarial pipeline. Stores `breaking_parameters`, `greek_drifts`, and `fragility_surface` as JSON columns. Relationships: belongs to one FinancialModel, has one Report.

**Report** — The complete audit output for one ValidationRun. Stores `executive_summary` (AI prose), `sr11_7_compliance` (governance JSON), and `report_data` (full results blob). Relationships: belongs to one ValidationRun.

### 7.5 API Routes — Complete Route Table

**File:** `backend/app/api/v1/router.py` assembles all five sub-routers.

#### Authentication — `/api/v1/auth`

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | /auth/register | No | Create a new user account with email and password |
| POST | /auth/login | No | Verify credentials, receive a 7-day JWT token |
| GET | /auth/me | Yes | Return the currently authenticated user's profile |

#### Financial Models — `/api/v1/models`

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | /models | Yes | Upload a new pricing model (name, code, asset_class) |
| GET | /models | No | List all models in the system with metadata |
| GET | /models/{id} | No | Get a specific model and its stored assumptions |
| PUT | /models/{id} | Yes | Update model code, name, or description |
| DELETE | /models/{id} | Yes | Delete model and cascade-delete all validations and reports |
| POST | /models/synthesize | No | Convert natural language prompt to Python pricing code via AI |
| POST | /models/{id}/assumptions | No | Run AST assumption extraction and store results |

#### Validations — `/api/v1/validations`

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | /validations | No | Launch the full adversarial validation pipeline (6-step async flow) |
| GET | /validations | No | List all past validation runs ordered by creation date descending |
| GET | /validations/{id} | No | Get a specific validation result with hexagonal scores |
| GET | /validations/{id}/report | No | Get the complete stored audit report object |

#### Market Data — `/api/v1/market`

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | /market/quote/{ticker} | No | Fetch live spot price, HV21, implied volatility for any ticker |

#### Infrastructure

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | /health | No | Liveness probe — returns engine versions and status |

### 7.6 Authentication System

Authentication uses **JSON Web Tokens (JWT)** — a widely-used industry standard for stateless API authentication.

**The complete login flow:**

1. User sends `POST /auth/login` with `{"email": "...", "password": "..."}` in the request body.
2. The backend queries the `users` table for a row where `email` matches.
3. `passlib.context.verify(plain_password, stored_hash)` is called. bcrypt verifies the password against the stored hash without ever reversing or storing the plain text.
4. If the password matches, the backend calls `jwt.encode({"sub": user.id, "exp": now + 7days}, SECRET_KEY)` and returns the encoded token.
5. The frontend stores this token (typically in memory or localStorage) and includes it in every subsequent request as the HTTP header: `Authorization: Bearer eyJhbGc...`
6. For protected endpoints, the `get_current_user` FastAPI dependency extracts and decodes the token. If it is invalid, expired, or missing, the dependency raises `HTTPException(401)` and the request is rejected.

Passwords are hashed with bcrypt's work factor of 12 rounds — meaning each password verification requires ~250ms of CPU work, making dictionary attacks impractical.

---

## 8. The Reasoning Engines — The Heart of the Project

These eight Python files in `backend/app/engine/` contain all the quantitative intelligence. Understanding this layer is understanding the project.

### 8.1 AST Security Parser

**File:** `backend/app/engine/ast_parser.py`

**The problem it solves:** Users can upload arbitrary Python code. Executing untrusted code directly would allow attackers to: read files from the server, make network requests, spawn processes, exfiltrate data, or crash the server with infinite loops or memory exhaustion.

**The solution — Static AST Inspection:**

Python's built-in `ast` module parses any Python source code into an Abstract Syntax Tree without executing it. An AST is a tree of "nodes" where each node represents a syntactic element (a function definition, an assignment, a binary operation, a function call, etc.).

The `BlackScholesASTVisitor` class walks every node in this tree before any compilation or execution happens, enforcing three layers of rules:

**Layer 1 — Allowlist of legal syntax node types.** Only these Python constructs are permitted:
- Function definitions (`def`)
- Return statements
- Variable assignments
- Arithmetic operations (+, -, *, /, **, %)
- Comparison operators (<, >, ==, !=, <=, >=)
- Conditional expressions (if/else as ternary)
- Function calls (with restrictions — see Layer 3)
- Import statements (with restrictions — see Layer 2)
- Constants and variable names

Critically excluded: for loops, while loops, class definitions, try/except blocks, with statements, generators, list comprehensions, yield expressions, lambda (only in specific contexts), and raise statements.

**Layer 2 — Import whitelist.** Only these modules may be imported: `math`, `scipy`, `scipy.stats`, `numpy`, `typing`. Any attempt to import `os`, `sys`, `subprocess`, `socket`, `pathlib`, `shutil`, `pickle`, or any other module immediately raises `ASTSecurityError`.

**Layer 3 — Prohibited attribute blocklist.** Any attribute access to these names is rejected: `__class__`, `__subclasses__`, `__globals__`, `__code__`, `__builtins__`, `__import__`, `eval`, `exec`, `subprocess`, `socket`, `system`, `popen`, `os`, `__bases__`, `__mro__`, `__init__`, `__dict__`, `__module__`, `__getattribute__`.

**Parameter mapping:** After security validation passes, the parser extracts the function name and intelligently maps parameter names to canonical roles using a flexible synonym mapping:

- Parameters named S, spot, spot_price, or price → mapped to canonical "spot"
- Parameters named K, strike, or strike_price → mapped to "strike"
- Parameters named T, maturity, tenor, time_to_maturity, or time → mapped to "maturity"
- Parameters named r, rate, risk_free_rate, or rf → mapped to "rate"
- Parameters named vol, sigma, volatility, or v → mapped to "volatility"

This allows diverse naming conventions to work correctly without requiring users to use specific variable names.

### 8.2 Sandboxed Model Evaluator

**File:** `backend/app/engine/sandbox.py`

**The problem it solves:** Static AST inspection catches syntactic threats, but some exploits only manifest at runtime. The sandbox adds a second layer by restricting the execution environment itself, not just the code's syntax.

**Restricted globals execution:**

Instead of calling Python's `exec(code)` with the full global namespace (which includes access to all built-in functions and the module system), the sandbox constructs a severely restricted `__builtins__` dictionary:

```python
safe_globals = {
    "__builtins__": {
        "__import__": safe_import,  # Custom import that only allows math/scipy/numpy
        "abs": abs,
        "min": min,
        "max": max,
        "pow": pow,
        "range": range,
        "len": len,
        "float": float,
        "int": int,
        "bool": bool,
        "round": round
        # Note: open(), print(), eval(), exec(), __class__, __subclasses__ ALL absent
    },
    "math": math,
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
    "erf": math.erf,
    "pi": math.pi,
    "norm_cdf": lambda x: stats.norm.cdf(x),
    "cdf": lambda x: stats.norm.cdf(x),
}
```

The `safe_import` function intercepts every `import` call at runtime and raises `ImportError` for anything not in `{"math", "scipy", "scipy.stats", "numpy"}`.

**Thread-safe execution with hard timeout:**

```python
def evaluate(code, spot, strike, maturity, rate, volatility, timeout_seconds=5.0):
    eval_fn = SandboxedModelEvaluator.create_executable_callable(code)
    result_holder = {}
    error_holder = {}

    def _worker():
        try:
            result_holder["res"] = eval_fn(spot, strike, maturity, rate, volatility)
        except Exception as e:
            error_holder["err"] = str(e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join(timeout=timeout_seconds)

    if t.is_alive():
        raise RuntimeError(f"Sandboxed model execution timed out after {timeout_seconds}s")
```

The daemon flag ensures the thread does not prevent server shutdown. The 5.0-second timeout kills any execution that runs too long (infinite loops, computationally expensive operations).

**Why this combination works:** Even if a determined attacker somehow crafted code that passes AST inspection, the restricted builtins environment means functions like `open()`, `print()`, and `__import__()` are not available at runtime. And even if somehow a restricted version of `__import__` were exploited, the 5-second timeout would kill any complex attack chain before it could complete meaningful harm.

### 8.3 QuantLib Ground Truth Pricer

**File:** `backend/app/engine/quantlib_pricer.py`

**The role:** Every comparison needs a reference. When FRAGMENT says "your model's price is wrong," it needs an authoritative correct price to compare against. QuantLib's `AnalyticEuropeanEngine` provides that reference — the mathematically exact Black-Scholes-Merton price computed in C++ to floating-point machine precision.

**The pricing pipeline:**

```python
# 1. Set up market data as QuantLib quote handles
spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
rate_handle = ql.YieldTermStructureHandle(ql.FlatForward(today, risk_free_rate, day_count))
vol_handle = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, calendar, volatility, day_count))

# 2. Construct the Black-Scholes-Merton stochastic process
bsm_process = ql.BlackScholesMertonProcess(spot_handle, dividend_handle, rate_handle, vol_handle)

# 3. Define the option contract — European call or put
payoff = ql.PlainVanillaPayoff(ql.Option.Call, strike)
exercise = ql.EuropeanExercise(maturity_date)
option = ql.EuropeanOption(payoff, exercise)

# 4. Attach the analytical pricing engine and compute
option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
price = option.NPV()  # Net Present Value = the fair option price
```

**Greek normalization conventions** used (matching market standard):
- Vega: QuantLib returns per unit volatility change (Δσ=1.0). Divided by 100 to get per 1% volatility point.
- Theta: QuantLib returns annual decay. Divided by 365 to get per-calendar-day decay.
- Rho: QuantLib returns per 100% rate shift. Divided by 100 to get per 1% (100 bps) rate move.

These normalizations ensure the Greeks returned by FRAGMENT match the conventions used by option traders and risk managers in practice.

### 8.4 Adversarial Search Engine — SciPy Differential Evolution

**File:** `backend/app/engine/adversarial_engine.py`

**The problem:** There are infinitely many possible combinations of spot price, volatility, interest rate, and time to maturity. We need to find the specific combination that makes the user's model most wrong. We cannot test all combinations exhaustively — that would take forever.

**The solution — Differential Evolution:**

Differential Evolution (DE) is a global optimization algorithm developed by Storn and Price (1997). It maintains a population of candidate solutions (parameter vectors), iteratively improves them by combining and mutating population members, and converges on the global optimum without requiring gradient information.

DE is specifically chosen over gradient descent because:
1. The pricing error landscape is non-convex — there are local maxima that gradient descent would get stuck at
2. The objective function is not differentiable (it involves calling user-submitted code)
3. DE is deterministic given a random seed, ensuring reproducibility

**The 4-dimensional search space:**

| Dimension | What It Represents | Search Bounds |
|-----------|-------------------|---------------|
| Spot Multiplier | Scale factor applied to base spot price | 0.60× to 1.40× (60% to 140% of base) |
| Volatility Multiplier | Scale factor applied to base volatility | 0.40× to 3.00× (40% to 300% of base) |
| Risk-Free Rate | Absolute rate value | max(0.001, base_rate - 0.04) to base_rate + 0.06 |
| Time to Maturity | Absolute maturity in years | max(0.05, base_maturity × 0.20) to base_maturity × 2.50 |

**The objective function** (what DE is minimizing — negative of what we want to maximize):

```python
def _objective(x):
    spot_mult, vol_mult, rate_val, maturity_val = x

    ql_price = QuantLibPricer.price_european_option(
        spot=base_spot * spot_mult,
        strike=base_strike,   # Strike is always held fixed
        maturity_years=maturity_val,
        risk_free_rate=rate_val,
        volatility=base_volatility * vol_mult,
        ...
    )

    user_price = sandboxed_user_fn(
        spot=base_spot * spot_mult,
        strike=base_strike,
        maturity=maturity_val,
        rate=rate_val,
        volatility=base_volatility * vol_mult
    )

    # Scale-relative error formula
    abs_err = abs(user_price - ql_price)
    scale_floor = max(ql_price, current_spot * 0.005)  # Floor = 0.5% of spot
    return -abs_err / scale_floor  # Negative because DE minimizes, we want to maximize
```

The 0.5% spot floor is critical for correctness. Without it, a deep out-of-the-money option with a theoretical price of $0.001 and a user price of $0.011 would appear to have a 1000% relative error, dominating the search even though the $0.010 absolute error is negligible. The floor anchors all errors relative to spot size.

**Multi-seed statistical confidence:**

```python
seeds = [42, 101, 2024]
seed_results = []
for seed_val in seeds:
    res = optimize.differential_evolution(
        _objective,
        bounds=bounds,
        strategy='best1bin',  # Standard DE strategy
        maxiter=35,           # Maximum evolution generations
        popsize=15,           # Population size (15 × 4 dims = 60 candidates)
        tol=1e-5,
        seed=seed_val
    )
    seed_results.append(res)
```

Running with three different seeds (initial random populations) provides:
1. **Robustness against local optima** — different starting populations may find different breaking points
2. **Statistical confidence bounds** — the standard deviation across seed results creates a 95% confidence interval: `mean ± 1.96 × std`
3. **Stability score** — `max(0, 100 - (std/mean) × 100)` measures how consistent the finding is across seeds. A score of 100 means all seeds found the exact same breaking point.

**Greek drift computation at the worst-case:**

After finding the breaking parameters, the engine uses central finite differences to estimate the user model's sensitivity at those parameters:

```
h_s = max(spot × 0.001, 0.01)   # Perturbation in spot (0.1% minimum)
h_v = max(vol × 0.001, 0.001)   # Perturbation in vol (0.1% minimum)

user_delta = (user(spot + h_s, ...) - user(spot - h_s, ...)) / (2 × h_s)
user_vega  = (user(spot, ..., vol + h_v) - user(spot, ..., vol - h_v)) / (2 × h_v)
```

These are compared to QuantLib's analytical Greeks (computed exactly from the closed-form formula's partial derivatives). Large divergence means the model not only gives wrong prices but also wrong hedging ratios — a critical risk for any trading operation.

**Fragility surface generation:**

The engine additionally computes a 7×7 grid of pricing errors across a Spot × Volatility parameter space:
- Spot axis: 7 points from 70% to 130% of base spot
- Vol axis: 7 points from 50% to 200% of base volatility
- Rate and maturity are held at their base values for this 2D slice

This 49-point error matrix is the data source for the 3D surface visualization on the audit report page.

### 8.5 Fragility Scorer

**File:** `backend/app/engine/fragility_scorer.py`

**The scoring formula:**

The Fragility Index is a weighted composite of three independent signals:

```
Component 1: Base Case Accuracy     weight = 0.25 (25%)
  value = min(rel_base_err × 5, 25)
  rel_base_err = (base_error / max(base_quantlib_price, 0.50)) × 100

Component 2: Adversarial Error      weight = 0.55 (55%)
  value = min(pct_adversarial_error, 100)

Component 3: Greek Drift Penalty    weight = 0.20 (20%)
  value = min(delta_drift × 40 + vega_drift × 50, 30)

Fragility Score = 0.25 × C1 + 0.55 × C2 + 0.20 × C3
```

The 55% weight on adversarial error reflects that stress test behavior is the most important predictor of model risk in real-world conditions. The Greek drift component captures hedging risk that is orthogonal to pure pricing accuracy.

**Classification tiers (SR 11-7 aligned):**

| Score Range | Tier | Regulatory Implication |
|-------------|------|----------------------|
| 0.0 – 15.0 | ROBUST | Approved for automated production use within validated parameter bounds |
| 15.1 – 40.0 | MODERATE | Requires periodic re-validation and enhanced monitoring controls |
| 40.1 – 70.0 | FRAGILE | Restricted use; requires continuous monitoring and human review before trade execution |
| 70.1 – 100.0 | CRITICAL | Not approved for production use; requires fundamental model redesign |

**Dynamic risk attribution:**

```python
vol_sensitivity  = |breaking_vol  - base_vol|  / base_vol
spot_sensitivity = |breaking_spot - base_spot| / base_spot
rate_sensitivity = |breaking_rate - base_rate| / base_rate
total_sensitivity = vol_sensitivity + spot_sensitivity + rate_sensitivity

attr_vol  = (vol_sensitivity  / total_sensitivity) × 100   # e.g., 68%
attr_spot = (spot_sensitivity / total_sensitivity) × 100   # e.g., 22%
attr_rate = (rate_sensitivity / total_sensitivity) × 100   # e.g., 10%
```

These three percentages always sum to exactly 100%, providing an interpretable decomposition of which market factor drove the model's fragility.

**Actionable recommendation generation:**

```python
if fragility_score > 30.0:
    max_safe_vol = round(breaking_vol × 0.85 × 100, 1)
    recommendation = (
        f"Enforce input validation guard: Constrain volatility inputs to sigma <= {max_safe_vol}%. "
        f"Do not deploy for unhedged long-tenor options without continuous delta-gamma rebalancing."
    )
else:
    recommendation = (
        "Model passed adversarial validation search. Safe for production automated option pricing "
        "within standard volatility bounds."
    )
```

The 85% threshold on the breaking volatility creates a safety margin below the identified failure point.

### 8.6 Assumption Extraction Engine

**File:** `backend/app/engine/assumption_engine.py`

**The core insight:** A model's mathematical assumptions are implicit in what the code does and does not do. The BSM formula assumes constant volatility because the sigma parameter is passed unchanged to the d1/d2 computation. Proving this requires analyzing code structure statically.

**The five assumption categories checked:**

**1. Volatility Dynamics** — Is the volatility constant or state-dependent?
- Evidence for constant vol: No AST assignment nodes that modify sigma/vol variables using spot S or strike K values
- Evidence for local vol skew: An assignment node exists where the target variable name contains "vol" or "sigma" and the right-hand side AST dump contains references to spot or strike

**2. Interest Rate Dynamics** — Is the rate constant or does the model handle multiple rates?
- Evidence for dual rate: Function parameter names include "q", "dividend", "rf", or "foreign_rate"
- Evidence for constant rate: Single rate parameter "r" passed directly to discount factor math.exp(-r*T)

**3. Asset Return Distribution** — What distributional assumption is made?
- Evidence for lognormal (GBM): AST contains a Name node with id "erf", "norm_cdf", "cdf", or "norm" — these are the Gaussian CDF functions used in the Black-Scholes d1/d2 formula

**4. Numerical Stability (Boundary Guards)** — Are there protections against division by zero?
- Evidence for guards: AST Call nodes to `max()` function where the arguments include references to maturity T or volatility sigma (guarding against T→0 and σ→0 singularities)
- Evidence for unguarded singularities: No such max() calls found around denominator expressions

**5. Exercise Structure** — Is the option European or American?
- Always reported as European for closed-form BSM implementations (the closed form is only valid for European exercise)

Each assumption is returned with a `confidence` score (0.0 to 1.0) reflecting how definitively the AST pattern supports the conclusion.

### 8.7 Model Expectation Suite

**File:** `backend/app/engine/expectations.py`

**The philosophy:** This module implements a Great Expectations-style formal verification approach for option pricing. Rather than asking "does this model match some reference?", it asks "does this model satisfy mathematical contracts that all correct pricing models must satisfy?"

The six assertions are derived from fundamental option theory, not from empirical data. They hold regardless of which specific pricing model is used.

**Assertion 1 — Price Non-Negativity**
```
user_price >= 0.0
```
Rationale: An option grants a right, never an obligation. The worst outcome for the holder is that they do not exercise it, meaning they lose nothing beyond the premium paid. Therefore no option can have a negative value.

**Assertion 2 — No-Arbitrage Upper Bound (Call)**
```
call_price <= spot_price (with 0.1% tolerance)
```
Rationale: If a call option cost more than the underlying stock itself, you could buy the stock directly and sell the call for a risk-free profit (arbitrage). This cannot persist in any efficient market.

**Assertion 3 — No-Arbitrage Upper Bound (Put)**
```
put_price <= strike × exp(-rate × maturity) (with 0.1% tolerance)
```
Rationale: The maximum a put pays is the strike price if the underlying falls to zero. The present value of that maximum payment is K × e^(-rT). If the put cost more, you would hold cash (lend at risk-free rate) and exercise the put at expiry for a guaranteed profit.

**Assertion 4 — QuantLib Benchmark Alignment**
```
|user_price - quantlib_price| / max(quantlib_price, 0.50) <= 1.5%
```
This is the only empirical assertion — it compares against the QuantLib reference at the submitted base-case parameters. The 0.5 floor prevents deep OTM options from creating artificially high percentage errors.

**Assertion 5 — Delta Bounds**
```
Call: 0.0 <= delta <= 1.0
Put:  -1.0 <= delta <= 0.0
```
Rationale: Delta represents the probability-adjusted hedge ratio. A call's value increases by at most $1 for every $1 increase in spot (when deep in-the-money), and by at least $0 (when deep out-of-the-money). Put deltas are the mirror image.

**Assertion 6 — Gamma Non-Negativity (Convexity)**
```
gamma >= -0.00001 (small tolerance for floating-point precision)
```
Rationale: Option value is a convex function of the underlying price. Gamma, the second derivative of option price with respect to spot, must be non-negative. Negative gamma would imply a non-convex relationship — which would itself create arbitrage opportunities.

**Assertion 7 — Put-Call Parity**
The theoretical call-put differential is computed and reported (not a pass/fail assertion, but an informational check): `C - P = S - K × e^(-rT)`.

---

## 9. AI Services

### 9.1 OpenRouter Executive Report Generator

**File:** `backend/app/services/report_ai.py` — `generate_executive_summary()`

**What OpenRouter is:** OpenRouter (openrouter.ai) is an AI API gateway that provides unified access to over 100 different language models through a single OpenAI-compatible REST API. Instead of managing separate API keys and SDKs for Google Gemini, Anthropic Claude, OpenAI GPT, and others, you use one endpoint and switch models by changing a string.

**The default model — google/gemini-2.5-flash:** This is Google's fastest and most cost-efficient Gemini model. At approximately $0.001 per validation report, it is extremely affordable. The model produces high-quality structured prose with strong mathematical and regulatory domain knowledge.

**System prompt (persona establishment):**
```
"You are a Senior Model Risk Manager and Quantitative Auditor 
specializing in Federal Reserve SR 11-7 governance guidelines. 
Synthesize executive-level, mathematically sound model risk reviews."
```

**User prompt (what gets sent per validation):**
The prompt includes: the model name, fragility score and tier, the breaking scenario parameters (perturbed spot, vol, rate, user price, QuantLib price, dollar error, percentage error), and the list of extracted model assumptions.

The prompt requests a four-section report:
1. **Executive Overview** — High-level summary of model performance and fragility classification
2. **Mathematical Assumption Breakdown** — Analysis of why specific assumptions (e.g., constant volatility dσ/dt=0) fail under stress
3. **Adversarial Worst-Case Analysis** — Technical explanation of how the breaking parameter set degrades pricing accuracy
4. **SR 11-7 Regulatory Compliance Audit** — Specific governance recommendations, monitoring requirements, and operational boundaries

**API call parameters:**
- `max_tokens: 800` — Enough for a comprehensive but concise report
- `temperature: 0.3` — Low randomness ensures consistent, professional tone without creativity

**Graceful degradation:** The `get_api_key()` method checks both the environment variable and the Settings object. If neither yields a key, the system automatically calls `_generate_template_summary()` instead — a deterministic function that fills a prose template with the numerical results. The platform works fully without an API key.

### 9.2 Prompt-to-Model Synthesizer

**File:** `backend/app/services/report_ai.py` — `synthesize_model_from_prompt()`

**What it enables:** A user who knows the Black-Scholes formula from a textbook but cannot write Python code can type: "European put option using Black-Scholes with dividend yield" and receive a correct, sandboxable Python function automatically.

**The AI instruction:**
```
"You are a Quantitative Software Engineer. Convert natural language descriptions, 
formulas, or mathematical requirements into executable Python functions for option pricing. 
The function MUST take exactly 5 parameters: S (spot), K (strike), T (maturity in years), 
r (risk-free rate), sigma (volatility). Only use standard Python math or scipy.stats. 
Return valid JSON with keys: name, description, code."
```

Low temperature (0.2) is used to ensure the generated Python code is deterministic and syntactically correct — this is a code generation task where consistency is more important than creativity.

**Security after generation:** The AI-generated code is passed through the same AST security parser and sandbox as any user-submitted code. Even AI-generated code must pass all security checks before execution.

**Keyword-based fallback without API:**
- Prompt contains "put" → returns pre-written Black-Scholes European Put
- Prompt contains "garman" or "fx" or "currency" → returns Garman-Kohlhagen FX model
- Otherwise → returns Black-Scholes European Call

### 9.3 6-Axis Hexagonal Radar Scorer

**File:** `backend/app/services/report_ai.py` — `compute_hexagonal_scores()`

Six completely independent risk dimension scores are computed from the adversarial validation results:

**Axis 1 — Conceptual Soundness**
```
score = 95.0  if AST boundary guards found in code
      = max(30.0, round(90.0 - fragility_score × 0.4, 1))  otherwise
```
Measures whether the model's code structure reflects sound quantitative engineering practices.

**Axis 2 — Numerical Stability**
```
score = max(10, min(100, 100 - min(pct_error × 1.8, 85)))
```
Measures whether the model produces well-behaved numerical outputs under stress, without overflow, underflow, or NaN propagation.

**Axis 3 — Parameter Robustness**
```
score = max(10, min(100, optimizer_stability - fragility_score × 0.3))
```
`optimizer_stability` comes from the multi-seed DE search — it measures how consistently the adversarial search finds the same breaking point across different random initializations. High robustness means the model fails consistently (reproducibly), which is a prerequisite for reliable risk management.

**Axis 4 — Boundary Condition Safety**
```
score = max(10, min(100, 98 - min(pct_error × 1.4, 75)))
```
Specifically measures behavior near degenerate parameter regions: zero volatility (σ→0), near-expiry options (T→0), and deep out-of-the-money options.

**Axis 5 — Greek Fidelity**
```
score = max(10, min(100, 100 - (delta_drift × 50 + vega_drift × 60)))
```
Measures the accuracy of hedging sensitivities. delta_drift and vega_drift are the absolute differences between the user model's finite-difference Greeks and QuantLib's analytical Greeks at the adversarial worst-case parameters. A model that prices correctly but hedges incorrectly is still dangerous for trading operations.

**Axis 6 — Benchmark Alignment**
```
score = max(10, min(100, 100 - min(abs_error × 8 + pct_error × 1.2, 85)))
```
Measures how closely the model matches QuantLib under the submitted base-case parameters — not under stress, but under "normal" market conditions. This tests basic implementation correctness.

---

## 10. Market Data Service

**File:** `backend/app/services/yfinance_provider.py`

**Purpose:** Fetch real market data to pre-populate the validation form with realistic conditions, rather than requiring users to look up market data themselves.

**What is fetched for each ticker:**

The provider calls `yf.Ticker(symbol).history(period="1mo")` to get one month of daily OHLCV data.

**Spot Price:** The last closing price in the history DataFrame.

**21-Day Historical Volatility (HV21):**
```python
log_returns = log(Close[t] / Close[t-1])  for all t
daily_vol = std(log_returns, ddof=1)       # Sample std dev (unbiased)
HV21 = daily_vol × sqrt(252)               # Annualized using 252 trading days
```
This is the realized volatility calculation used by professional options desks. The ddof=1 (sample standard deviation) is used rather than ddof=0 (population standard deviation) for unbiased estimation when sample size is finite.

**Implied Volatility:**
```python
options_dates = ticker.options            # Available expiry dates
chain = ticker.option_chain(options_dates[0])  # Nearest expiry
calls = chain.calls
atm_call = calls.sort_values(|calls['strike'] - spot|).iloc[0]  # Nearest to ATM
implied_vol = atm_call['impliedVolatility']
```
If the option chain is unavailable (market closed, data delayed), the fallback is `HV21 × 1.10` — applying a 10% volatility risk premium above historical volatility, reflecting that option sellers demand compensation for bearing volatility uncertainty.

**Risk-Free Rate:** Hard-coded at 5.25% — the approximate U.S. 10-Year Treasury yield as of mid-2026. Updated manually when the benchmark rate changes significantly.

**Fallback snapshot:** If Yahoo Finance is unreachable (network error, API rate limiting, market closed), the provider returns pre-defined reasonable values for five supported tickers (AAPL: $225.50, SPY: $545.20, NVDA: $120.80, TSLA: $210.40, MSFT: $440.30) and flags the response with `"status": "FALLBACK_SIMULATED"`.

---

## 11. Complete Validation Data Flow — Step by Step

This section traces exactly what happens from the moment a user clicks "Run Adversarial Validation" to the moment the audit report appears on screen.

**Step 1 — User action in /editor:**
User has selected a stored model (or written new code in the Monaco editor), set market parameters (spot=$100, strike=$100, vol=20%, rate=5%, maturity=1yr, option_type=call), and clicked the Run button.

**Step 2 — Frontend POST /api/v1/validations:**
```json
{
  "model_id": "3f4a-...",
  "spot_price": 100.0,
  "strike_price": 100.0,
  "volatility": 0.20,
  "risk_free_rate": 0.05,
  "time_to_maturity": 1.0,
  "dividend_yield": 0.0,
  "option_type": "call"
}
```

**Step 3 — Backend database lookup:**
Queries `financial_models` for the model row. Loads the Python source code string and all associated Assumption records.

**Step 4 — Adversarial Engine (runs in asyncio thread pool, non-blocking):**

4a. AST Parser runs `parse_and_validate_model_code(model.code)` → Returns function name and parameter mapping, OR raises ASTSecurityError with detailed violation list.

4b. Sandbox creates a restricted callable via `SandboxedModelEvaluator.create_executable_callable(model.code)` → Returns a typed function `(spot, strike, maturity, rate, vol) -> float`.

4c. QuantLib baseline: `QuantLibPricer.price_european_option(base params)` → Returns `{"price": 10.45, "greeks": {"delta": 0.636, "gamma": 0.019, "vega": 0.375, "theta": -0.012, "rho": 0.532}}`.

4d. User model baseline: `user_fn(base_spot, base_strike, base_maturity, base_rate, base_vol)` → Returns `10.45` (or close to it for a correct model).

4e. SciPy DE search: `differential_evolution(objective, bounds, seeds=[42,101,2024], maxiter=35, popsize=15)` → Runs approximately 35 × 60 = 2,100 objective function evaluations per seed, for ~6,300 total evaluations, each calling both QuantLib and the user model. Finds worst-case parameters: e.g., spot=$140, vol=60%, rate=5%, maturity=0.25yr.

4f. QuantLib at worst-case: Computes exact price at the breaking parameters. e.g., $43.87.

4g. User model at worst-case: e.g., $41.20.

4h. Greek drift: Finite-difference delta and vega for user model at worst-case parameters. Compares to QuantLib analytical Greeks.

4i. Fragility surface: 7×7 = 49 (QuantLib + user model) evaluations to build the error grid.

4j. Returns full result dict: `{base_metrics, breaking_parameters, greek_drifts, fragility_surface}`.

**Step 5 — Fragility Scorer:**
Computes: fragility_score=35.2, classification="MODERATE", risk_attribution={vol:68%, spot:22%, rate:10%}, actionable_recommendation="...".

**Step 6 — Hexagonal Radar Scorer:**
Computes 6 axis scores: conceptual=86, stability=79, robustness=73, boundary=75, greek_fidelity=82, alignment=81.

**Step 7 — Expectation Suite:**
Runs 7 assertions, returns list of pass/fail results with detail strings.

**Step 8 — Database commit:**
Creates a `ValidationRun` row with all results. Also creates a `Report` row (see Step 9). `await db.commit()`.

**Step 9 — AI Executive Summary:**
Async `httpx.AsyncClient().post("https://openrouter.ai/api/v1/chat/completions", ...)` sends the prompt to Gemini. Response is stored in the Report row's `executive_summary` column. If no API key, deterministic template is used instead.

**Step 10 — Response to frontend:**
The full `ValidationResponse` Pydantic model is serialized to JSON and returned with HTTP 201 Created status. Frontend receives the validation ID.

**Step 11 — Frontend redirect:**
`router.push("/validations/" + response.id)` navigates to the audit report page.

**Step 12 — Audit report renders:**
`GET /api/v1/validations/{id}` fetches the stored results. React components render all sections in parallel.

---

## 12. Frontend — How It Is Built

### 12.1 Stack and Configuration

The frontend is Next.js 14 using the App Router. All route components are React Server Components by default, with client-side interactivity added via the `"use client"` directive where needed (3D scenes, interactive forms, charts).

TypeScript is configured with strict mode in `tsconfig.json` — `strict: true` enables all strictness flags including null checks, implicit any detection, and strict function types.

**next.config.js** enables transpilation of Three.js (an ES module) for compatibility with the CommonJS module system used by Next.js's webpack bundler.

### 12.2 Routing Structure

Next.js App Router maps file system paths to URL routes automatically:

| File | URL | Rendering Mode |
|------|-----|----------------|
| src/app/page.tsx | / | Client (3D WebGL) |
| src/app/dashboard/page.tsx | /dashboard | Client (data fetching) |
| src/app/editor/page.tsx | /editor | Client (Monaco, forms) |
| src/app/market/page.tsx | /market | Client (auto-refresh) |
| src/app/validations/[id]/page.tsx | /validations/:id | Client (3D, chart) |

The `[id]` square bracket syntax creates a dynamic segment. When the user visits `/validations/abc-123`, the page component receives `params: { id: "abc-123" }` and uses that ID to fetch the specific validation run from the API.

**src/app/layout.tsx** is the root layout — it wraps every page with the common HTML shell, imports the Inter font from Google Fonts, sets the page title and metadata, and renders the global CSS.

### 12.3 Global Design System

**File:** `src/app/globals.css`

The design system is built on CSS custom properties:

```css
:root {
  --bg-primary:    #030712;        /* Deep space black — main page background */
  --bg-secondary:  #0a0f1e;        /* Dark navy — cards and panels */
  --bg-glass:      rgba(15,20,40,0.7); /* Frosted glass base color */
  --accent-cyan:   #06b6d4;        /* Primary interactive accent */
  --accent-violet: #7c3aed;        /* Secondary accent (gradients, badges) */
  --accent-amber:  #f59e0b;        /* Warning state accent */
  --text-primary:  #f8fafc;        /* Near-white body text */
  --text-muted:    #94a3b8;        /* Subdued secondary text */
}
```

**Typography rules strictly enforced:**
- `Inter` (Google Fonts sans-serif) for all UI text: headings, labels, buttons, badges, navigation, body text, descriptions, status messages, error states, loading states, tabs, inputs
- `JetBrains Mono` ONLY for: Python code inside Monaco Editor, raw floating-point numbers (e.g., $104.25, 21.4%), and mathematical identifiers in formulas

This distinction ensures the interface feels natural and human rather than technical and robotic.

**Glassmorphism cards:**
```css
.glass-card {
  background: rgba(15, 20, 40, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(6, 182, 212, 0.15);
  border-radius: 16px;
}
```

**Micro-animations:**
- `transition: all 0.2s ease` on interactive elements for instant hover feedback
- `@keyframes pulse-glow` on accent elements for a living, breathing quality
- `@keyframes fade-in` on content blocks for smooth page load experience

### 12.4 Landing Page — page.tsx (Route: /)

The public-facing showcase designed to immediately communicate the platform's sophistication.

**Sections in order:**

**Navigation bar** — Fixed-position top bar with FRAGMENT logo (geometric icon + wordmark), navigation links to Dashboard, Editor, Market, and a Sign In button. Uses `backdrop-filter: blur` so content scrolls behind a frosted navbar.

**Hero section** — Full viewport height. The HeroScene3D WebGL canvas fills the background with animated stochastic GBM paths. Centered content: headline "Adversarial Validation for Quantitative Models", subheadline explaining the value proposition, two CTA buttons (Start Validating → /dashboard, View Architecture → scrolls to methodology section).

**Stats bar** — Three animated counters displayed in a horizontal row showing platform capabilities (e.g., "19 Tests Passing", "5 API Endpoints", "4 Fragility Tiers").

**Live 3D Fragility Surface showcase** — The FragilitySurface3D component rendered in a prominent card with Auto-Rotate and Wireframe toggle buttons. This is the most technically impressive visual on the page — a live rotating 3D mesh.

**Methodology section** — Three-column grid with icons and prose: (1) Submit Model Code — write Python or use AI synthesis, (2) Adversarial Search — SciPy DE finds worst-case market conditions, (3) Audit Report — fragility score, surface, and SR 11-7 governance report.

**Capabilities section** — Six feature cards in a 3-column grid: Adversarial Search Engine, QuantLib Ground Truth, SR 11-7 Governance, Sandbox Isolation, Live Market Data, AI Executive Reports.

**Risk Radar section** — A mock HexagonalRadarChart demonstrating the 6-axis scoring system with a prose explanation of what each axis measures.

**Submission modes section** — Four cards explaining how models enter the system: Code Editor, AI Formula Synthesizer, File Upload (.py file drag-and-drop), Preset Templates (six standard model choices).

**CTA section** — "Ready to Validate Your Model?" with a final button to /dashboard.

### 12.5 Dashboard — dashboard/page.tsx (Route: /dashboard)

The operational model inventory and management hub.

On mount, `GET /api/v1/models` is called. If the response is empty (first run), auto-seeding is triggered which populates the database with four demo models: Black-Scholes European Call, Bachelier Normal Model, Garman-Kohlhagen FX Option, and Black-Scholes Put with Boundary Guards.

**Interactive features:**
- Real-time search filtering: type into the search bar and the displayed model cards filter instantly without any API call (client-side filtering of already-fetched data)
- Asset class tabs: All / Equity Options / Foreign Exchange / Fixed Income / Rates
- Grid view: 3-column card grid where each card shows model name, description, asset class badge (color-coded), version tag, creation date, number of validations run, and the last fragility score with a tier chip (green=ROBUST, yellow=MODERATE, orange=FRAGILE, red=CRITICAL)
- Table view: Compact list view with the same information in a sortable table format
- Run Validation button on each card: navigates to /editor?model_id=... with the model pre-selected
- Delete button: removes the model with a confirmation dialog, then refreshes the list
- New Model button (top right): navigates to /editor with a blank editor

### 12.6 Model Sandbox Editor — editor/page.tsx (Route: /editor)

The primary workspace — the most interactive and complex page in the application.

**Four model ingestion modes (tabbed interface):**

**Tab 1 — Code Editor:**
The Monaco Editor component occupies the main panel. It is configured for Python language mode with:
- Full syntax highlighting
- Bracket and quote auto-matching
- Line numbers with cursor position indicator
- Minimap (collapsed for space efficiency)
- VS Code dark theme matching the application color scheme

**Tab 2 — AI Formula Synthesizer:**
A textarea where users type in natural language (e.g., "European call option using Black-Scholes with continuous dividend yield") or paste a LaTeX formula. On clicking Synthesize, `POST /api/v1/models/synthesize` is called. A loading spinner shows while the AI generates the code. On success, the generated Python function is inserted into the Monaco Editor and the tab switches to Code Editor for review and editing before submission.

**Tab 3 — File Upload:**
A drag-and-drop zone. Users can drag a .py file from their desktop or click to browse. The file contents are read client-side using the FileReader API and inserted into the Monaco Editor.

**Tab 4 — Preset Templates:**
Six pre-written, correct, and sandbox-safe implementations that load instantly:
- Black-Scholes European Call (standard BSM)
- Black-Scholes European Put
- Garman-Kohlhagen FX Option (for currency options)
- Bachelier Normal Model (linear rather than log-normal returns)
- BSM Call with Zero-Vol and Zero-Tenor Guards (robust edge-case handling)
- BSM with Simple Local Volatility Approximation

**Market parameters form:**
Below the editor, a structured form collects: Spot Price (dollar amount), Strike Price (dollar amount), Time to Maturity (decimal years, e.g., 0.25 for 3 months), Risk-Free Rate (percentage, converted to decimal before sending), Implied Volatility (percentage), Dividend Yield (percentage), Option Type (Call or Put radio).

**Live ticker search:**
A small input field lets users type a ticker symbol (e.g., AAPL). On pressing Enter or clicking Fetch, `GET /api/v1/market/quote/AAPL` is called and the returned spot price and implied volatility are auto-populated into the form. A status badge shows "LIVE" or "SIMULATED" based on the data source.

**Assumption display panel:**
After the model code is submitted and validated, `POST /api/v1/models/{id}/assumptions` is called. The returned assumptions are displayed in an expandable accordion list, each showing:
- Assumption name
- Category badge
- Mathematical form in a code block
- Description of the AST evidence found
- Confidence percentage
- Is Violated in Stress indicator (red warning if true)

**Validation launch:**
The "Run Adversarial Validation" button (prominent, accent-colored, full-width) sends `POST /api/v1/validations` with the model ID and all parameter form values. A progress stepper shows the pipeline steps in real time. On success, the browser navigates to `/validations/{new_id}`.

### 12.7 Live Market Monitor — market/page.tsx (Route: /market)

A real-time dashboard showing live market conditions for options pricing.

**Ticker navigation:**
Five quick-select tabs (AAPL, SPY, NVDA, TSLA, MSFT) and a free-form search input. Selecting any tab or submitting a ticker immediately calls `GET /api/v1/market/quote/{ticker}` and renders the results.

**Data display cards:**
Four metric cards arranged in a 2×2 grid:
- Spot Price — large number, source badge (DELAYED or SIMULATED), timestamp
- Historical Volatility (21-day annualized) — percentage with a description of calculation methodology
- Implied Volatility (30-day ATM) — percentage from option chain or estimated
- Risk-Free Rate — the benchmark Treasury rate

**Volatility regime identification:**
A color-coded banner below the metrics identifies the current market regime based on the implied volatility:
- Green (<15%): Low Volatility — calm market, option premiums are depressed
- Cyan (15-30%): Normal Volatility — standard conditions
- Amber (30-50%): Elevated Volatility — heightened uncertainty, option premiums elevated
- Red (>50%): Extreme Volatility — crisis conditions, BSM assumptions most severely violated

**Auto-refresh:** A 60-second countdown timer triggers automatic data refresh. A manual Refresh button is also available.

**Error handling:** If Yahoo Finance is unreachable, the page shows a clearly labeled "SIMULATED" status badge and uses the fallback snapshot values, so the page is always usable even without network access.

### 12.8 Validation Audit Report — validations/[id]/page.tsx (Route: /validations/:id)

The complete audit output page — the culmination of the entire pipeline.

On mount: `GET /api/v1/validations/{id}` fetches the stored validation run with hexagonal scores. `GET /api/v1/validations/{id}/report` fetches the full report object with executive summary and SR 11-7 compliance data.

**Page sections in order:**

**1. Header** — Model name (large, primary heading), validation timestamp, fragility tier badge (color-coded chip: ROBUST=emerald, MODERATE=amber, FRAGILE=orange, CRITICAL=red), the numerical fragility score displayed prominently.

**2. Action bar** — Export Report button (downloads the full report_data JSON as a timestamped file), Re-run Validation button (navigates back to /editor with the model pre-loaded).

**3. 6-Axis Health Radar** — `HexagonalRadarChart` component rendered in a 50% width card. Below the chart, each axis is listed with its score and a brief description of what it measures.

**4. Risk Attribution** — Three horizontal progress bars showing the percentage attribution to: Volatility Regime Risk, Spot Tail Convexity, Interest Rate Sensitivity. Colors reflect severity (higher attribution = more prominent color).

**5. Worst-Case Breaking Scenario** — A structured card showing the adversarial parameters that caused the maximum error: perturbed spot price, perturbed volatility (%), perturbed interest rate (%), time to maturity. Below this: user model price at breaking point, QuantLib analytical price at breaking point, absolute dollar error, percentage error. Below this: optimizer stability score, 95% confidence interval, the three seed values evaluated.

**6. Statistical Reproducibility** — A technical detail card showing: strategy (best1bin), maxiter (35), popsize (15), QuantLib version (1.43), SciPy version, NumPy version, Python version. This section exists to support regulatory audit requirements for computational reproducibility.

**7. Expectation Suite Results** — A table with seven rows, each showing: expectation name, success icon (green checkmark or red X), and the detail string with observed values.

**8. Fragility Surface (3D)** — The `FragilitySurface3D` component rendered in a full-width card with WebGL. The 7×7 error matrix from the validation run is passed as a prop and rendered as an interactive 3D mesh. Auto-rotate is enabled by default.

**9. Executive Narrative** — The AI-generated or template-generated prose report displayed in a styled text block with the four sections: Executive Overview, Mathematical Assumption Breakdown, Adversarial Worst-Case Analysis, SR 11-7 Regulatory Compliance Audit.

**10. SR 11-7 Governance Assessment** — A structured checklist card showing: Conceptual Soundness (PASS/WARNING), Ongoing Monitoring (REQUIRED), Sensitivity Analysis (PASSED — Differential Evolution Search), Actionable Recommendation (the specific operational boundary recommendation from the fragility scorer).

**11. Extracted Assumptions** — An expandable accordion list of all code-derived mathematical assumptions from the assumption engine. Each row shows: assumption name, category badge, mathematical form, evidence description, confidence percentage, stress test status.

---

## 13. 3D Visual Components

### 13.1 HeroScene3D — Stochastic GBM Particle Field

**File:** `src/components/HeroScene3D.tsx`

**What the user sees:** Multiple glowing, animated colored lines flowing across the screen — each one a simulated stock price path over time. The paths vary in steepness and curvature, showing the natural randomness of financial market trajectories. The scene slowly pans to give a sense of depth and motion.

**Mathematical basis:** Each path simulates Geometric Brownian Motion — the stochastic differential equation:

```
dS = μS·dt + σS·dW

Discretized for simulation:
S[t+1] = S[t] × exp((μ - 0.5σ²)·dt + σ·√dt·Z)
where Z ~ Normal(0,1)
```

This is the same process that underlies the Black-Scholes model, making the visual mathematically meaningful rather than purely decorative.

**Three.js implementation:**
- `WebGLRenderer({ antialias: true, alpha: true })` — hardware-accelerated 3D with transparent background
- `PerspectiveCamera(75, aspect, 0.1, 1000)` — 75-degree field of view
- `BufferGeometry.setFromPoints(points)` — each GBM path is a series of 3D points converted to a geometry
- `LineBasicMaterial({ color, transparent: true, opacity })` — glowing colored lines
- `requestAnimationFrame` loop calling `camera.position.z -= 0.005` for the slow forward pan

The component mounts by creating a full-viewport canvas element and unmounts cleanly by removing event listeners and disposing all Three.js resources to prevent memory leaks.

### 13.2 FragilitySurface3D — WebGL Error Topology

**File:** `src/components/FragilitySurface3D.tsx`

**What the user sees:** An interactive 3D mountain-like surface where the height at each point represents how wrong the user's model is at that combination of spot price and volatility. Hovering over peaks (where the model is most wrong) and valleys (where it is accurate) provides intuitive spatial understanding of the error landscape. Red floating spheres mark the most dangerous regions.

**Mathematical meaning:** The surface is literally the adversarial engine's fragility surface — a 2D slice of the pricing error function `ε(S, σ) = |user_price(S, σ) - ql_price(S, σ)|` across a 7×7 grid.

**Three.js mesh construction:**

```typescript
// For a 7×7 grid of error values:
const positions = new Float32Array(49 * 3);  // 49 vertices, xyz each
for (let i = 0; i < 7; i++) {           // volatility axis
  for (let j = 0; j < 7; j++) {         // spot axis
    const idx = (i * 7 + j) * 3;
    positions[idx]     = (j / 6) * 4 - 2;              // X: spot axis
    positions[idx + 1] = errorMatrix[i][j] * heightScale; // Y: error height
    positions[idx + 2] = (i / 6) * 4 - 2;              // Z: vol axis
  }
}

// Build triangle faces connecting adjacent grid cells:
// Each 1×1 cell becomes 2 triangles (6 index values)
const indices = [];
for (let i = 0; i < 6; i++) {
  for (let j = 0; j < 6; j++) {
    // Triangle 1: top-left, bottom-left, bottom-right
    indices.push(i*7+j, (i+1)*7+j, (i+1)*7+(j+1));
    // Triangle 2: top-left, bottom-right, top-right
    indices.push(i*7+j, (i+1)*7+(j+1), i*7+(j+1));
  }
}
```

**Color gradient:** Each vertex is colored based on its error height using a linear interpolation from green (low error, safe) through yellow (moderate) to red (high error, dangerous). This is computed as a per-vertex `vertexColors` array on the geometry.

**Auto-rotate:** A quaternion rotation applied each frame:
```typescript
const rotationAxis = new THREE.Vector3(0, 1, 0.1).normalize();
mesh.quaternion.premultiply(
  new THREE.Quaternion().setFromAxisAngle(rotationAxis, 0.005)
);
```

**Wireframe mode:** Toggles between `MeshBasicMaterial({ vertexColors: true, side: DoubleSide })` and `MeshBasicMaterial({ wireframe: true, color: "#06b6d4" })`.

**Risk spheres:** Local maxima in the 7×7 error grid are identified and rendered as `SphereGeometry(0.05, 8, 8)` with `MeshBasicMaterial({ color: "#ef4444" })` floating 0.2 units above their corresponding surface position. A pulsing scale animation is applied to each sphere in the render loop.

### 13.3 HexagonalRadarChart — 6-Axis Risk Radar

**File:** `src/components/HexagonalRadarChart.tsx`

**What the user sees:** A hexagonal web chart where six axes radiate from the center, one per risk dimension. The filled polygon shows the model's scores — larger and more symmetrical is better, smaller or lopsided indicates specific weaknesses.

**Chart.js radar configuration:**

```typescript
const chartConfig = {
  type: "radar",
  data: {
    labels: [
      "Conceptual Soundness",
      "Numerical Stability",
      "Parameter Robustness",
      "Boundary Safety",
      "Greek Fidelity",
      "Benchmark Alignment"
    ],
    datasets: [{
      data: [scores.conceptual, scores.stability, scores.robustness,
             scores.boundary, scores.greek_fidelity, scores.alignment],
      fill: true,
      backgroundColor: "rgba(6, 182, 212, 0.3)",   // Cyan with 30% opacity
      borderColor: "rgba(6, 182, 212, 0.9)",        // Solid cyan border
      pointBackgroundColor: "rgba(6, 182, 212, 1.0)",
      pointRadius: 4,
    }]
  },
  options: {
    scales: {
      r: {
        min: 0, max: 100,
        ticks: { display: false },
        grid: { color: "rgba(148, 163, 184, 0.2)" },
        pointLabels: {
          font: { family: "Inter", size: 12 },
          color: "#94a3b8"
        }
      }
    },
    plugins: {
      legend: { display: false }
    },
    animation: {
      duration: 800,
      easing: "easeInOutQuad"
    }
  }
};
```

All scores are already clamped to [10, 100] by the scorer, so the minimum shape is never degenerate.

---

## 14. API Keys — What They Are, Where to Get Them, Where to Put Them

### Key 1 — OpenRouter API Key

**Purpose:** Powers two features:
1. AI-generated executive audit reports (4-section regulatory governance narrative)
2. Natural language → Python pricing function synthesis

**Required:** No. Both features gracefully fall back to deterministic alternatives without the key.

**Cost estimate:** Approximately $0.001 per validation report using the default `google/gemini-2.5-flash` model. A $5 credit would last thousands of validation runs.

**How to obtain:**

1. Open a browser and go to `https://openrouter.ai`
2. Click "Sign Up" and create a free account (email verification required)
3. After signing in, navigate to the "Keys" section in the left sidebar
4. Click "Create Key" — give it a name like "FRAGMENT-local"
5. Copy the generated key immediately — it starts with `sk-or-v1-` followed by a long hex string. **This is the only time the full key is shown.**
6. Add billing credit: go to "Credits" and add a minimum of $1 to activate API access
7. Optionally: set a usage limit per month to prevent unexpected charges

**Where to put it:**

Create the file `backend/.env` by copying the template:

```bash
# Windows PowerShell
copy backend\.env.example backend\.env

# macOS/Linux
cp backend/.env.example backend/.env
```

Edit `backend/.env` and fill in your key:

```
# FRAGMENT Environment Configuration
PROJECT_NAME="FRAGMENT - Adversarial Validation Platform"
API_V1_STR="/api/v1"
SECRET_KEY="change-this-to-a-random-64-char-string-in-production"

# Database — SQLite for local dev (no setup needed)
DATABASE_URL="sqlite+aiosqlite:///./fragment.db"
REDIS_URL="redis://localhost:6379/0"

# OpenRouter AI Integration
# Sign up at openrouter.ai and create a key
OPENROUTER_API_KEY="sk-or-v1-your-actual-key-here"
OPENROUTER_MODEL="google/gemini-2.5-flash"
```

**Security rules:**
- The `.env` file is listed in `.gitignore` and will NEVER be committed to the repository
- The key is loaded only server-side by pydantic-settings — it is never sent to the browser
- Do not paste your key into any frontend code, JavaScript file, or any file that might be committed

**Alternative AI models you can use with the same key:**

| OPENROUTER_MODEL value | Provider | Speed | Cost per 1K tokens | Quality |
|------------------------|----------|-------|-------------------|---------|
| google/gemini-2.5-flash | Google | Fast | ~$0.0001 | Excellent |
| google/gemini-2.5-pro | Google | Medium | ~$0.001 | Best |
| anthropic/claude-3.5-sonnet | Anthropic | Medium | ~$0.003 | Best |
| anthropic/claude-3.5-haiku | Anthropic | Fast | ~$0.0008 | Good |
| openai/gpt-4o-mini | OpenAI | Fast | ~$0.0002 | Good |
| meta-llama/llama-3.1-70b-instruct | Meta | Medium | ~$0.0005 | Good (free tier available) |

To use a different model, simply change the `OPENROUTER_MODEL` value in `.env` and restart the backend.

### Other Services — No Keys Required

| Service | How Used | Authentication |
|---------|----------|----------------|
| Yahoo Finance (via yfinance Python library) | Live stock prices and option chain IV | None — free public API (15-min delayed) |
| QuantLib | Analytical option pricing | None — installed as Python package, no network calls |
| SQLite | Local database storage | None — local file (fragment.db) |

---

## 15. Local Development Setup — Start to Finish

Follow these exact steps on a fresh machine to get both the backend and frontend running.

### Prerequisites

Install these if not already installed:
- **Python 3.10 or higher** — verify with `python --version`
- **Node.js 18 or higher** — verify with `node --version`
- **npm 9 or higher** — verify with `npm --version`
- **Git** — verify with `git --version`

On Windows, QuantLib requires Visual C++ build tools to compile. Install from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Step 1 — Clone the Repository

```bash
git clone https://github.com/dathasaiswaroopgudimella-png/Quant-portifolio.git
cd "Quant portifolio"
```

### Step 2 — Backend Setup

```bash
cd backend

# Create a Python virtual environment to isolate dependencies
python -m venv venv

# Activate the virtual environment:
#   Windows PowerShell:
.\venv\Scripts\Activate.ps1
#   Windows Command Prompt:
.\venv\Scripts\activate.bat
#   macOS / Linux:
source venv/bin/activate

# Install all Python dependencies (this may take several minutes for QuantLib)
pip install -r requirements.txt

# Create your local environment file from the template
#   Windows:
copy .env.example .env
#   macOS / Linux:
cp .env.example .env

# Optionally edit .env to add your OpenRouter API key
# Open .env in any text editor and set OPENROUTER_API_KEY

# Start the backend server with auto-reload on code changes
python -m uvicorn app.main:app --reload --port 8000
```

On first run, you will see:
```
INFO:root: Initializing FRAGMENT backend database tables...
INFO:root: FRAGMENT core engine ready.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

The file `backend/fragment.db` is automatically created with all 5 database tables.

**Verify the backend is running:**
Open `http://localhost:8000/health` in your browser. You should see:
```json
{
  "status": "healthy",
  "service": "FRAGMENT Engine",
  "quantlib_version": "1.43",
  "sandbox_isolation": "ACTIVE"
}
```

**Explore the interactive API documentation:**
Open `http://localhost:8000/docs` for the full Swagger UI where you can test every endpoint directly in the browser.

### Step 3 — Frontend Setup

Open a new terminal window (keep the backend terminal running):

```bash
# Navigate to the frontend directory
cd "Quant portifolio/frontend"

# Install all JavaScript dependencies
npm install

# Start the Next.js development server
npm run dev
```

You will see:
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Environments: .env.local
  ✓ Ready in 2.3s
```

### Step 4 — Access the Application

Open `http://localhost:3000` in your browser.

The landing page should appear with:
- Animated 3D GBM particle field in the hero section
- FRAGMENT logo and navigation
- 3D fragility surface demo

The entire application is now running locally.

### Step 5 (Optional) — Run the Test Suite

In the backend directory with the virtual environment activated:

```bash
# Run all 19 tests with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_adversarial_engine.py -v

# Run with coverage report
python -m pytest --cov=app --cov-report=term-missing

# Run only security tests
python -m pytest tests/test_security_sandboxing.py -v
```

Expected output:
```
========================= test session starts =========================
platform win32 -- Python 3.10.x, pytest-9.x.x
collected 19 items

tests/test_adversarial_engine.py .....                          [ 26%]
tests/test_quantitative_edge_cases.py .....                     [ 52%]
tests/test_quantlib_pricer.py ..                                [ 63%]
tests/test_sandbox.py ..                                        [ 73%]
tests/test_security_sandboxing.py .....                         [100%]

========================= 19 passed in 4.03s =========================
```

---

## 16. Docker Deployment

For production-like deployment using Docker and Docker Compose.

### What Docker Provides

Docker packages the application and all its dependencies into isolated containers. This means the exact same containers run identically on your laptop, a teammate's machine, and a cloud server.

Docker Compose orchestrates multiple containers as a single application stack.

### The Service Stack

`docker-compose.yml` defines four services:

**postgres** — PostgreSQL 15 database (replaces SQLite in production). Includes health check, persistent volume, and auto-setup of the `fragment_db` database.

**redis** — Redis 7 in-memory cache server. Currently defined for future use (caching validation results, session management). Includes health check.

**backend** — FastAPI application. Builds from `./backend/Dockerfile`. Depends on `postgres` and `redis` being healthy before starting. Exposes port 8000.

**frontend** — Next.js application. Builds from `./frontend/Dockerfile`. Sets `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`. Exposes port 3000. Depends on `backend`.

### Docker Commands

```bash
# Build all containers from scratch and start the stack
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d --build

# View real-time logs for the backend
docker-compose logs -f backend

# View real-time logs for the frontend
docker-compose logs -f frontend

# Stop all running containers
docker-compose down

# Stop containers and delete all data volumes (fresh start)
docker-compose down -v

# Rebuild only one service
docker-compose up --build backend
```

### Adding Environment Variables to Docker

To use your OpenRouter API key in Docker, edit the `backend` service in `docker-compose.yml`:

```yaml
backend:
  build:
    context: ./backend
    dockerfile: Dockerfile
  container_name: fragment_backend
  environment:
    DATABASE_URL: postgresql+asyncpg://postgres:postgrespassword@postgres:5432/fragment_db
    REDIS_URL: redis://redis:6379/0
    SECRET_KEY: fragment_production_secret_key_change_this
    OPENROUTER_API_KEY: sk-or-v1-your-actual-key-here
    OPENROUTER_MODEL: google/gemini-2.5-flash
```

Alternatively, create a `.env` file in the root directory (where `docker-compose.yml` lives) and Docker Compose will read it automatically:

```
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
```

### Important Differences Between Local Dev and Docker

| Setting | Local Development | Docker Production |
|---------|------------------|-------------------|
| Database | SQLite (fragment.db) | PostgreSQL 15 |
| Database URL | sqlite+aiosqlite:///./fragment.db | postgresql+asyncpg://postgres:password@postgres:5432/fragment_db |
| Redis | Not needed (optional) | Running as a service |
| Hot reload | Yes (--reload flag) | No (production mode) |
| QuantLib build time | Already installed in venv | Built inside container (takes ~5-10 min first time) |

---

## 17. Test Suite

**Location:** `backend/tests/` — 19 pure unit tests. No network calls. No database required. No API keys needed.

Tests are designed to run in any order and are completely independent of each other. The entire suite runs in approximately 4 seconds on typical hardware.

### test_quantlib_pricer.py — 2 tests

Tests that QuantLib's pricing engine produces mathematically correct results.

**Test 1 — ATM call price accuracy:**
Prices a standard at-the-money European call option (S=K=100, T=1, r=0.05, σ=0.20) and verifies the result matches the known analytical Black-Scholes value within $0.01 tolerance. The expected value is approximately $10.45.

**Test 2 — Put-Call parity:**
Computes both call and put prices for the same parameters. Verifies that `|C - P - (S - K·e^{-rT})| < 0.001`. If QuantLib's pricing engine is internally consistent, this fundamental no-arbitrage relation must hold to high precision.

### test_adversarial_engine.py — 5 tests

Tests the core adversarial search pipeline end-to-end.

**Test 1 — Search bounds respected:**
Runs the adversarial search and verifies that the returned breaking parameters fall within the specified search bounds. Spot multiplier must be in [0.60, 1.40]. Volatility multiplier must be in [0.40, 3.00].

**Test 2 — Fragility score validity:**
Runs the full validation pipeline on a standard BSM model and verifies that the fragility score is a float in [0.0, 100.0].

**Test 3 — Seed reproducibility:**
Runs the search twice with the same seed and verifies the results are identical (same breaking parameters to 4 decimal places). This tests the determinism required for regulatory reproducibility.

**Test 4 — Correct model outperforms flawed model:**
Tests two models: a correct BSM implementation and a deliberately flawed version (returns `S × σ × T` instead of the actual Black-Scholes formula). Verifies that the flawed model receives a higher fragility score than the correct one.

**Test 5 — Greek drift format:**
Verifies that the returned greek_drifts dictionary contains "delta_drift" and "vega_drift" keys with numeric (float) values.

### test_quantitative_edge_cases.py — 5 tests

Tests QuantLib's pricing behavior at mathematical edge cases that real-world models commonly encounter.

**Test 1 — Deep ITM call:**
Spot=200, Strike=100 (call is deeply in-the-money with 100% intrinsic value). The price must approximate `S - K·e^{-rT} = 200 - 100·e^{-0.05} ≈ 104.88`. Tests that QuantLib handles extreme moneyness correctly.

**Test 2 — Near-expiry option:**
T=0.001 years (approximately 8 hours to expiry). The price must approximate the intrinsic value `max(S - K, 0)`. Tests that QuantLib handles near-zero maturity without numerical instability.

**Test 3 — Zero volatility:**
σ=0.001 (essentially zero). For a call, price must equal `max(S - K·e^{-rT}, 0)` — the pure time value of money discounted intrinsic value. Tests the degenerate limit of the BSM formula.

**Test 4 — High volatility:**
σ=1.5 (150% annualized — crisis-level volatility). The price must satisfy the no-arbitrage upper bound: `call_price ≤ S = 100`. Tests that extreme volatility does not cause overflow or bound violations.

**Test 5 — Long maturity:**
T=5.0 years (five-year option). Tests that QuantLib correctly handles long-dated contracts without calendar arithmetic errors.

### test_sandbox.py — 2 tests

Tests the security isolation of the sandboxed execution environment.

**Test 1 — Valid BSM execution:**
Submits a correct Black-Scholes call pricing function. Verifies that `SandboxedModelEvaluator.evaluate(code, 100, 100, 1.0, 0.05, 0.20)` returns a reasonable float (approximately $10.45, within $1.00 tolerance).

**Test 2 — Malicious code rejection:**
Submits code containing `import os; os.system("rm -rf /")`. Verifies that `SandboxedModelEvaluator.evaluate()` raises an `ASTSecurityError` (not an actual system call). The AST parser must catch this before any compilation.

### test_security_sandboxing.py — 5 tests

Tests every security boundary of the combined AST + sandbox system.

**Test 1 — os import blocked:**
Code containing `import os` must raise `ASTSecurityError` during `parse_and_validate_model_code()`.

**Test 2 — sys import blocked:**
Code containing `import sys` must raise `ASTSecurityError`.

**Test 3 — subprocess blocked:**
Code containing `import subprocess` must raise `ASTSecurityError`.

**Test 4 — __import__ access blocked:**
Code containing `__import__('os')` must raise `ASTSecurityError` — the prohibited attribute `__import__` must be caught at the AST level.

**Test 5 — Infinite loop timeout:**
Code containing `while True: pass` must raise `RuntimeError` with a message containing "timed out" within approximately 5 seconds. This verifies the thread timeout mechanism works correctly.

---

## 18. Frequently Asked Questions

**Q: What does "adversarial" mean in this context?**

It means the system acts as an intelligent adversary to the model — actively trying to find its worst possible failure case, not just testing it at random or pre-defined points. This mirrors how security researchers "red team" software systems to find vulnerabilities. The goal is not to break the model for fun but to identify the exact conditions under which it would produce dangerous errors in a production trading environment.

**Q: Why use Differential Evolution instead of gradient descent or brute force?**

Gradient descent requires the objective function to be differentiable. The pricing error landscape as a function of market parameters is non-smooth (it involves calling user-submitted code that may have discontinuities) and is multimodal (multiple local maxima). Gradient descent would get stuck in the nearest local maximum and miss the true global worst case.

Brute force (testing every combination) is computationally infeasible. With 4 continuous dimensions and reasonable resolution (100 points per dimension), that is 100^4 = 100 million evaluations. At 10ms per evaluation, that would take 278 hours.

Differential Evolution is the right tool: it is designed for global optimization of non-differentiable, multimodal functions and typically finds good solutions in far fewer than 10,000 evaluations. With popsize=15 and maxiter=35, it uses approximately 6,300 evaluations per seed — finishing in seconds.

**Q: Why QuantLib specifically, and not just implementing Black-Scholes myself?**

Any custom implementation could itself have bugs that make it an unreliable reference. QuantLib has been used in production by banks, central banks, and asset managers since 2000. Its analytical engine has been independently verified by thousands of quantitative practitioners. This makes it the gold standard comparator — when FRAGMENT says your model diverges from QuantLib, that is a meaningful statement.

Additionally, QuantLib handles all the subtle implementation details correctly: calendar day counting, maturity rounding, dividend yield term structures, Greek normalization conventions. Getting all of these right in a custom implementation is a non-trivial undertaking.

**Q: What happens if someone uploads malicious Python code?**

Three independent layers of defense protect the server:

First, the AST static inspection (`ast_parser.py`) analyzes the code's structure before any compilation. Dangerous syntax patterns — os imports, subprocess calls, while loops, class definitions, prohibited attribute access — are rejected immediately without the code ever being compiled or executed.

Second, even if somehow a piece of code passed the AST check, the sandbox (`sandbox.py`) executes it in a restricted Python environment where dangerous builtins (`open`, `print`, `__import__`, `eval`, `exec`) are simply absent from the globals dictionary. Any runtime attempt to call these raises a NameError.

Third, the 5-second timeout kills any execution that runs longer than expected. This prevents denial-of-service attacks via computationally expensive code.

**Q: Does the system work without any API key?**

Yes, fully. All mathematical computation — the adversarial engine, QuantLib pricing, fragility scoring, assumption extraction, expectation suite — runs entirely locally on your machine using only the Python libraries installed via `pip install -r requirements.txt`. No network access is required for any of this.

Only two features require an OpenRouter API key: the AI-generated executive report narrative, and the natural language to Python model synthesis. Both features detect the absence of a key and automatically fall back to deterministic alternatives. The fallback report uses a structured template filled with the actual numerical results. The fallback synthesizer uses keyword matching to return pre-written standard model implementations.

**Q: What is SR 11-7 and why does it matter?**

SR 11-7 is a supervisory letter issued by the Federal Reserve's Division of Banking Supervision and Regulation in April 2011. Its full title is "Guidance on Model Risk Management." It applies to all U.S. financial institutions supervised by the Federal Reserve.

The guidance defines "model risk" as the risk that models produce incorrect outputs that lead to adverse consequences (financial losses, poor business decisions, regulatory violations). It requires institutions to: develop models with appropriate documentation and testing, independently validate models using rigorous methods including stress testing and sensitivity analysis, and continuously monitor model performance over time.

FRAGMENT's audit reports are deliberately structured to address SR 11-7's three core requirements: conceptual soundness assessment (are the model's mathematical assumptions well-founded?), sensitivity analysis (how does the model behave across the input parameter space — addressed by the adversarial search), and ongoing monitoring recommendations (what boundaries must be enforced in production?).

**Q: How accurate is the 6-axis hexagonal score?**

The six axis scores are mathematically derived from the adversarial validation results using calibrated formulas. They are not AI opinions or heuristic guesses — each axis uses a specific mathematical signal (fragility score, percentage error, optimizer stability, Greek drift magnitudes) with defined formulas.

However, the absolute calibration of these formulas was set by the project designers and has not been empirically validated against a large dataset of industry-validated models. They should be interpreted as relative indicators within the platform rather than as absolute regulatory metrics. A "Conceptual Soundness" score of 80 means the model performed better on this platform's conceptual soundness metric than a model scoring 60 — but it does not guarantee regulatory approval.

**Q: Can the platform price American options, exotic options, or interest rate derivatives?**

In its current form, the platform is designed and validated for European vanilla options — calls and puts that can only be exercised at expiration and pay `max(S-K, 0)` or `max(K-S, 0)` respectively. The QuantLib pricer uses `EuropeanExercise` and `PlainVanillaPayoff`. The adversarial search bounds are calibrated for this payoff structure.

Extending to American options would require: switching the QuantLib engine to `ql.BinomialVanillaEngine` or `ql.FdBlackScholesVanillaEngine`, updating the `EuropeanExercise` to `ql.AmericanExercise`, and revising the expectation suite since some assertions (like put-call parity) do not hold for American options.

Extending to exotic options (barriers, Asians, lookbacks) or interest rate derivatives would require more substantial changes to the pricing engine and possibly a different ground truth library (e.g., QuantLib's bond engines or rate models).

**Q: Where is all the data stored?**

All data is stored locally in a single SQLite file: `backend/fragment.db`. This file contains all users, models, assumptions, validation runs, and reports. Nothing is sent to external servers except the optional OpenRouter API calls for AI report generation.

There is no analytics, telemetry, usage tracking, or cloud database in the default configuration. The entire application can run completely offline (except for the optional AI features and the optional Yahoo Finance market data).

The `fragment.db` file can be safely deleted to reset the application to a clean state — it will be recreated automatically on the next server start.

**Q: How do I update the risk-free rate to current market levels?**

The risk-free rate displayed in the market monitor and used as the default in the validation form is hard-coded in `backend/app/services/yfinance_provider.py`:

```python
"risk_free_rate": 0.0525,  # Benchmark US 10Y Treasury yield
```

Update this value (as a decimal, so 5.00% = 0.05) and restart the backend. The market data API response will then return the updated rate to pre-populate the validation form.

---

*This document represents the complete knowledge base for the FRAGMENT Adversarial Validation Platform.*
*Repository: https://github.com/dathasaiswaroopgudimella-png/Quant-portifolio*
*Last updated: August 2026*
