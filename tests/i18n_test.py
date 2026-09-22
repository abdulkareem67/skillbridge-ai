"""Phase 4: the translation engine and the locale plumbing on every page.

The app ships English only for now, so these test the machinery (lookup,
fallback, negotiation, direction) plus the guarantee that every page carries the
locale attributes and never leaks a raw translation key.
"""
import re

import pytest

PAGES_PUBLIC = ["/", "/login", "/register", "/demo", "/privacy", "/terms"]
PAGES_AUTHED = ["/dashboard", "/cv-upload", "/skill-analysis", "/roadmap", "/opportunities", "/advisor", "/settings", "/onboarding"]

# The namespaces used by t("namespace.key"). If one of these appears verbatim in
# visible page text, a key wasn't resolved.
NAMESPACES = [
    "common.", "nav.", "footer.", "auth.", "login.", "register.", "landing.",
    "onboarding.", "settings.", "demo.", "dashboard.", "cv.", "analysis.",
    "roadmap.", "opportunities.", "advisor.", "legal.", "meta.",
]


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
def test_translate_returns_english():
    from app import i18n

    assert i18n.translate("nav.dashboard", "en") == "Dashboard"


def test_missing_key_returns_the_key_not_blank():
    from app import i18n

    assert i18n.translate("nav.does_not_exist", "en") == "nav.does_not_exist"


def test_unknown_locale_falls_back_to_english():
    from app import i18n

    # "ur" isn't shipped, so it must fall back rather than return blank.
    assert i18n.translate("nav.dashboard", "ur") == "Dashboard"


def test_variables_are_interpolated():
    from app import i18n

    out = i18n.translate("common.switch_account", "en", count=3)
    assert "3" in out and "{count}" not in out


def test_a_missing_variable_never_raises():
    from app import i18n

    # Leaves the placeholder rather than 500-ing the page over a copy detail.
    assert "{count}" in i18n.translate("common.switch_account", "en")


def test_direction_registry():
    from app import i18n

    assert i18n.direction("en") == "ltr"
    assert i18n.direction("ur") == "rtl"
    assert i18n.direction("ar") == "rtl"


def test_only_english_is_shipped_today():
    """A reminder of the current state: adding a locale file lights it up."""
    from app import i18n

    assert i18n.available_locales() == ["en"]


@pytest.mark.parametrize(
    "header, expected",
    [
        ("ur,en;q=0.9", "en"),   # ur not shipped -> English
        ("en-GB,en;q=0.8", "en"),
        ("", "en"),
        ("fr", "en"),
    ],
)
def test_negotiate_from_accept_language(header, expected):
    from app import i18n

    class Req:
        cookies = {}
        query_params = {}
        headers = {"accept-language": header}

    assert i18n.negotiate_locale(Req()) == expected


def test_js_bundle_is_flat_and_has_client_keys():
    from app import i18n

    bundle = i18n.js_bundle("en")
    assert bundle["err_network"]
    assert all(isinstance(v, str) for v in bundle.values())


# --------------------------------------------------------------------------- #
# Page plumbing
# --------------------------------------------------------------------------- #
def test_every_public_page_declares_locale(client):
    for path in PAGES_PUBLIC:
        body = client.get(path).text
        assert 'lang="en"' in body, path
        assert 'dir="ltr"' in body, path
        assert 'hreflang="en"' in body, path
        assert 'hreflang="x-default"' in body, path


def test_authed_pages_declare_locale(client, account):
    for path in PAGES_AUTHED:
        # onboarding/dashboard may redirect depending on setup; follow it.
        body = client.get(path, follow_redirects=True).text
        assert 'lang="en"' in body, path


def test_no_page_leaks_a_raw_translation_key(client, account):
    for path in PAGES_PUBLIC + PAGES_AUTHED:
        body = client.get(path, follow_redirects=True).text
        assert "{{ t(" not in body, (path, "unrendered t()")
        assert "{{ ui." not in body, (path, "unrendered macro")
        # a namespace prefix inside visible text (not an asset path) means a key leaked
        for ns in NAMESPACES:
            for m in re.findall(r">[^<>]*\b" + re.escape(ns) + r"[a-z_]+\b[^<>]*<", body):
                assert ".js" in m or ".css" in m, (path, "leaked key", m[:40])


def test_js_message_bundle_is_injected(client):
    assert "__I18N__" in client.get("/").text


def test_set_language_ignores_unknown_codes(client):
    # Only shipped locales may be set; an unknown code changes nothing.
    r = client.get("/set-language/xx", follow_redirects=False)
    assert "locale=" not in r.headers.get("set-cookie", "")
