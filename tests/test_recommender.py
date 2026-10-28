from recommender import recommend


def test_recommendations_cover_gaps():
    recommendations = recommend([
        {
            "skill": "NLP",
            "category": "Unverified or not found",
            "excerpts": [],
            "explanation": "",
            "next_step": "",
        },
        {
            "skill": "Python",
            "category": "Demonstrated",
            "excerpts": ["Built a Python app."],
            "explanation": "",
            "next_step": "",
        },
    ])
    assert recommendations["courses"]
    assert recommendations["projects"]
    assert any(step["skill"] == "NLP" for step in recommendations["roadmap"])
