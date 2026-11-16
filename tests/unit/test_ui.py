# The chat page: its pages, the security headers, the login, sign-up and logout through the
# API, the texts in both languages and the rules for the page files. A new app database for
# each test, no model

import json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from mrag import auth, db, ui
from mrag.api import app
from mrag.translations import LANGUAGES, TEXT, translator

PASSWORD = "correct horse battery staple"
TEMPLATES = ui.HERE / "templates" / "ui"


@pytest.fixture
def client(database):
    return TestClient(app)


def page_config(response):
    found = re.search(
        r'<script type="application/json" id="page-config">(.*?)</script>', response.text
    )
    assert found, "the page has no settings block"
    return json.loads(found.group(1))


def open_page(client, path="/login"):
    # Opens a page like a browser and returns the token of its session for the forms
    response = client.get(path)
    assert response.status_code == 200
    return {auth.CSRF_HEADER: page_config(response)["csrf"]}


def set_option(key, value):
    with db.get_sessionmaker()() as s:
        s.merge(db.AppSetting(key=key, value=value))
        s.commit()


def add_user(email="ada@example.org", blocked=False):
    with db.get_sessionmaker()() as s:
        user = auth.create_user(s, email, "Ada", PASSWORD)
        user.blocked = blocked
        s.commit()


def sessions():
    with db.get_sessionmaker()() as s:
        return [(row.user_id is not None) for row in s.scalars(select(db.BrowserSession))]


# Pages and headers


