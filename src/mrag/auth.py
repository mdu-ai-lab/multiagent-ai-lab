# Logins for the chat page: password hashing, sessions kept in the database, the token
# against forged requests from other sites and the roles member and admin.
# The rules follow the OWASP cheat sheets on password storage, sessions, forged requests and
# authentication. ui.py and api.py use the FastAPI parts at the end of this file.

import hashlib
import secrets
import unicodedata
from collections.abc import Iterator
from datetime import timedelta
from functools import lru_cache
from typing import Annotated

from argon2 import PasswordHasher, profiles
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from mrag import db
from mrag.config import PROJECT_ROOT, get_settings

COOKIE = "mrag_session"
# The page sends the token of its session in this header with every changing request
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

MIN_PASSWORD = 15
MAX_PASSWORD = 128
COMMON_PASSWORDS = PROJECT_ROOT / "configs" / "common-passwords.txt"

# Argon2id with 64 MiB of memory, 3 passes and 4 lanes (argon2-cffi's RFC 9106 low-memory
# profile), above the OWASP minimum of 19 MiB, 2 passes and 1 lane. A check takes about 30 ms
# on the Mac. Each hash keeps its own salt and settings, so old hashes stay readable
HASHER = PasswordHasher.from_parameters(profiles.RFC_9106_LOW_MEMORY)

# last_seen_at is written at most once a minute, so opening pages does not write every time
SEEN_EVERY = timedelta(minutes=1)


class AccountError(Exception):
    # A refused account change. The code is a key for the page texts (translations.py)
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class LoginFailed(Exception):
    # One error for an unknown email, a wrong password and a blocked account, so a login
    # attempt never tells which accounts exist
    pass


def normal(password: str) -> str:
    # The same password typed on different keyboards can arrive in different Unicode forms
    return unicodedata.normalize("NFKC", password)


def normalize_email(email: str) -> str:
    return email.strip().lower()


@lru_cache
def common_passwords() -> frozenset[str]:
    lines = COMMON_PASSWORDS.read_text(encoding="utf-8").splitlines()
    return frozenset(line for line in lines if line and not line.startswith("#"))


def password_problem(password: str, email: str = "", name: str = "") -> str | None:
    # Why a new password is refused. None means it is fine. There are no rules on character types
    password = normal(password)
    if len(password) < MIN_PASSWORD:
        return "password_too_short"
    if len(password) > MAX_PASSWORD:
        return "password_too_long"
    lowered = password.lower()
    if lowered in common_passwords():
        return "password_common"
    email = normalize_email(email)
    personal = {email, email.split("@")[0], name.strip().lower()} - {""}
    if lowered in personal:
        return "password_personal"
    return None


def hash_password(password: str) -> str:
    return HASHER.hash(normal(password))


def verify_password(stored: str, password: str) -> bool:
    try:
        return HASHER.verify(stored, normal(password))
    except (VerificationError, InvalidHashError):
        return False


@lru_cache
def _unknown_email_hash() -> str:
    # Checked when no account has the email, so that takes as long as a wrong password
    return HASHER.hash(secrets.token_urlsafe(16))


def create_user(s: Session, email: str, name: str, password: str, role: str = "member") -> db.User:
    email = normalize_email(email)
    name = name.strip()
    if len(email) > 254 or " " in email or "@" not in email.strip("@"):
        raise AccountError("email_invalid")
    if not 1 <= len(name) <= 60:
        raise AccountError("name_invalid")
    if role not in ("member", "admin"):
        raise AccountError("role_invalid")
    problem = password_problem(password, email, name)
    if problem:
        raise AccountError(problem)
    # Telling that an email is taken shows that the account exists. Without email sending
    # there is no way around it. Login throttling comes later
    if s.scalar(select(db.User.id).where(db.User.email == email)) is not None:
        raise AccountError("email_taken")
    user = db.User(email=email, name=name, password_hash=hash_password(password), role=role)
    s.add(user)
    s.flush()
    return user


def check_login(s: Session, email: str, password: str) -> db.User:
    user = s.scalar(select(db.User).where(db.User.email == normalize_email(email)))
    # Every attempt runs one hash check, also for an unknown email or a far too long password
    if len(password) > MAX_PASSWORD:
        password = ""
    right = verify_password(user.password_hash if user else _unknown_email_hash(), password)
    if user is None or not right or user.blocked:
        raise LoginFailed
    if HASHER.check_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.last_login_at = db.utcnow()
    return user


def time_limits(remember: bool) -> tuple[timedelta, timedelta]:
    # (without use, in total)
    settings = get_settings()
    if remember:
        return timedelta(days=settings.remember_idle_days), timedelta(days=settings.remember_days)
    return timedelta(minutes=settings.session_idle_minutes), timedelta(hours=settings.session_hours)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def start_session(
    s: Session, user: db.User | None, remember: bool = False
) -> tuple[str, db.BrowserSession]:
    # 32 random bytes: 256 bits, more than the 128 OWASP asks for
    token = secrets.token_urlsafe(32)
    now = db.utcnow()
    _, total = time_limits(remember)
    row = db.BrowserSession(
        token_hash=token_hash(token),
        user_id=user.id if user else None,
        csrf_token=secrets.token_urlsafe(32),
        remember=remember,
        created_at=now,
        last_seen_at=now,
        expires_at=now + total,
    )
    s.add(row)
    s.flush()
    return token, row


