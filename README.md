# 🔬 Autonomous AI Scientist

An end-to-end autonomous multi-agent scientific discovery platform that turns tabular datasets into validated scientific findings, reproducible Jupyter Notebooks, and structured executive reports.

---

## 🌟 Key Features

- **Automated Data Profiling & Leakage Audit**: Automatically detects column types, missingness, statistical distributions, target candidates (classification vs. regression), and screens for primary key leakage or high multicollinearity ($r \ge 0.95$).
- **Multi-Agent Hypothesis Formulation**: Combines Gemini LLM hypothesis generation with an advanced statistical heuristic engine to propose domain-aware, testable scientific hypotheses with quantitative target effect sizes.
- **AST-Validated Python Sandbox**: Generates deterministic Python statistical scripts (Mann-Whitney U, Pearson Correlation, Chi-Square Independence, One-Way ANOVA, Random Forest Cross-Validation) and executes them in an isolated, security-checked AST sandbox with self-healing capabilities.
- **False Discovery Rate (FDR) Guardrails**: Employs the **Benjamini-Hochberg (BH)** procedure ($\alpha = 0.05$) to eliminate $p$-hacking alongside stringent effect size cutoffs ($R^2 \ge 0.30$, Cohen's $d \ge 0.30$, Cramér's $V \ge 0.20$).
- **Reproducible Artifact Generation**: Automatically outputs formatted executive Markdown reports and standalone, fully executable Jupyter Notebooks (`.ipynb`) with visual plots and statistical evaluations.
- **Real-Time Live Event Stream**: Server-Sent Events (SSE) feed real-time agent execution logs, active pipeline stages, and step-by-step progress directly to the React UI.

---

## 🏗️ Architecture & Project Structure

```
llm and ml project/
├── backend/
│   ├── app.py                 # FastAPI application server with CORS & SSE endpoints
│   ├── requirements.txt       # Python dependencies
│   ├── engine/
│   │   ├── orchestrator.py    # Multi-agent research pipeline coordinator
│   │   └── sandbox.py         # AST security validator & isolated Python script sandbox
│   └── agents/
│       ├── profiler.py        # DataProfilerAgent for EDA and leakage checks
│       ├── hypothesizer.py    # HypothesizerAgent (Gemini LLM & Heuristic engine)
│       ├── code_engineer.py   # CodeEngineerAgent for statistical script generation
│       ├── validator.py       # StatisticalValidatorAgent for Benjamini-Hochberg FDR control
│       └── reporter.py        # ScienceWriterAgent for Markdown & Jupyter Notebook outputs
├── frontend/
│   ├── package.json           # Vite & React 19 configuration
│   ├── index.html             # Main HTML entrypoint
│   └── src/
│       ├── App.jsx            # Main React Dashboard container
│       ├── index.css          # Glassmorphism & custom design system
│       └── components/
│           ├── DatasetUpload.jsx    # Dataset selection, CSV upload & target configuration
│           ├── LiveLoopMonitor.jsx  # Real-time SSE thinking loop progress monitor
│           └── ReportViewer.jsx     # Interactive scientific findings & notebook viewer
├── data/                      # Sample datasets (e.g., sample_churn.csv)
├── uploads/                   # User-uploaded custom CSV datasets
└── README.md                  # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.10` or higher
- **Node.js**: `18.0` or higher (with `npm`)

---

### 1. Backend Setup & Startup

1. Navigate to the project root directory:
   ```bash
   cd "c:\Users\admin\Desktop\llm and ml project"
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. (Optional) Set your Gemini API key for LLM hypothesis generation:
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your-gemini-api-key"
   ```
   *(Note: If no API key is provided, the platform automatically falls back to its built-in statistical heuristic engine.)*

4. Start the FastAPI backend server:
   ```bash
   python backend/app.py
   ```
   The backend API will start on **`http://127.0.0.1:5050`**.

---

### 2. Frontend Setup & Startup

1. Open a new terminal window and navigate to the `frontend` folder:
   ```bash
   cd "c:\Users\admin\Desktop\llm and ml project\frontend"
   ```

2. Install node dependencies (if not already installed):
   ```bash
   npm install
   ```

3. Launch the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to:
   👉 **[http://localhost:3030/](http://localhost:3030/)**

---

## 📊 How to Use

1. **Dataset Selection**: Choose a preloaded dataset (e.g., `sample_churn.csv`) or upload your own `.csv` file.
2. **Target Variable Configuration**: Inspect column profiles, select your target dependent variable, and choose the task type (*Classification* or *Regression*).
3. **Run Investigation**: Click **"Run Autonomous AI Scientist"**.
4. **Live Loop Monitor**: Watch real-time agent activity logs and live stage transitions through the 5-step scientific discovery pipeline:
   1. *Data Profiling*
   2. *Hypothesis Formulation*
   3. *Sandbox Execution*
   4. *FDR & Effect Validation*
   5. *Report Generation*
5. **Inspect & Download Results**: Review confirmed scientific discoveries, statistical metrics, negative control checks, and download the auto-generated Jupyter Notebook.

---

## 🛡️ Methodological Guardrails

- **Benjamini-Hochberg FDR Control**: Controls false positive rates across simultaneous hypothesis tests ($\alpha = 0.05$).
- **Effect Size Thresholding**: Requires non-trivial statistical effect magnitude beyond mere $p$-value significance ($R^2 \ge 0.30$, Cohen's $d \ge 0.30$, Cramér's $V \ge 0.20$).
- **Negative Controls**: Tests expected non-causal noise features to establish baseline sensitivity.
- **AST Code Safety**: Prevents execution of dangerous modules (`os`, `sys`, `socket`) within the sandbox.
