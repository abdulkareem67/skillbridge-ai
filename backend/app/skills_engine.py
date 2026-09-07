"""Rule-based recommendation engine: skill-gap analysis, roadmap generation,
opportunity matching, and the career-advisor chatbot. No external AI API key
is required — this runs fully offline using the knowledge base in skills_data.py."""

import difflib
import re
from urllib.parse import quote_plus

from .skills_data import (
    ROLES,
    RESOURCES,
    DEFAULT_RESOURCE,
    OPPORTUNITIES,
    ROLE_CERTIFICATIONS,
    SKILL_DICTIONARY,
    all_required_skills,
    field_for_role,
)


def analyze_gap(user_skills: list[str], role: str) -> dict:
    required = all_required_skills(role)
    user_set = {s.lower() for s in user_skills}
    matched = [s for s in required if s.lower() in user_set]
    missing = [s for s in required if s.lower() not in user_set]
    match_pct = round(100 * len(matched) / len(required)) if required else 0
    return {
        "role": role,
        "required_skills": required,
        "matched_skills": matched,
        "missing_skills": missing,
        "match_percent": match_pct,
        "strengths": matched,
        "weaknesses": missing,
    }


def build_roadmap(user_skills: list[str], role: str) -> dict:
    phases = ROLES[role]
    user_set = {s.lower() for s in user_skills}
    roadmap = {}
    durations = {"beginner": "2-4 weeks per topic", "intermediate": "4-6 weeks (projects)", "advanced": "6-8 weeks (industry-level)"}
    for phase in ("beginner", "intermediate", "advanced"):
        topics = []
        for skill in phases[phase]:
            resource = RESOURCES.get(skill, DEFAULT_RESOURCE)
            topics.append({
                "skill": skill,
                "already_have": skill.lower() in user_set,
                "resource": resource,
            })
        roadmap[phase] = {
            "duration": durations[phase],
            "topics": topics,
        }
    return roadmap


def _apply_links(title: str, opp_type: str) -> list[dict]:
    query = title.strip()
    role_query = quote_plus(title)
    links = [
        {"label": "Search on Rozee.pk", "url": f"https://www.rozee.pk/job/jsearch/q/{quote_plus(query)}"},
        {"label": "Search on LinkedIn", "url": f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(query)}&location=Pakistan"},
        {"label": "Search on Indeed", "url": f"https://pk.indeed.com/jobs?q={quote_plus(query)}"},
        {"label": "Search on Bayt.com", "url": f"https://www.bayt.com/en/pakistan/jobs/{role_query}-jobs/"},
        {"label": "Search on Mustakbil", "url": f"https://www.mustakbil.com/jobs/search?q={role_query}"},
        {"label": "Search on BrightSpyre", "url": f"https://www.brightspyre.com/jobs/keyword/{role_query}"},
        {"label": "Search on Glassdoor", "url": f"https://www.glassdoor.com/Job/pakistan-{role_query}-jobs-SRCH_IL.0,8_IN181_KO9.htm"},
    ]
    if opp_type == "Internship":
        links.append({"label": "Search on Internee.pk", "url": f"https://internee.pk/?s={role_query}"})
    return links


def match_opportunities(
    user_skills: list[str],
    location: str | None = None,
    target_role: str | None = None,
    include_other_fields: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Rank opportunities by skill overlap. When the candidate has a target role set,
    opportunities outside that role's field (e.g. Web Development listings for a
    Cybersecurity Analyst) are dropped unless include_other_fields is True or the
    candidate's skill match is strong enough (40%+) to be worth surfacing anyway."""
    user_set = {s.lower() for s in user_skills}
    target_field = field_for_role(target_role)
    results = []
    for opp in OPPORTUNITIES:
        req = opp["skills"]
        matched = [s for s in req if s.lower() in user_set]
        pct = round(100 * len(matched) / len(req)) if req else 0

        if target_field and not include_other_fields and opp.get("field") != target_field and pct < 40:
            continue

        entry = dict(opp)
        entry["match_percent"] = pct
        entry["matched_skills"] = matched
        entry["in_target_field"] = (opp.get("field") == target_field) if target_field else True
        entry["apply_links"] = _apply_links(opp["title"], opp["type"])
        results.append(entry)
    results.sort(key=lambda x: (x["in_target_field"], x["match_percent"]), reverse=True)
    if location and location.lower() != "pakistan":
        results.sort(key=lambda x: (x["in_target_field"], x["location"].lower() == location.lower(), x["match_percent"]), reverse=True)
    return results[:limit]


