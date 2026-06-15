"""8 - Use a server-side filter: find items whose subject begins with "P"."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY
from gwsoap.types.Filter import Filter
from gwsoap.types.FilterEntry import FilterEntry
from gwsoap.types.FilterOp import FilterOp


with GWEasySoap.connect_trusted_app(
    GW_SOAP_URL, GW_USER, GW_TRUSTED_APP_NAME, GW_TRUSTED_APP_KEY
) as gw:
    f = Filter(element=FilterEntry(op=FilterOp.BEGINS, field="subject", value="P"))
    items = gw.get_items(None, filter=f, count=10)
    print(f"{len(items)} match(es):")
    for item in items:
        print(f"  {item.subject}")
