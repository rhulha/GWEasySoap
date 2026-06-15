"""A pythonic helper around the auto-generated ``gwsoap`` GroupWise SOAP client."""

import logging
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence, Union

from gwsoap.service.groupwise_client import GroupWiseClient
from gwsoap.soap.exceptions import SoapFaultException
from gwsoap.soap.request_context import RequestContext

from gwsoap.methods.LoginRequest import LoginRequest
from gwsoap.methods.LogoutRequest import LogoutRequest
from gwsoap.methods.GetUserListRequest import GetUserListRequest
from gwsoap.methods.GetAddressBookListRequest import GetAddressBookListRequest
from gwsoap.methods.GetItemsRequest import GetItemsRequest
from gwsoap.methods.GetItemRequest import GetItemRequest
from gwsoap.methods.RemoveItemRequest import RemoveItemRequest
from gwsoap.methods.SendItemRequest import SendItemRequest
from gwsoap.methods.CreateItemRequest import CreateItemRequest
from gwsoap.methods.ModifyItemRequest import ModifyItemRequest
from gwsoap.methods.GetFolderListRequest import GetFolderListRequest

from gwsoap.types.AddressBookItem import AddressBookItem
from gwsoap.types.Appointment import Appointment
from gwsoap.types.CategoryRefList import CategoryRefList
from gwsoap.types.ContainerRef import ContainerRef
from gwsoap.types.Custom import Custom
from gwsoap.types.CustomList import CustomList
from gwsoap.types.Distribution import Distribution
from gwsoap.types.DistributionType import DistributionType
from gwsoap.types.FolderType import FolderType
from gwsoap.types.From import From
from gwsoap.types.ItemChanges import ItemChanges
from gwsoap.types.Mail import Mail
from gwsoap.types.MessageBody import MessageBody
from gwsoap.types.MessagePart import MessagePart
from gwsoap.types.PlainText import PlainText
from gwsoap.types.Recipient import Recipient
from gwsoap.types.RecipientList import RecipientList
from gwsoap.types.RecipientType import RecipientType
from gwsoap.types.SharedFolder import SharedFolder
from gwsoap.types.SystemFolder import SystemFolder
from gwsoap.types.TrustedApplication import TrustedApplication

from .exceptions import GWEasySoapError

logger = logging.getLogger(__name__)

GW_SYSTEM_ADDRESS_BOOK_NAME = "GroupWiseSystemAddressBook"

RecipientLike = Union[Mapping[str, Any], Any]


