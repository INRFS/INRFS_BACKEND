import json
import os
import urllib.error
import urllib.request

from dotenv import load_dotenv

load_dotenv()


def send_welcome_email(
    email: str | None,
    name: str,
    username: str | None,
    password: str,
    role: str,
) -> bool:
    if not email:
        return False

    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")
    sender_name = os.getenv("BREVO_SENDER_NAME", "INRFS")
    template_id = os.getenv("BREVO_WELCOME_TEMPLATE_ID")
    login_url = os.getenv("BREVO_LOGIN_URL")

    missing = []
    if not api_key:
        missing.append("BREVO_API_KEY")
    if not sender_email:
        missing.append("BREVO_SENDER_EMAIL")
    if not template_id:
        missing.append("BREVO_WELCOME_TEMPLATE_ID")
    if not login_url:
        missing.append("BREVO_LOGIN_URL")

    if missing:
        print("BREVO CONFIGURATION MISSING:", ", ".join(missing))
        return False

    try:
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email,
            },
            "to": [
                {
                    "email": email,
                    "name": name,
                }
            ],
            "templateId": int(template_id),
            "params": {
                "name": name,
                "username": username or "",
                "password": password,
                "role": role,
                "login_url": login_url,
            },
        }

        request = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            status_code = response.getcode()
            response_body = response.read().decode(
                "utf-8",
                errors="replace",
            )

        if 200 <= status_code < 300:
            print(f"BREVO WELCOME EMAIL SENT TO: {email}")
            return True

        print(
            "BREVO EMAIL FAILED:",
            status_code,
            response_body,
        )
        return False

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )
        print(
            "BREVO EMAIL HTTP ERROR:",
            exc.code,
            body,
        )
        return False
    except Exception as exc:
        print("BREVO EMAIL ERROR:", repr(exc))
        return False


def send_otp_email(
    email: str,
    name: str,
    otp: str,
    expiry_minutes: int = 5,
) -> bool:
    if not email:
        return False

    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")
    sender_name = os.getenv("BREVO_SENDER_NAME", "INRFS")
    template_id = os.getenv("BREVO_OTP_TEMPLATE_ID")

    missing = []

    if not api_key:
        missing.append("BREVO_API_KEY")

    if not sender_email:
        missing.append("BREVO_SENDER_EMAIL")

    if not template_id:
        missing.append("BREVO_OTP_TEMPLATE_ID")

    if missing:
        print("BREVO CONFIGURATION MISSING:", ", ".join(missing))
        return False

    try:
        payload = {
            "sender": {
                "name": sender_name,
                "email": sender_email,
            },
            "to": [
                {
                    "email": email,
                    "name": name or "User",
                }
            ],
            "templateId": int(template_id),
            "params": {
                "name": name or "User",
                "otp": otp,
                "expiry_minutes": expiry_minutes,
            },
        }

        request = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "accept": "application/json",
                "api-key": api_key,
                "content-type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            status_code = response.getcode()
            response_body = response.read().decode(
                "utf-8",
                errors="replace",
            )

        if 200 <= status_code < 300:
            print(f"BREVO OTP EMAIL SENT TO: {email}")
            return True

        print(
            "BREVO OTP EMAIL FAILED:",
            status_code,
            response_body,
        )
        return False

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(
            "utf-8",
            errors="replace",
        )
        print(
            "BREVO OTP EMAIL HTTP ERROR:",
            exc.code,
            body,
        )
        return False
    except Exception as exc:
        print("BREVO OTP EMAIL ERROR:", repr(exc))
        return False