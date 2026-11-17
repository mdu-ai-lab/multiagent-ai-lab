# Passwords, sessions, the token against forged requests and the roles, on a new app database
# for each test. A small FastAPI app checks the parts that ui.py and api.py use.

from datetime import timedelta
from typing import Annotated

import pytest
from argon2 import PasswordHasher
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from mrag import auth, db

GOOD = "correct horse battery staple"


def add_user(s: Session, email: str = "Ada@Example.org", role: str = "member") -> db.User:
    return auth.create_user(s, email, "Ada Lovelace", GOOD, role)


# Passwords


def test_hashes_are_argon2id_at_or_above_the_owasp_minimum():
    stored = auth.hash_password(GOOD)
    kind, version, settings, *_ = stored.removeprefix("$").split("$")
    values = dict(item.split("=") for item in settings.split(","))
    assert (kind, version) == ("argon2id", "v=19")
    assert int(values["m"]) >= 19 * 1024 and int(values["t"]) >= 2 and int(values["p"]) >= 1
    assert auth.hash_password(GOOD) != stored, "every hash needs its own salt"


def test_a_password_is_checked_in_its_normal_unicode_form():
    stored = auth.hash_password("Ångström is a unit of length")
    assert auth.verify_password(stored, "Ångström is a unit of length")
    assert not auth.verify_password(stored, "Angstrom is a unit of length")


def test_a_broken_hash_counts_as_a_wrong_password():
    assert not auth.verify_password("not a hash", GOOD)


@pytest.mark.parametrize(
    ("password", "problem"),
    [
        ("a" * 14, "password_too_short"),
        ("a" * 129, "password_too_long"),
        ("1qaz2wsx3edc4rfv", "password_common"),
        ("1QAZ2WSX3EDC4RFV", "password_common"),
        ("ada.lovelace@example.org", "password_personal"),
        ("Ada Lovelace the first", None),
        ("only lower case letters here", None),
        ("kettle-lamp-oak", None),
        ("a" * 128, None),
    ],
)
def test_password_rules(password, problem):
    assert auth.password_problem(password, "ada.lovelace@example.org", "Ada") == problem


def test_the_common_password_list_is_read():
    # The licence header is skipped. Only the 48 long entries of Django's list are kept
    common = auth.common_passwords()
    assert len(common) == 48
    assert "1qaz2wsx3edc4rfv" in common
    assert all(15 <= len(word) <= 128 and word == word.lower() for word in common)


# Accounts and login


def test_an_email_is_saved_in_lower_case_and_only_once(session):
    user = add_user(session)
    assert user.email == "ada@example.org"
    with pytest.raises(auth.AccountError, match="email_taken"):
        add_user(session, "  ADA@example.ORG ")


@pytest.mark.parametrize(
    ("email", "name", "password", "code"),
    [
        ("no-at-sign", "Ada", GOOD, "email_invalid"),
        ("ada @example.org", "Ada", GOOD, "email_invalid"),
        ("ada@example.org", "  ", GOOD, "name_invalid"),
        ("ada@example.org", "Ada", "short", "password_too_short"),
    ],
)
def test_wrong_account_details_are_refused(session, email, name, password, code):
    with pytest.raises(auth.AccountError, match=code):
        auth.create_user(session, email, name, password)


def test_login_works_and_records_the_time(session):
    add_user(session)
    user = auth.check_login(session, " ADA@example.org", GOOD)
    assert user.last_login_at is not None


@pytest.mark.parametrize("case", ["unknown email", "wrong password", "blocked", "too long"])
def test_every_failed_login_looks_the_same(session, case, monkeypatch):
    user = add_user(session)
    email, password = "ada@example.org", GOOD
    if case == "unknown email":
        email = "grace@example.org"
    elif case == "wrong password":
        password = GOOD + "!"
    elif case == "blocked":
        user.blocked = True
    else:
        password = "a" * 10_000
    checks = []
    real_verify = auth.verify_password
    monkeypatch.setattr(auth, "verify_password", lambda *a: checks.append(1) or real_verify(*a))
    with pytest.raises(auth.LoginFailed):
        auth.check_login(session, email, password)
    # One hash check every time, so the time taken shows nothing either
    assert checks == [1]


