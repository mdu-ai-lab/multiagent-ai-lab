# The admin panel of the preview on a new app database: who may open it, the numbers, the
# users, the feedback, the settings and the activity log. Admins never see chat text, never
# change their own account here and the last admin always stays

import json
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from mrag import admin, api, auth, db

PASSWORD = "correct horse battery staple"


@pytest.fixture
def client(database):
    return TestClient(app=api.app)


def page_config(html):
    found = re.search(r'<script type="application/json" id="page-config">(.*?)</script>', html)
    assert found
    return json.loads(found.group(1))


def add_user(email, name="Someone", role="member", blocked=False):
    with db.get_sessionmaker()() as s:
        user = auth.create_user(s, email, name, PASSWORD, role)
        user.blocked = blocked
        s.commit()
        return user.id


def log_in(client, email):
    # Logs in through the login page and the API, as a browser does
    client.cookies.clear()
    csrf = page_config(client.get("/login").text)["csrf"]
    body = {"email": email, "password": PASSWORD}
    response = client.post("/v1/auth/login", json=body, headers={auth.CSRF_HEADER: csrf})
    assert response.is_success
    client.headers[auth.CSRF_HEADER] = page_config(client.get("/").text)["csrf"]


@pytest.fixture
def boss(client):
    # An admin, logged in
    user_id = add_user("boss@example.org", "Boss Person", role="admin")
    log_in(client, "boss@example.org")
    return user_id


def sessions_of(user_id):
    with db.get_sessionmaker()() as s:
        query = select(db.BrowserSession).where(db.BrowserSession.user_id == user_id)
        return len(s.scalars(query).all())


def log_entries():
    with db.get_sessionmaker()() as s:
        rows = s.scalars(select(db.AuditEntry).order_by(db.AuditEntry.id))
        return [(row.admin_label, row.action, row.target, row.details) for row in rows]


# Who may open the admin panel


def test_guests_go_to_the_login_and_members_see_not_allowed(client):
    response = client.get("/admin", follow_redirects=False)
    assert (response.status_code, response.headers["location"]) == (303, "/login")
    add_user("ada@example.org")
    log_in(client, "ada@example.org")
    page = client.get("/admin")
    assert page.status_code == 403 and "Only admins can open this page." in page.text
    for path in ("/v1/admin/stats", "/v1/admin/users", "/v1/admin/log"):
        assert client.get(path).json() == {"detail": "admin_only"}, path


def test_the_admin_panel_of_the_preview(client, boss):
    html = client.get("/admin").text
    for part in (
        'id="usersBody"',
        'id="feedbackList"',
        'id="guestMode"',
        'id="guestLimitForm"',
        'id="signupOpen"',
        'id="logBody"',
        'id="createUserForm"',
        "Allow guests",
    ):
        assert part in html, part
    config = page_config(html)
    assert config["me"] == {"id": boss, "name": "Boss Person", "email": "boss@example.org"}


def test_every_change_needs_the_token(client, boss):
    ada = add_user("ada@example.org")
    del client.headers[auth.CSRF_HEADER]
    for method, path, body in (
        ("post", "/v1/admin/users", {"name": "X", "email": "x@example.org", "password": PASSWORD}),
        ("patch", f"/v1/admin/users/{ada}", {"blocked": True}),
        ("post", f"/v1/admin/users/{ada}/reset-password", None),
        ("delete", f"/v1/admin/users/{ada}", None),
        ("patch", "/v1/admin/settings", {"signup_open": False}),
    ):
        kwargs = {"json": body} if body is not None else {}
        assert client.request(method, path, **kwargs).json() == {"detail": "forged_request"}, path


# Numbers and lists


