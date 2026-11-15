# Admin settings of the chat page (saved in the app_settings table) and the admin commands
# in Terminal. The first admin account is made here, because sign-up is off by default:
#   uv run python -m mrag.admin create-admin <email> <name>
#   uv run python -m mrag.admin list-users

import argparse
import getpass
import sys
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mrag import auth, db
from mrag.translations import TEXT

# Used while an admin has not changed a setting: guests and sign-up stay off
DEFAULTS: dict[str, Any] = {"guest_mode": False, "guest_limit": 5, "signup_open": False}
# The name the activity log shows for actions done in Terminal
TERMINAL = "Terminal"


def settings(s: Session) -> dict[str, Any]:
    saved = {row.key: row.value for row in s.scalars(select(db.AppSetting))}
    return {key: saved.get(key, default) for key, default in DEFAULTS.items()}


def create_admin(s: Session, email: str, name: str, password: str) -> db.User:
    user = auth.create_user(s, email, name, password, role="admin")
    s.add(db.AuditEntry(admin_label=TERMINAL, action="create_admin", target=user.email))
    return user


def users(s: Session) -> list[db.User]:
    return list(s.scalars(select(db.User).order_by(db.User.id)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m mrag.admin", description="Admin commands of the chat page"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-admin", help="create an admin account")
    create.add_argument("email")
    create.add_argument("name")
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
