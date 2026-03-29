# Resume–JD Matcher

A Streamlit web application that evaluates how well a resume matches a job description, with role-specific scoring for Consulting, Product, and Analytics roles.

## Features

- **ATS Match Score** — deterministic keyword matching between resume and job description (0–100).
- **Role-Specific Fit Score** — rule-based scoring across dimensions like Problem Solving, Leadership, Stakeholder Exposure, and Business Impact.
- **Missing Keywords** — highlights important JD terms absent from the resume.
- **Bullet Improvement Suggestions** — heuristic-based rewrite hints for each experience bullet (LLM-ready stub for future integration).

## Project Structure

```
app.py                 # Streamlit UI entry point
parser.py              # PDF text extraction and bullet detection
scoring.py             # ATS keyword extraction and matching
consulting_model.py    # Role-specific fit scoring models
bullet_rewriter.py     # Bullet rewrite suggestions (LLM-ready stub)
requirements.txt       # Python dependencies
```

## Setup

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## Usage

1. Upload a resume PDF in the sidebar.
2. Paste a job description or upload it as a PDF.
3. Select a role type (Consulting, Product, or Analytics).
4. Click **Evaluate Resume** to see scores, missing keywords, and bullet suggestions.

## LLM Integration

The `bullet_rewriter.py` module contains a placeholder function. To enable LLM-powered rewrites:

1. Install the Anthropic SDK: `pip install anthropic`
2. Set your API key: `export ANTHROPIC_API_KEY=sk-...`
3. Uncomment the `rewrite_bullet_llm` function in `bullet_rewriter.py` and wire it into `rewrite_bullet`.
