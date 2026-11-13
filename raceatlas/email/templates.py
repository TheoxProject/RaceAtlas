import re
from dataclasses import dataclass
from html import escape

from .config import EmailInputError, mailbox

SUBJECTS = {
    "confirmation": "Confirmez votre adresse e-mail — RaceAtlas",
    "reset": "Réinitialisez votre mot de passe — RaceAtlas",
}


@dataclass(frozen=True, repr=False)
class EmailMessage:
    recipient: str
    subject: str
    html: str
    text: str


def render_message(base, purpose, recipient, token):
    mailbox(recipient)
    if (
        not isinstance(purpose, str)
        or purpose not in SUBJECTS
        or not isinstance(token, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token)
    ):
        raise EmailInputError()
    confirmation = purpose == "confirmation"
    fragment = "confirm-email" if confirmation else "reset-password"
    link = f"{base}#{fragment}={token}"
    heading = (
        "Bienvenue sur RaceAtlas !" if confirmation else "Un nouveau départ pour votre compte."
    )
    introduction = (
        "Confirmez votre adresse e-mail pour préparer votre saison cycliste."
        if confirmation
        else "Vous avez demandé à réinitialiser votre mot de passe RaceAtlas."
    )
    button = "Confirmer mon adresse e-mail" if confirmation else "Réinitialiser mon mot de passe"
    expiry = "24 heures" if confirmation else "30 minutes"
    ignore = "Si vous n’êtes pas à l’origine de cette demande, ignorez cet e-mail."
    safe_link = escape(link, quote=True)
    html = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(SUBJECTS[purpose])}</title></head>
<body style="margin:0;background:#f3f5f8;font-family:Arial,sans-serif;color:#111F37">
<main style="max-width:560px;margin:32px auto;background:#fff;
border:1px solid #dce2e9;border-radius:14px;overflow:hidden">
<header style="padding:25px 28px;background:#111F37;color:#fff;font-size:26px;font-weight:bold">
Race<span style="color:#F97316">Atlas</span></header>
<section style="padding:28px">
<h1 style="font-size:24px;line-height:1.25;margin:0 0 18px">{heading}</h1>
<p style="font-size:16px;line-height:1.6">{introduction}</p>
<p style="margin:28px 0"><a href="{safe_link}" style="display:inline-block;padding:15px 19px;
background:#F97316;color:#111F37;text-decoration:none;border-radius:8px;
font-weight:bold">{button}</a></p>
<p style="font-size:14px;line-height:1.6">Ce lien expire dans <strong>{expiry}</strong>.</p>
<p style="font-size:13px;line-height:1.6;color:#526078">{ignore}</p>
<p style="font-size:12px;line-height:1.6;color:#526078">
Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :</p>
<p style="font-size:12px;line-height:1.6;overflow-wrap:anywhere">
<a href="{safe_link}" style="color:#111F37">{safe_link}</a></p>
</section><footer style="padding:16px 28px;border-top:1px solid #e2e6ec;
font-size:12px;color:#526078">RaceAtlas · Votre saison, votre terrain de jeu.</footer>
</main></body></html>'''
    text = (
        f"{heading}\n\n{introduction}\n\n{button} :\n{link}\n\n"
        f"Ce lien expire dans {expiry}.\n\n{ignore}\n\nRaceAtlas"
    )
    return EmailMessage(recipient, SUBJECTS[purpose], html, text)
