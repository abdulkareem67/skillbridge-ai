"""Sign in with Google (OpenID Connect, authorization-code flow).

Off unless GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set, so the site works
exactly as before until someone configures it. The secret never leaves the
server: the browser only ever sees Google's consent page and our callback.

Uses urllib from the standard library for the one outbound call, rather than
pulling in an HTTP client for a single POST.
"""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import jwt

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
VALID_ISSUERS = ("accounts.google.com", "https://accounts.google.com")

STATE_COOKIE = "oauth_state"
STATE_MAX_AGE = 10 * 60


class GoogleSignInError(Exception):
    """Anything that means we must not sign this person in."""


def client_id() -> str | None:
    return os.environ.get("GOOGLE_CLIENT_ID") or None


def client_secret() -> str | None:
    return os.environ.get("GOOGLE_CLIENT_SECRET") or None


def is_enabled() -> bool:
    return bool(client_id() and client_secret())


def redirect_uri(request) -> str:
    """Where Google sends the user back. Must match the console *exactly*.

    Set GOOGLE_REDIRECT_URI to pin it. Otherwise it's derived from the request,
    forced to https in production, where a proxy can make the app believe it was
    reached over plain http and produce a URI Google would reject.
    """
    explicit = os.environ.get("GOOGLE_REDIRECT_URI")
    if explicit:
        return explicit
    url = str(request.url_for("google_callback"))
    if os.environ.get("VERCEL") and url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    return url


def authorization_url(request, state: str) -> str:
    params = {
        "client_id": client_id(),
        "redirect_uri": redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)


def exchange_code(code: str, uri: str) -> dict:
    """Trade the one-time code for the user's verified identity claims."""
    body = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id(),
        "client_secret": client_secret(),
        "redirect_uri": uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise GoogleSignInError("Could not reach Google to finish signing in.") from exc

    id_token = payload.get("id_token")
    if not id_token:
        raise GoogleSignInError("Google did not return an identity token.")
    return verify_claims(id_token)


def verify_claims(id_token: str) -> dict:
    """Check the ID token is meant for us, current, and names a verified email.

    The token comes straight from Google's token endpoint over TLS, in exchange
    for a code plus our client secret, so Google's guidance is that its signature
    need not be re-verified. What must still be checked is who it was issued for
    and by whom — otherwise a token minted for some other app could sign
    someone in here.
    """
    try:
        claims = jwt.decode(id_token, options={"verify_signature": False})
    except jwt.PyJWTError as exc:
        raise GoogleSignInError("Google returned an unreadable identity token.") from exc

    if claims.get("iss") not in VALID_ISSUERS:
        raise GoogleSignInError("Identity token was not issued by Google.")
    audience = claims.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if client_id() not in audiences:
        raise GoogleSignInError("Identity token was issued for a different application.")
    if int(claims.get("exp", 0)) < time.time():
        raise GoogleSignInError("Identity token has expired.")
    # Signing in by email links to any existing account with that address, so
    # only an address Google has actually verified may do that.
    if not claims.get("email") or claims.get("email_verified") not in (True, "true"):
        raise GoogleSignInError("Your Google account's email address isn't verified.")
    return claims
