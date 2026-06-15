"""gweasysoap - a pythonic helper library for the GroupWise SOAP API."""

from .client import GWEasySoap, GW_SYSTEM_ADDRESS_BOOK_NAME
from .exceptions import GWEasySoapError

__version__ = "0.1.0"

__all__ = ["GWEasySoap", "GWEasySoapError", "GW_SYSTEM_ADDRESS_BOOK_NAME"]
