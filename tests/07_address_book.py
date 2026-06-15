"""7 - Read the system address book and list its entries."""

from gweasysoap import GWEasySoap
from config import GW_SOAP_URL, GW_USER, GW_PASSWORD


with GWEasySoap.connect(GW_SOAP_URL, GW_USER, GW_PASSWORD) as gw:
    book = gw.get_system_address_book()
    if book is None:
        raise SystemExit("System address book not found")

    print(f"Address book: {book.name}")
    entries = gw.get_address_book_entries(book)
    print(f"{len(entries)} entry/entries:")
    for entry in entries:
        print(f"  {entry.name}")
