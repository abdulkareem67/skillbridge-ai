"""Translation and locale handling.

There is no build step here, so instead of a framework this is a small runtime:
UI strings live in ``locales/<code>.json`` and templates look them up with
``t("namespace.key")``. English is the source language and the fallback for any
key a locale hasn't translated yet — a missing translation shows the English
text, never a raw key.

Only locales that actually have a file are offered, so the language switcher
appears exactly when there's more than one language to switch to. Adding a
language is therefore a drop-in: write ``locales/ur.json`` and it lights up, no
code change. The registry below just records each language's display name and
writing direction so the rest of the app doesn't hard-code them.
"""
import json
from pathlib import Path

DEFAULT_LOCALE = "en"
LOCALE_COOKIE = "locale"

# Every language we intend to support, with its endonym (the name in its own
# script) and text direction. A language appears in the UI only once its JSON
# file exists; until then this is just intent.
LOCALE_INFO = {
    "en": {"name": "English", "dir": "ltr"},
    "ur": {"name": "اردو", "dir": "rtl"},
    "ar": {"name": "العربية", "dir": "rtl"},
    "hi": {"name": "हिन्दी", "dir": "ltr"},
    "bn": {"name": "বাংলা", "dir": "ltr"},
    "zh": {"name": "中文", "dir": "ltr"},
}
RTL_LOCALES = {code for code, info in LOCALE_INFO.items() if info["dir"] == "rtl"}

_LOCALES_DIR = Path(__file__).resolve().parent / "locales"

# Loaded once at import. The set of files doesn't change at runtime, and English
# is always present because the app ships it.
_translations: dict[str, dict] = {}


def _load() -> None:
    for path in sorted(_LOCALES_DIR.glob("*.json")):
        code = path.stem
        if code not in LOCALE_INFO:
            continue
        try:
            _translations[code] = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            # A broken locale file must never take the site down; skip it and
            # fall back to English for that language.
            continue


_load()


def available_locales() -> list[str]:
    """Locale codes that have a file, English first."""
    codes = [c for c in LOCALE_INFO if c in _translations]
    return sorted(codes, key=lambda c: (c != DEFAULT_LOCALE, c))


def is_supported(code: str | None) -> bool:
    return bool(code) and code in _translations


def direction(locale: str) -> str:
    return LOCALE_INFO.get(locale, {}).get("dir", "ltr")


def _lookup(locale: str, key: str):
    """Walk the dotted key into a locale's nested dict; None if absent."""
    node = _translations.get(locale)
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None


def translate(key: str, locale: str = DEFAULT_LOCALE, **variables) -> str:
    """The string for ``key`` in ``locale``, falling back to English then the key.

    ``{name}`` style placeholders are filled from ``variables``. A missing
    variable leaves its placeholder untouched rather than raising, so a template
    change can never 500 a page over a copy detail.
    """
    text = _lookup(locale, key)
    if text is None and locale != DEFAULT_LOCALE:
        text = _lookup(DEFAULT_LOCALE, key)
    if text is None:
        # Surfacing the key (not an empty string) makes a missing entry obvious
        # in development instead of silently blank.
        return key
    if variables:
        try:
            return text.format(**variables)
        except (KeyError, IndexError, ValueError):
            return text
    return text


def negotiate_locale(request) -> str:
    """Pick the locale for this request.

    Order: a ?lang= in the URL (what the hreflang alternates link to), then an
    explicit cookie the person set, then the browser's Accept-Language, then
    English. Only ever returns a locale we actually have a file for.
    """
    query = getattr(request, "query_params", None)
    requested = query.get("lang") if query is not None else None
    if is_supported(requested):
        return requested

    cookie = request.cookies.get(LOCALE_COOKIE)
    if is_supported(cookie):
        return cookie

    header = request.headers.get("accept-language", "")
    for part in header.split(","):
        code = part.split(";")[0].strip().lower()
        if not code:
            continue
        base = code.split("-")[0]
        if is_supported(base):
            return base
    return DEFAULT_LOCALE


def js_bundle(locale: str) -> dict[str, str]:
    """The whole ``js`` namespace for this locale, English-filled, as flat keys.

    Everything the front-end renders at runtime lives under ``js`` in the locale
    files, so the page can translate any client-built string from the same
    source as the server without shipping the rest of the copy to the browser.
    """
    base = dict(_translations.get(DEFAULT_LOCALE, {}).get("js", {}))
    base.update(_translations.get(locale, {}).get("js", {}))
    return base
