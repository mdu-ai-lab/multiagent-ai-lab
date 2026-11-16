# Admin settings of the chat page (saved in the app_settings table), the work of the admin
# panel and the admin commands in Terminal. The first admin account is made here, because a
# new sign-up is always a member:
#   uv run python -m mrag.admin create-admin <email> <name>
#   uv run python -m mrag.admin make-admin <email>
#   uv run python -m mrag.admin list-users
# The API checks the admin role before every call. Admins see how many chats a user has, never
# the chat text. An admin cannot change the own account here and the last admin always stays

import argparse
import getpass
import json
import secrets
import sys
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from mrag import auth, db
from mrag.translations import TEXT

# Used while an admin has not changed a setting: guest mode and sign-up start on, as in the
# chat page preview
DEFAULTS: dict[str, Any] = {"guest_mode": True, "guest_limit": 5, "signup_open": True}
# The name the activity log shows for actions done in Terminal
TERMINAL = "Terminal"
# Newest entries the activity log shows
LOG_SIZE = 300


def settings(s: Session) -> dict[str, Any]:
    saved = {row.key: row.value for row in s.scalars(select(db.AppSetting))}
    return {key: saved.get(key, default) for key, default in DEFAULTS.items()}


def log(
    s: Session, admin: db.User | None, action: str, target: str = "", details: str = ""
) -> None:
    # One entry of the activity log. Without an admin the action came from Terminal
    s.add(
        db.AuditEntry(
            admin_id=admin.id if admin else None,
            admin_label=admin.email if admin else TERMINAL,
            action=action,
            target=target,
            details=details,
        )
    )


def temp_password() -> str:
    # Easy to read out loud: no 0/O or 1/l, in three groups like abcd-efgh-jkmn
    letters = "abcdefghjkmnpqrstuvwxyz23456789"
    return "-".join("".join(secrets.choice(letters) for _ in range(4)) for _ in range(3))


def active_admins(s: Session) -> int:
    count = s.scalar(
        select(func.count()).where(db.User.role == "admin", db.User.blocked.is_(False))
    )
    return int(count or 0)


def find_user(s: Session, user_id: int) -> db.User:
    user = s.get(db.User, user_id)
    if user is None:
        raise auth.AccountError("user_not_found")
    return user


def other_user(s: Session, admin: db.User, user_id: int) -> db.User:
    # An admin never changes the own account from the admin panel
    if user_id == admin.id:
        raise auth.AccountError("self")
    return find_user(s, user_id)


def create_admin(s: Session, email: str, name: str, password: str) -> db.User:
    user = auth.create_user(s, email, name, password, role="admin")
    log(s, None, "create_user", user.email, "admin")
    return user


def make_admin(s: Session, email: str) -> db.User:
    user = s.scalar(select(db.User).where(db.User.email == auth.normalize_email(email)))
    if user is None:
        raise auth.AccountError("user_not_found")
    if user.role != "admin":
        user.role = "admin"
        # A change of rights ends every login of the account
        auth.end_sessions(s, user.id)
        log(s, None, "make_admin", user.email)
    return user


def users(s: Session) -> list[db.User]:
    return list(s.scalars(select(db.User).order_by(db.User.id)))


# The admin panel


def stats(s: Session) -> dict[str, int]:
    def count(query: Any) -> int:
        return int(s.scalar(query) or 0)

    week_ago = db.utcnow() - timedelta(days=7)
    today = db.utcnow().date()
    return {
        "users": count(select(func.count()).select_from(db.User)),
        "admins": count(select(func.count()).where(db.User.role == "admin")),
        "blocked": count(select(func.count()).where(db.User.blocked.is_(True))),
        "new_users": count(select(func.count()).where(db.User.created_at >= week_ago)),
        # Chats and messages of accounts. Guest chats go with their session, guests have their
        # own count per day
        "chats": count(select(func.count()).where(db.Chat.user_id.is_not(None))),
        "messages": count(
            select(func.count())
            .select_from(db.Message)
            .join(db.Chat, db.Chat.id == db.Message.chat_id)
            .where(db.Message.role == "user", db.Chat.user_id.is_not(None))
        ),
        "open_feedback": count(select(func.count()).where(db.Feedback.done.is_(False))),
        "guest_today": count(select(db.GuestDay.messages).where(db.GuestDay.day == today)),
    }


def user_list(s: Session) -> list[dict[str, Any]]:
    # Newest first, with the number of chats. Never their text
    chats = (
        select(func.count())
        .select_from(db.Chat)
        .where(db.Chat.user_id == db.User.id)
        .scalar_subquery()
    )
    rows = s.execute(select(db.User, chats).order_by(db.User.created_at.desc(), db.User.id.desc()))
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "blocked": user.blocked,
            "created_at": user.created_at,
            "last_login": user.last_login_at,
            "chats": int(count or 0),
        }
        for user, count in rows
    ]


def create_user(
    s: Session, admin: db.User, name: str, email: str, password: str, role: str
) -> db.User:
    user = auth.create_user(s, email, name, password, role)
    log(s, admin, "create_user", user.email, role)
    return user


