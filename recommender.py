"""Gap-aware course, project, and roadmap recommendations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).parent / "data"


def _load(filename: str) -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


def recommend(assessments: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    gaps = {item["skill"] for item in assessments if item["category"] != "Demonstrated"}
    courses = _rank(_load("courses.json"), gaps)
    projects = _rank(_load("projects.json"), gaps)
    roadmap = []
    covered: set[str] = set()
    for item in courses + projects:
        new_skills = [skill for skill in item.get("skills_covered", []) if skill in gaps - covered]
        for skill in new_skills:
            roadmap.append({
                "skill": skill,
                "resource": item["title"],
                "type": "Course" if "provider" in item else "Project",
                "prerequisites": item.get("prerequisites", []),
                "estimated_time": item.get("estimated_time", "2–4 weeks"),
                "evidence": f"Retain a working implementation and a short explanation of design and evaluation decisions.",
            })
        covered.update(new_skills)
    return {"courses": courses[:6], "projects": projects[:6], "roadmap": roadmap}


def _rank(items: list[dict[str, Any]], gaps: set[str]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: len(gaps.intersection(item.get("skills_covered", []))),
        reverse=True,
    )
