"""4 - Log in as the first usable mailbox on the post office."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY


with GWEasySoap.connect_any_user(
    GW_SOAP_URL, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY
) as gw:
    print(f"Logged in as: {gw.user_name} <{gw.user_email}>")
