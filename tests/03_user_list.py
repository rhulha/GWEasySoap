"""3 - List the post office mailboxes (uses the trusted-app key, no session)."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY, VERIFY_SSL


gw = GWEasySoap(verify_ssl=VERIFY_SSL)
mailboxes = gw.get_user_mailboxes(GW_SOAP_URL, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY)

print(f"Found {len(mailboxes)} mailbox(es):")
for mb in mailboxes:
    print(f"  {mb['display_name']} <{mb['email']}>  (userid={mb['userid']})")
