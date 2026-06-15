"""9 - Drill into a single mailbox item and fetch its decoded body text."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY, VERIFY_SSL


with GWEasySoap.connect_trusted_app(
    GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY, verify_ssl=VERIFY_SSL
) as gw:
    mailbox = gw.get_mailbox()
    items = gw.get_folder_items(mailbox.id, count=5) if mailbox else []
    if not items:
        raise SystemExit("Mailbox is empty - nothing to read")

    first = items[0]
    print(f"Subject: {getattr(first, 'subject', None)}")
    print("Body:")
    print(gw.get_body(first) or "  (no text body)")