def test_an_old_hash_is_renewed_at_login(session, monkeypatch):
    weak = PasswordHasher(time_cost=1, memory_cost=8 * 1024, parallelism=1)
    user = add_user(session)
    user.password_hash = weak.hash(GOOD)
    auth.check_login(session, "ada@example.org", GOOD)
    assert "m=65536,t=3,p=4" in user.password_hash
    assert auth.verify_password(user.password_hash, GOOD)


# Sessions


def test_only_the_hash_of_the_session_token_is_stored(session):
    token, row = auth.start_session(session, add_user(session))
    assert len(token) >= 43
    assert row.token_hash == auth.token_hash(token) != token
    assert auth.find_session(session, token) is row
    assert auth.find_session(session, token + "x") is None
    assert auth.find_session(session, None) is None


@pytest.mark.parametrize(
    ("remember", "unused", "ends"),
    [
        (False, timedelta(minutes=29), False),
        (False, timedelta(minutes=31), True),
        (True, timedelta(days=29), False),
        (True, timedelta(days=31), True),
    ],
)
def test_a_session_ends_after_its_time_without_use(session, remember, unused, ends):
    token, row = auth.start_session(session, add_user(session), remember)
    row.last_seen_at = db.utcnow() - unused
    assert (auth.find_session(session, token) is None) == ends


@pytest.mark.parametrize(("remember", "hours"), [(False, 12), (True, 30 * 24)])
def test_a_session_ends_after_its_total_time(session, remember, hours):
    token, row = auth.start_session(session, add_user(session), remember)
    assert row.expires_at - row.created_at == timedelta(hours=hours)
    row.expires_at = db.utcnow() - timedelta(seconds=1)
    assert auth.find_session(session, token) is None
    assert session.scalars(select(db.BrowserSession)).all() == []


def test_login_starts_a_new_session_and_ends_the_guest_one_with_its_chats(session):
    add_user(session)
    guest_token, guest = auth.start_session(session, None)
    session.add(db.Chat(session_id=guest.id, title="Guest chat"))
    session.flush()

    token, user = auth.log_in(session, "ada@example.org", GOOD, False, guest)
    session.commit()

    assert token != guest_token
    assert auth.find_session(session, guest_token) is None
    found = auth.find_session(session, token)
    assert found is not None and found.user_id == user.id
    assert session.scalars(select(db.Chat)).all() == []


def test_a_password_change_ends_every_session_and_keeps_this_browser(session):
    user = add_user(session)
    old_token, _ = auth.start_session(session, user)
    other_token, _ = auth.start_session(session, user)
    with pytest.raises(auth.AccountError, match="password_wrong"):
        auth.change_password(session, user, "not the password", "a brand new passphrase", False)

    token = auth.change_password(session, user, GOOD, "a brand new passphrase", False)

    assert auth.find_session(session, old_token) is None
    assert auth.find_session(session, other_token) is None
    assert auth.find_session(session, token) is not None
    assert auth.check_login(session, "ada@example.org", "a brand new passphrase") is user


def test_expired_sessions_are_removed(session):
    user = add_user(session)
    _, old = auth.start_session(session, user)
    _, unused = auth.start_session(session, user, remember=True)
    keep_token, _ = auth.start_session(session, user)
    old.expires_at = db.utcnow() - timedelta(minutes=1)
    unused.last_seen_at = db.utcnow() - timedelta(days=31)
    assert auth.remove_expired_sessions(session) == 2
    assert auth.find_session(session, keep_token) is not None


# The FastAPI parts


