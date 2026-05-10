import cgi
import http.server
import io
import json
import mimetypes
import os
import socketserver
import subprocess
import sys
from datetime import datetime
from urllib.parse import parse_qs, quote, urlparse

import pandas as pd

from .portal_config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    ALLOWED_EXTENSIONS,
    AVAILABLE_EXTENSIONS,
    CONFIG,
    LOGS_DIR,
    PORT,
    UPLOAD_BASE_DIR,
)
from .portal_data import (
    PortalDataError,
    assign_default_paper_types,
    ensure_directories,
    ensure_valid_paper_types,
    get_question_paper_file_path_for_type,
    has_student_submitted,
    get_game_leaderboard,
    latest_question_paper_path,
    list_question_paper_files,
    load_data,
    load_logs,
    log_submission,
    paper_type_labels,
    record_submission_ip,
    save_data,
    save_question_paper_files_for_type,
    save_student_files,
    submitted_roll_for_ip,
    student_submission_files,
    update_game_score,
)
from .portal_security import generate_password
from .portal_sessions import SessionStore
from .portal_templates import (
    admin_dashboard_page,
    admin_home_page,
    admin_home_page_multi,
    admin_navbar,
    admin_students_page,
    alert_retry_page,
    info_page,
    login_page,
    question_materials_page,
    student_games_page,
    student_home_page,
    student_upload_page,
    upload_success_page,
)
from .portal_timer import (
    add_late_request,
    approve_late_request,
    cleanup_stale_late_requests,
    clear_late_request,
    get_late_request_status,
    get_late_requests,
    get_student_timer_status,
    get_timer_status,
    is_submission_locked_for_student,
    pause_timer,
    reject_late_request,
    reset_timer,
    resume_timer,
    set_exam_times,
)

SESSIONS = SessionStore()

_ALLOWED_LOGIN_NOTICES = frozenset({"invalid", "session", "data", "assets"})


def _open_folder(path: str) -> None:
    """Open a folder in the OS file manager — cross-platform, generic."""
    if sys.platform == "win32":
        # Windows: os.startfile uses the registered handler (Explorer by default)
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        # Linux/BSD: try xdg-open first, then common GUI file managers
        _FM_CANDIDATES = ["xdg-open", "thunar", "nautilus", "dolphin", "pcmanfm", "nemo", "caja"]
        import shutil
        for cmd in _FM_CANDIDATES:
            if shutil.which(cmd):
                subprocess.Popen([cmd, path])
                return
        raise RuntimeError(
            "No file manager found. Install thunar, nautilus, dolphin, or pcmanfm."
        )


