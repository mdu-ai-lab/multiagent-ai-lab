# The chat web page: HTML pages from templates/ui with the CSS and JavaScript in static/.
# Jinja2 escapes every value it puts into a page. The page scripts read and change data only
# through the API under /v1. Every page gets a session for its browser, so its forms can send
# the token against forged requests. Every response gets the security headers below

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from mrag import admin, auth, db
from mrag.translations import LANGUAGES, TEXT, translator

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
templates = Jinja2Templates(directory=HERE / "templates" / "ui")
router = APIRouter(include_in_schema=False)

APP_NAME = "MDU AI Lab"
THEMES = ("dark", "light", "system")
# The page settings of a user and their values while nothing is saved
DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "dark",
    "language": "en",
    "enter_sends": True,
    "show_examples": True,
    "sidebar_collapsed": False,
}

# Scripts, styles, pictures and requests only from this server. No inline scripts, no plugins
# and no framing by other sites. The page settings travel in a JSON block, which is no script
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; "
    "frame-ancestors 'none'"
)
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "same-origin",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
# FastAPI's API documentation pages load their scripts from a CDN, so they get no CSP
DOCS_PATHS = ("/docs", "/redoc")


class SecurityHeaders:
    # Adds the headers to every response, also to streamed ones. A plain ASGI wrapper, because
    # FastAPI's own middleware type can hold back a streamed answer when the browser leaves
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        docs = str(scope["path"]).startswith(DOCS_PATHS)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    headers[name] = value
                if not docs:
                    headers["Content-Security-Policy"] = CSP
            await send(message)

        await self.app(scope, receive, send_with_headers)


@lru_cache(maxsize=64)
def _fingerprint(name: str, modified: int) -> str:
    return hashlib.sha256((STATIC / name).read_bytes()).hexdigest()[:10]


def asset_url(name: str) -> str:
    # The link ends with a short fingerprint of the file, so a browser loads a changed file at
    # once instead of an old copy
    return f"/static/{name}?v={_fingerprint(name, (STATIC / name).stat().st_mtime_ns)}"


def page_settings(request: Request, user: db.User | None) -> dict[str, Any]:
    # A user's saved settings. Without a login the language and theme cookies of the browser
    settings = dict(DEFAULT_SETTINGS)
    if user is not None:
        settings.update({k: v for k, v in user.settings.items() if k in DEFAULT_SETTINGS})
        return settings
    if request.cookies.get("lang") in LANGUAGES:
        settings["language"] = request.cookies["lang"]
    if request.cookies.get("theme") in THEMES:
        settings["theme"] = request.cookies["theme"]
    return settings


class Visit:
    # The browser session of a page request, started now when the browser has none
    def __init__(self, request: Request, s: Session) -> None:
        self.request, self.s = request, s
        self.new_token: str | None = None
        browser = auth.find_session(s, request.cookies.get(auth.COOKIE))
        user = s.get(db.User, browser.user_id) if browser and browser.user_id else None
        if browser is not None and browser.user_id is not None and (user is None or user.blocked):
            # The user was blocked or deleted: this browser starts again as a guest
            s.delete(browser)
            browser, user = None, None
        if browser is None:
            self.new_token, browser = auth.start_session(s, None)
        s.commit()
        self.browser, self.user = browser, user
        self.options = admin.settings(s)

    def finish(self, response: Response) -> Response:
        if self.new_token is not None:
            auth.set_session_cookie(response, self.request, self.new_token, remember=False)
        return response

    def redirect(self, path: str) -> Response:
        return self.finish(RedirectResponse(path, status_code=303))

    def render(self, template: str, **extra: Any) -> Response:
        settings = page_settings(self.request, self.user)
        lang = settings["language"]
        user = self.user
        config = {
            "csrf": self.browser.csrf_token,
            "lang": lang,
            "texts": TEXT[lang],
            "user": {"name": user.name, "email": user.email, "role": user.role} if user else None,
        }
        context = {
            "app_name": APP_NAME,
            "lang": lang,
            "theme": settings["theme"],
            "t": TEXT[lang],
            "tr": translator(lang),
            "user": user,
            "options": self.options,
            "asset": asset_url,
            "config": config,
            **extra,
        }
        response = templates.TemplateResponse(self.request, template, context)
        # Pages hold the session's token and personal data, so browsers never keep a copy
        response.headers["Cache-Control"] = "no-store"
        return self.finish(response)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, s: auth.DbSession) -> Response:
    visit = Visit(request, s)
    if visit.user is None and not visit.options["guest_mode"]:
        return visit.redirect("/login")
    return visit.render("index.html")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, s: auth.DbSession) -> Response:
    visit = Visit(request, s)
    if visit.user is not None:
        return visit.redirect("/")
    return visit.render("login.html")


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request, s: auth.DbSession) -> Response:
    visit = Visit(request, s)
    if visit.user is not None:
        return visit.redirect("/")
    return visit.render("signup.html")
