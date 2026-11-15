# Admin settings of the chat page, saved in the app_settings table. The admin panel and the
# admin commands in Terminal use them too

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from mrag import db

# Used while an admin has not changed a setting: guests and sign-up stay off
DEFAULTS: dict[str, Any] = {"guest_mode": False, "guest_limit": 5, "signup_open": False}


def settings(s: Session) -> dict[str, Any]:
    saved = {row.key: row.value for row in s.scalars(select(db.AppSetting))}
    return {key: saved.get(key, default) for key, default in DEFAULTS.items()}
