# The chat page of the preview on a new app database: what guests and users see, the account
# settings, the feedback, the export, deleting an account and answers in safe Markdown

import json
import re
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from mrag import api, auth, db, service, ui
from mrag.translations import TEXT

PASSWORD = "correct horse battery staple"


@pytest.fixture
def client(database):
    return TestClient(app=api.app)


def page_config(html):
    found = re.search(r'<script type="application/json" id="page-config">(.*?)</script>', html)
    assert found
    return json.loads(found.group(1))


def log_in(client, email="ada@example.org", name="Ada Lovelace", role="member"):
    # Logs in through the login page and the API, as a browser does
    with db.get_sessionmaker()() as s:
        auth.create_user(s, email, name, PASSWORD, role)
        s.commit()
    csrf = page_config(client.get("/login").text)["csrf"]
    body = {"email": email, "password": PASSWORD}
    assert client.post("/v1/auth/login", json=body, headers={auth.CSRF_HEADER: csrf}).is_success
    client.headers[auth.CSRF_HEADER] = page_config(client.get("/").text)["csrf"]


def the_user():
    with db.get_sessionmaker()() as s:
        return s.scalars(select(db.User)).one()


# What the page shows


def test_a_guest_gets_the_chat_page_of_the_preview(client):
    html = client.get("/").text
    for part in (
        'id="sidebar"',
        'id="history"',
        'id="composer"',
        'id="attachBtn"',
        'id="guestBar"',
        'id="authModal"',
        'href="/login"',
        'href="/signup"',
    ):
        assert part in html, part
    assert 'id="settingsModal"' not in html and 'id="accountMenu"' not in html
    config = page_config(html)
    assert (config["user"], config["guest_left"], config["guest_limit"]) == (None, 5, 5)
    assert config["t"] == TEXT["en"] and config["max_message_length"] == 4000


def test_a_user_gets_the_account_menu_and_settings(client):
    log_in(client)
    html = client.get("/").text
    for part in (
        'id="accountMenu"',
        'id="settingsModal"',
        'id="feedbackModal"',
        'id="aboutModal"',
        '<span class="account-avatar" id="accountInitials">AL</span>',
        "How can I help you, Ada?",
    ):
        assert part in html, part
    assert 'id="authModal"' not in html and 'id="guestBar"' not in html
    assert page_config(html)["user"] == {
        "name": "Ada Lovelace",
        "email": "ada@example.org",
        "role": "member",
    }


def test_the_admin_panel_item_waits_for_the_admin_page(client):
    log_in(client, role="admin")
    assert 'href="/admin"' not in client.get("/").text


def test_the_top_bar_shows_the_model_of_this_profile(client):
    main = next(m for m in service.models().models if m.role == "main")
    label = ui.model_label(main.name, main.source)
    html = client.get("/").text
    assert f'<span class="model-name">{label}</span>' in html
    assert '<span class="pill">Local</span>' in html


def test_texts_that_promise_file_reading_stay_hidden(client):
    # The guest window is on the guest page, the help window on the page of a user
    guest_page = client.get("/").text
    assert 'id="authModal"' in guest_page
    assert f">{TEXT['en']['gm_uploads']}</li>" not in guest_page
    assert f">{TEXT['en']['gm_no_uploads']}</li>" not in guest_page
    log_in(client)
    user_page = client.get("/").text
    assert f"<summary>{TEXT['en']['faq3_q']}</summary>" in user_page
    assert f"<summary>{TEXT['en']['faq2_q']}</summary>" not in user_page


def test_the_hidden_sidebar_is_kept(client):
    assert 'class="sb-collapsed"' not in client.get("/").text
    client.cookies.set("sidebar", "collapsed")
    assert '<html lang="en" data-theme="dark" class="sb-collapsed">' in client.get("/").text
    client.cookies.delete("sidebar")
    log_in(client)
    client.patch("/v1/me/preferences", json={"sidebar_collapsed": True})
    assert 'class="sb-collapsed"' in client.get("/").text


