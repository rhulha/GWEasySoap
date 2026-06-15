"""1 - The simplest case: log in with a password and print who we are."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_PASSWORD, VERIFY_SSL


with GWEasySoap.connect(GW_SOAP_URL, GW_USER, GW_PASSWORD, verify_ssl=VERIFY_SSL) as gw:
    print(f"Logged in as: {gw.user_name} <{gw.user_email}>")
