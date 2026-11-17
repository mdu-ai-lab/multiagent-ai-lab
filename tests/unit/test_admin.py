# The admin commands in Terminal on a new app database: the first admin account and the list
# of accounts. The typed password is replaced by a fixed one

import pytest
from alembic import command
from sqlalchemy import select

from mrag import admin, auth, db

PASSWORD = "correct horse battery staple"


@pytest.fixture
def typed(monkeypatch):
    # The answers to the two password questions
    answers = [PASSWORD, PASSWORD]
    monkeypatch.setattr(admin.getpass, "getpass", lambda prompt="": answers.pop(0))
    return answers


def test_create_admin_makes_an_admin_who_can_log_in(database, typed, capsys):
    assert admin.main(["create-admin", "Ada@Example.org", "Ada"]) == 0
    assert "Admin account created: ada@example.org" in capsys.readouterr().out
    with db.get_sessionmaker()() as s:
        user = auth.check_login(s, "ada@example.org", PASSWORD)
        assert user.role == "admin"
        entry = s.scalars(select(db.AuditEntry)).one()
        assert (entry.admin_label, entry.action, entry.target, entry.details) == (
            "Terminal",
            "create_user",
            "ada@example.org",
            "admin",
        )


def test_two_different_passwords_create_nothing(database, typed, capsys):
    typed[1] = "another password entirely"
    assert admin.main(["create-admin", "ada@example.org", "Ada"]) == 1
    assert "do not match" in capsys.readouterr().out
    with db.get_sessionmaker()() as s:
        assert admin.users(s) == []


@pytest.mark.parametrize(
    ("password", "message"),
    [("short one", "at least 15 characters"), ("1qaz2wsx3edc4rfv", "too common")],
)
def test_the_password_rules_apply(database, typed, capsys, password, message):
    typed[:] = [password, password]
    assert admin.main(["create-admin", "ada@example.org", "Ada"]) == 1
    assert message in capsys.readouterr().out


def test_an_email_is_used_once(database, typed, capsys):
    admin.main(["create-admin", "ada@example.org", "Ada"])
    typed[:] = [PASSWORD, PASSWORD]
    assert admin.main(["create-admin", "ada@example.org", "Ada again"]) == 1
    assert "already exists" in capsys.readouterr().out


def test_list_users(database, typed, capsys):
    admin.main(["create-admin", "ada@example.org", "Ada"])
    capsys.readouterr()
    assert admin.main(["list-users"]) == 0
    line = capsys.readouterr().out.strip()
    assert line.split("\t")[:5] == ["1", "ada@example.org", "Ada", "admin", "active"]
    assert line.endswith("UTC")


def test_an_old_database_is_refused(database, capsys):
    command.downgrade(database, "base")
    assert admin.main(["list-users"]) == 1
    assert "alembic upgrade head" in capsys.readouterr().out


def test_make_admin_gives_an_existing_account_admin_rights(database, capsys):
    with db.get_sessionmaker()() as s:
        user = auth.create_user(s, "grace@example.org", "Grace", PASSWORD)
        auth.start_session(s, user)
        s.commit()
    assert admin.main(["make-admin", "Grace@Example.org"]) == 0
    assert "Admin rights given to grace@example.org" in capsys.readouterr().out
    with db.get_sessionmaker()() as s:
        assert s.scalars(select(db.User.role)).one() == "admin"
        # A change of rights ends every login of the account
        assert s.scalars(select(db.BrowserSession)).all() == []
        entry = s.scalars(select(db.AuditEntry)).one()
        assert (entry.admin_label, entry.action, entry.target) == (
            "Terminal",
            "make_admin",
            "grace@example.org",
        )
    assert admin.main(["make-admin", "nobody@example.org"]) == 1
    assert "User not found." in capsys.readouterr().out
