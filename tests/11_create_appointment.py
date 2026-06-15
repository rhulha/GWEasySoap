"""11 - The hardest case: create a one-hour appointment in the calendar."""

from datetime import datetime, timedelta

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY, VERIFY_SSL


with GWEasySoap.connect_trusted_app(
    GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY, verify_ssl=VERIFY_SSL
) as gw:
    start = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    end = start + timedelta(hours=1)

    gw.create_appointment(
        subject="gweasysoap test appointment",
        body="Created by the gweasysoap test suite.",
        from_display_name=gw.user_name,
        from_email=gw.user_email,
        start=start,
        end=end,
    )
    print(f"Created appointment {start:%Y-%m-%d %H:%M} - {end:%H:%M}")

    print("Calendar now contains:")
    for item in gw.get_calendar_items(count=50):
        print(f"  {getattr(item, 'start_date', None)}  {item.subject}")
