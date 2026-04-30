# Assessment Submission Portal

Local Python submission portal with admin + student flows.

## Run

```bash
pip install -r portal_app/requirements.txt
python3 server.py
```

Open: `http://localhost:8080`

## Default Admin

- Username: `admin`
- Password: `admin123`

## Main Features

- Admin and student login
- Question paper upload by admin
- Student question paper view + one-time submission
- No re-upload after first submission
- Admin student management and dashboard
- Password reset (single/all)
- Export credentials to Excel
- Configurable max files and allowed extensions
- Strict extension validation with student-friendly retry popup
- Light/Dark mode toggle

## Structure

- `server.py` (launcher only)
- `portal_app/server_app.py`
- `portal_app/portal_config.py`
- `portal_app/portal_data.py`
- `portal_app/portal_security.py`
- `portal_app/portal_sessions.py`
- `portal_app/portal_templates.py`
- `portal_app/static/style.css`
- `portal_app/requirements.txt`
