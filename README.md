# gweasysoap

A small, pythonic helper library on top of the auto-generated
[`gwsoap`](https://pypi.org/project/gwsoap/) GroupWise SOAP client. It hides the
request/context boilerplate and gives you simple methods for logging in,
reading folders and items, sending mail, and creating appointments.

## Installation

```bash
pip install gweasysoap
```

This pulls in `gwsoap>=1.0.3`.

## Quick start

```python
from gweasysoap import GWEasySoap

# Use it as a context manager so the session is always logged out.
with GWEasySoap.connect_trusted_app(
    "https://gw.example.com:7191/soap", "jdoe", "MyApp", "trusted-key"
) as gw:
    print("Logged in as", gw.user_name, gw.user_email)

    mailbox = gw.get_mailbox()
    for item in gw.get_folder_items(mailbox.id, count=20):
        print(item.subject)

    gw.send_mail(
        subject="Hello",
        body_text="Sent from gweasysoap",
        recipients=[{"display_name": "Jane", "email": "jane@example.com"}],
    )
```

### Logging in

```python
# Username / password
gw = GWEasySoap.connect(endpoint, "jdoe", "secret")

# Trusted application key (impersonate a specific user)
gw = GWEasySoap.connect_trusted_app(endpoint, "jdoe", "MyApp", "trusted-key")

# Trusted application key, first usable mailbox on the post office
gw = GWEasySoap.connect_any_user(endpoint, "MyApp", "trusted-key")
```

Each `connect*` factory raises `GWEasySoapError` on failure. The matching
instance methods (`login`, `login_trusted_app`, `login_with_any_user`) return a
boolean instead, if you prefer to manage the instance yourself.

Constructor options: `application` (the name reported to GroupWise),
`debug`, and `verify_ssl`.

### What you can do

- **Users / mailboxes** – `get_user_list`, `get_user_mailboxes`
- **Proxies** – `get_proxy_list`
- **Address book** – `get_system_address_book`, `get_address_book_entries`
- **Folders** – `get_mailbox`, `get_trash_folder`, `get_calendar`,
  `get_system_folder`, `get_folder_list`, `get_shared_folder_by_name`
- **Items** – `get_items`, `get_folder_items`, `get_calendar_items`,
  `get_item`, `get_full_item`, `get_body`, `remove_item`
- **Mail** – `send_mail`
- **Appointments** – `create_appointment`, `create_appointment_in_folder`,
  `add_category`
- **Session** – `whoami`, `user_name`, `user_email`, `logout`

## License

MIT