def test_the_dashboard_numbers_and_never_any_chat_text(client, boss):
    ada = add_user("ada@example.org", "Ada")
    add_user("bad@example.org", blocked=True)
    with db.get_sessionmaker()() as s:
        chat = db.Chat(user_id=ada, title="Secret plans")
        s.add(chat)
        s.flush()
        s.add(db.Message(chat_id=chat.id, role="user", content="My secret question"))
        s.add(db.Message(chat_id=chat.id, role="assistant", content="A secret answer"))
        s.add(db.Feedback(user_id=ada, kind="idea", message="Dark mode"))
        s.add(db.GuestDay(day=db.utcnow().date(), messages=4))
        s.commit()
    stats = client.get("/v1/admin/stats").json()
    assert stats == {
        "users": 3,
        "admins": 1,
        "blocked": 1,
        "new_users": 3,
        "chats": 1,
        "messages": 1,
        "open_feedback": 1,
        "guest_today": 4,
    }
    users = client.get("/v1/admin/users").json()
    assert {u["email"]: u["chats"] for u in users} == {
        "boss@example.org": 0,
        "ada@example.org": 1,
        "bad@example.org": 0,
    }
    everything = json.dumps(
        [
            client.get(p).json()
            for p in ("/v1/admin/stats", "/v1/admin/users", "/v1/admin/feedback", "/v1/admin/log")
        ]
    )
    assert "secret" not in everything.lower()


# Users


def test_create_a_user(client, boss):
    body = {"name": "Grace", "email": "Grace@Example.org", "password": PASSWORD, "role": "admin"}
    assert "id" in client.post("/v1/admin/users", json=body).json()
    again = client.post("/v1/admin/users", json=body)
    assert (again.status_code, again.json()) == (400, {"detail": "email_taken"})
    weak = {**body, "email": "x@example.org", "password": "short"}
    assert client.post("/v1/admin/users", json=weak).json() == {"detail": "password_too_short"}
    assert log_entries()[-1] == ("boss@example.org", "create_user", "grace@example.org", "admin")


def test_block_and_unblock_end_the_logins(client, boss):
    ada = add_user("ada@example.org")
    with db.get_sessionmaker()() as s:
        auth.start_session(s, s.get(db.User, ada))
        s.commit()
    assert client.patch(f"/v1/admin/users/{ada}", json={"blocked": True}).json() == {
        "updated": True
    }
    assert sessions_of(ada) == 0
    with db.get_sessionmaker()() as s, pytest.raises(auth.LoginFailed):
        auth.check_login(s, "ada@example.org", PASSWORD)
    client.patch(f"/v1/admin/users/{ada}", json={"blocked": False})
    assert [entry[1] for entry in log_entries()] == ["block", "unblock"]


def test_a_role_change_ends_the_logins_of_that_user(client, boss):
    ada = add_user("ada@example.org")
    with db.get_sessionmaker()() as s:
        auth.start_session(s, s.get(db.User, ada))
        s.commit()
    client.patch(f"/v1/admin/users/{ada}", json={"role": "admin"})
    assert sessions_of(ada) == 0
    client.patch(f"/v1/admin/users/{ada}", json={"role": "member"})
    assert [entry[1] for entry in log_entries()] == ["make_admin", "make_member"]


def test_reset_password_gives_a_temporary_password_once(client, boss):
    ada = add_user("ada@example.org")
    with db.get_sessionmaker()() as s:
        auth.start_session(s, s.get(db.User, ada))
        s.commit()
    password = client.post(f"/v1/admin/users/{ada}/reset-password").json()["password"]
    # As in the preview: three groups of four easy letters, like abcd-efgh-jkmn
    assert re.fullmatch(r"[a-hj-km-np-z2-9]{4}(-[a-hj-km-np-z2-9]{4}){2}", password)
    assert sessions_of(ada) == 0
    with db.get_sessionmaker()() as s:
        assert auth.check_login(s, "ada@example.org", password)
        stored = s.scalars(select(db.User.password_hash).where(db.User.id == ada)).one()
        assert password not in stored


def test_delete_a_user_with_the_chats(client, boss):
    ada = add_user("ada@example.org")
    with db.get_sessionmaker()() as s:
        s.add(db.Chat(user_id=ada, title="Chat"))
        s.commit()
    assert client.delete(f"/v1/admin/users/{ada}").json() == {"deleted": True}
    with db.get_sessionmaker()() as s:
        assert s.get(db.User, ada) is None
        assert s.scalars(select(db.Chat)).all() == []
    assert log_entries()[-1][1:3] == ("delete_user", "ada@example.org")
    missing = client.delete(f"/v1/admin/users/{ada}")
    assert (missing.status_code, missing.json()) == (404, {"detail": "user_not_found"})


