# Assessment Submission Portal

A local, secure, and student-friendly submission portal built with Python.

It supports admin and student workflows, multi-material question paper delivery, one-time submissions, configurable file-type controls, IP-level anti-duplicate protection, and a clean UI with dark mode.

---

## Features

- Admin and student login flow
- Admin upload for question paper + multiple supporting materials
- Student material listing with open/download actions
- One-time final submission (no re-upload)
- One submission per IP address (different roll numbers from same IP are blocked)
- Admin student management, dashboard, and credential export
- Configurable max file limit and allowed extensions
- Strict upload validation with clear retry alerts
- Submission success page shows exact uploaded filename(s)
- Dark/Light mode toggle

---

## Project Structure

- `server.py` - launcher entry point
- `portal_app/server_app.py` - routes and request handling
- `portal_app/portal_config.py` - config and constants
- `portal_app/portal_data.py` - Excel/log/file operations
- `portal_app/portal_security.py` - password and token utilities
- `portal_app/portal_sessions.py` - session lifecycle
- `portal_app/portal_templates.py` - HTML templates
- `portal_app/static/style.css` - shared styles
- `portal_app/requirements.txt` - dependencies
- `submission_ip_track.txt` - IP usage tracker for accepted submissions

---

## Prerequisites

- Python 3.10+ recommended
- `pip`

---

## Setup (Recommended: Virtual Environment)

### 1) Go to project folder

```bash
cd /home/ayyzenn/Desktop/server
```

### 2) Create virtual environment

```bash
python3 -m venv .env
```

### 3) Activate virtual environment

On Linux/macOS:

```bash
source .env/bin/activate
```

On Windows (PowerShell):

```powershell
.env\Scripts\Activate.ps1
```

On Windows (CMD):

```cmd
.env\Scripts\activate.bat
```

### 4) Install dependencies

```bash
pip install -r portal_app/requirements.txt
```

---

## Run the Portal

From the project directory:

```bash
python3 server.py
```

On some Windows setups, use:

```cmd
python server.py
```

Open in browser on **this machine**:

- [http://localhost:8080](http://localhost:8080)

**Binding:** By default the server listens on **all network interfaces**, so other PCs on your LAN can connect using `http://<this-computer-IP>:8080`.

To listen on **localhost only** (no LAN access):

```bash
PORTAL_BIND=127.0.0.1 python3 server.py
```

If `PORTAL_BIND=127.0.0.1` is set in your environment, remove it for LAN access.

---

## Access from another PC on the LAN (e.g. 172.16.4.x)

1. Start the portal **without** `PORTAL_BIND=127.0.0.1`.
2. On the server machine, check its IP: `ip a` or `hostname -I`.
3. On the **other** device use `http://172.16.4.<server>:8080` (adjust IP/port).
4. If that fails while `http://127.0.0.1:8080` works on the server itself, it is almost always **firewall**, **wrong subnet**, or **AP/client isolation** on Wi‑Fi — not the Python code.

### Check that the port is open on the server

```bash
ss -tlnp | grep 8080
```

You should see `0.0.0.0:8080` or `*:8080`. If you only see `127.0.0.1:8080`, LAN clients cannot connect (fix `PORTAL_BIND` or how you start the server).

### Linux firewall (examples)

**nftables** (common on Arch) — inspect rules, then allow TCP 8080 if needed (chain names vary):

```bash
sudo nft list ruleset | less
```

**firewalld**:

```bash
sudo firewall-cmd --add-port=8080/tcp --permanent && sudo firewall-cmd --reload
```

**ufw**:

```bash
sudo ufw allow 8080/tcp comment 'portal' && sudo ufw reload
```

### Windows

Windows Defender Firewall → Advanced → Inbound rules → New rule → TCP → port **8080** → Allow.

---

## Linux, macOS, and Windows

The portal uses Python’s standard library and `os.path`, so it runs on typical Linux distributions (including Ubuntu and Arch), macOS, and Windows. Use a virtual environment on any OS, then install dependencies from `portal_app/requirements.txt` as shown above.

---

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`

---

## Notes

- Wrong username/password shows a clear message **on the login page** (no raw browser credential error page); applies to admin and student accounts.
- Expired or missing sessions redirect back to login with a short explanation.
- If `students.xlsx` cannot be read or saved, you get a login-page hint instead of an unexplained server error.
- Missing question material files show a friendly page with a link back to the materials list.
- Keep `students.xlsx` in project root with at least:
  - `Roll No.`
  - `Student Name`
- Folders like `question_paper/` and `submissions/` are auto-created if missing.
- `submission_ip_track.txt` is auto-created and stores one accepted submission IP per line.
- IP protection behavior:
  - Same student trying again -> blocked by one-time submission rule first.
  - Different student from already-used IP -> blocked with IP reuse message.
- For best reliability, always run inside the virtual environment.

### Slow login or long waits on each click

- **Fixed in code:** the server no longer performs reverse DNS lookups for client IPs (that often causes multi‑second delays on LAN addresses like `172.16.x.x`).
- If it is still slow: keep `students.xlsx` reasonably small, avoid storing it on a slow/network drive, and temporarily exclude the project folder from aggressive antivirus “scan every read” if you see disk thrashing.