class GWEasySoap:
    """High-level, session-aware wrapper for the GroupWise SOAP API.

    Create it directly and call one of the ``login*`` methods, use one of the
    ``connect*`` classmethod factories, or use it as a context manager so the
    session is always logged out::

        with GWEasySoap.connect_trusted_app(endpoint, user, app, key) as gw:
            mailbox = gw.get_mailbox()
    """

    def __init__(self, application: str = "GWEasySoap", debug: bool = False,
                 verify_ssl: bool = True):
        self.client: Optional[GroupWiseClient] = None
        self.session: Optional[str] = None
        self.login_resp = None
        self.application = application
        self.debug = debug
        self.verify_ssl = verify_ssl

    # -- factories ---------------------------------------------------------

    @classmethod
    def connect(cls, endpoint: str, username: str, password: str, **kwargs) -> "GWEasySoap":
        """Log in with a username/password and return the connected instance."""
        gw = cls(**kwargs)
        if not gw.login(endpoint, username, password):
            raise GWEasySoapError(f"Login failed for user {username!r}")
        return gw

    @classmethod
    def connect_trusted_app(cls, endpoint: str, username: str, tapp_name: str,
                            tapp_key: str, **kwargs) -> "GWEasySoap":
        """Log in via a trusted application key and return the connected instance."""
        gw = cls(**kwargs)
        if not gw.login_trusted_app(endpoint, username, tapp_name, tapp_key):
            raise GWEasySoapError(f"Trusted app login failed for user {username!r}")
        return gw

    @classmethod
    def connect_any_user(cls, endpoint: str, tapp_name: str, tapp_key: str,
                         **kwargs) -> "GWEasySoap":
        """Log in as the first usable mailbox on the post office (trusted app)."""
        gw = cls(**kwargs)
        gw.login_with_any_user(endpoint, tapp_name, tapp_key)
        return gw

    # -- context manager ---------------------------------------------------

    def __enter__(self) -> "GWEasySoap":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.logout()

    # -- login -------------------------------------------------------------

    def login(self, endpoint: str, username: str, password: str) -> bool:
        """Log in with a plain username and password."""
        auth = PlainText(username=username, password=password)
        return self._login_with_redirect(endpoint, auth)

    def login_trusted_app(self, endpoint: str, username: str, tapp_name: str,
                          tapp_key: str) -> bool:
        """Log in on behalf of ``username`` using a trusted application key."""
        auth = TrustedApplication(username=username, name=tapp_name, key=tapp_key)
        return self._login_with_redirect(endpoint, auth)

    def login_with_any_user(self, endpoint: str, tapp_name: str, tapp_key: str) -> bool:
        """Try the trusted-app login against post office users until one succeeds."""
        last_fault = None
        attempts = 0
        for info in self.get_user_list(endpoint, tapp_name, tapp_key):
            if info.recip_type != RecipientType.USER or not info.userid:
                continue
            if attempts >= 10:
                break
            attempts += 1
            try:
                if self.login_trusted_app(endpoint, info.userid, tapp_name, tapp_key):
                    return True
            except SoapFaultException as e:
                last_fault = e
        if last_fault is not None:
            raise last_fault
        raise GWEasySoapError(
            "No usable GroupWise mailbox found - does this post office have any?"
        )

    def _login_with_redirect(self, endpoint: str, auth) -> bool:
        login_resp = self._attempt_login(endpoint, auth)
        if login_resp is not None and login_resp.redirect_to_host:
            # The mailbox lives on another post office; its Host carries no
            # scheme, so retry against that POA trying both http and https.
            host = login_resp.redirect_to_host[0]
            logger.info("Login redirected to host %s:%s", host.ip_address, host.port)
            login_resp = self._attempt_redirect(endpoint, host, auth)

        if login_resp is None or login_resp.status is None or login_resp.status.code != 0:
            return False
        self.login_resp = login_resp
        self.session = login_resp.session
        return True

    def _attempt_login(self, endpoint: str, auth):
        self.client = GroupWiseClient(endpoint, debug=self.debug, verify_ssl=self.verify_ssl)
        login_req = LoginRequest(auth=auth, application=self.application, language="en")
        return self.client.login(login_req)

    def _attempt_redirect(self, endpoint: str, host, auth):
        import http.client
        from urllib.parse import urlsplit, urlunsplit

        parts = urlsplit(endpoint)
        netloc = f"{host.ip_address}:{host.port}"
        schemes = [parts.scheme, "https" if parts.scheme == "http" else "http"]
        last_err = None
        for scheme in schemes:
            target = urlunsplit((scheme, netloc, parts.path, parts.query, parts.fragment))
            try:
                return self._attempt_login(target, auth)
            except (OSError, http.client.HTTPException) as e:
                last_err = e
        if last_err is not None:
            raise last_err
        return None

    # -- connected user ----------------------------------------------------

    def whoami(self):
        """Return the ``userinfo`` of the logged-in user, or ``None``."""
        return self.login_resp.userinfo if self.login_resp else None

    @property
    def user_name(self) -> str:
        info = self.whoami()
        return (info.name if info else "") or ""

    @property
    def user_email(self) -> str:
        info = self.whoami()
        return (getattr(info, "email", None) if info else "") or ""

    # -- users (no session needed) ----------------------------------------

    def get_user_list(self, endpoint: str, tapp_name: str, tapp_key: str) -> list:
        """Return the raw user records for the post office at ``endpoint``."""
        client = GroupWiseClient(endpoint, debug=self.debug, verify_ssl=self.verify_ssl)
        response = client.get_user_list(GetUserListRequest(name=tapp_name, key=tapp_key))
        self._raise_on_bad_status(response, "get_user_list")
        if response and response.users and response.users.user:
            return response.users.user
        return []

    def get_user_mailboxes(self, endpoint: str, tapp_name: str, tapp_key: str) -> list:
        """Return the post office mailboxes as plain dicts."""
        return [
            {
                "userid": u.userid,
                "display_name": u.name or u.userid,
                "email": u.email or u.userid,
                "uuid": u.uuid,
            }
            for u in self.get_user_list(endpoint, tapp_name, tapp_key)
            if u.recip_type == RecipientType.USER and u.userid
        ]

    # -- address book ------------------------------------------------------

    def get_system_address_book(self):
        """Return the GroupWise system address book, or ``None``."""
        response = self.client.get_address_book_list(GetAddressBookListRequest(), self._ctx)
        books = response.books
        if not books or not books.book:
            return None
        for book in books.book:
            if book and book.id and book.id.startswith(GW_SYSTEM_ADDRESS_BOOK_NAME + "@"):
                return book
        return None

    def get_address_book_entries(self, book, count: Optional[int] = None) -> list:
        """Return the :class:`AddressBookItem` entries inside ``book``."""
        response = self.client.get_items(
            GetItemsRequest(container=book.id, count=count), self._ctx
        )
        items = response.items
        if not items or not items.item:
            return []
        return [item for item in items.item if isinstance(item, AddressBookItem)]

    # -- folders -----------------------------------------------------------

    def get_system_folder(self, folder_type):
        """Return the system folder of the given :class:`FolderType`, or ``None``."""
        request = GetFolderListRequest(parent="folders", recurse=False, imap=False, nntp=False)
        response = self.client.get_folder_list(request, self._ctx)
        folders = response.folders
        if not folders or not folders.folder:
            return None
        for folder in folders.folder:
            if isinstance(folder, SystemFolder) and folder.folder_type == folder_type:
                return folder
        return None

    def get_mailbox(self):
        return self.get_system_folder(FolderType.MAILBOX)

    def get_trash_folder(self):
        return self.get_system_folder(FolderType.TRASH)

    def get_calendar(self):
        return self.get_system_folder(FolderType.CALENDAR)

    def get_folder_list(self) -> list:
        """Return every folder in the mailbox (recursive)."""
        request = GetFolderListRequest(parent="folders", recurse=True, imap=False, nntp=False)
        response = self.client.get_folder_list(request, self._ctx)
        folders = response.folders
        if not folders or not folders.folder:
            return []
        return folders.folder

    def get_shared_folder_by_name(self, name: str):
        """Return the :class:`SharedFolder` with the given name, or ``None``."""
        for folder in self.get_folder_list():
            if isinstance(folder, SharedFolder) and folder.name == name:
                return folder
        return None

    # -- items -------------------------------------------------------------

    def get_items(self, container_id: str, filter: Optional[str] = None,
                  count: Optional[int] = None) -> list:
        """Return the items inside a container (folder or address book)."""
        request = GetItemsRequest(container=container_id, filter=filter, count=count)
        response = self.client.get_items(request, self._ctx)
        items = response.items
        if not items or not items.item:
            return []
        return items.item

    def get_folder_items(self, folder_id: str, count: int = 200) -> list:
        return self.get_items(folder_id, count=count)

    def get_calendar_items(self, count: int = 200) -> list:
        calendar = self.get_calendar()
        return self.get_items(calendar.id, count=count) if calendar else []

    def get_item(self, item_id: str):
        """Return a single item by id."""
        response = self.client.get_item(GetItemRequest(id=item_id), self._ctx)
        return response.item if response and response.item else None

    def get_full_item(self, item_id: str):
        """Return a single item including its message body view."""
        from gwsoap.types.View import View

        request = GetItemRequest(id=item_id, view=View(value=["message"]))
        response = self.client.get_item(request, self._ctx)
        return response.item if response and response.item else None

    def get_body(self, item) -> str:
        """Return the decoded plain-text body of ``item``."""
        full = self.get_full_item(item.id)
        message = getattr(full, "message", None)
        if not message or not message.part:
            return ""
        value = message.part[0].value
        return value.decode("utf-8", errors="replace") if value is not None else ""

    def remove_item(self, container: str, item_id: str) -> None:
        """Remove an item from a container."""
        response = self.client.remove_item(
            RemoveItemRequest(container=container, id=item_id), self._ctx
        )
        self._raise_on_bad_status(response, "remove_item")

    # -- mail --------------------------------------------------------------

    def send_mail(self, subject: str, body_text: str,
                  recipients: Sequence[RecipientLike],
                  return_sent_items_id: bool = True) -> Optional[str]:
        """Send a plain-text mail.

        ``recipients`` may be dicts or objects carrying ``display_name``/``name``,
        ``email``/``userid`` and an optional ``uuid``.
        """
        self._require_session()
        recipient_list = RecipientList(
            recipient=[
                Recipient(
                    display_name=self._recipient_value(r, "display_name")
                    or self._recipient_value(r, "name")
                    or self._recipient_value(r, "userid"),
                    email=self._recipient_value(r, "email")
                    or self._recipient_value(r, "userid"),
                    uuid=self._recipient_value(r, "uuid"),
                    dist_type=DistributionType.TO,
                    recip_type=RecipientType.USER,
                )
                for r in recipients
            ]
        )
        request = SendItemRequest(
            item=Mail(
                subject=subject,
                distribution=Distribution(recipients=recipient_list),
                message=MessageBody(part=[MessagePart(value=body_text.encode("utf-8"))]),
                return_sent_items_id=return_sent_items_id,
            )
        )
        response = self.client.send_item(request, self._ctx)
        self._raise_on_bad_status(response, "send_mail")
        return response.id

    # -- appointments ------------------------------------------------------

    def create_appointment(self, subject: str, body: str, from_display_name: str,
                           from_email: str, start: datetime, end: datetime,
                           custom_field: str = "") -> None:
        """Create an appointment in the connected user's calendar."""
        apt = Appointment(
            subject=subject,
            distribution=Distribution(
                from_value=From(display_name=from_display_name, email=from_email),
                recipients=RecipientList(recipient=[
                    Recipient(
                        display_name=self.user_name,
                        email=self.user_email,
                        dist_type=DistributionType.TO,
                        recip_type=RecipientType.USER,
                    )
                ]),
            ),
            message=self._text_message(body),
            start_date=start,
            end_date=end,
            customs=CustomList(custom=[Custom(field="etermin", value=custom_field)])
            if custom_field else None,
        )
        self._raise_on_bad_status(
            self.client.create_item(CreateItemRequest(item=apt), self._ctx), "create_appointment"
        )

    def create_appointment_in_folder(self, folder_id: str, subject: str, body: str,
                                     start: datetime, end: datetime) -> None:
        """Create an appointment inside a specific (e.g. shared) folder."""
        apt = Appointment(
            subject=subject,
            container=[ContainerRef(value=folder_id)],
            message=self._text_message(body),
            start_date=start,
            end_date=end,
        )
        self._raise_on_bad_status(
            self.client.create_item(CreateItemRequest(item=apt), self._ctx),
            "create_appointment_in_folder",
        )

    def add_category(self, item_id: str, category_name: str) -> None:
        """Tag an existing item with a category."""
        updates = ItemChanges(add=Appointment(categories=CategoryRefList(category=[category_name])))
        self._raise_on_bad_status(
            self.client.modify_item(ModifyItemRequest(id=item_id, updates=updates), self._ctx),
            "add_category",
        )

    # -- lifecycle ---------------------------------------------------------

    def logout(self) -> None:
        """Log out and clear the session (safe to call when not logged in)."""
        if self.client and self.session:
            try:
                self.client.logout(LogoutRequest(), self._ctx)
            except SoapFaultException as e:
                logger.warning("Logout failed: %s", e.fault_string)
            finally:
                self.session = None
                self.login_resp = None

    # -- helpers -----------------------------------------------------------

    @property
    def _ctx(self) -> RequestContext:
        self._require_session()
        return RequestContext(session_id=self.session)

    def _require_session(self) -> None:
        if not self.client or not self.session:
            raise GWEasySoapError("Not logged in")

    @staticmethod
    def _text_message(body: str):
        return MessageBody(part=[MessagePart(value=body.encode("utf-8"))]) if body else None

    @staticmethod
    def _recipient_value(recipient: RecipientLike, name: str):
        if isinstance(recipient, Mapping):
            return recipient.get(name)
        return getattr(recipient, name, None)

    @staticmethod
    def _raise_on_bad_status(response, action: str) -> None:
        status = getattr(response, "status", None)
        if status and status.code not in (None, 0):
            raise GWEasySoapError(
                f"{action} failed: {status.description} (code {status.code})",
                code=status.code,
            )
