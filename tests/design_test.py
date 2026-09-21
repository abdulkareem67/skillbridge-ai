"""Design-system guarantees from Phase 2.

These lock in decisions that are easy to undo by accident: emoji creeping back
in as icons, an icon referencing a symbol that isn't in the sprite, or the demo
drifting away from the real engine.
"""
import re

PAGES = ["/", "/demo", "/login", "/register", "/privacy", "/terms"]

# Pictographs only. Arrows, bullets and typographic dashes are fine.
EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF⬀-⯿]"
)


def test_no_emoji_is_rendered_as_an_icon(client):
    for path in PAGES:
        found = EMOJI.findall(client.get(path).text)
        assert not found, f"{path} still renders emoji: {found[:5]}"


def test_every_icon_reference_resolves(client):
    """A <use> pointing at a symbol that isn't in the sprite renders nothing."""
    for path in PAGES:
        body = client.get(path).text
        defined = set(re.findall(r'<symbol id="i-([a-z-]+)"', body))
        assert defined, f"{path} is missing the icon sprite"
        used = set(re.findall(r'<use href="#i-([a-z-]+)"', body))
        assert used <= defined, f"{path} uses undefined icons: {sorted(used - defined)}"


def test_landing_shows_a_timeline_not_a_carousel(client):
    body = client.get("/").text
    assert 'class="timeline"' in body
    assert body.count("timeline-step") >= 4
    # The carousel hid three steps behind a timer.
    assert "slideshow" not in body
    assert "slide-dot" not in body


def test_features_do_not_repeat_the_steps(client):
    """The feature grid used to restate the four steps word for word."""
    body = client.get("/").text.lower()
    features = body.split('id="features"', 1)[1]
    for repeated in ("cv upload & skill extraction", "ai skill gap analysis", "personalized roadmap"):
        assert repeated not in features, f"feature grid still repeats a step: {repeated}"


# --------------------------------------------------------------------------- #
# Demo
# --------------------------------------------------------------------------- #
def test_demo_is_public_and_shows_a_real_report(client):
    response = client.get("/demo")
    assert response.status_code == 200
    assert re.search(r"\d+%", response.text), "no match score rendered"


def test_demo_profiles_give_different_reports(client):
    from app.demo_data import DEMO_PROFILES, build_demo_report

    scores = {p["slug"]: build_demo_report(p)["gap"]["match_percent"] for p in DEMO_PROFILES}
    assert len(DEMO_PROFILES) >= 2
    assert len(set(scores.values())) > 1, f"every demo profile scores the same: {scores}"


def test_demo_report_comes_from_the_real_engine(client):
    """The page must show what the engine produced, not hand-written numbers."""
    from app.demo_data import build_demo_report, get_profile

    profile = get_profile("junior-developer")
    report = build_demo_report(profile)
    body = client.get("/demo", params={"profile": "junior-developer"}).text

    assert f"{report['gap']['match_percent']}%" in body
    assert profile["target_role"] in body
    for skill in report["gap"]["missing_skills"][:2]:
        assert skill in body, f"missing skill {skill} not shown"


def test_unknown_demo_profile_falls_back(client):
    assert client.get("/demo", params={"profile": "nope"}).status_code == 200


def test_demo_needs_no_account(client):
    """It must work signed out — that is the entire point of it."""
    client.post("/api/auth/logout")
    assert client.get("/demo", follow_redirects=False).status_code == 200
