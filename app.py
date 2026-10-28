"""Streamlit interface for the Skill Gap Analyzer."""

from __future__ import annotations

import re
from html import escape

import pandas as pd
import streamlit as st

from analyzer import analyze
from recommender import recommend
from utils.resume_parser import ResumeParseError, extract_pdf_text


PAPER = "#F3F1E8"
INK = "#101820"
SLATE = "#202D35"
LIME = "#D6FF62"
TEAL = "#59B8A5"

st.set_page_config(
    page_title="SKILL / GAP",
    page_icon="↗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --paper: {PAPER};
            --ink: {INK};
            --slate: {SLATE};
            --lime: {LIME};
            --teal: {TEAL};
            --rule: rgba(16, 24, 32, .18);
            --muted: #5b6565;
            --paper-panel: #ffffff;
            --teal-panel: #e4f2ee;
            --error-bg: #fbe8e5;
            --error-ink: #7b2118;
        }}
        .stApp {{
            background: var(--paper);
            color: var(--ink);
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        .stApp, .stApp * {{
            box-sizing: border-box;
        }}
        .stApp p, .stApp li, .stApp span, .stApp label, .stApp input,
        .stApp textarea, .stApp button, .stApp [role="radiogroup"],
        .stApp [data-testid="stMarkdownContainer"] {{
            color: var(--ink);
        }}
        .block-container {{
            max-width: 1240px;
            padding: 2.2rem 3.5rem 5rem;
        }}
        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            background: var(--paper);
        }}
        h1, h2, h3, p, label, .stMarkdown {{
            color: var(--ink);
        }}
        h1, h2 {{
            letter-spacing: -.04em;
        }}
        h1 {{
            font-family: 'Newsreader', Georgia, serif;
            font-size: clamp(3.5rem, 7vw, 6.6rem);
            font-weight: 400;
            line-height: .91;
            margin: 1.3rem 0 1.4rem;
            max-width: 760px;
        }}
        h2 {{
            font-size: 2rem;
            margin: .2rem 0 .6rem;
        }}
        h3 {{
            font-size: 1.15rem;
            letter-spacing: -.02em;
        }}
        .stCaption, small {{
            color: var(--muted) !important;
        }}
        .mono, .eyebrow, .section-index, .metric-label, .skill-tag, .roadmap-number {{
            font-family: 'DM Mono', 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: .08em;
        }}
        .eyebrow, .section-index {{
            font-size: .67rem;
            font-weight: 500;
            color: var(--muted);
        }}
        .masthead {{
            border-bottom: 1px solid var(--ink);
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            padding-bottom: .9rem;
        }}
        .wordmark {{
            font-family: 'DM Mono', monospace;
            font-size: .95rem;
            font-weight: 500;
            letter-spacing: .13em;
        }}
        .masthead-right {{
            display: flex;
            gap: 1.5rem;
            font-family: 'DM Mono', monospace;
            font-size: .64rem;
            color: var(--muted);
            text-transform: uppercase;
        }}
        .intro {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) 260px;
            gap: 4rem;
            align-items: end;
            padding: 3.8rem 0 4.2rem;
            border-bottom: 1px solid var(--rule);
        }}
        .intro-copy {{
            font-size: 1rem;
            line-height: 1.55;
            max-width: 510px;
        }}
        .intro-note {{
            border-left: 3px solid var(--lime);
            padding: .2rem 0 .2rem 1rem;
            font-size: .82rem;
            line-height: 1.5;
        }}
        .section-head {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            border-bottom: 1px solid var(--ink);
            padding: 2.4rem 0 .7rem;
            margin-bottom: 1.2rem;
        }}
        .section-head h2 {{
            margin: 0;
            font-size: 1.6rem;
        }}
        .desk-label {{
            background: var(--slate);
            color: var(--paper);
            padding: .55rem .75rem;
            font: .65rem 'DM Mono', monospace;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .field-note {{
            color: var(--muted);
            font-size: .76rem;
            line-height: 1.4;
            margin: -.45rem 0 .6rem;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(255, 255, 255, .22);
            border: 1px solid var(--ink);
            border-radius: 0;
            padding: 1rem 1.15rem;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] > div {{
            border-color: transparent;
        }}
        .input-footer {{
            border-top: 1px solid var(--rule);
            margin-top: .8rem;
            padding-top: .8rem;
            color: var(--muted);
            font: .68rem 'DM Mono', monospace;
            text-transform: uppercase;
            letter-spacing: .05em;
        }}
        textarea {{
            background: var(--paper-panel) !important;
            border: 1px solid var(--ink) !important;
            border-radius: 0 !important;
            color: var(--ink) !important;
            caret-color: var(--ink) !important;
            font-size: .91rem !important;
            line-height: 1.55 !important;
        }}
        textarea::placeholder, input::placeholder {{
            color: #596363 !important;
            opacity: 1 !important;
        }}
        textarea:focus {{
            border: 2px solid var(--ink) !important;
            box-shadow: 4px 4px 0 var(--lime) !important;
            outline: none !important;
        }}
        [data-baseweb="textarea"], [data-baseweb="input"] {{
            background: var(--paper-panel) !important;
            border-color: var(--ink) !important;
            color: var(--ink) !important;
        }}
        [data-baseweb="textarea"] *, [data-baseweb="input"] * {{
            color: var(--ink) !important;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: var(--paper-panel);
            border: 1px dashed var(--ink);
            border-radius: 0;
        }}
        [data-testid="stFileUploaderDropzone"] *,
        [data-testid="stFileUploader"] small,
        [data-testid="stFileUploader"] button {{
            color: var(--ink) !important;
        }}
        [data-testid="stFileUploader"] button {{
            background: var(--lime) !important;
            border: 1px solid var(--ink) !important;
        }}
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] [role="radiogroup"],
        [data-testid="stRadio"] p {{
            color: var(--ink) !important;
            font-size: .76rem !important;
        }}
        [data-testid="stRadio"] [role="radio"] {{
            border-color: var(--ink) !important;
        }}
        [data-testid="stRadio"] [role="radio"][aria-checked="true"] {{
            background: var(--ink) !important;
        }}
        .stButton > button {{
            background: var(--lime);
            border: 1px solid var(--ink);
            border-radius: 0;
            color: var(--ink);
            font-weight: 700;
            min-height: 3rem;
            padding: 0 1.4rem;
            transition: transform .15s ease, box-shadow .15s ease;
        }}
        .stButton > button:hover {{
            background: var(--lime);
            color: var(--ink);
            transform: translate(-2px, -2px);
            box-shadow: 4px 4px 0 var(--ink);
        }}
        .stButton > button:focus, .stDownloadButton > button:focus {{
            outline: 2px solid var(--teal) !important;
            outline-offset: 2px;
        }}
        .stButton > button:active {{
            background: var(--teal) !important;
            color: var(--ink) !important;
            transform: translate(0, 0);
            box-shadow: none;
        }}
        .stButton > button:disabled, .stDownloadButton > button:disabled {{
            background: #d5d8d2 !important;
            border-color: #7d8580 !important;
            color: #4a524f !important;
        }}
        .stDownloadButton > button {{
            background: var(--slate) !important;
            border: 1px solid var(--ink) !important;
            border-radius: 0 !important;
            color: var(--paper) !important;
        }}
        .stDownloadButton > button *,
        .stDownloadButton > button:hover,
        .stDownloadButton > button:hover * {{
            color: var(--paper) !important;
        }}
        [data-testid="stAlert"] {{
            border-radius: 0 !important;
            border: 1px solid var(--ink) !important;
        }}
        [data-testid="stAlert"] p,
        [data-testid="stAlert"] div {{
            color: var(--ink) !important;
        }}
        [data-testid="stAlert"][kind="error"] {{
            background: var(--error-bg) !important;
            color: var(--error-ink) !important;
        }}
        [data-testid="stAlert"][kind="error"] p,
        [data-testid="stAlert"][kind="error"] div {{
            color: var(--error-ink) !important;
        }}
        [data-testid="stAlert"][kind="warning"] {{
            background: var(--teal-panel) !important;
        }}
        [data-testid="stAlert"][kind="success"] {{
            background: var(--teal-panel) !important;
        }}
        [data-testid="stExpander"] {{
            background: var(--paper-panel) !important;
            border: 1px solid var(--ink) !important;
            border-radius: 0 !important;
            color: var(--ink) !important;
            margin: .6rem 0;
        }}
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary *,
        [data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {{
            color: var(--ink) !important;
        }}
        [data-testid="stExpander"] summary:hover {{
            background: var(--teal-panel) !important;
        }}
        [data-testid="stExpander"] > details > div {{
            background: var(--paper-panel) !important;
            border-top: 1px solid var(--rule);
        }}
        .metric-strip {{
            display: grid;
            grid-template-columns: 1fr 1fr 1.4fr;
            border-top: 1px solid var(--ink);
            border-bottom: 1px solid var(--ink);
            margin: 1.1rem 0 2.5rem;
        }}
        .metric-block {{
            padding: 1rem 1.1rem 1.1rem 0;
            border-right: 1px solid var(--rule);
            margin-right: 1.1rem;
        }}
        .metric-block:last-child {{ border-right: 0; }}
        .metric-label {{ font-size: .62rem; color: var(--muted); }}
        .metric-value {{
            font: 2.8rem 'Newsreader', Georgia, serif;
            line-height: 1;
            margin-top: .45rem;
        }}
        .metric-detail {{ font-size: .72rem; color: var(--muted); margin-top: .35rem; }}
        .coverage-bar {{
            height: 7px;
            background: rgba(16, 24, 32, .12);
            margin-top: .85rem;
        }}
        .coverage-fill {{ height: 100%; background: var(--teal); }}
        .finding-band {{
            border-top: 1px solid var(--ink);
            padding: 1rem 0 .8rem;
            margin-top: 1rem;
        }}
        .finding-band-head {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: baseline;
            margin-bottom: .7rem;
        }}
        .finding-band-title {{ font-size: 1.05rem; font-weight: 700; }}
        .count {{ font: .68rem 'DM Mono', monospace; color: var(--muted); }}
        .finding-empty {{ color: var(--muted); font-size: .85rem; padding: .7rem 0; }}
        .skill-tag {{
            display: inline-block;
            border: 1px solid var(--ink);
            background: var(--slate);
            color: var(--paper) !important;
            max-width: 100%;
            overflow-wrap: anywhere;
            padding: .33rem .5rem;
            margin: 0 .35rem .35rem 0;
            font-size: .62rem;
            letter-spacing: .04em;
        }}
        .skill-finding {{
            background: var(--paper-panel);
            border: 1px solid var(--rule);
            border-top: 3px solid var(--teal);
            padding: .85rem 1rem;
            min-height: 100%;
        }}
        .skill-finding > p {{
            margin: .35rem 0;
        }}
        .skill-finding h3 {{
            color: var(--ink);
            font-family: 'Newsreader', Georgia, serif;
            font-size: 1.5rem;
            margin: 0 0 .9rem;
        }}
        .quote-block {{
            background: var(--teal-panel);
            border-left: 3px solid var(--teal);
            color: var(--ink);
            font-size: .87rem;
            line-height: 1.45;
            margin: .35rem 0 .9rem;
            padding: .7rem .9rem;
        }}
        mark {{
            background: var(--lime);
            color: var(--ink);
            padding: 0 .08em;
        }}
        .why-counts {{
            color: var(--ink);
            font-size: .84rem;
            line-height: 1.45;
            margin: .35rem 0 0;
        }}
        .unverified-group {{
            border-bottom: 1px solid var(--rule);
            padding: .3rem 0 1rem;
        }}
        .evidence-card {{
            border-left: 3px solid var(--teal);
            background: rgba(89, 184, 165, .1);
            margin: .5rem 0 0;
            padding: .8rem 1rem;
        }}
        .evidence-label {{
            color: var(--muted);
            font: .61rem 'DM Mono', monospace;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .evidence-text {{ font-size: .87rem; line-height: 1.45; margin-top: .35rem; }}
        .recommendation {{
            background: var(--paper-panel);
            border: 1px solid var(--rule);
            border-top: 3px solid var(--teal);
            padding: 1.1rem 1.1rem 1.35rem;
            margin: .8rem 0;
            min-height: 180px;
        }}
        .recommendation-title {{
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: .25rem;
        }}
        .recommendation-meta {{
            color: var(--muted);
            font: .67rem 'DM Mono', monospace;
            line-height: 1.6;
            text-transform: uppercase;
        }}
        .recommendation-description {{ font-size: .84rem; line-height: 1.45; margin: .6rem 0; }}
        .catalogue-tag {{
            display: inline-block;
            color: var(--slate);
            background: var(--lime);
            max-width: 100%;
            overflow-wrap: anywhere;
            font: .6rem 'DM Mono', monospace;
            letter-spacing: .04em;
            padding: .25rem .4rem;
            margin-right: .25rem;
        }}
        .roadmap {{
            border-left: 1px solid var(--ink);
            margin: 1.2rem 0 0 .8rem;
            padding-left: 2rem;
        }}
        .roadmap-step {{
            position: relative;
            background: rgba(255, 255, 255, .35);
            padding: 1rem 1.15rem 1.5rem;
            border-bottom: 1px solid var(--rule);
            margin-bottom: 1.5rem;
        }}
        .roadmap-step::before {{
            content: '';
            position: absolute;
            left: -2.35rem;
            top: .2rem;
            width: .6rem;
            height: .6rem;
            background: var(--lime);
            border: 1px solid var(--ink);
        }}
        .roadmap-number {{ color: var(--muted); font-size: .62rem; }}
        .roadmap-skill {{ font: 1.5rem 'Newsreader', Georgia, serif; margin: .2rem 0; }}
        .roadmap-resource {{ font-size: .83rem; line-height: 1.5; }}
        .roadmap-evidence {{ color: var(--muted); font-size: .78rem; line-height: 1.5; margin-top: .45rem; }}
        .empty-state {{
            background: rgba(255, 255, 255, .3);
            border: 1px dashed var(--ink);
            padding: 1.4rem;
            margin: 1rem 0 2rem;
        }}
        .empty-state-title {{ font: 1.3rem 'Newsreader', Georgia, serif; }}
        .empty-state-copy {{ color: var(--muted); font-size: .83rem; line-height: 1.5; max-width: 600px; }}
        .disclaimer {{
            border-top: 1px solid var(--ink);
            margin-top: 3.5rem;
            padding-top: .8rem;
            color: var(--muted);
            font-size: .72rem;
            line-height: 1.5;
        }}
        a, a:visited {{
            color: var(--ink) !important;
            text-decoration-thickness: 1px;
        }}
        a:hover {{
            color: var(--slate) !important;
            background: var(--lime);
        }}
        [data-testid="stDataFrame"] {{
            border: 1px solid var(--ink);
        }}
        [data-testid="stDataFrame"] * {{
            color: var(--ink) !important;
        }}
        @media (max-width: 760px) {{
            .block-container {{ padding: 1.2rem 1rem 3rem; }}
            .masthead-right {{ gap: .6rem; font-size: .55rem; }}
            .intro {{ grid-template-columns: 1fr; gap: 1.5rem; padding: 2.5rem 0; }}
            h1 {{ font-size: 4rem; }}
            .metric-strip {{ grid-template-columns: 1fr 1fr; }}
            .metric-block:nth-child(3) {{ grid-column: 1 / -1; border-top: 1px solid var(--rule); padding-top: 1rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_head(index: str, title: str, label: str | None = None) -> None:
    label_markup = f'<span class="desk-label">{escape(label)}</span>' if label else ""
    st.markdown(
        f"""
        <div class="section-head">
            <div><span class="section-index">{index}</span><h2>{title}</h2></div>
            {label_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_strip(result: dict) -> None:
    coverage = result["demonstrated_coverage"]
    if coverage is None:
        coverage_value = "—"
        coverage_detail = "No recognized job skills"
        fill = 0
    else:
        coverage_value = f"{coverage:.1f}%"
        coverage_detail = "Concrete application evidence"
        fill = max(0, min(100, coverage))
    similarity = result["document_similarity"]
    st.markdown(
        f"""
        <div class="metric-strip">
            <div class="metric-block">
                <div class="metric-label">Skill coverage</div>
                <div class="metric-value">{coverage_value}</div>
                <div class="metric-detail">{coverage_detail}</div>
                <div class="coverage-bar"><div class="coverage-fill" style="width:{fill}%"></div></div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Document similarity</div>
                <div class="metric-value">{similarity:.1f}%</div>
                <div class="metric-detail">TF-IDF / cosine signal only</div>
            </div>
            <div class="metric-block">
                <div class="metric-label">Recognized requirements</div>
                <div class="metric-value">{len(result["required_skills"]):02d}</div>
                <div class="metric-detail">Distinct skills found in the role description</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _quoted_excerpts(excerpts: list[str], skill: str, highlight_skill: bool = False) -> str:
    quoted = []
    for excerpt in excerpts:
        text = escape(str(excerpt))
        if highlight_skill:
            escaped_skill = escape(skill)
            text = re.sub(
                re.escape(escaped_skill),
                lambda match: f"<mark>{match.group(0)}</mark>",
                text,
                flags=re.IGNORECASE,
            )
        quoted.append(f'<div class="quote-block">“{text}”</div>')
    return "".join(quoted)


def render_finding(item: dict) -> None:
    skill = str(item["skill"])
    job_excerpts = item.get("job_excerpts", [])
    profile_excerpts = item.get("excerpts", [])
    job_text = _quoted_excerpts(job_excerpts, skill) or (
        '<div class="quote-block">“Required by the job description.”</div>'
    )
    profile_text = _quoted_excerpts(
        profile_excerpts,
        skill,
        highlight_skill=item["category"] == "Demonstrated",
    ) or '<div class="quote-block">“No matching profile excerpt found.”</div>'
    why = (
        "Your profile uses this skill in an applied context (project, work or assignment)."
        if item["category"] == "Demonstrated"
        else str(item["explanation"])
    )
    st.markdown(
        f"""
        <div class="skill-finding">
            <h3>{escape(skill)}</h3>
            <div class="evidence-label">Job requirement:</div>
            {job_text}
            <div class="evidence-label">Found in your profile:</div>
            {profile_text}
            <div class="evidence-label">Why this counts:</div>
            <p class="why-counts">{escape(why)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_findings(result: dict) -> None:
    categories = (
        ("Demonstrated", "01", "Demonstrated matches", "Concrete application is described."),
        ("Mentioned, but not demonstrated", "02", "Mentioned, not demonstrated", "Named in the profile, but practical application is not established."),
        ("Partially supported", "03", "Partial matches", "Related evidence exists; the exact requirement remains open."),
        ("Unverified or not found", "04", "Unverified / not found", "No adequate evidence was detected in the supplied profile."),
    )
    for category, number, title, description in categories:
        items = [item for item in result["assessments"] if item["category"] == category]
        st.markdown(
            f"""
            <div class="finding-band">
                <div class="finding-band-head">
                    <div><span class="section-index">{number} / EVIDENCE</span><div class="finding-band-title">{title}</div></div>
                    <span class="count">{len(items):02d} skills</span>
                </div>
                <div class="field-note">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not items:
            st.markdown('<div class="finding-empty">Nothing in this category.</div>', unsafe_allow_html=True)
        elif category == "Unverified or not found":
            tags = "".join(
                f'<span class="skill-tag">{escape(str(item["skill"]))}</span>'
                for item in items
            )
            st.markdown(
                f"""
                <div class="unverified-group">
                    <div>{tags}</div>
                    <div class="why-counts">No adequate evidence was detected in the supplied profile.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for item in items:
                render_finding(item)


def render_catalogue(recommendations: dict) -> None:
    section_head("04", "The learning catalogue")
    st.markdown(
        '<p class="field-note">Resources are ranked by how many identified gaps they cover. A recommendation is a next step, not evidence that the project is already complete.</p>',
        unsafe_allow_html=True,
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("#### Learning resources")
        for course in recommendations["courses"]:
            skills = "".join(f'<span class="catalogue-tag">{escape(skill)}</span>' for skill in course["skills_covered"])
            url = course.get("url")
            title = f'<a href="{escape(url)}" target="_blank">{escape(course["title"])} ↗</a>' if url else escape(course["title"])
            prerequisites = ", ".join(course.get("prerequisites", [])) or "None listed"
            st.markdown(
                f"""
                <div class="recommendation">
                    <div class="recommendation-title">{title}</div>
                    <div class="recommendation-meta">{escape(course["provider"])} · {escape(course["difficulty"])} · {escape(course.get("estimated_time", "Self-paced"))}</div>
                    <div class="recommendation-description">{escape(course["description"])}</div>
                    <div>{skills}</div>
                    <div class="recommendation-meta">Prerequisites: {escape(prerequisites)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right:
        st.markdown("#### Build to prove it")
        for project in recommendations["projects"]:
            skills = "".join(f'<span class="catalogue-tag">{escape(skill)}</span>' for skill in project["skills_covered"])
            prerequisites = ", ".join(project.get("prerequisites", [])) or "None listed"
            st.markdown(
                f"""
                <div class="recommendation">
                    <div class="recommendation-title">{escape(project["title"])}</div>
                    <div class="recommendation-meta">PRACTICAL PROJECT · {escape(project.get("estimated_time", "2–4 weeks"))}</div>
                    <div class="recommendation-description">{escape(project["objective"])} {escape(project.get("expected_learning_outcome", ""))}</div>
                    <div>{skills}</div>
                    <div class="recommendation-meta">Prerequisites: {escape(prerequisites)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


inject_styles()
st.markdown(
    """
    <div class="masthead">
        <div class="wordmark">SKILL / GAP</div>
        <div class="masthead-right"><span>Career intelligence / 01</span><span>Evidence over inference</span></div>
    </div>
    <div class="intro">
        <div>
            <div class="eyebrow">NLP-BASED ROLE RESEARCH TOOL</div>
            <h1>Your next role.<br>Your missing pieces.</h1>
            <p class="intro-copy">A clear-eyed comparison between what a role asks for and what your profile can currently demonstrate.</p>
        </div>
        <div class="intro-note"><strong>Read the result carefully.</strong><br>Named skills are not treated as proof of proficiency. Every classification is grounded in the text you provide.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

section_head("01", "Set the comparison desk")
with st.container(border=True):
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("#### Candidate profile")
        st.markdown('<div class="field-note">Paste a profile, or use a selectable-text PDF. Files are processed in memory and not stored.</div>', unsafe_allow_html=True)
        input_mode = st.radio(
            "Profile source",
            options=("Paste profile text", "Upload a text-based PDF"),
            horizontal=True,
            label_visibility="collapsed",
        )
        profile_text = ""
        if input_mode == "Paste profile text":
            profile_text = st.text_area(
                "Candidate profile",
                height=280,
                placeholder="Projects, work experience, coursework, tools used...\n\nTip: concrete verbs help the evidence review: built, implemented, evaluated, deployed.",
                label_visibility="collapsed",
            )
        else:
            uploaded_file = st.file_uploader("Upload resume PDF", type=["pdf"], label_visibility="collapsed")
            if uploaded_file is not None:
                try:
                    profile_text = extract_pdf_text(uploaded_file.getvalue())
                    st.success("Text extracted and ready for analysis.")
                except ResumeParseError as exc:
                    st.error(str(exc))
        st.markdown('<div class="input-footer">PROFILE / TEXT OR PDF · NO PERMANENT STORAGE</div>', unsafe_allow_html=True)

    with right:
        st.markdown("#### Target role")
        st.markdown('<div class="field-note">Paste the job description you want to investigate. The skill dictionary recognizes a curated technical vocabulary.</div>', unsafe_allow_html=True)
        job_description = st.text_area(
            "Target job description",
            height=280,
            placeholder="Responsibilities, required skills, tools, and qualifications...",
            label_visibility="collapsed",
        )
        st.markdown('<div class="input-footer">ROLE / JOB DESCRIPTION · SKILLS ARE EXTRACTED, NOT GUESSED</div>', unsafe_allow_html=True)

analyze_clicked = st.button("Run the comparison  ↗", type="primary", use_container_width=False)
if analyze_clicked:
    if not profile_text.strip():
        st.error("Provide candidate profile text before starting the analysis.")
    elif not job_description.strip():
        st.error("Provide a target job description before starting the analysis.")
    else:
        st.session_state["analysis_result"] = analyze(profile_text, job_description)

result = st.session_state.get("analysis_result")
if result is None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="section-index">02 / AWAITING INPUT</div>
            <div class="empty-state-title">The comparison is quiet for now.</div>
            <div class="empty-state-copy">Add both sides of the desk above. The report will separate demonstrated evidence from mentions, partial support, and skills that remain unverified.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    recommendations = recommend(result["assessments"])
    section_head("02", "The evidence report")
    render_metric_strip(result)
    if result["demonstrated_coverage"] is None:
        st.warning("No recognized skills were found in the job description. Coverage cannot be calculated; add more specific technical requirements to the role text.")
    render_findings(result)
    render_catalogue(recommendations)
    report = pd.DataFrame(result["assessments"]).to_csv(index=False)
    st.download_button(
        "Download the evidence log (CSV)",
        data=report,
        file_name="skill_gap_assessment.csv",
        mime="text/csv",
    )

st.markdown(
    """
    <div class="disclaimer"><strong>Scope note.</strong> This is a career-development aid, not an automated hiring decision system. Assessments are based only on supplied profile text and are not independent verification of proficiency, credentials, employment history, or project quality.</div>
    """,
    unsafe_allow_html=True,
)
