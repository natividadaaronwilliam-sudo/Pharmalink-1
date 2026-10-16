import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr


GENERIC_FORGOT_MESSAGE = (
    "If an account matches that ID and email, a password reset link has been sent to the email on file."
)


def _clean(value: str) -> str:
    return (value or "").strip().strip('"').strip("'")


def send_mail(to_email: str, subject: str, body_html: str) -> dict:
    host = _clean(os.getenv("SMTP_HOST", "smtp.gmail.com")) or "smtp.gmail.com"
    port_raw = _clean(os.getenv("SMTP_PORT", "587")) or "587"
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 587
    user = _clean(os.getenv("SMTP_EMAIL", ""))
    password = _clean(os.getenv("SMTP_APP_PASSWORD", "")).replace(" ", "")
    from_name = _clean(os.getenv("SMTP_FROM_NAME", "PharmaLink")) or "PharmaLink"
    to_email = _clean(to_email)

    if not user or not password:
        return {"success": False, "message": "SMTP is not configured."}
    if not to_email:
        return {"success": False, "message": "Missing recipient email."}

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((from_name, user))
    msg["To"] = to_email
    msg.set_content("Please view this purchase order in an HTML email app.")
    msg.add_alternative(body_html or "", subtype="html")

    attempts = []
    if port == 465:
        attempts.append((host, 465, "ssl"))
    else:
        attempts.append((host, port, "starttls"))
        if (host, 465) != (host, port):
            attempts.append((host, 465, "ssl"))

    last_error = "The email server rejected the message."
    for smtp_host, smtp_port, mode in attempts:
        try:
            if mode == "ssl":
                smtp = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
            else:
                smtp = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
            with smtp:
                smtp.login(user, password)
                smtp.send_message(msg)
            return {"success": True, "message": "sent"}
        except Exception as exc:
            last_error = str(exc) or type(exc).__name__
    return {"success": False, "message": last_error}
