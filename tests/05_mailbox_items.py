"""5 - Open the mailbox folder and list the items inside it."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY


with GWEasySoap.connect_trusted_app(
    GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY
) as gw:
    mailbox = gw.get_mailbox()
    if mailbox is None:
        raise SystemExit("Mailbox not found")

    print(f"Mailbox: {mailbox.name} (id={mailbox.id})")
    items = gw.get_folder_items(mailbox.id, count=20)
    print(f"{len(items)} item(s):")
    for item in items:
        print(f"  {getattr(item, 'subject', None) or item.name}")
