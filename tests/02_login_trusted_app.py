"""2 - Log in on behalf of a user with a trusted application key (no password)."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY


with GWEasySoap.connect_trusted_app(
    GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY
) as gw:
    info = gw.whoami()
    print("User info:")
    for attr in ("display_name", "name", "email"):
        value = getattr(info, attr, None)
        if value:
            print(f"  {attr}: {value}")
