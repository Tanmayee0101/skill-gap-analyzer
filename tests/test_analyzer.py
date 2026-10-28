from analyzer import analyze, extract_skills


def test_aliases_are_normalized():
    found = extract_skills("I built a model with sklearn and natural language processing.")
    assert "scikit-learn" in found
    assert "NLP" in found


def test_skill_list_without_application_is_not_demonstrated():
    result = analyze(
        "Skills: Python, machine learning",
        "We need Python and machine learning.",
    )
    assessments = {item["skill"]: item for item in result["assessments"]}
    assert assessments["Python"]["category"] == "Mentioned, but not demonstrated"
    assert assessments["Machine Learning"]["category"] == "Mentioned, but not demonstrated"


def test_related_skill_is_partial_not_demonstrated():
    result = analyze("Built a Python script for file processing.", "Machine learning")
    assessment = result["assessments"][0]
    assert assessment["skill"] == "Machine Learning"
    assert assessment["category"] == "Partially supported"


def test_project_evidence_counts_once():
    result = analyze(
        "Skills: Python\nProjects: Built a Python text classifier.",
        "Python",
    )
    assert result["demonstrated_coverage"] == 100
