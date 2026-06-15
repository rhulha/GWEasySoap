"""10 - Send a plain-text mail to the connected user (a safe self-send)."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY


with GWEasySoap.connect_trusted_app(
    GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY
) as gw:
    recipient = {"display_name": gw.user_name, "email": gw.user_email}
    ids = gw.send_mail(
        subject="Hello from gweasysoap",
        body_text="This message was sent by the gweasysoap test suite.",
        recipients=[recipient],
    )
    print("Sent mail; sent-items id(s):", ids or "(none returned)")
