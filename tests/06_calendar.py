"""6 - List the appointments in the calendar."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY, VERIFY_SSL


with GWEasySoap.connect_trusted_app(
    GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY, verify_ssl=VERIFY_SSL
) as gw:
    items = gw.get_calendar_items(count=50)
    print(f"{len(items)} calendar item(s):")
    for item in items:
        start = getattr(item, "start_date", None)
        print(f"  {start}  {item.subject}")
