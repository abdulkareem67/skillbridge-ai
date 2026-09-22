"""Whether someone has finished setting up, and where to send them next.

"Set up" means the two things every screen depends on: a target role and at
least one skill. Without them the dashboard, analysis and roadmap are all empty,
and landing a brand-new user on a page of zeros is the worst first impression
the product can make. Location is asked for but optional — a missing one just
means global job boards.

Derived from data rather than stored as a flag, so there is no schema change and
nothing to fall out of sync: a user who deletes all their skills is correctly
treated as not set up again.
"""


def needs_onboarding(db, user_id: int) -> bool:
    user = db.execute("SELECT target_role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or not user["target_role"]:
        return True
    has_skill = db.execute("SELECT 1 FROM skills WHERE user_id = ? LIMIT 1", (user_id,)).fetchone()
    return has_skill is None


def next_page(db, user_id: int) -> str:
    return "/onboarding" if needs_onboarding(db, user_id) else "/dashboard"