def application_strategy(matched_opportunities: list[dict]) -> dict:
    """Personalized, ordered application plan built from the candidate's live match scores."""
    if not matched_opportunities:
        return {"steps": ["Add skills to your profile first so we can find and rank opportunities for you."], "priority": []}

    strong = [o for o in matched_opportunities if o["match_percent"] >= 70]
    moderate = [o for o in matched_opportunities if 40 <= o["match_percent"] < 70]
    priority = (strong or moderate or matched_opportunities)[:3]

    steps = []
    if strong:
        steps.append(f"Apply to your {len(strong)} strong-match role(s) first (70%+ match) — these are worth applying to today: {', '.join(o['title'] + ' at ' + o['company'] for o in strong[:3])}.")
    elif moderate:
        steps.append(f"You have no 70%+ matches yet, but these are close (40-69%): {', '.join(o['title'] + ' at ' + o['company'] for o in moderate[:3])}. Apply now and keep learning the missing skills in parallel.")
    else:
        steps.append("Your matches are still under 40% — apply to entry-level/internship listings anyway (employers often train for the rest) while you work through your Roadmap.")

    top = priority[0]
    lead_skills = top["matched_skills"][:3]
    steps.append(f"Before applying to {top['title']}, reorder your CV so {', '.join(lead_skills) or 'your strongest skills'} appear first — match the language in the posting.")
    steps.append("Write a 3-4 line cover message: (1) the role + where you found it, (2) one matched skill with a concrete example, (3) enthusiasm for the company, (4) a call to action to discuss further.")
    steps.append("Apply within 1-3 days of a posting going live — Pakistani SMEs and startups often close roles fast once they get a few good applicants.")
    steps.append("Track every application (company, date, status) in a simple spreadsheet so you can follow up after 5-7 days if you hear nothing.")

    return {"steps": steps, "priority": priority}


def categorize_all(user_skills: list[dict]) -> dict:
    buckets = {"technical": [], "soft": [], "tool": [], "certification": []}
    for item in user_skills:
        cat = item["category"] if item["category"] in buckets else "technical"
        buckets[cat].append(item["skill_name"])
    return buckets


def recommend_certifications(role: str | None) -> list[str]:
    if role and role in ROLE_CERTIFICATIONS:
        return ROLE_CERTIFICATIONS[role]
    return ["AWS Certified Cloud Practitioner", "Google Data Analytics Certificate"]


def resume_tips(categorized: dict, gap: dict | None) -> list[str]:
    """Rule-based CV improvement suggestions from the candidate's current profile."""
    tips = []
    total = sum(len(v) for v in categorized.values())

    if total == 0:
        return ["Upload your CV or add skills manually so we can generate tailored resume tips."]

    if not categorized.get("soft"):
        tips.append("Add soft skills (e.g. Communication, Teamwork, Problem Solving) — recruiters in Pakistan screen for these alongside technical ability.")
    if not categorized.get("certification"):
        tips.append("List at least one certification, even an in-progress one — it signals commitment and is an easy CV differentiator for entry-level roles.")
    if len(categorized.get("technical", [])) + len(categorized.get("tool", [])) < 4:
        tips.append("Your technical/tool skill list looks thin — add specific tools and languages you've used in coursework or projects, not just general terms.")
    if gap and gap["missing_skills"]:
        tips.append(f"Your target role still shows gaps in {', '.join(gap['missing_skills'][:3])} — even a small personal project using these will strengthen your CV immediately.")

    tips.append("Quantify achievements where possible ('optimized query reducing load time by 30%' beats 'worked on database').")
    tips.append("Add links to GitHub, a portfolio, or LinkedIn so recruiters can verify your listed skills.")
    return tips


def generate_improved_cv(name: str, categorized: dict, role: str | None, gap: dict | None) -> dict:
    """Builds an AI-restructured CV: a written professional summary, cleaned skill
    sections ordered by relevance, project suggestions for gaps, and CV recommendations."""
    technical = categorized.get("technical", [])
    tools = categorized.get("tool", [])
    soft = categorized.get("soft", [])
    certs = categorized.get("certification", [])
    top_skills = (technical + tools)[:5]

    if role and top_skills:
        summary = (
            f"Motivated {role} candidate with hands-on experience in {', '.join(top_skills)}. "
            f"{'Backed by ' + ', '.join(soft[:3]) + '.' if soft else ''} "
            f"Seeking to apply these skills in a {role} role, with a clear learning plan to close remaining "
            f"skill gaps and deliver measurable impact from day one."
        ).strip()
    elif top_skills:
        summary = (
            f"Motivated early-career candidate skilled in {', '.join(top_skills)}"
            + (f" and {', '.join(soft[:2])}." if soft else ".")
            + " Eager to apply technical skills to real-world projects and grow into a specialized role."
        )
    else:
        summary = "Motivated early-career candidate building a foundation of in-demand technical and soft skills."

    project_suggestions = []
    if gap and gap.get("missing_skills"):
        for skill in gap["missing_skills"][:3]:
            project_suggestions.append(f"Build a small project applying {skill} and add it to your CV with a GitHub link and a one-line result/impact statement.")

    return {
        "summary": summary,
        "technical_skills": technical,
        "tools": tools,
        "soft_skills": soft,
        "certifications": certs,
        "project_suggestions": project_suggestions,
        "recommendations": resume_tips(categorized, gap),
    }


