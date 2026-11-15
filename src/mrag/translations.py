# Every text of the chat page in English and Swedish. The server fills the pages with them and
# the page scripts get the same table, so there is one place for all texts.
# {name} style parts are filled in when a text is used. The err_ texts belong to the error
# codes of the API ("detail" in its answers). The Swedish texts still need a check by a
# Swedish speaker

import re
from collections.abc import Callable

LANGUAGES = {"en": "English", "sv": "Svenska"}

TEXT: dict[str, dict[str, str]] = {
    "en": {
        "app_subtitle": "Assistant",
        "log_in": "Log in",
        "sign_up": "Sign up",
        "log_out": "Log out",
        "logged_in_as": "Logged in as {name}",
        "welcome": "How can I help you today?",
        # Login and sign-up pages
        "auth_pitch": "Log in to keep your chats",
        "perk1": "Saved chat history",
        "perk1_sub": "Pick up where you left off",
        "perk2": "Only you can open your chats",
        "perk2_sub": "Other users and admins cannot read them",
        "perk3": "Streamed answers",
        "perk3_sub": "Watch each answer appear as it is written",
        "show": "Show",
        "hide": "Hide",
        "login_title": "Welcome back",
        "login_sub": "Log in to continue to {app}.",
        "email": "Email",
        "password": "Password",
        "remember": "Keep me logged in for up to 30 days",
        "no_account": "No account yet?",
        "create_one": "Create one",
        "or": "or",
        "continue_guest": "Continue as guest",
        "signup_title": "Create your account",
        "signup_sub": "It takes less than a minute.",
        "signup_closed": "Sign-up is turned off. Ask an admin for an account.",
        "name": "Name",
        "password_hint": "At least 15 characters. Common passwords are refused.",
        "confirm_password_label": "Confirm password",
        "create_account": "Create account",
        "have_account": "Already have an account?",
        # Error codes of the API
        "err_login_failed": "Email or password is incorrect.",
        "err_email_invalid": "Enter a valid email address.",
        "err_name_invalid": "Enter your name (up to 100 characters).",
        "err_email_taken": "An account with this email already exists.",
        "err_password_too_short": "The password needs at least 15 characters.",
        "err_password_too_long": "The password can have at most 128 characters.",
        "err_password_common": "This password is too common. Choose another one.",
        "err_password_personal": "The password must not be your email or your name.",
        "err_password_match": "The passwords do not match.",
        "err_signup_closed": "Sign-up is turned off. Ask an admin for an account.",
        "err_forged_request": "This page is out of date. Reload it and try again.",
        "err_login_required": "Please log in first.",
        "err_invalid_input": "Check the fields and try again.",
        "err_network": "No connection to the server. Try again.",
        "err_unknown": "Something went wrong. Try again.",
    },
    "sv": {
        "app_subtitle": "Assistent",
        "log_in": "Logga in",
        "sign_up": "Registrera dig",
        "log_out": "Logga ut",
        "logged_in_as": "Inloggad som {name}",
        "welcome": "Hur kan jag hjälpa dig i dag?",
        "auth_pitch": "Logga in för att spara dina chattar",
        "perk1": "Sparad chatthistorik",
        "perk1_sub": "Fortsätt där du slutade",
        "perk2": "Bara du kan öppna dina chattar",
        "perk2_sub": "Andra användare och administratörer kan inte läsa dem",
        "perk3": "Svaret skrivs fram",
        "perk3_sub": "Se varje svar växa fram medan det skrivs",
        "show": "Visa",
        "hide": "Dölj",
        "login_title": "Välkommen tillbaka",
        "login_sub": "Logga in för att fortsätta till {app}.",
        "email": "E-post",
        "password": "Lösenord",
        "remember": "Håll mig inloggad i upp till 30 dagar",
        "no_account": "Inget konto än?",
        "create_one": "Skapa ett",
        "or": "eller",
        "continue_guest": "Fortsätt som gäst",
        "signup_title": "Skapa ditt konto",
        "signup_sub": "Det tar mindre än en minut.",
        "signup_closed": "Registreringen är avstängd. Be en administratör om ett konto.",
        "name": "Namn",
        "password_hint": "Minst 15 tecken. Vanliga lösenord godtas inte.",
        "confirm_password_label": "Bekräfta lösenord",
        "create_account": "Skapa konto",
        "have_account": "Har du redan ett konto?",
        "err_login_failed": "Fel e-postadress eller lösenord.",
        "err_email_invalid": "Ange en giltig e-postadress.",
        "err_name_invalid": "Ange ditt namn (högst 100 tecken).",
        "err_email_taken": "Det finns redan ett konto med den här e-postadressen.",
        "err_password_too_short": "Lösenordet måste ha minst 15 tecken.",
        "err_password_too_long": "Lösenordet får ha högst 128 tecken.",
        "err_password_common": "Lösenordet är för vanligt. Välj ett annat.",
        "err_password_personal": "Lösenordet får inte vara din e-postadress eller ditt namn.",
        "err_password_match": "Lösenorden stämmer inte överens.",
        "err_signup_closed": "Registreringen är avstängd. Be en administratör om ett konto.",
        "err_forged_request": "Sidan är inaktuell. Ladda om den och försök igen.",
        "err_login_required": "Logga in först.",
        "err_invalid_input": "Kontrollera fälten och försök igen.",
        "err_network": "Ingen anslutning till servern. Försök igen.",
        "err_unknown": "Något gick fel. Försök igen.",
    },
}


def translator(lang: str) -> Callable[..., str]:
    table = TEXT.get(lang, TEXT["en"])

    def tr(key: str, **values: object) -> str:
        text = table.get(key) or TEXT["en"].get(key, key)
        # One pass, so braces inside user text are never filled in by mistake
        return re.sub(r"\{(\w+)\}", lambda m: str(values.get(m.group(1), m.group(0))), text)

    return tr