def test_an_admin_never_changes_the_own_account_here(client, boss):
    for method, path, body in (
        ("patch", f"/v1/admin/users/{boss}", {"blocked": True}),
        ("patch", f"/v1/admin/users/{boss}", {"role": "member"}),
        ("post", f"/v1/admin/users/{boss}/reset-password", None),
        ("delete", f"/v1/admin/users/{boss}", None),
    ):
        kwargs = {"json": body} if body is not None else {}
        assert client.request(method, path, **kwargs).json() == {"detail": "self"}, path


def test_the_last_admin_always_stays(client, boss):
    other = add_user("other@example.org", role="admin")
    log_in(client, "other@example.org")
    client.patch(f"/v1/admin/users/{boss}", json={"blocked": True})
    # Now "other" is the only active admin, so nobody can remove that account. The check is
    # the same for every admin, so it is run here from the panel of a second admin
    with db.get_sessionmaker()() as s:
        with pytest.raises(auth.AccountError, match="last_admin"):
            admin.update_user(s, s.get(db.User, boss), other, "member", None)
        with pytest.raises(auth.AccountError, match="last_admin"):
            admin.update_user(s, s.get(db.User, boss), other, None, True)
        with pytest.raises(auth.AccountError, match="last_admin"):
            admin.delete_user(s, s.get(db.User, boss), other)


# Feedback, settings and the activity log


def test_feedback_done_and_reopen(client, boss):
    ada = add_user("ada@example.org", "Ada")
    with db.get_sessionmaker()() as s:
        s.add(db.Feedback(user_id=ada, kind="problem", message="Broken"))
        s.commit()
    [entry] = client.get("/v1/admin/feedback").json()
    assert (entry["name"], entry["email"], entry["done"]) == ("Ada", "ada@example.org", False)
    assert client.patch(f"/v1/admin/feedback/{entry['id']}", json={"done": True}).json() == {
        "done": True
    }
    client.patch(f"/v1/admin/feedback/{entry['id']}", json={"done": False})
    assert [e[1:3] for e in log_entries()] == [
        ("feedback_done", "ada@example.org"),
        ("feedback_reopen", "ada@example.org"),
    ]
    missing = client.patch("/v1/admin/feedback/999", json={"done": True})
    assert (missing.status_code, missing.json()) == (404, {"detail": "feedback_not_found"})


def test_settings_change_the_page(client, boss):
    assert client.get("/v1/admin/settings").json() == admin.DEFAULTS
    saved = client.patch(
        "/v1/admin/settings", json={"guest_mode": False, "guest_limit": 2, "signup_open": False}
    ).json()
    assert saved == {"guest_mode": False, "guest_limit": 2, "signup_open": False}
    bad = client.patch("/v1/admin/settings", json={"guest_limit": 101})
    assert (bad.status_code, bad.json()) == (400, {"detail": "guest_limit_range"})
    [(_, action, _, details)] = log_entries()
    assert action == "settings" and "guest_limit: 5 -> 2" in details
    # A visitor now has to log in and cannot sign up
    visitor = TestClient(app=api.app)
    assert visitor.get("/", follow_redirects=False).headers["location"] == "/login"
    assert "Sign-up is turned off" in visitor.get("/signup").text


def test_the_activity_log_shows_the_newest_first(client, boss):
    for number in range(3):
        add_user(f"user{number}@example.org")
    with db.get_sessionmaker()() as s:
        for user in s.scalars(select(db.User).where(db.User.role == "member")):
            admin.log(s, s.get(db.User, boss), "block", user.email)
        s.commit()
    rows = client.get("/v1/admin/log").json()
    assert [row["target"] for row in rows] == [
        "user2@example.org",
        "user1@example.org",
        "user0@example.org",
    ]
    assert rows[0]["admin_label"] == "boss@example.org"