def update_user(
    s: Session, admin: db.User, user_id: int, role: str | None, blocked: bool | None
) -> None:
    user = other_user(s, admin, user_id)
    losing_admin = (
        user.role == "admin" and not user.blocked and (role == "member" or blocked is True)
    )
    if losing_admin and active_admins(s) <= 1:
        raise auth.AccountError("last_admin")
    if role is not None and role != user.role:
        user.role = role
        # A change of rights ends every login of the account
        auth.end_sessions(s, user.id)
        log(s, admin, "make_admin" if role == "admin" else "make_member", user.email)
    if blocked is not None and blocked != user.blocked:
        user.blocked = blocked
        if blocked:
            # Logged out at once on every device
            auth.end_sessions(s, user.id)
        log(s, admin, "block" if blocked else "unblock", user.email)


def reset_password(s: Session, admin: db.User, user_id: int) -> str:
    # A new temporary password, shown to the admin once. Only its hash is stored
    user = other_user(s, admin, user_id)
    password = temp_password()
    user.password_hash = auth.hash_password(password)
    auth.end_sessions(s, user.id)
    log(s, admin, "reset_password", user.email)
    return password


def delete_user(s: Session, admin: db.User, user_id: int) -> None:
    # Sessions, chats and messages go with the account (the database deletes them)
    user = other_user(s, admin, user_id)
    if user.role == "admin" and not user.blocked and active_admins(s) <= 1:
        raise auth.AccountError("last_admin")
    log(s, admin, "delete_user", user.email)
    s.delete(user)


def feedback_list(s: Session) -> list[dict[str, Any]]:
    rows = s.execute(
        select(db.Feedback, db.User.name, db.User.email)
        .outerjoin(db.User, db.User.id == db.Feedback.user_id)
        .order_by(db.Feedback.created_at.desc(), db.Feedback.id.desc())
    )
    return [
        {
            "id": entry.id,
            "kind": entry.kind,
            "message": entry.message,
            "created_at": entry.created_at,
            "done": entry.done,
            "name": name,
            "email": email,
        }
        for entry, name, email in rows
    ]


def set_feedback_done(s: Session, admin: db.User, feedback_id: int, done: bool) -> None:
    entry = s.get(db.Feedback, feedback_id)
    if entry is None:
        raise auth.AccountError("feedback_not_found")
    entry.done = done
    sender = s.get(db.User, entry.user_id) if entry.user_id else None
    log(s, admin, "feedback_done" if done else "feedback_reopen", sender.email if sender else "")


def update_settings(s: Session, admin: db.User, change: dict[str, Any]) -> dict[str, Any]:
    if "guest_limit" in change and not 0 <= change["guest_limit"] <= 100:
        raise auth.AccountError("guest_limit_range")
    old = settings(s)
    changed = {key: value for key, value in change.items() if value != old[key]}
    for key, value in changed.items():
        s.merge(db.AppSetting(key=key, value=value))
    if changed:
        details = ", ".join(
            f"{key}: {json.dumps(old[key])} -> {json.dumps(new)}" for key, new in changed.items()
        )
        log(s, admin, "settings", "", details)
    return {**old, **changed}


def activity(s: Session) -> list[dict[str, Any]]:
    query = select(db.AuditEntry).order_by(db.AuditEntry.id.desc()).limit(LOG_SIZE)
    return [
        {
            "admin_label": entry.admin_label,
            "action": entry.action,
            "target": entry.target,
            "details": entry.details,
            "created_at": entry.created_at,
        }
        for entry in s.scalars(query)
    ]


# Terminal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m mrag.admin", description="Admin commands of the chat page"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-admin", help="create an admin account")
    create.add_argument("email")
    create.add_argument("name")
    promote = commands.add_parser("make-admin", help="give an existing account admin rights")
    promote.add_argument("email")
    commands.add_parser("list-users", help="list every account")
    args = parser.parse_args(argv)

    if not db.schema_is_current():
        print("The app database is not up to date. Run: uv run alembic upgrade head")
        return 1
    with db.get_sessionmaker()() as s:
        if args.command == "list-users":
            for user in users(s):
                state = "blocked" if user.blocked else "active"
                created = user.created_at.strftime("%Y-%m-%d %H:%M UTC")
                print(f"{user.id}\t{user.email}\t{user.name}\t{user.role}\t{state}\t{created}")
            return 0
        if args.command == "make-admin":
            try:
                user = make_admin(s, args.email)
            except auth.AccountError as error:
                print(TEXT["en"].get(f"err_{error.code}", error.code))
                return 1
            s.commit()
            print(f"Admin rights given to {user.email}")
            return 0
        # The password is typed without showing it, so it never lands in the Terminal history
        password = getpass.getpass("Password (at least 15 characters): ")
        if password != getpass.getpass("The same password again: "):
            print(TEXT["en"]["err_password_match"])
            return 1
        try:
            user = create_admin(s, args.email, args.name, password)
        except auth.AccountError as error:
            print(TEXT["en"].get(f"err_{error.code}", error.code))
            return 1
        s.commit()
        print(f"Admin account created: {user.email}. Log in at http://127.0.0.1:8000/login")
    return 0


if __name__ == "__main__":
    sys.exit(main())
