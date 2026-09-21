"""Sample profiles for the signed-out demo.

Only the *people* are invented. Their reports are produced by running the real
engine over these skill lists, so the demo cannot drift away from what the
product actually does — if the matching logic changes, the demo changes with it.

Each profile deliberately lands in a different place: a clear strength, a
half-finished switch, and someone near-ready. Seeing a 41% report matters more
than seeing three flattering ones.
"""
from .skills_engine import analyze_gap, build_roadmap

DEMO_PROFILES = [
    {
        "slug": "final-year-student",
        "name": "Final-year CS student",
        "blurb": "Solid fundamentals from coursework, no industry tooling yet.",
        "target_role": "Data Analyst",
        "location": "Lahore",
        "skills": [
            "Python", "Excel", "SQL", "Communication", "Teamwork",
            "Problem Solving", "Statistics",
        ],
    },
    {
        "slug": "career-switcher",
        "name": "Career switcher from teaching",
        "blurb": "Strong soft skills, early in the technical climb.",
        "target_role": "UI/UX Designer",
        "location": "London",
        "skills": [
            "Communication", "Teamwork", "Problem Solving", "Time Management",
            "Figma", "Wireframing",
        ],
    },
    {
        "slug": "junior-developer",
        "name": "Junior developer, 1 year in",
        "blurb": "Shipping already; aiming at the next role up.",
        "target_role": "Full Stack Developer",
        "location": "Dubai",
        "skills": [
            "HTML", "CSS", "JavaScript", "React", "Git", "REST APIs",
            "Node.js", "SQL", "Problem Solving",
        ],
    },
]


def get_profile(slug: str | None) -> dict:
    """The requested profile, or the first one when the slug is unknown."""
    for profile in DEMO_PROFILES:
        if profile["slug"] == slug:
            return profile
    return DEMO_PROFILES[0]


def build_demo_report(profile: dict) -> dict:
    """Run the real analysis over a sample profile."""
    gap = analyze_gap(profile["skills"], profile["target_role"])
    roadmap = build_roadmap(profile["skills"], profile["target_role"])
    return {"profile": profile, "gap": gap, "roadmap": roadmap}
