# Skill Gap Analyzer

An NLP-based Streamlit application for comparing a candidate profile with a
target job description, identifying evidence-supported skill gaps, and
generating a learning roadmap.

## Architecture

```text
skill-gap-analyzer/
├── app.py                    # Streamlit user interface
├── analyzer.py               # Text processing and evidence assessment
├── recommender.py            # Course, project, and roadmap ranking
├── requirements.txt
├── data/
│   ├── skills.json           # Canonical skills and aliases
│   ├── courses.json          # Curated learning resources
│   └── projects.json         # Practical project catalogue
├── utils/
│   └── resume_parser.py      # Text-based PDF extraction
└── tests/
    ├── test_analyzer.py
    └── test_recommender.py
```

The application will use spaCy `PhraseMatcher` for canonical skill extraction
and scikit-learn TF-IDF/cosine similarity as a separate document-comparison
signal. Similarity will not be used as evidence of proficiency. Skill
classifications will rely on explicit project, work, assignment, or other
practical evidence in the supplied profile.

The Streamlit interface uses an editorial comparison-desk layout rather than a
generic dashboard: a split candidate/role workspace, evidence-led finding
bands, a gap-aware learning catalogue, and a numbered roadmap. It uses the
project palette (`#101820`, `#202D35`, `#D6FF62`, `#F3F1E8`, `#59B8A5`) with
system font fallbacks, so the visual identity does not depend on an external
font download.

## Dependency setup (Windows PowerShell)

From the project directory:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The first version does not require a downloaded spaCy language model because
skill matching uses `PhraseMatcher` patterns. If a future feature needs a
statistical model, install it separately and keep a rule-based fallback.

## Run the app

```powershell
streamlit run app.py
```

## NLP and assessment rules

1. Input text is normalized for matching while original excerpts are retained
   for evidence display.
2. spaCy `PhraseMatcher` recognizes canonical skills and aliases, so repeated
   aliases do not inflate the number of skills.
3. A skill is **Demonstrated** only when a matched excerpt also describes a
   practical activity such as building, implementing, training, analyzing, or
   deploying. A named skill without that evidence is **Mentioned, but not
   demonstrated**.
4. Related skills are reported as **Partially supported**, never as proof of the
   required skill. A missing mention is **Unverified or not found**, not proof
   that the candidate lacks the skill.
5. Demonstrated coverage is calculated only from demonstrated required skills.
   TF-IDF/cosine similarity is shown separately and is not a proficiency or
   hiring score.
6. Recommendations are ranked by the number of un-demonstrated required skills
   covered by each resource or project.

## Limitations and future enhancements

The first version supports selectable-text PDFs only, uses a curated technical
skill dictionary, and applies transparent rule-based evidence heuristics.
Resume text cannot independently verify proficiency, credentials, or project
quality. Future versions could add configurable skill taxonomies, stronger
section-aware evidence extraction, user-reviewed classifications, and
evaluation against an annotated test set.