def test_a_first_visit_gets_a_guest_session_and_the_login_page(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Welcome back" in response.text
    assert auth.COOKIE in response.cookies
    assert sessions() == [False]
    config = page_config(response)
    assert config["user"] is None and len(config["csrf"]) >= 43
    # The same browser keeps its session on the next page
    client.get("/signup")
    assert sessions() == [False]


def test_every_page_has_the_security_headers(client):
    for path in ("/login", "/signup", "/v1/health"):
        headers = client.get(path).headers
        assert headers["content-security-policy"] == ui.CSP
        assert "script-src 'self'" in ui.CSP and "unsafe-inline" not in ui.CSP
        for name, value in ui.SECURITY_HEADERS.items():
            assert headers[name] == value
    assert client.get("/login").headers["cache-control"] == "no-store"


def test_the_api_documentation_keeps_working_without_the_csp(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"


def test_guests_see_the_start_page_until_an_admin_turns_guest_mode_off(client):
    assert client.get("/").status_code == 200
    assert '<a class="btn-ghost btn-block" href="/">' in client.get("/login").text
    set_option("guest_mode", False)
    response = client.get("/", follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, "/login")
    assert '<a class="btn-ghost btn-block" href="/">' not in client.get("/login").text


def test_the_css_and_scripts_load_with_a_fingerprint(client):
    page = client.get("/login").text
    links = re.findall(r'(?:href|src)="(/static/[^"]+)"', page)
    assert {link.split("?")[0] for link in links} == {"/static/style.css", "/static/auth.js"}
    for link in links:
        assert re.search(r"\?v=[0-9a-f]{10}$", link)
        assert client.get(link).status_code == 200


# Login, sign-up and logout


def test_login_starts_a_new_session_and_ends_the_guest_one(client):
    add_user()
    headers = open_page(client)
    guest_cookie = client.cookies[auth.COOKIE]
    response = client.post(
        "/v1/auth/login",
        json={"email": "ADA@example.org", "password": PASSWORD},
        headers=headers,
    )
    assert response.json() == {"name": "Ada", "email": "ada@example.org", "role": "member"}
    assert client.cookies[auth.COOKIE] != guest_cookie
    assert sessions() == [True]
    assert client.get("/login", follow_redirects=False).headers["location"] == "/"
    assert '<span class="account-name" id="accountName">Ada</span>' in client.get("/").text


@pytest.mark.parametrize("case", ["wrong password", "unknown email", "blocked"])
def test_every_failed_login_gives_the_same_answer(client, case):
    add_user(blocked=case == "blocked")
    email = "grace@example.org" if case == "unknown email" else "ada@example.org"
    password = "wrong password here" if case == "wrong password" else PASSWORD
    response = client.post(
        "/v1/auth/login", json={"email": email, "password": password}, headers=open_page(client)
    )
    assert (response.status_code, response.json()) == (401, {"detail": "login_failed"})


def test_login_without_the_page_token_is_refused(client):
    add_user()
    client.get("/login")
    response = client.post(
        "/v1/auth/login", json={"email": "ada@example.org", "password": PASSWORD}
    )
    assert response.json() == {"detail": "forged_request"}


def test_keep_me_logged_in_gives_a_lasting_cookie(client):
    add_user()
    response = client.post(
        "/v1/auth/login",
        json={"email": "ada@example.org", "password": PASSWORD, "remember": True},
        headers=open_page(client),
    )
    assert f"max-age={30 * 24 * 3600}" in response.headers["set-cookie"].lower()


def test_sign_up_is_on_by_default_and_an_admin_can_turn_it_off(client):
    assert '<a href="/signup">Create one</a>' in client.get("/login").text
    set_option("signup_open", False)
    assert '<a href="/signup">' not in client.get("/login").text
    headers = open_page(client, "/signup")
    assert "Sign-up is turned off" in client.get("/signup").text
    response = client.post(
        "/v1/auth/signup",
        json={"name": "Ada", "email": "ada@example.org", "password": PASSWORD},
        headers=headers,
    )
    assert (response.status_code, response.json()) == (403, {"detail": "signup_closed"})


def test_sign_up_creates_a_member_and_logs_in(client):
    set_option("signup_open", True)
    headers = open_page(client, "/signup")
    response = client.post(
        "/v1/auth/signup",
        json={"name": "Ada", "email": "ada@example.org", "password": PASSWORD},
        headers=headers,
    )
    assert response.json()["role"] == "member"
    assert sessions() == [True]
    assert '<span class="account-name" id="accountName">Ada</span>' in client.get("/").text


@pytest.mark.parametrize(
    ("password", "code"),
    [("short one", "password_too_short"), ("1qaz2wsx3edc4rfv", "password_common")],
)
def test_sign_up_refuses_weak_passwords(client, password, code):
    set_option("signup_open", True)
    response = client.post(
        "/v1/auth/signup",
        json={"name": "Ada", "email": "ada@example.org", "password": password},
        headers=open_page(client, "/signup"),
    )
    assert (response.status_code, response.json()) == (400, {"detail": code})


def test_logout_ends_the_session(client):
    add_user()
    headers = open_page(client)
    client.post(
        "/v1/auth/login", json={"email": "ada@example.org", "password": PASSWORD}, headers=headers
    )
    headers = {auth.CSRF_HEADER: page_config(client.get("/"))["csrf"]}
    assert client.post("/v1/auth/logout", headers=headers).status_code == 204
    assert sessions() == []
    assert page_config(client.get("/"))["user"] is None


def test_a_blocked_user_starts_again_as_a_guest(client):
    add_user()
    client.post(
        "/v1/auth/login",
        json={"email": "ada@example.org", "password": PASSWORD},
        headers=open_page(client),
    )
    with db.get_sessionmaker()() as s:
        s.scalars(select(db.User)).one().blocked = True
        s.commit()
    page = client.get("/")
    assert (
        '<span class="account-name" id="accountName">Ada</span>' not in page.text
        and page_config(page)["user"] is None
    )
    assert sessions() == [False]


# Texts


def test_both_languages_have_every_text():
    assert set(LANGUAGES) == set(TEXT)
    assert set(TEXT["en"]) == set(TEXT["sv"])
    for key in TEXT["en"]:
        placeholders = {lang: set(re.findall(r"\{(\w+)\}", TEXT[lang][key])) for lang in TEXT}
        assert placeholders["en"] == placeholders["sv"], key


def test_every_error_code_of_the_login_has_a_text():
    codes = set(re.findall(r'AccountError\("(\w+)"\)', (ui.HERE / "auth.py").read_text()))
    codes |= {"login_failed", "signup_closed", "forged_request", "login_required"}
    codes |= {"password_match", "invalid_input", "network", "unknown"}
    missing = {code for code in codes if f"err_{code}" not in TEXT["en"]}
    # password_wrong belongs to the account settings, which add their texts with them
    assert missing <= {"password_wrong", "role_invalid"}


def test_the_language_cookie_switches_the_page_to_swedish(client):
    client.cookies.set("lang", "sv")
    page = client.get("/login")
    assert "Välkommen tillbaka" in page.text and '<html lang="sv"' in page.text
    client.cookies.set("lang", "xx")
    assert '<html lang="en"' in client.get("/login").text


def test_user_text_in_a_translation_is_filled_in_once():
    tr = translator("en")
    assert tr("welcome_user", name="{name} <b>") == "How can I help you, {name} <b>?"


def test_a_name_with_html_is_shown_as_text(client):
    set_option("signup_open", True)
    client.post(
        "/v1/auth/signup",
        json={"name": "<script>alert(1)</script>", "email": "x@example.org", "password": PASSWORD},
        headers=open_page(client, "/signup"),
    )
    page = client.get("/").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


# Rules for the page files


def test_pages_have_no_inline_scripts_and_no_inline_styles():
    for path in TEMPLATES.glob("*.html"):
        html = path.read_text()
        for tag in re.findall(r"<script[^>]*>", html):
            assert 'src="' in tag or 'type="application/json"' in tag, f"{path.name}: {tag}"
        assert "style=" not in html, path.name
        assert not re.search(r"\son[a-z]+=", html), f"{path.name} has an inline event handler"


def test_scripts_never_insert_text_as_html():
    for path in (ui.STATIC).glob("*.js"):
        for line in path.read_text().splitlines():
            assert "insertAdjacentHTML" not in line and "outerHTML" not in line, path.name
            found = re.search(r"innerHTML\s*=\s*(.+);", line)
            if found:
                # Empty, a fixed icon or the answer HTML the server made safe (test_chat_page.py).
                # "icon" is the argument of menuButton, which only ever gets one of ICONS
                value = found.group(1)
                assert value in ('""', "msg.html", "icon") or value.startswith("ICONS."), line


def test_nothing_is_loaded_from_the_internet():
    files = [*TEMPLATES.glob("*.html"), *ui.STATIC.glob("*")]
    for path in files:
        text = path.read_text()
        assert not re.search(r"""(src|href)=["']https?://""", text), path.name
        assert "@import" not in text and "//cdn" not in text, path.name
