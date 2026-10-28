"""Evidence-based NLP analysis for candidate profiles and job descriptions."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from spacy.matcher import PhraseMatcher


# ONE shared spaCy object for the whole file. The matcher and every Doc
# must use the same nlp.vocab, otherwise match IDs cannot be converted
# back into skill names (the E018 error).
nlp = spacy.blank("en")

EVIDENCE_VERBS = (
    "built", "developed", "implemented", "created", "trained", "deployed",
    "analyzed", "analysed", "designed", "automated", "evaluated", "engineered",
    "used", "worked", "led", "wrote", "integrated", "processed",
)
CONCRETE_SECTIONS = ("project", "experience", "internship", "assignment")

# Whole-word patterns, so "network" or "framework" do not count as evidence.
_VERB_PATTERN = re.compile(r"\b(" + "|".join(EVIDENCE_VERBS) + r")\b")
_SECTION_PATTERN = re.compile(r"\b(" + "|".join(CONCRETE_SECTIONS) + r")\b")


def load_skills(path: Path | None = None) -> list[dict[str, Any]]:
    skill_path = path or Path(__file__).parent / "data" / "skills.json"
    return json.loads(skill_path.read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _build_matcher(skills: list[dict[str, Any]]) -> tuple[PhraseMatcher, dict[str, dict[str, Any]]]:
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    lookup: dict[str, dict[str, Any]] = {}
    for skill in skills:
        patterns = [skill["name"], *skill.get("aliases", [])]
        matcher.add(skill["name"], [nlp.make_doc(pattern) for pattern in patterns])
        lookup[skill["name"]] = skill
    return matcher, lookup


def _sentence_for_span(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start))
    right_candidates = [
        position for position in (text.find(".", end), text.find("\n", end)) if position >= 0
    ]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1:right + 1].strip()


def extract_skills(text: str, skills: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    catalog = skills or load_skills()
    matcher, lookup = _build_matcher(catalog)
    doc = nlp.make_doc(text)  # same nlp as the matcher
    found: dict[str, dict[str, Any]] = {}
    for match_id, start, end in matcher(doc):
        canonical = nlp.vocab.strings[match_id]  # same vocab as the matcher
        span = doc[start:end]
        item = found.setdefault(
            canonical,
            {"skill": canonical, "mentions": [], "evidence": []},
        )
        mention = span.text
        if mention not in item["mentions"]:
            item["mentions"].append(mention)
        sentence = _sentence_for_span(text, span.start_char, span.end_char)
        if sentence not in item["evidence"]:
            item["evidence"].append(sentence)
        item["aliases"] = lookup[canonical].get("aliases", [])
    return found


def _has_practical_evidence(excerpt: str) -> bool:
    lowered = excerpt.lower()
    return bool(_VERB_PATTERN.search(lowered) or _SECTION_PATTERN.search(lowered))


def assess_required_skills(
    profile_text: str,
    required: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    # Extract candidate skills once instead of once per required skill.
    if candidate is None:
        candidate = extract_skills(profile_text)

    assessments = []
    for skill, requirement in required.items():
        evidence = candidate.get(skill)
        excerpts = evidence["evidence"] if evidence else []
        practical = [excerpt for excerpt in excerpts if _has_practical_evidence(excerpt)]
        if practical:
            category = "Demonstrated"
            excerpts = practical
            explanation = "The profile describes practical application of this skill."
            next_step = "Add measurable outcomes, scope, or evaluation details to strengthen the evidence."
        elif excerpts:
            category = "Mentioned, but not demonstrated"
            explanation = "The skill is named, but the supplied text does not show a concrete application."
            next_step = "Add a project, assignment, or work example showing how the skill was applied."
        else:
            related = [
                name for name in requirement.get("related", [])
                if name in candidate
            ]
            if related:
                category = "Partially supported"
                excerpts = [f"Related skill found: {', '.join(related)}."]
                explanation = "Related evidence exists, but it does not establish the required skill itself."
                next_step = f"Practise {skill} directly and document an implementation."
            else:
                category = "Unverified or not found"
                explanation = "No adequate evidence for this requirement was detected in the supplied profile."
                next_step = f"Build a small practical example using {skill} and retain the resulting artefacts."
        assessments.append({
            "skill": skill,
            "category": category,
            "required_evidence": requirement.get("description", ""),
            "job_excerpts": requirement.get("evidence", []),
            "excerpts": excerpts,
            "explanation": explanation,
            "next_step": next_step,
        })
    return assessments


def analyze(profile_text: str, job_text: str) -> dict[str, Any]:
    skills = load_skills()
    required = extract_skills(job_text, skills)
    candidate = extract_skills(profile_text, skills)
    assessments = assess_required_skills(profile_text, required, candidate)
    demonstrated = sum(item["category"] == "Demonstrated" for item in assessments)
    coverage = demonstrated / len(assessments) * 100 if assessments else None
    similarity = 0.0
    if profile_text.strip() and job_text.strip():
        matrix = TfidfVectorizer(stop_words="english").fit_transform([profile_text, job_text])
        similarity = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0] * 100)
    return {
        "candidate_skills": sorted(candidate),
        "required_skills": sorted(required),
        "assessments": assessments,
        "demonstrated_coverage": coverage,
        "document_similarity": similarity,
    }