def test_a_guest_sees_the_messages_left(client):
    client.get("/")
    with db.get_sessionmaker()() as s:
        s.scalars(select(db.BrowserSession)).one().guest_messages = 3
        s.commit()
    assert page_config(client.get("/").text)["guest_left"] == 2


def test_a_message_is_at_most_4000_characters(client):
    log_in(client)
    response = client.post("/v1/chat", json={"message": "x" * 4001})
    assert response.status_code == 422


# Account settings


def test_change_the_name(client):
    log_in(client)
    assert client.patch("/v1/me", json={"name": "  Grace Hopper "}).json() == {
        "name": "Grace Hopper",
        "initials": "GH",
    }
    assert the_user().name == "Grace Hopper"
    response = client.patch("/v1/me", json={"name": "x" * 61})
    assert (response.status_code, response.json()) == (400, {"detail": "name_invalid"})


def test_settings_are_saved_and_kept_in_cookies(client):
    log_in(client)
    saved = client.patch("/v1/me/preferences", json={"theme": "light", "language": "sv"}).json()
    assert saved == {**ui.DEFAULT_SETTINGS, "theme": "light", "language": "sv"}
    assert the_user().settings == saved
    assert client.cookies["lang"] == "sv" and client.cookies["theme"] == "light"
    assert '<html lang="sv" data-theme="light"' in client.get("/").text
    assert client.patch("/v1/me/preferences", json={"theme": "pink"}).status_code == 422


def test_change_the_password(client):
    log_in(client)
    with db.get_sessionmaker()() as s:
        auth.start_session(s, s.scalars(select(db.User)).one())
        s.commit()
    body = {
        "current_password": "wrong one entirely",
        "new_password": "a brand new passphrase",
        "confirm_password": "a brand new passphrase",
    }
    assert client.post("/v1/me/password", json=body).json() == {"detail": "password_wrong"}
    body["current_password"] = PASSWORD
    body["confirm_password"] = "something else"
    assert client.post("/v1/me/password", json=body).json() == {"detail": "password_match"}
    body["confirm_password"] = body["new_password"]
    old_cookie = client.cookies[auth.COOKIE]
    assert client.post("/v1/me/password", json=body).json() == {"changed": True}
    # This browser has a new session. The other login ended
    assert client.cookies[auth.COOKIE] != old_cookie
    with db.get_sessionmaker()() as s:
        assert len(s.scalars(select(db.BrowserSession)).all()) == 1
        assert auth.check_login(s, "ada@example.org", "a brand new passphrase")


def test_export_gives_only_the_own_chats_as_a_file(client, monkeypatch):
    log_in(client)
    with db.get_sessionmaker()() as s:
        ada = s.scalars(select(db.User)).one()
        grace = auth.create_user(s, "grace@example.org", "Grace", PASSWORD)
        for owner, title in ((ada, "Ada's chat"), (grace, "Grace's chat")):
            chat = db.Chat(user_id=owner.id, title=title)
            s.add(chat)
            s.flush()
            s.add(db.Message(chat_id=chat.id, role="user", content="Hello"))
        s.commit()
    response = client.get("/v1/me/export")
    assert response.headers["content-disposition"].startswith('attachment; filename="mdu-ai-lab-')
    data = response.json()
    assert data["user"] == {"name": "Ada Lovelace", "email": "ada@example.org"}
    assert [chat["title"] for chat in data["chats"]] == ["Ada's chat"]
    assert data["chats"][0]["messages"][0]["text"] == "Hello"


def test_delete_the_own_account(client):
    log_in(client)
    response = client.post("/v1/me/delete", json={"password": "not my password"})
    assert response.json() == {"detail": "password_wrong"}
    assert client.post("/v1/me/delete", json={"password": PASSWORD}).json() == {"deleted": True}
    with db.get_sessionmaker()() as s:
        assert s.scalars(select(db.User)).all() == []
        assert s.scalars(select(db.BrowserSession)).all() == []


