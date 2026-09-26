"""Per-market configuration.

The product serves people job-hunting in different countries, so anything that
is true of one country only — which job boards are worth searching, which
professional licence matters, which currency salaries are quoted in — belongs
here rather than hard-coded into the engine.

`GLOBAL` is the fallback and must stay usable on its own: a visitor who has told
us nothing about where they are still gets working job-board links.

Markets are identified by ISO 3166-1 alpha-2 codes so the same keys can later be
matched against a geo-IP country header.
"""
import re
from urllib.parse import quote_plus

# Boards that work anywhere. `{q}` is the url-encoded role title, `{loc}` the
# url-encoded location term for that market.
_GLOBAL_BOARDS = [
    ("LinkedIn", "https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}"),
    ("Glassdoor", "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}"),
]

_REMOTE_BOARDS = [
    ("RemoteOK", "https://remoteok.com/remote-{q}-jobs"),
    ("We Work Remotely", "https://weworkremotely.com/remote-jobs/search?term={q}"),
]

MARKETS = {
    "PK": {
        "name": "Pakistan",
        "location_term": "Pakistan",
        "currency": "PKR",
        "languages": ["en", "ur"],
        "cities": [
            "pakistan", "lahore", "karachi", "islamabad", "rawalpindi",
            "faisalabad", "peshawar", "quetta", "multan", "sialkot", "haripur",
        ],
        "boards": [
            ("Rozee.pk", "https://www.rozee.pk/job/jsearch/q/{q}"),
            ("Mustakbil", "https://www.mustakbil.com/jobs/search?q={q}"),
            ("BrightSpyre", "https://www.brightspyre.com/jobs/keyword/{q}"),
            ("Indeed", "https://pk.indeed.com/jobs?q={q}"),
        ],
        "internship_boards": [("Internee.pk", "https://internee.pk/?s={q}")],
        # Engineering practice is licensed per country; naming the right body
        # matters more than naming a body that happens to be local to us.
        "engineering_licence": "PEC (Pakistan Engineering Council) registration",
    },
    "AE": {
        "name": "United Arab Emirates",
        "location_term": "United Arab Emirates",
        "currency": "AED",
        "languages": ["en", "ar"],
        "cities": ["united arab emirates", "uae", "dubai", "abu dhabi", "sharjah", "ajman"],
        "boards": [
            ("Bayt.com", "https://www.bayt.com/en/uae/jobs/{q}-jobs/"),
            ("GulfTalent", "https://www.gulftalent.com/uae/jobs/title/{q}"),
            ("Naukrigulf", "https://www.naukrigulf.com/{q}-jobs"),
            ("Indeed", "https://ae.indeed.com/jobs?q={q}"),
        ],
        "internship_boards": [],
        "engineering_licence": "Society of Engineers – UAE registration",
    },
    "SA": {
        "name": "Saudi Arabia",
        "location_term": "Saudi Arabia",
        "currency": "SAR",
        "languages": ["en", "ar"],
        "cities": ["saudi arabia", "ksa", "riyadh", "jeddah", "dammam", "mecca", "medina"],
        "boards": [
            ("Bayt.com", "https://www.bayt.com/en/saudi-arabia/jobs/{q}-jobs/"),
            ("GulfTalent", "https://www.gulftalent.com/saudi-arabia/jobs/title/{q}"),
            ("Indeed", "https://sa.indeed.com/jobs?q={q}"),
        ],
        "internship_boards": [],
        "engineering_licence": "Saudi Council of Engineers membership",
    },
    "GB": {
        "name": "United Kingdom",
        "location_term": "United Kingdom",
        "currency": "GBP",
        "languages": ["en"],
        "cities": [
            "united kingdom", "uk", "england", "scotland", "wales", "london",
            "manchester", "birmingham", "leeds", "edinburgh", "glasgow", "bristol",
        ],
        "boards": [
            ("Reed", "https://www.reed.co.uk/jobs/{q}-jobs"),
            ("Totaljobs", "https://www.totaljobs.com/jobs/{q}"),
            ("Indeed", "https://uk.indeed.com/jobs?q={q}"),
        ],
        "internship_boards": [("Prospects", "https://www.prospects.ac.uk/search?query={q}")],
        "engineering_licence": "Chartered Engineer (CEng) registration",
    },
    "US": {
        "name": "United States",
        "location_term": "United States",
        "currency": "USD",
        "languages": ["en"],
        "cities": [
            "united states", "usa", "new york", "san francisco", "austin",
            "seattle", "chicago", "boston", "los angeles", "denver", "atlanta",
        ],
        "boards": [
            ("Indeed", "https://www.indeed.com/jobs?q={q}"),
            ("ZipRecruiter", "https://www.ziprecruiter.com/jobs-search?search={q}"),
        ],
        "internship_boards": [("Handshake", "https://joinhandshake.com/search/?query={q}")],
        "engineering_licence": "Professional Engineer (PE) licence",
    },
    "GLOBAL": {
        "name": "Global",
        "location_term": "",
        "currency": "USD",
        "languages": ["en"],
        "cities": [],
        "boards": [("Indeed", "https://www.indeed.com/jobs?q={q}")],
        "internship_boards": [],
        "engineering_licence": "your national engineering body's registration",
    },
}

DEFAULT_MARKET = "GLOBAL"


def market_for_location(location: str | None) -> str:
    """Best-guess market code for a free-text location. Falls back to GLOBAL."""
    if not location:
        return DEFAULT_MARKET
    needle = location.strip().lower()
    if not needle or needle == "remote":
        return DEFAULT_MARKET
    for code, market in MARKETS.items():
        if code == DEFAULT_MARKET:
            continue
        # Whole words only: a plain substring test put "Milwaukee" and "Ukraine"
        # in the UK because both contain "uk".
        if any(re.search(r"(?<![a-z])" + re.escape(city) + r"(?![a-z])", needle) for city in market["cities"]):
            return code
    return DEFAULT_MARKET


def get_market(code: str | None) -> dict:
    return MARKETS.get(code or DEFAULT_MARKET, MARKETS[DEFAULT_MARKET])


def job_board_links(title: str, opp_type: str, market_code: str | None = None) -> list[dict]:
    """Where to search for a real opening for this role, in the right country.

    These point at live job boards rather than pretending to be live listings
    themselves, so the advice stays true however stale the example roles get.
    """
    market = get_market(market_code)
    query = quote_plus(title.strip())
    slug = quote_plus(title.strip().lower().replace(" ", "-"))
    location_term = quote_plus(market["location_term"]) if market["location_term"] else ""

    def build(entries):
        links = []
        for label, template in entries:
            url = template.replace("{q}", slug if "-jobs" in template or "/title/" in template else query)
            url = url.replace("{loc}", location_term)
            links.append({"label": f"Search on {label}", "url": url})
        return links

    links = build(market["boards"]) + build(_GLOBAL_BOARDS)
    if opp_type == "Internship":
        links += build(market["internship_boards"])
    if opp_type in ("Remote", "Freelance"):
        links += build(_REMOTE_BOARDS)
    return links
