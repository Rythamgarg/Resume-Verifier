# ResumeATS

AI-powered ATS resume checker with role-specific scoring for MBA students. Upload your resume, paste a job description, and get instant feedback — no API key required for core features.

## Features

- **Deterministic ATS Score (0-100)** — keyword match, section structure, quantification, and skills alignment — always works, no API needed
- **Role-Specific Fit Scoring** — tailored rubrics for Consulting and Product Management with dimension-level breakdowns
- **LLM Deep Analysis** *(optional)* — qualitative strengths, gaps, and narrative feedback via Groq/Llama 3.1 70B
- **Bullet Point Rewriter** *(optional)* — LLM-powered rewrite suggestions in action-result format

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/rythamgarg/resume-verifier.git
cd resume-verifier/resume-ats
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Add Groq API key

```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and add your Groq API key
```

### 5. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Streamlit Cloud Deployment

1. Push the repo to GitHub.
2. Connect to [Streamlit Cloud](https://streamlit.io/cloud).
3. In the app settings, add `GROQ_API_KEY` under **Secrets**.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI | Streamlit |
| PDF Parsing | pdfplumber |
| ATS Scoring | scikit-learn (TF-IDF + cosine similarity) |
| Role Scoring | Rule-based keyword detection |
| LLM | Groq SDK + Llama 3.1 70B |

## Project Structure

```
resume-ats/
├── app.py                      # Streamlit UI
├── parser.py                   # PDF text extraction
├── ats_scorer.py               # Deterministic ATS engine
├── role_scorer.py              # Consulting + PM rubrics
├── llm_analyzer.py             # Groq/Llama deep analysis
├── bullet_rewriter.py          # LLM bullet rewriter
├── utils.py                    # Shared helpers
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example
├── README.md
└── .gitignore
```

## License

MIT