def test_the_last_admin_cannot_delete_the_account(client):
    log_in(client, role="admin")
    response = client.post("/v1/me/delete", json={"password": PASSWORD})
    assert (response.status_code, response.json()) == (400, {"detail": "last_admin"})


def test_feedback(client):
    log_in(client)
    response = client.post("/v1/feedback", json={"kind": "idea", "message": "   "})
    assert response.json() == {"detail": "feedback_empty"}
    assert client.post("/v1/feedback", json={"kind": "praise", "message": "x"}).status_code == 422
    assert client.post("/v1/feedback", json={"kind": "idea", "message": " Dark mode "}).json() == {
        "sent": True
    }
    with db.get_sessionmaker()() as s:
        entry = s.scalars(select(db.Feedback)).one()
        assert (entry.kind, entry.message) == ("idea", "Dark mode")


def test_account_settings_need_a_login_and_the_token(client):
    client.get("/")
    for method, path, body in (
        ("patch", "/v1/me", {"name": "x"}),
        ("patch", "/v1/me/preferences", {"theme": "dark"}),
        ("post", "/v1/feedback", {"kind": "idea", "message": "x"}),
    ):
        response = getattr(client, method)(path, json=body)
        assert response.json() == {"detail": "forged_request"}, path
    assert client.get("/v1/me/export").json() == {"detail": "login_required"}
    log_in(client)
    del client.headers[auth.CSRF_HEADER]
    assert client.patch("/v1/me", json={"name": "x"}).json() == {"detail": "forged_request"}


# Answers in Markdown


@pytest.mark.parametrize(
    ("answer", "present", "absent"),
    [
        ("**bold** and a list:\n\n- one\n- two", ["<strong>bold</strong>", "<li>one</li>"], []),
        ("<script>alert(1)</script>", ["&lt;script&gt;"], ["<script>"]),
        ("[x](javascript:alert(1))", [], ["<a "]),
        ("![p](https://example.org/p.png)", [], ["<img"]),
        ("[site](https://example.org)", ['rel="noopener noreferrer"', 'target="_blank"'], []),
        ("| a | b |\n|---|---|\n| 1 | 2 |", ["<table>", "<td>1</td>"], []),
    ],
)
def test_answers_are_shown_as_safe_markdown(answer, present, absent):
    html = ui.answer_html(answer)
    for part in present:
        assert part in html
    for part in absent:
        assert part not in html


def test_a_saved_answer_comes_with_its_html(client):
    log_in(client)
    with db.get_sessionmaker()() as s:
        chat = db.Chat(user_id=s.scalars(select(db.User.id)).one(), title="Chat")
        s.add(chat)
        s.flush()
        s.add(db.Message(chat_id=chat.id, role="user", content="**not formatted**"))
        s.add(db.Message(chat_id=chat.id, role="assistant", content="**bold**"))
        s.commit()
        chat_id = chat.id
    user_turn, answer = client.get(f"/v1/chats/{chat_id}").json()["messages"]
    assert user_turn["html"] is None
    assert answer["html"] == "<p><strong>bold</strong></p>\n"


# Texts and scripts


def test_every_error_code_has_a_text_in_both_languages():
    sources = [(ui.HERE / name).read_text() for name in ("api.py", "auth.py", "service.py")]
    codes = set()
    for text in sources:
        codes |= set(re.findall(r'HTTPException\(\d+, "(\w+)"\)', text))
        codes |= set(re.findall(r'AccountError\("(\w+)"\)', text))
    loop = (ui.HERE / "harness" / "loop.py").read_text()
    codes |= set(re.findall(r'\(\w+Error, "(\w+)"\)', loop))
    assert {"chat_not_found", "guest_limit", "model_unavailable", "time_limit"} <= codes
    for lang in TEXT:
        missing = {code for code in codes if f"err_{code}" not in TEXT[lang]}
        assert missing == {"role_invalid"} or not missing, (lang, missing)


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is not installed")
def test_the_page_scripts_are_valid_javascript():
    for path in ui.STATIC.glob("*.js"):
        subprocess.run(["node", "--check", str(path)], check=True)
