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

```bash
python3 server.py
```

Open in browser:

- [http://localhost:8080](http://localhost:8080)

---

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`

---

## Notes

- Keep `students.xlsx` in project root with at least:
  - `Roll No.`
  - `Student Name`
- Folders like `question_paper/` and `submissions/` are auto-created if missing.
- `submission_ip_track.txt` is auto-created and stores one accepted submission IP per line.
- IP protection behavior:
  - Same student trying again -> blocked by one-time submission rule first.
  - Different student from already-used IP -> blocked with IP reuse message.
- For best reliability, always run inside the virtual environment.