def find_session(s: Session, token: str | None) -> db.BrowserSession | None:
    if not token:
        return None
    query = select(db.BrowserSession).where(db.BrowserSession.token_hash == token_hash(token))
    row = s.scalar(query)
    if row is None:
        return None
    now = db.utcnow()
    idle, _ = time_limits(row.remember)
    if now >= row.expires_at or now - row.last_seen_at >= idle:
        s.delete(row)
        s.flush()
        return None
    if now - row.last_seen_at >= SEEN_EVERY:
        row.last_seen_at = now
    return row


def log_in(
    s: Session, email: str, password: str, remember: bool, old: db.BrowserSession | None
) -> tuple[str, db.User]:
    user = check_login(s, email, password)
    # Every login starts a new session. The old one ends, with a guest's chats
    if old is not None:
        s.delete(old)
    token, _ = start_session(s, user, remember)
    return token, user


def end_sessions(s: Session, user_id: int) -> None:
    # After logout everywhere, a password change, blocking or a role change
    s.execute(delete(db.BrowserSession).where(db.BrowserSession.user_id == user_id))


def change_password(s: Session, user: db.User, current: str, new: str, remember: bool) -> str:
    if not verify_password(user.password_hash, current):
        raise AccountError("password_wrong")
    problem = password_problem(new, user.email, user.name)
    if problem:
        raise AccountError(problem)
    user.password_hash = hash_password(new)
    end_sessions(s, user.id)
    # This browser stays logged in with a new session
    token, _ = start_session(s, user, remember)
    return token


def remove_expired_sessions(s: Session) -> int:
    now = db.utcnow()
    idle_short, _ = time_limits(False)
    idle_long, _ = time_limits(True)
    sessions = db.BrowserSession
    result = s.execute(
        delete(sessions).where(
            or_(
                sessions.expires_at <= now,
                (sessions.remember.is_(False)) & (sessions.last_seen_at <= now - idle_short),
                (sessions.remember.is_(True)) & (sessions.last_seen_at <= now - idle_long),
            )
        )
    )
    return int(getattr(result, "rowcount", 0) or 0)


# FastAPI parts. Each request gets its own database session. The endpoints commit themselves


def database() -> Iterator[Session]:
    with db.get_sessionmaker()() as s:
        yield s


DbSession = Annotated[Session, Depends(database)]


def set_session_cookie(response: Response, request: Request, token: str, remember: bool) -> None:
    # Without "Keep me logged in" the cookie ends when the browser closes. The server limits
    # apply in both cases. Secure is set whenever the page is served over HTTPS
    _, total = time_limits(remember)
    response.set_cookie(
        COOKIE,
        token,
        max_age=int(total.total_seconds()) if remember else None,
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
        path="/",
    )


def clear_session_cookie(response: Response, request: Request) -> None:
    response.delete_cookie(
        COOKIE, httponly=True, samesite="strict", secure=request.url.scheme == "https", path="/"
    )


def browser_session(request: Request, s: DbSession) -> db.BrowserSession | None:
    # Saved at once, so an ended session or a new last_seen_at also counts on reading pages
    row = find_session(s, request.cookies.get(COOKIE))
    s.commit()
    return row


SessionRow = Annotated[db.BrowserSession | None, Depends(browser_session)]


def check_request_origin(request: Request, browser: SessionRow) -> None:
    # Against forged requests from other sites: every changing request needs the secret token
    # of its session. Browsers also tell where a request comes from, which is checked as well
    if request.method in SAFE_METHODS:
        return
    site = request.headers.get("sec-fetch-site")
    if site is not None and site not in ("same-origin", "none"):
        raise HTTPException(403, "forged_request")
    origin = request.headers.get("origin")
    if origin is not None and origin != f"{request.url.scheme}://{request.url.netloc}":
        raise HTTPException(403, "forged_request")
    sent = request.headers.get(CSRF_HEADER, "")
    if browser is None or not secrets.compare_digest(sent.encode(), browser.csrf_token.encode()):
        raise HTTPException(403, "forged_request")


def current_user(s: DbSession, browser: SessionRow) -> db.User | None:
    if browser is None or browser.user_id is None:
        return None
    user = s.get(db.User, browser.user_id)
    if user is None or user.blocked:
        s.delete(browser)
        s.commit()
        return None
    return user


def require_user(user: Annotated[db.User | None, Depends(current_user)]) -> db.User:
    if user is None:
        raise HTTPException(401, "login_required")
    return user


def require_admin(user: Annotated[db.User, Depends(require_user)]) -> db.User:
    if user.role != "admin":
        raise HTTPException(403, "admin_only")
    return user
