# Assessment Submission Portal

Lightweight local/LAN portal for exam material delivery and one-time student submissions.

This project is designed for real classroom/lab use with many concurrent logins. Recent performance hardening includes:

- Multithreaded request handling for parallel clients
- Thread-safe in-memory cache for `students.xlsx` to reduce repeated Excel reads
- Session operations made thread-safe for concurrent requests

---

## Features

- Admin and student authentication flow
- Multi-paper-type question material delivery (A/B/C...)
- Student one-time final submission flow
- Global exam timer with start/end, pause/resume, and reset controls
- Student-side timer warnings and automatic lock when exam time ends
- Late submission request flow (student request, teacher approve/reject)
- Student-specific extra-time window after approval
- Per-IP anti-duplicate submission protection
- Admin tools:
  - paper setup and uploads
  - student management
   - submission dashboard with auto-refresh and filter
   - late request decision controls
  - credential export
- Configurable upload rules (max files + allowed extensions)
- File preview with per-file size and empty-file validation
- Async single-student password reset from admin table
- Admin-editable student instructions shown on student home page
- Built-in mini games (Snake + Flappy Bird) for students
- Dark/light mode UI toggle

---

## Project Structure

- `server.py`: launcher entry point
- `portal_app/server_app.py`: HTTP routes, request handlers, server startup
- `portal_app/portal_data.py`: roster/questions/submission file I/O
- `portal_app/portal_config.py`: constants and runtime config defaults
- `portal_app/portal_sessions.py`: admin/student session store
- `portal_app/portal_templates.py`: rendered HTML pages
- `portal_app/static/style.css`: shared styles
- `portal_app/requirements.txt`: Python dependencies
- `students.xlsx`: student roster + passwords + paper type assignments
- `submissions/`: uploaded student files (organized per roll no.)
- `question_paper/`: uploaded exam materials (organized per paper type)
- `logs/submission_logs.csv`: timestamped submission activity
- `logs/submission_ip_track.txt`: accepted IP-to-roll tracking
- `logs/exam_timer.json`: persisted timer state
- `logs/late_requests.json`: persisted late-request state
- `logs/game_leaderboard.csv`: persisted game leaderboard

---

## Prerequisites

- Python `3.10+`
- `pip`
- Same LAN for server machine and student devices

---

## Setup

### 1) Open project directory

```bash
cd /home/ayyzenn/Desktop/server
```

### 2) Create and activate virtual environment

```bash
python3 -m venv .env
source .env/bin/activate
```

Windows PowerShell:

```powershell
.env\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r portal_app/requirements.txt
```

---

## Run the Server

```bash
python3 server.py
```

If needed on Windows:

```cmd
python server.py
```

Default URL on host machine:

- [http://127.0.0.1:8080](http://127.0.0.1:8080)

LAN URL for students:

- `http://<server-lan-ip>:8080`

If you intentionally want localhost-only mode:

```bash
PORTAL_BIND=127.0.0.1 python3 server.py
```

---

## Admin Point of View (Full Runbook)

### Before exam day

1. Ensure `students.xlsx` exists in project root with at least:
   - `Roll No.`
   - `Student Name`
2. Start server and verify login page loads on host machine.
3. Login as admin with default credentials (change in code if needed):
   - Username: `admin`
   - Password: `admin123`
4. Open Admin Home:
   - Set paper type count (A/B/C...) if required.
   - Upload all question materials for each paper type.
5. Open Student Management:
   - Verify each student row exists.
   - Confirm paper type assignment.
   - Configure max files and allowed extensions.
6. Open Dashboard:
   - Confirm page refreshes and statuses load normally.

### During exam

1. Keep server terminal open; do not close it.
2. Share LAN URL with students.
3. Monitor `Dashboard` for submission status and late requests.
4. If needed, use student password reset actions from admin panel.
5. When a student requests extra time after timeout, use Dashboard actions:
   - `Approve` to grant temporary extra submission time
   - `Reject` to deny and keep submission locked
6. Use `Export Credentials` when required by invigilation process.

### After exam

1. Collect files from `submissions/<roll-no>/`.
2. Optionally archive:
   - `submissions/`
   - `logs/submission_logs.csv`
   - `logs/submission_ip_track.txt`
3. Stop server with `Ctrl+C`.

---

## Student Point of View

1. Open portal URL shared by admin.
2. Login using:
   - Username: roll number (example `20P-0051`)
   - Password: assigned password
3. On student home:
   - Click `View Materials` to open/download question files.
   - Click `Submit Solution` to upload final files.
   - Optional: click `Play Game` for mini games.
4. On submission page:
   - Select files (respect extension and count rules)
   - Tick confirmation checkbox
   - Submit once (final submission is one-time only)
5. If exam time has ended:
   - Student sees locked state
   - Student can request extra time from teacher
   - After approval, student sees temporary extra-time submission access
6. Successful upload page confirms submitted file names.

---

## Late Request Lifecycle

1. Exam reaches `ended` phase for student.
2. Student submits `Request Extra Time`.
3. Request appears in Admin Dashboard `Late Submission Requests`.
4. Admin decides:
   - `Approve`: student enters `extra_time` phase for a short window.
   - `Reject`: student remains locked and sees rejection status.
5. Request status is visible in the dashboard and synced to student UI.

---

## Performance & Scale Notes (Important)

The server is now suitable for high-concurrency classroom bursts, but these operating practices are still important:

- Use wired LAN for host machine if possible.
- Keep project on local SSD (not network drive).
- Keep `students.xlsx` local and not open in Excel during exam.
- Avoid heavy background CPU tasks on host machine.
- Avoid scanning/backup tools that lock files during exam window.
- Keep one server instance running (do not start multiple on same port).

Recommended pre-exam stress test:

1. Start server.
2. Open 20-40 parallel browser sessions (or use multiple devices).
3. Test simultaneous login and navigation.
4. Resolve network/firewall issues before exam day.

---

## LAN and Firewall Checklist

### Verify binding and listening port

```bash
ss -tlnp | rg 8080
```

Expected: `0.0.0.0:8080` or `*:8080`.

### Find server LAN IP

```bash
hostname -I
```

### UFW (if enabled)

```bash
sudo ufw allow 8080/tcp comment 'portal'
sudo ufw reload
sudo ufw status verbose
```

### firewalld

```bash
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```

### nftables inspection

```bash
sudo nft list ruleset
```

---

## Logs, Data, and What They Mean

- `students.xlsx`: source of truth for student records and passwords
- `logs/submission_logs.csv`: append-only submission timestamps and IPs
- `logs/submission_ip_track.txt`: first accepted roll number per IP
- `logs/exam_timer.json`: current timer start/end/pause state
- `logs/late_requests.json`: late-request history and statuses
- `logs/game_leaderboard.csv`: saved game scores
- `submissions/`: actual uploaded student files
- `question_paper/type_<x>/`: files students can view/download

---

## Manual End-to-End Test Checklist

Run these before live exam use:

1. Admin login and page access (`Admin Home`, `Manage Students`, `Dashboard`).
2. Question paper upload and student `View Materials` visibility.
3. Student upload validation:
   - valid allowed files
   - disallowed extension rejection
   - empty file rejection
4. Timer lock behavior at/after timeout.
5. Late request flow:
   - student request creation
   - admin approve and student extra-time access
   - admin reject and student rejection visibility
6. Access control checks:
   - invalid/expired token on protected APIs returns `401`
7. Post-submit lock:
   - student session closed after successful submission
   - re-login shows `Submission Already Completed`

---

## Configuration / Customization

Edit `portal_app/portal_config.py` to modify:

- `PORT` (default 8080)
- session TTL
- extension allowlist defaults
- admin credentials

Edit `portal_app/portal_templates.py` for page/UI behavior.

Edit `portal_app/static/style.css` for styling.

---

## Troubleshooting

### Symptom: students get timeout or long delay

Check in this order:

1. Host machine can open `http://127.0.0.1:8080`.
2. `ss -tlnp | rg 8080` shows listening on non-localhost.
3. Firewall allows TCP 8080.
4. Server and clients are on same subnet / no AP isolation.
5. `students.xlsx` is not open by another app.

### Symptom: localhost itself feels slow

Most common causes:

- file lock/slow disk access on `students.xlsx`
- antivirus/backup scanning project directory
- multiple apps saturating CPU/disk

### Symptom: student cannot re-submit

Expected behavior: one-time final submission is enforced.

### Symptom: two students on same NAT IP blocked

Expected behavior by current policy: one accepted roll number per IP.

---

## Security Notes

- Use a trusted exam network.
- Rotate admin password before real exam sessions.
- Backup project folder before exam.
- Do not expose this service directly to public internet.