@pytest.fixture
def client(database):
    app = FastAPI()
    guard = [Depends(auth.check_request_origin)]

    @app.post("/guest", dependencies=guard)
    def guest(s: auth.DbSession) -> dict[str, str]:
        token, row = auth.start_session(s, None)
        s.commit()
        return {"token": token, "csrf": row.csrf_token}

    @app.get("/me")
    def me(user: Annotated[db.User, Depends(auth.require_user)]) -> dict[str, str]:
        return {"email": user.email}

    @app.post("/change", dependencies=guard)
    def change() -> dict[str, bool]:
        return {"done": True}

    @app.get("/admin")
    def admin(user: Annotated[db.User, Depends(auth.require_admin)]) -> dict[str, str]:
        return {"email": user.email}

    @app.post("/cookie")
    def cookie(response: auth.Response, request: auth.Request) -> None:
        auth.set_session_cookie(response, request, "abc", remember=False)

    return TestClient(app)


def log_in_client(client, role: str = "member") -> str:
    with db.get_sessionmaker()() as s:
        user = add_user(s, role=role)
        token, row = auth.start_session(s, user)
        csrf = row.csrf_token
        s.commit()
    client.cookies.set(auth.COOKIE, token)
    return csrf


def test_reading_needs_no_token_but_changing_needs_the_right_one(client):
    csrf = log_in_client(client)
    assert client.get("/me").json() == {"email": "ada@example.org"}
    assert client.post("/change").status_code == 403
    assert client.post("/change", headers={auth.CSRF_HEADER: "wrong"}).status_code == 403
    assert client.post("/change", headers={auth.CSRF_HEADER: csrf}).json() == {"done": True}


@pytest.mark.parametrize(
    "headers",
    [
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "same-site"},
        {"Origin": "https://evil.example"},
    ],
)
def test_a_request_from_another_site_is_refused_even_with_the_token(client, headers):
    csrf = log_in_client(client)
    answer = client.post("/change", headers={auth.CSRF_HEADER: csrf, **headers})
    assert (answer.status_code, answer.json()) == (403, {"detail": "forged_request"})


def test_the_same_site_headers_of_a_real_browser_pass(client):
    csrf = log_in_client(client)
    headers = {
        auth.CSRF_HEADER: csrf,
        "Sec-Fetch-Site": "same-origin",
        "Origin": "http://testserver",
    }
    assert client.post("/change", headers=headers).status_code == 200


def test_a_request_without_a_session_is_refused(client):
    assert client.post("/change", headers={auth.CSRF_HEADER: "anything"}).status_code == 403
    assert client.get("/me").status_code == 401


def test_only_admins_open_admin_routes(client):
    log_in_client(client, role="member")
    assert client.get("/admin").json() == {"detail": "admin_only"}
    client.cookies.clear()
    with db.get_sessionmaker()() as s:
        user = auth.create_user(s, "grace@example.org", "Grace", GOOD, "admin")
        token, _ = auth.start_session(s, user)
        s.commit()
    client.cookies.set(auth.COOKIE, token)
    assert client.get("/admin").json() == {"email": "grace@example.org"}


def test_a_blocked_user_is_logged_out_at_once(client):
    log_in_client(client)
    with db.get_sessionmaker()() as s:
        user = s.scalars(select(db.User)).one()
        user.blocked = True
        s.commit()
    assert client.get("/me").status_code == 401
    with db.get_sessionmaker()() as s:
        assert s.scalars(select(db.BrowserSession)).all() == []


@pytest.mark.parametrize(
    ("base", "secure"), [("http://testserver", False), ("https://testserver", True)]
)
def test_the_cookie_flags(client, base, secure):
    client.base_url = base
    header = client.post("/cookie").headers["set-cookie"].lower()
    assert "httponly" in header and "samesite=strict" in header and "path=/" in header
    assert ("secure" in header.replace("samesite", "")) == secure
    assert "max-age" not in header