class SecureLabHandler(http.server.BaseHTTPRequestHandler):
    # Avoid reverse DNS on every request — BaseHTTPRequestHandler.address_string()
    # calls socket.getfqdn() by default, which can stall responses for many seconds
    # when DNS is slow or unreachable (common on LAN IPs like 172.16.x.x).
    def address_string(self):
        return str(self.client_address[0])

    def end_headers(self):
        # Always close the TCP connection after POST so the next browser request
        # gets a fresh connection. Avoids rare HTTP/1.1 keep-alive desync when
        # multipart parsing or error paths interact badly with the socket buffer.
        if getattr(self, "_portal_post_close", False):
            self.send_header("Connection", "close")
        super().end_headers()

    def parse_request_context(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def get_query_value(self, query, key, default=""):
        values = query.get(key, [default])
        return values[0] if values else default

    def admin_url(self, path, token):
        return f"{path}?token={quote(token)}"

    def student_url(self, path, roll, token):
        return f"{path}?roll={quote(str(roll))}&token={quote(str(token))}"

    def is_admin_authenticated(self, query):
        return SESSIONS.is_admin_authenticated(self.get_query_value(query, "token"))

    def is_student_authenticated(self, roll, token):
        return SESSIONS.is_student_authenticated(roll, token)

    def current_allowed_extensions(self):
        configured = CONFIG.get("allowed_extensions")
        if configured:
            return {ext.lower() for ext in configured}
        return set(ALLOWED_EXTENSIONS)

    def current_paper_types(self):
        return paper_type_labels(CONFIG.get("question_paper_count", 1))

    def student_assigned_paper_type(self, roll):
        df = load_data()
        paper_types = self.current_paper_types()
        df = ensure_valid_paper_types(df, paper_types)
        user = df[df["Roll No."].astype(str) == str(roll)]
        if user.empty:
            return paper_types[0]
        assigned = str(user.iloc[0].get("Paper Type", "")).upper().strip()
        if assigned not in set(paper_types):
            return paper_types[0]
        return assigned

    def send_html(self, html):
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
            return True
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            # Client closed socket before response body completed.
            return False

    def send_error_safe(self, code, message):
        try:
            self.send_error(code, message)
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            return

    def send_json(self, payload, status_code=200):
        try:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return True
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            return False

    def serve_static_css(self):
        base_dir = os.path.dirname(__file__)
        css_path = os.path.join(base_dir, "static", "style.css")
        if not os.path.exists(css_path):
            self.send_html(
                info_page(
                    "Missing Stylesheet",
                    "The portal stylesheet file could not be found on the server. "
                    "Ensure portal_app/static/style.css exists next to the application.",
                    "Go to Login",
                    "/",
                )
            )
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/css; charset=utf-8")
        self.end_headers()
        try:
            with open(css_path, "rb") as file_handle:
                self.wfile.write(file_handle.read())
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            return

    def show_info_page(self, title, message, action_text="Return to Login", action_href="/"):
        self.send_html(info_page(title, message, action_text, action_href))

    def redirect_login_notice(self, notice: str):
        notice_clean = str(notice or "").strip().lower()
        if notice_clean not in _ALLOWED_LOGIN_NOTICES:
            notice_clean = "invalid"
        self.redirect(f"/?notice={quote(notice_clean)}")

    def show_login_form(self, query):
        notice = str(self.get_query_value(query, "notice", "")).strip().lower()
        if notice not in _ALLOWED_LOGIN_NOTICES:
            notice = ""
        self.send_html(login_page(notice=notice))

    def do_GET(self):
        try:
            path, query = self.parse_request_context()
            if path in ["/", "/admin"]:
                self.show_login_form(query)
            elif path == "/static/style.css":
                self.serve_static_css()
            # ── Public timer status ──────────────────────────────────────────
            elif path == "/api/timer":
                self.send_json(get_timer_status())
            # ── Student-specific timer ───────────────────────────────────────
            elif path == "/api/student_timer":
                roll = str(self.get_query_value(query, "roll", "")).strip()
                token = str(self.get_query_value(query, "token", "")).strip()
                if not self.is_student_authenticated(roll, token):
                    self.send_json({"ok": False, "error": "Session expired"}, status_code=401)
                    return
                status = get_student_timer_status(roll)
                status["ok"] = True
                self.send_json(status)
            # ── Admin: dashboard JSON data (scroll-preserving refresh) ───────
            elif path == "/admin_dashboard_data":
                if not self.is_admin_authenticated(query):
                    self.send_json({"ok": False, "error": "Unauthorized"}, status_code=401)
                    return
                self.send_admin_dashboard_data()
            # ── Admin: late requests list ────────────────────────────────────
            elif path == "/api/late_requests":
                if not self.is_admin_authenticated(query):
                    self.send_json({"ok": False, "error": "Unauthorized"}, status_code=401)
                    return
                requests = get_late_requests()
                df = load_data()
                name_map = {
                    str(r["Roll No."]).strip(): str(r.get("Student Name", "")).strip()
                    for _, r in df.iterrows()
                }
                for req in requests:
                    if not req.get("name"):
                        req["name"] = name_map.get(str(req.get("roll", "")), "")
                    has_files = bool(student_submission_files(str(req.get("roll", ""))))
                    req["submitted"] = has_files
                self.send_json({"ok": True, "requests": requests})
            elif path == "/student":
                self.show_student_home(query)
            elif path == "/student_submit":
                self.show_student_portal(query)
            elif path == "/question_paper":
                self.show_question_materials(query)
            elif path == "/student_games":
                self.show_student_games(query)
            elif path == "/game_leaderboard":
                self.show_game_leaderboard(query)
            elif path == "/question_paper_file":
                self.serve_question_paper_file(query)
            elif path == "/admin_panel":
                if not self.is_admin_authenticated(query):
                    self.redirect_login_notice("session")
                    return
                self.show_admin_panel(query)
            elif path == "/admin_students":
                if not self.is_admin_authenticated(query):
                    self.redirect_login_notice("session")
                    return
                self.show_admin_students(query)
            elif path == "/admin_dashboard":
                if not self.is_admin_authenticated(query):
                    self.redirect_login_notice("session")
                    return
                self.show_admin_dashboard(query)
            elif path == "/admin_open_folder":
                if not self.is_admin_authenticated(query):
                    self.send_json({"ok": False, "error": "Unauthorized"}, status_code=401)
                    return
                self.handle_open_submission_folder(query)
            elif path == "/export_credentials":
                if not self.is_admin_authenticated(query):
                    self.redirect_login_notice("session")
                    return
                self.export_credentials_excel()
            else:
                self.show_info_page(
                    "Page Not Found",
                    "This URL is not part of the portal. Use the login page to continue.",
                    "Go to Login",
                    "/",
                )
        except PortalDataError:
            self.redirect_login_notice("data")
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            return
        except Exception:
            self.send_error_safe(500, "Unexpected server error")

    def do_POST(self):
        self._portal_post_close = True
        try:
            path, query = self.parse_request_context()

            # ── /api/* JSON endpoints ────────────────────────────────────────
            if path.startswith("/api/"):
                self.handle_api_post(path)
                return

            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST"},
            )
            action = form.getvalue("action")

            if action == "login":
                username = str(form.getvalue("username", "")).strip()
                pw = str(form.getvalue("password", "")).strip()

                if username == ADMIN_USERNAME and pw == ADMIN_PASSWORD:
                    admin_token = SESSIONS.create_admin_session()
                    self.redirect(self.admin_url("/admin_panel", admin_token))
                    return

                df = load_data()
                user = df[
                    (df["Roll No."].astype(str) == username)
                    & (df["Password"].astype(str) == pw)
                ]
                if user.empty:
                    self.redirect_login_notice("invalid")
                    return
                if has_student_submitted(username):
                    self.show_info_page(
                        "Submission Already Completed",
                        "You have already submitted your assignment. Re-upload is not allowed.",
                        "Back to Login",
                        "/",
                    )
                    return

                student_token = SESSIONS.create_student_session(username)
                self.redirect(self.student_url("/student", username, student_token))

            elif action == "upload":
                roll = str(form.getvalue("roll_no", "")).strip()
                token = str(form.getvalue("auth_token", "")).strip()
                if not self.is_student_authenticated(roll, token):
                    self.redirect_login_notice("session")
                    return
                if str(form.getvalue("confirm_submit", "")) != "yes":
                    retry_url = self.student_url("/student_submit", roll, token)
                    self.send_html(
                        alert_retry_page(
                            "Confirmation Required",
                            "Please tick the confirmation checkbox before submitting your files.",
                            "Final submission confirmation was not checked.",
                            retry_url,
                        )
                    )
                    return
                if has_student_submitted(roll):
                    SESSIONS.end_student_session(roll)
                    self.show_info_page(
                        "Already Submitted",
                        "Your submission record already exists. Re-submission is not permitted.",
                        "Back to Login",
                        "/",
                    )
                    return
                client_ip = str(self.client_address[0]).strip()
                existing_roll_for_ip = submitted_roll_for_ip(client_ip)
                if existing_roll_for_ip and existing_roll_for_ip != roll:
                    SESSIONS.end_student_session(roll)
                    self.show_info_page(
                        "Submission Blocked: IP Already Used",
                        "This network IP has already been used to submit by another student "
                        f"(Roll No. {existing_roll_for_ip}). Multiple students cannot submit from the same IP.",
                        "Back to Login",
                        "/",
                    )
                    return

                # ── Timer lock check (server-side) ───────────────────────────
                if is_submission_locked_for_student(roll):
                    self.send_html(
                        alert_retry_page(
                            "Submission Time Ended",
                            "The submission window has closed. No further uploads are accepted.",
                            "Exam timer has expired. Contact your teacher if you need extra time.",
                            self.student_url("/student_submit", roll, token),
                        )
                    )
                    return

                file_items = form["lab_files"]
                if not isinstance(file_items, list):
                    file_items = [file_items]
                if len(file_items) > CONFIG["max_files"]:
                    retry_url = self.student_url("/student_submit", roll, token)
                    self.send_html(
                        alert_retry_page(
                            "Upload Limit Exceeded",
                            f"You can upload up to {CONFIG['max_files']} files only. Please remove extra files and try again.",
                            f"Limit exceeded. Maximum {CONFIG['max_files']} files are allowed.",
                            retry_url,
                        )
                    )
                    return

                allowed_extensions = self.current_allowed_extensions()
                selected_files = []
                disallowed_files = []
                for item in file_items:
                    if hasattr(item, "filename") and item.filename:
                        selected_files.append(item.filename)
                        ext = os.path.splitext(item.filename)[1].lower()
                        if ext not in allowed_extensions:
                            disallowed_files.append(item.filename)

                if not selected_files:
                    retry_url = self.student_url("/student_submit", roll, token)
                    self.send_html(
                        alert_retry_page(
                            "No File Selected",
                            "Please select at least one valid file, then submit again.",
                            "No file selected. Please choose at least one file.",
                            retry_url,
                        )
                    )
                    return
                if disallowed_files:
                    retry_url = self.student_url("/student_submit", roll, token)
                    allowed_text = ", ".join(sorted(allowed_extensions))
                    self.send_html(
                        alert_retry_page(
                            "File Type Not Allowed",
                            "One or more selected files are not allowed. Please choose files with approved extensions and try again.",
                            "Disallowed file type(s): "
                            + ", ".join(disallowed_files)
                            + ". Allowed: "
                            + allowed_text,
                            retry_url,
                        )
                    )
                    return

                uploaded_files = save_student_files(roll, file_items, allowed_extensions)
                if not uploaded_files:
                    retry_url = self.student_url("/student_submit", roll, token)
                    self.send_html(
                        alert_retry_page(
                            "No Valid File Uploaded",
                            "No valid file could be uploaded. Please check selected files and try again.",
                            "No valid files were uploaded.",
                            retry_url,
                        )
                    )
                    return

                log_submission(roll, client_ip)
                record_submission_ip(client_ip, roll)
                self.send_html(upload_success_page(roll, uploaded_files))
                SESSIONS.end_student_session(roll)

            elif action == "submit_game_score":
                roll = str(form.getvalue("roll_no", "")).strip()
                token = str(form.getvalue("auth_token", "")).strip()
                game = str(form.getvalue("game", "")).strip().lower()
                try:
                    score = int(str(form.getvalue("score", "0")).strip() or "0")
                except ValueError:
                    self.send_json({"ok": False, "error": "Invalid score"}, status_code=400)
                    return
                if not self.is_student_authenticated(roll, token):
                    self.send_json({"ok": False, "error": "Session expired"}, status_code=401)
                    return
                update_game_score(game=game, roll=roll, score=score)
                self.send_json({"ok": True})
                return

            elif action == "set_exam_timer":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                start_str = str(form.getvalue("exam_start", "")).strip()
                end_str = str(form.getvalue("exam_end", "")).strip()
                if not start_str or not end_str:
                    self.send_error(400, "Start and end times are required.")
                    return
                try:
                    start_epoch = datetime.fromisoformat(start_str).timestamp()
                    end_epoch = datetime.fromisoformat(end_str).timestamp()
                except ValueError:
                    self.send_error(400, "Invalid date/time format.")
                    return
                if end_epoch <= start_epoch:
                    self.send_error(400, "End time must be after start time.")
                    return
                set_exam_times(start_epoch, end_epoch)
                self.redirect(self.admin_url("/admin_panel", admin_token))

            elif action == "reset_timer_full":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                reset_timer()
                self.redirect(self.admin_url("/admin_panel", admin_token))

            elif action == "update_settings":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                CONFIG["max_files"] = int(form.getvalue("max_files", 4))
                self.redirect(self.admin_url("/admin_students", admin_token) + "#actions")

            elif action == "update_paper_settings":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                try:
                    requested_count = int(form.getvalue("question_paper_count", 1))
                except ValueError:
                    self.send_error(400, "Paper count must be a number.")
                    return
                safe_count = max(1, min(26, requested_count))
                CONFIG["question_paper_count"] = safe_count
                df = load_data()
                df = assign_default_paper_types(df, self.current_paper_types())
                save_data(df)
                self.redirect(self.admin_url("/admin_panel", admin_token))

            elif action == "update_extensions":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return

                selected = {
                    str(ext).strip().lower()
                    for ext in form.getlist("allowed_extensions")
                    if str(ext).strip()
                }
                valid_selected = sorted(selected.intersection(set(AVAILABLE_EXTENSIONS)))
                if not valid_selected:
                    self.send_error(400, "Select at least one allowed extension.")
                    return
                CONFIG["allowed_extensions"] = valid_selected
                self.redirect(self.admin_url("/admin_students", admin_token) + "#actions")

            elif action == "reset_user":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                roll_to_reset = str(form.getvalue("target_roll"))
                df = load_data()
                df.loc[df["Roll No."].astype(str) == roll_to_reset, "Password"] = (
                    generate_password()
                )
                save_data(df)
                self.redirect(self.admin_url("/admin_students", admin_token) + "#actions")

            elif action == "reset_all_users":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                if str(form.getvalue("confirm_reset_all", "")) != "yes":
                    self.send_error(400, "Please confirm reset-all before submitting.")
                    return
                df = load_data()
                for idx in df.index:
                    df.at[idx, "Password"] = generate_password()
                save_data(df)
                self.redirect(self.admin_url("/admin_students", admin_token) + "#actions")

            elif action == "upload_question_paper":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                paper_types = self.current_paper_types()
                missing = []
                saved_count = 0
                for paper_type in paper_types:
                    field_name = f"question_paper_file_{paper_type}"
                    if field_name not in form:
                        missing.append(paper_type)
                        continue
                    file_items = form[field_name]
                    if not isinstance(file_items, list):
                        file_items = [file_items]
                    uploaded_for_type = save_question_paper_files_for_type(
                        paper_type, file_items
                    )
                    if uploaded_for_type == 0:
                        missing.append(paper_type)
                        continue
                    saved_count += uploaded_for_type
                if missing:
                    self.send_error(
                        400,
                        "Please upload at least one file for paper type(s): "
                        + ", ".join(missing),
                    )
                    return
                if saved_count == 0:
                    self.send_error(400, "Please choose valid paper files.")
                    return
                self.redirect(self.admin_url("/admin_panel", admin_token))

            elif action == "set_student_paper_type":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                roll_to_set = str(form.getvalue("target_roll", "")).strip()
                selected_type = str(form.getvalue("paper_type", "")).strip().upper()
                allowed_types = set(self.current_paper_types())
                if selected_type not in allowed_types:
                    self.send_error(400, "Invalid paper type selected.")
                    return
                df = load_data()
                mask = df["Roll No."].astype(str) == roll_to_set
                if not mask.any():
                    self.show_info_page(
                        "Student Not Found",
                        "That roll number is not in the student roster.",
                        "Back to Student Management",
                        self.admin_url("/admin_students", admin_token),
                    )
                    return
                df.loc[mask, "Paper Type"] = selected_type
                save_data(df)
                self.redirect(self.admin_url("/admin_students", admin_token))
            elif action == "update_instructions":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.redirect_login_notice("session")
                    return
                instructions = str(form.getvalue("instructions", "")).strip()
                CONFIG["submission_instructions"] = instructions
                self.redirect(self.admin_url("/admin_students", admin_token))

            else:
                self.send_error(400, "Unsupported action")
        except PortalDataError:
            self.redirect_login_notice("data")
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            return
        except Exception:
            self.send_error_safe(500, "Unexpected server error")
        finally:
            self._portal_post_close = False

    def handle_api_post(self, path: str) -> None:
        """Handle all /api/* POST requests; always responds with JSON."""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST"},
            )

            # ── Admin: pause / resume timer ──────────────────────────────────
            if path == "/api/timer_control":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.send_json({"ok": False, "error": "Unauthorized"}, status_code=401)
                    return
                action = str(form.getvalue("action", "")).strip()
                if action == "pause":
                    pause_timer()
                elif action == "resume":
                    resume_timer()
                else:
                    self.send_json({"ok": False, "error": "Unknown action"}, status_code=400)
                    return
                self.send_json({"ok": True, "timer": get_timer_status()})

            # ── Admin: approve / reject late request ─────────────────────────
            elif path == "/api/handle_late_request":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.send_json({"ok": False, "error": "Unauthorized"}, status_code=401)
                    return
                roll = str(form.getvalue("roll", "")).strip()
                decision = str(form.getvalue("decision", "")).strip().lower()
                if not roll or decision not in ("approve", "reject"):
                    self.send_json({"ok": False, "error": "Invalid parameters"}, status_code=400)
                    return
                if decision == "approve":
                    ok = approve_late_request(roll)
                else:
                    ok = reject_late_request(roll)
                self.send_json({"ok": ok})

            # ── Admin: reset one student's password (async) ──────────────────
            elif path == "/api/reset_password":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.send_json({"ok": False, "error": "Unauthorized"}, status_code=401)
                    return
                target_roll = str(form.getvalue("target_roll", "")).strip()
                if not target_roll:
                    self.send_json({"ok": False, "error": "Roll number required"}, status_code=400)
                    return
                df = load_data()
                mask = df["Roll No."].astype(str) == target_roll
                if not mask.any():
                    self.send_json({"ok": False, "error": "Student not found"}, status_code=404)
                    return
                new_pw = generate_password()
                df.loc[mask, "Password"] = new_pw
                save_data(df)
                self.send_json({"ok": True, "new_password": new_pw, "roll": target_roll})

            # ── Student: request extra time ──────────────────────────────────
            elif path == "/api/request_extra_time":
                roll = str(form.getvalue("roll_no", "")).strip()
                token = str(form.getvalue("auth_token", "")).strip()
                if not self.is_student_authenticated(roll, token):
                    self.send_json({"ok": False, "error": "Session expired"}, status_code=401)
                    return
                df = load_data()
                user = df[df["Roll No."].astype(str) == roll]
                name = str(user.iloc[0]["Student Name"]) if not user.empty else roll
                already = add_late_request(roll, name)
                if not already:
                    # Request already exists — return current status
                    current_status = get_late_request_status(roll) or "pending"
                    self.send_json({"ok": True, "already_requested": True, "status": current_status})
                    return
                self.send_json({"ok": True, "already_requested": False, "status": "pending"})

            else:
                self.send_json({"ok": False, "error": "Unknown API endpoint"}, status_code=404)

        except PortalDataError:
            self.send_json({"ok": False, "error": "Data error"}, status_code=500)
        except (BrokenPipeError, ConnectionResetError, TimeoutError, OSError):
            return
        except Exception:
            self.send_json({"ok": False, "error": "Server error"}, status_code=500)

    def send_admin_dashboard_data(self) -> None:
        """Return JSON snapshot of dashboard: rows + stats + timer + late requests."""
        try:
            df = load_data()
            logs = load_logs()
            rows = []
            submitted_count = 0
            pending_count = 0
            submitted_rolls: set = set()
            for _, row in df.iterrows():
                roll_str = str(row["Roll No."])
                student_name = str(row.get("Student Name", ""))
                user_logs = logs[logs["Roll No."].astype(str) == roll_str]
                last_ip = (
                    user_logs.iloc[-1]["IP Address"] if not user_logs.empty else "No Activity"
                )
                if "Timestamp" in user_logs.columns and not user_logs.empty:
                    parsed_time = pd.to_datetime(user_logs.iloc[-1]["Timestamp"], errors="coerce")
                    last_time = (
                        parsed_time.strftime("%Y-%m-%d %I:%M:%S %p")
                        if not pd.isna(parsed_time)
                        else "No Upload"
                    )
                else:
                    last_time = "No Upload"

                has_files = bool(student_submission_files(roll_str))
                if has_files:
                    submitted_count += 1
                    status_key = "submitted"
                    submitted_rolls.add(roll_str)
                else:
                    pending_count += 1
                    status_key = "pending"

                rows.append({
                    "name": student_name,
                    "roll": roll_str,
                    "ip": last_ip,
                    "time": last_time,
                    "status": status_key,
                })

            # Clean up stale late requests (no files + no active extra-time window)
            cleanup_stale_late_requests(submitted_rolls)

            # Enrich late requests with submission status and student names
            name_map = {str(r["Roll No."]).strip(): str(r.get("Student Name", "")).strip()
                        for _, r in df.iterrows()}
            late_reqs = []
            for req in get_late_requests():
                entry = dict(req)
                if not entry.get("name"):
                    entry["name"] = name_map.get(str(entry.get("roll", "")), "")
                entry["submitted"] = bool(student_submission_files(str(entry.get("roll", ""))))
                late_reqs.append(entry)

            self.send_json({
                "ok": True,
                "submitted_count": submitted_count,
                "pending_count": pending_count,
                "total_count": len(df),
                "rows": rows,
                "timer": get_timer_status(),
                "late_requests": late_reqs,
            })
        except PortalDataError:
            self.send_json({"ok": False, "error": "Data error"}, status_code=500)

    def handle_open_submission_folder(self, query):
        """Open a student's submission folder in the OS file manager (server-side)."""
        roll = str(self.get_query_value(query, "roll", "")).strip()
        if not roll:
            self.send_json({"ok": False, "error": "Roll required"}, status_code=400)
            return
        # Prevent path traversal
        safe_roll = os.path.basename(roll)
        folder_path = os.path.realpath(os.path.join(UPLOAD_BASE_DIR, safe_roll))
        base_path = os.path.realpath(UPLOAD_BASE_DIR)
        if not folder_path.startswith(base_path + os.sep) and folder_path != base_path:
            self.send_json({"ok": False, "error": "Invalid roll"}, status_code=400)
            return
        if not os.path.isdir(folder_path):
            self.send_json({"ok": False, "error": "Folder not found"}, status_code=404)
            return
        try:
            _open_folder(folder_path)
            self.send_json({"ok": True, "path": folder_path})
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status_code=500)

    def export_credentials_excel(self):
        df = load_data().copy()
        export_df = pd.DataFrame(
            {
                "S#": range(1, len(df) + 1),
                "Roll No.": df["Roll No."].astype(str),
                "Student Name": df["Student Name"].astype(str),
                "Password": df["Password"].astype(str),
            }
        )
        mem = io.BytesIO()
        export_df.to_excel(mem, index=False)
        mem.seek(0)
        self.send_response(200)
        self.send_header(
            "Content-Type",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.send_header(
            "Content-Disposition", 'attachment; filename="student_credentials.xlsx"'
        )
        self.end_headers()
        self.wfile.write(mem.getvalue())

    def show_question_materials(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        if not self.is_student_authenticated(roll, token):
            self.redirect_login_notice("session")
            return

        assigned_paper_type = self.student_assigned_paper_type(roll)
        materials = list_question_paper_files(assigned_paper_type)
        if not materials:
            self.show_info_page(
                "No Materials Uploaded",
                f"Paper type {assigned_paper_type} is not uploaded yet. Please contact your teacher.",
                "Back",
                self.student_url("/student", roll, token),
            )
            return

        df = load_data()
        user = df[df["Roll No."].astype(str) == roll]
        student_name = str(user.iloc[0]["Student Name"]) if not user.empty else roll

        rows = ""
        for item in materials:
            name = item["name"]
            ext = os.path.splitext(name)[1].lower() or "-"
            size_kb = max(1, int(item["size_bytes"] / 1024))
            open_url = (
                self.student_url("/question_paper_file", roll, token)
                + f"&type={quote(assigned_paper_type)}&file={quote(name)}"
            )
            download_url = open_url + "&download=1"
            rows += (
                f"<tr><td>{name}</td><td>{ext}</td><td>{size_kb}</td>"
                f"<td>"
                f"<a class='btn-link btn-purple' target='_blank' rel='noopener noreferrer' href='{open_url}'>Open</a> "
                f"<a class='btn-link btn-teal' href='{download_url}'>Download</a>"
                f"</td></tr>"
            )

        self.send_html(
            question_materials_page(
                student_name=student_name,
                roll=roll,
                paper_type=assigned_paper_type,
                rows_html=rows,
                back_url=self.student_url("/student", roll, token),
            )
        )

    def serve_question_paper_file(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        if not self.is_student_authenticated(roll, token):
            self.redirect_login_notice("session")
            return

        assigned_paper_type = self.student_assigned_paper_type(roll)
        requested_type = str(self.get_query_value(query, "type", "")).strip().upper()
        if requested_type and requested_type != assigned_paper_type:
            self.show_info_page(
                "Access Denied",
                "You cannot open materials for a paper type other than the one assigned to you.",
                "Back to Portal",
                self.student_url("/student", roll, token),
            )
            return

        filename = self.get_query_value(query, "file", "").strip()
        file_path = get_question_paper_file_path_for_type(assigned_paper_type, filename)
        if not file_path:
            self.show_info_page(
                "File Not Found",
                "That material file is missing, renamed, or not allowed. "
                "Go back to the materials list and choose another file, or ask your instructor.",
                "Back to Materials",
                self.student_url("/question_paper", roll, token),
            )
            return

        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"

        as_download = self.get_query_value(query, "download", "") == "1"
        disposition = "attachment" if as_download else "inline"

        try:
            with open(file_path, "rb") as file_handle:
                payload = file_handle.read()
        except OSError:
            self.show_info_page(
                "Could Not Read File",
                "The file exists but could not be read from disk.",
                "Back to Materials",
                self.student_url("/question_paper", roll, token),
            )
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Disposition",
            f'{disposition}; filename="{os.path.basename(file_path)}"',
        )
        self.end_headers()
        self.wfile.write(payload)

    def show_upload_page(self, roll, name, token):
        self.send_html(
            student_upload_page(
                roll=roll,
                name=name,
                token=token,
                max_files=CONFIG["max_files"],
                allowed_ext_csv=", ".join(sorted(self.current_allowed_extensions())),
                instructions=CONFIG.get("submission_instructions", ""),
            )
        )

    def show_student_home(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        if not self.is_student_authenticated(roll, token):
            self.redirect_login_notice("session")
            return
        if has_student_submitted(roll):
            SESSIONS.end_student_session(roll)
            self.show_info_page(
                "Submission Already Completed",
                "You have already submitted your files. Re-upload is not allowed.",
                "Back to Login",
                "/",
            )
            return
        df = load_data()
        user = df[df["Roll No."].astype(str) == roll]
        if user.empty:
            SESSIONS.end_student_session(roll)
            self.show_info_page(
                "Student Record Not Found",
                "Your roll number is not listed in the current student roster, or the roster changed while you were signed in. Please contact your administrator.",
                "Return to Login",
                "/",
            )
            return
        name = str(user.iloc[0]["Student Name"])
        self.send_html(
            student_home_page(
                name=name,
                roll=roll,
                view_qp_url=self.student_url("/question_paper", roll, token),
                submit_url=self.student_url("/student_submit", roll, token),
                games_url=self.student_url("/student_games", roll, token),
                instructions=CONFIG.get("submission_instructions", ""),
            )
        )

    def show_student_portal(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        if not self.is_student_authenticated(roll, token):
            self.redirect_login_notice("session")
            return
        if has_student_submitted(roll):
            SESSIONS.end_student_session(roll)
            self.show_info_page(
                "Submission Already Completed",
                "You have already submitted your files. Re-upload is not allowed.",
                "Back to Login",
                "/",
            )
            return
        df = load_data()
        user = df[df["Roll No."].astype(str) == roll]
        if user.empty:
            SESSIONS.end_student_session(roll)
            self.show_info_page(
                "Student Record Not Found",
                "Your roll number is not listed in the current student roster, or the roster changed while you were signed in. Please contact your administrator.",
                "Return to Login",
                "/",
            )
            return
        self.show_upload_page(roll, user.iloc[0]["Student Name"], token)

    def show_student_games(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        if not self.is_student_authenticated(roll, token):
            self.redirect_login_notice("session")
            return
        if has_student_submitted(roll):
            SESSIONS.end_student_session(roll)
            self.show_info_page(
                "Submission Already Completed",
                "You have already submitted your files. Re-upload is not allowed.",
                "Back to Login",
                "/",
            )
            return
        df = load_data()
        user = df[df["Roll No."].astype(str) == roll]
        if user.empty:
            SESSIONS.end_student_session(roll)
            self.show_info_page(
                "Student Record Not Found",
                "Your roll number is not listed in the current student roster, or the roster changed while you were signed in. Please contact your administrator.",
                "Return to Login",
                "/",
            )
            return

        self.send_html(student_games_page(str(user.iloc[0]["Student Name"]), roll, token))

    def show_game_leaderboard(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        game = str(self.get_query_value(query, "game", "")).strip().lower()
        if not self.is_student_authenticated(roll, token):
            self.send_json({"ok": False, "error": "Session expired"}, status_code=401)
            return
        if game not in {"snake", "flappy", "pacman"}:
            self.send_json({"ok": False, "error": "Invalid game"}, status_code=400)
            return

        rows = get_game_leaderboard(game=game, limit=20)
        df = load_data()
        name_map = {
            str(row["Roll No."]).strip(): str(row.get("Student Name", "")).strip()
            for _, row in df.iterrows()
        }
        leaderboard = []
        for row in rows:
            leaderboard.append(
                {
                    "rank": int(row["rank"]),
                    "roll": str(row["roll"]),
                    "name": name_map.get(str(row["roll"]), ""),
                    "score": int(row["score"]),
                }
            )
        self.send_json({"ok": True, "game": game, "leaders": leaderboard})

    def render_admin_navbar(self, admin_token):
        return admin_navbar(
            admin_home_url=self.admin_url("/admin_panel", admin_token),
            students_url=self.admin_url("/admin_students", admin_token),
            dashboard_url=self.admin_url("/admin_dashboard", admin_token),
            export_url=self.admin_url("/export_credentials", admin_token),
            logout_url="/",
        )

    def show_admin_panel(self, query):
        admin_token = self.get_query_value(query, "token", "")
        paper_types = self.current_paper_types()
        paper_rows = ""
        for paper_type in paper_types:
            question_paper_path = latest_question_paper_path(paper_type)
            current_paper_name = (
                os.path.basename(question_paper_path)
                if question_paper_path
                else "No file uploaded yet"
            )
            current_paper_time = (
                pd.to_datetime(os.path.getmtime(question_paper_path), unit="s").strftime(
                    "%Y-%m-%d %I:%M:%S %p"
                )
                if question_paper_path
                else "-"
            )
            paper_rows += (
                f"<tr><td>{paper_type}</td><td>{current_paper_name}</td>"
                f"<td>{current_paper_time}</td></tr>"
            )
        self.send_html(
            admin_home_page_multi(
                navbar_html=self.render_admin_navbar(admin_token),
                students_url=self.admin_url("/admin_students", admin_token),
                admin_token=admin_token,
                paper_types=paper_types,
                paper_rows_html=paper_rows,
            )
        )

    def show_admin_students(self, query):
        admin_token = self.get_query_value(query, "token", "")
        df = load_data()
        paper_types = self.current_paper_types()
        df = ensure_valid_paper_types(df, paper_types)
        save_data(df)
        logs = load_logs()
        rows = ""
        for idx, row in df.iterrows():
            roll_str = str(row["Roll No."])
            user_logs = logs[logs["Roll No."].astype(str) == roll_str]
            last_ip = user_logs.iloc[-1]["IP Address"] if not user_logs.empty else "No Activity"
            student_password = str(row.get("Password", ""))
            files_list = student_submission_files(roll_str)
            status = "Submitted" if files_list else "Pending"
            files_html = "<br>".join(files_list) if files_list else "<i>No files</i>"
            selected_type = str(row.get("Paper Type", "")).upper().strip()
            options_html = ""
            for paper_type in paper_types:
                selected_attr = "selected" if paper_type == selected_type else ""
                options_html += (
                    f"<option value='{paper_type}' {selected_attr}>{paper_type}</option>"
                )
            rows += (
                f"<tr data-roll='{roll_str}'>"
                f"<td>{idx + 1}</td><td>{roll_str}</td><td>{row['Student Name']}</td>"
                f"<td class='pw-cell'>{student_password}</td>"
                f"<td><form method='POST' class='form-row'>"
                f"<input type='hidden' name='action' value='set_student_paper_type'>"
                f"<input type='hidden' name='admin_token' value='{admin_token}'>"
                f"<input type='hidden' name='target_roll' value='{roll_str}'>"
                f"<select name='paper_type'>{options_html}</select>"
                f"<input type='submit' value='Set' class='btn btn-secondary'>"
                f"</form></td>"
                f"<td>{status}</td><td>{last_ip}</td>"
                f"<td class='submission-files-cell'>{files_html}</td>"
                f"<td><button type='button' class='btn btn-dark reset-pw-btn' "
                f"onclick=\"resetPasswordAsync('{roll_str}', this)\">Reset</button></td></tr>"
            )
        self.send_html(
            admin_students_page(
                navbar_html=self.render_admin_navbar(admin_token),
                rows_html=rows,
                max_files=CONFIG["max_files"],
                admin_token=admin_token,
                export_url=self.admin_url("/export_credentials", admin_token),
                available_extensions=AVAILABLE_EXTENSIONS,
                selected_extensions=sorted(self.current_allowed_extensions()),
                paper_types=paper_types,
                current_instructions=CONFIG.get("submission_instructions", ""),
            )
        )

    def show_admin_dashboard(self, query):
        admin_token = self.get_query_value(query, "token", "")
        df = load_data()
        logs = load_logs()
        rows = ""
        submitted_count = 0
        pending_count = 0
        submitted_rolls: set = set()
        for _, row in df.iterrows():
            roll_str = str(row["Roll No."])
            student_name = str(row.get("Student Name", ""))
            user_logs = logs[logs["Roll No."].astype(str) == roll_str]
            last_ip = user_logs.iloc[-1]["IP Address"] if not user_logs.empty else "No Activity"
            if "Timestamp" in user_logs.columns and not user_logs.empty:
                parsed_time = pd.to_datetime(user_logs.iloc[-1]["Timestamp"], errors="coerce")
                last_time = (
                    parsed_time.strftime("%Y-%m-%d %I:%M:%S %p")
                    if not pd.isna(parsed_time)
                    else "No Upload"
                )
            else:
                last_time = "No Upload"

            has_files = bool(student_submission_files(roll_str))
            if has_files:
                submitted_count += 1
                status_key = "submitted"
                status = "Submitted"
                status_class = "status-green"
                submitted_rolls.add(roll_str)
                open_url = self.admin_url("/admin_open_folder", admin_token) + f"&roll={quote(roll_str)}"
                name_cell = (
                    f"<span class='dash-folder-link' "
                    f"onclick=\"openSubmissionFolder('{roll_str}')\" "
                    f"title='Click to open submission folder on server'>{student_name}</span>"
                )
            else:
                pending_count += 1
                status_key = "pending"
                status = "Pending"
                status_class = "status-red"
                name_cell = student_name

            rows += (
                f'<tr class="dashboard-row" data-status="{status_key}">'
                f"<td>{name_cell}</td><td>{roll_str}</td><td>{last_ip}</td>"
                f"<td>{last_time}</td><td><span class='{status_class}'>{status}</span></td></tr>"
            )

        # Clean up late requests for students with no submission and expired extra time
        cleanup_stale_late_requests(submitted_rolls)

        total_count = len(df)
        self.send_html(
            admin_dashboard_page(
                navbar_html=self.render_admin_navbar(admin_token),
                rows_html=rows,
                admin_token=admin_token,
                submitted_count=submitted_count,
                pending_count=pending_count,
                total_count=total_count,
            )
        )


    def redirect(self, path):
        self.send_response(303)
        self.send_header("Location", path)
        self.end_headers()


class ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 256


def run_server():
    ensure_directories()
    bind_host = os.environ.get("PORTAL_BIND", "")
    bind_hint = (
        bind_host
        if bind_host.strip()
        else "all interfaces (reachable from LAN; ensure firewall allows the port)"
    )
    try:
        with ReusableTCPServer((bind_host, PORT), SecureLabHandler) as httpd:
            _sock_host, sock_port = httpd.socket.getsockname()[:2]
            print(f"Portal listening on {_sock_host!s}:{sock_port}")
            print(f"Bind setting: {bind_hint}")
            print(f"  This machine:  http://127.0.0.1:{sock_port}")
            print(f"  Other devices: http://<this-computer-LAN-IP>:{sock_port}")
            if bind_host.strip() == "127.0.0.1":
                print(
                    "  WARNING: PORTAL_BIND=127.0.0.1 — only localhost can connect; "
                    "unset PORTAL_BIND to allow LAN access."
                )
            if sys.platform.startswith("win"):
                print("Tip (Windows): use python server.py if python3 is not on your PATH.")
            httpd.serve_forever()
    except OSError as exc:
        print(f"Could not start server on port {PORT}: {exc}")
        raise SystemExit(1) from exc
