# gweasysoap test scripts

Manual, runnable scripts that exercise the library against a live GroupWise post
office. They are ordered from the simplest task to the hardest.

## Setup

1. Install the package (from the project root):

   ```bash
   pip install -e .
   ```

2. Edit [config.py](config.py) so the URL, user and trusted-app key point at a
   reachable POA.

3. Run a script from inside this folder (so `config.py` is importable):

   ```bash
   cd tests
   python 01_login_password.py
   ```

## The scripts

| # | Script | What it shows |
|---|--------|---------------|
| 01 | `01_login_password.py` | Log in with a password, print the connected user |
| 02 | `02_login_trusted_app.py` | Trusted-application login (no password) |
| 03 | `03_user_list.py` | List the post office mailboxes (no session) |
| 04 | `04_login_any_user.py` | Log in as the first usable mailbox |
| 05 | `05_mailbox_items.py` | Open the mailbox folder and list its items |
| 06 | `06_calendar.py` | List calendar appointments |
| 07 | `07_address_book.py` | Read the system address book |
| 08 | `08_filter_items.py` | Server-side filter (subject begins with "P") |
| 09 | `09_read_body.py` | Fetch and decode a single item's body |
| 10 | `10_send_mail.py` | **Sends** a mail (self-send) |
| 11 | `11_create_appointment.py` | **Creates** a calendar appointment |

Scripts 10 and 11 modify the mailbox; run them only against a test account.