CHATBOT_INTENTS = [
    (["hi", "hello", "hey", "salam", "assalam"], "greeting"),
    (["thank", "shukriya", "thanks"], "thanks"),
    (["what is skillbridge", "how does this work", "what can you do", "help me"], "about"),
    (["don't know where", "dont know where", "how do i start", "where do i start", "not sure where to start", "no idea what to do", "confused about my career", "new to this", "just starting out"], "getting_started"),
    (["how to apply", "how do i apply", "how can i apply", "how will i apply", "how i apply", "apply for job", "apply for a job", "apply for jobs", "apply", "applying", "aply", "aplly", "appply"], "how_to_apply"),
    (["skills needed for", "skills required for", "skills for"], "skills_for_role"),
    (["match", "score", "how am i doing"], "match_score"),
    (["best career", "which career", "career for me", "suit me"], "career_fit"),
    (["what should i learn", "learn next", "next skill"], "next_skill"),
    (["improve my cv", "improve cv", "resume tips", "cv tips"], "cv_tips"),
    (["interview", "prepare for interview"], "interview_prep"),
    (["certification", "certificate"], "certifications"),
]


FUZZY_THRESHOLD = 0.82  # how close a word must be to a keyword to count as a typo


def _intent_exact(msg: str) -> str | None:
    """Precise keyword match (word-boundary, optional trailing 's')."""
    for keywords, name in CHATBOT_INTENTS:
        if any(re.search(r"\b" + re.escape(k) + r"s?\b", msg) for k in keywords):
            return name
    return None


def _phrase_matches_fuzzy(msg_words: list[str], keyword: str) -> bool:
    """Every word of the keyword must appear in the message — short/critical words
    (<= 3 chars, e.g. 'cv', 'to', 'my') must match exactly, longer words may be
    misspelled slightly (e.g. 'aply' -> 'apply', 'intervew' -> 'interview')."""
    for kw in keyword.split():
        if len(kw) <= 3:
            if kw not in msg_words:
                return False
        else:
            if not any(difflib.SequenceMatcher(None, kw, w).ratio() >= FUZZY_THRESHOLD for w in msg_words):
                return False
    return True


def _intent_fuzzy(msg: str) -> str | None:
    """Typo-tolerant fallback used only when no exact keyword matched."""
    words = re.findall(r"[a-z]+", msg)
    if not words:
        return None
    for keywords, name in CHATBOT_INTENTS:
        if any(_phrase_matches_fuzzy(words, k) for k in keywords):
            return name
    return None


_ML_PREDICT = None
_ML_TRIED = False


def _get_ml_predictor():
    """Lazily grab the fine-tuned classifier if it (and its deps) are available.
    Returns None when the model isn't trained or transformers isn't installed."""
    global _ML_PREDICT, _ML_TRIED
    if not _ML_TRIED:
        _ML_TRIED = True
        try:
            from ml.advisor_model import predict_intent
            _ML_PREDICT = predict_intent
        except Exception:
            _ML_PREDICT = None
    return _ML_PREDICT


def _intent_ml(message: str) -> str | None:
    """Intent from the trained DistilBERT model (only if confident and on-topic)."""
    predict = _get_ml_predictor()
    if predict is None:
        return None
    intent, _confidence = predict(message)
    if intent and intent != "fallback":
        return intent
    return None


def chatbot_reply(message: str, user_skills: list[str], role: str | None, gap: dict | None) -> str:
    msg = message.lower()
    # 1) Exact keyword match — instant and always correct when it fires.
    # 2) Fine-tuned model — understands novel phrasings/typos (if trained & installed).
    # 3) Fuzzy keyword match — lightweight typo tolerance as a final fallback.
    intent = _intent_exact(msg) or _intent_ml(message) or _intent_fuzzy(msg)

    if intent == "greeting":
        return ("Hi! I'm your AI Career Advisor. I can help you pick a career path, tell you what to learn next, "
                "review your CV, prep you for interviews, or recommend certifications — just ask.")

    if intent == "thanks":
        return "You're welcome! Keep pushing on your roadmap — consistency beats intensity. Anything else you'd like to ask?"

    if intent == "getting_started":
        if not user_skills:
            return ("No problem — everyone starts somewhere. Here's how to begin: "
                    "(1) Go to CV Upload and add any skills you have, even basic ones from school/college projects, part-time work, or hobbies — there's no bar too low. "
                    "(2) Go to Skill Analysis and try 2-3 different target roles (e.g. Web Developer, Data Analyst) to see which one you already match best. "
                    "(3) Open the Roadmap for your best-fit role and just start the first Beginner topic this week. "
                    "(4) Come back and ask me 'what should I learn next?' whenever you finish something.")
        return ("You've already got a head start with some skills logged — here's your next move: "
                "(1) Set a target role on Skill Analysis if you haven't (or try a couple to compare match scores), "
                "(2) follow the Beginner phase of your Roadmap one topic at a time, "
                "(3) check Opportunities for entry-level/internship roles you already partially match — applying while learning is normal, "
                "(4) ask me anytime you're stuck on what to do next.")

    if intent == "how_to_apply":
        return ("Go to the Opportunities page — I've built a 'How to Apply Based on Your CV' section there with a "
                "step-by-step plan using your actual match scores: which roles to apply to first, how to reorder your "
                "CV to lead with the right skills, a short cover-message template, and application tracking tips. "
                "Each listing also has direct search links on Rozee.pk, LinkedIn, and Indeed.")

    if intent == "about":
        return (f"SkillBridge AI compares your skills against real job-market requirements for {len(ROLES)} career tracks "
                "across Computer Science, Civil, Mechanical & Electrical Engineering, and Business & Finance — "
                "it shows your match score and missing skills, builds a phased learning roadmap with free resources, "
                "and matches you to Pakistani job/internship/freelance opportunities. Try the Skill Analysis and Roadmap pages.")

    if intent == "skills_for_role":
        matched_role = next((r for r in ROLES if r.lower() in msg), None)
        if matched_role:
            req = all_required_skills(matched_role)
            return f"To become a {matched_role}, you'll need: {', '.join(req)}."
        return f"I track these career tracks: {', '.join(ROLES.keys())}. Ask 'skills for <role name>' for a specific one."

    if intent == "match_score":
        if gap:
            return f"You're currently at a {gap['match_percent']}% match for {role}, with {len(gap['matched_skills'])} of {len(gap['required_skills'])} required skills covered."
        return "Set a target role on the Skill Analysis page first, and I'll show your live match score here."

    if intent == "career_fit":
        if not user_skills:
            return "Add some skills to your profile first, then I can match you to the best-fitting roles like Web Developer, Data Analyst, or Cybersecurity Analyst."
        scored = []
        for r in ROLES:
            req = all_required_skills(r)
            us = {s.lower() for s in user_skills}
            pct = round(100 * len([s for s in req if s.lower() in us]) / len(req))
            scored.append((r, pct))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:3]
        return "Based on your current skills, your best-fitting roles are: " + ", ".join(f"{r} ({p}% match)" for r, p in top) + "."

    if intent == "next_skill":
        if gap and gap.get("missing_skills"):
            nxt = gap["missing_skills"][:3]
            return f"For {gap['role']}, focus on learning these next: {', '.join(nxt)}. Start with the first one and build a small project to practice it."
        return "Select a target role and run a skill-gap analysis first — I'll tell you exactly which skills to prioritize."

    if intent == "cv_tips":
        return ("Go to the CV Upload page — I've already generated an AI-Improved CV for you there, with a "
                "rewritten professional summary, cleaned-up skill sections, and project suggestions, "
                "downloadable as a PDF. Quick wins in the meantime: (1) lead with a 2-line summary tailored to "
                "the job title, (2) quantify achievements ('reduced load time by 30%' beats 'improved performance'), "
                "(3) match skills to the job description keywords, and (4) add links to GitHub/portfolio projects.")

    if intent == "interview_prep":
        return ("Interview prep checklist: (1) Practice DSA problems on LeetCode/HackerRank for technical roles, "
                "(2) prepare 3-4 STAR-format stories for behavioral questions, "
                "(3) research the company and its products, "
                "(4) prepare questions to ask the interviewer, and "
                "(5) do a mock interview with a friend or on Pramp.")

    if intent == "certifications":
        certs = recommend_certifications(role)
        if role:
            return f"For {role}, the most valuable certification(s) to pursue are: {', '.join(certs)}. Most have free study material — check the Roadmap page for direct links."
        return ("Valuable certifications by field: Software/Cloud -> AWS Certified Cloud Practitioner; "
                "Data -> Google Data Analytics Certificate; "
                "Cybersecurity -> CompTIA Security+; "
                "Project roles -> PMP. Pick one aligned with your target role.")

    if role and gap:
        return (f"You're at a {gap['match_percent']}% match for {role}. "
                f"Your top missing skills are {', '.join(gap['missing_skills'][:3]) or 'none — great job!'}. "
                "Ask me 'what should I learn next?' or 'how can I improve my CV?' for specific guidance.")

    return ("I can help with: choosing a career path, deciding what to learn next, improving your CV, "
            "interview preparation, recommending certifications, or listing skills needed for a specific role "
            "(e.g. 'skills for Cloud Engineer'). Try asking 'What should I learn next?'")
