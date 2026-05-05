import cgi
import http.server
import io
import mimetypes
import os
import socketserver
from urllib.parse import parse_qs, quote, urlparse

import pandas as pd

from .portal_config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    ALLOWED_EXTENSIONS,
    AVAILABLE_EXTENSIONS,
    CONFIG,
    PORT,
)
from .portal_data import (
    assign_default_paper_types,
    ensure_directories,
    ensure_valid_paper_types,
    get_question_paper_file_path_for_type,
    has_student_submitted,
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
    student_home_page,
    student_upload_page,
    upload_success_page,
)

SESSIONS = SessionStore()


class SecureLabHandler(http.server.BaseHTTPRequestHandler):
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
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def serve_static_css(self):
        base_dir = os.path.dirname(__file__)
        css_path = os.path.join(base_dir, "static", "style.css")
        if not os.path.exists(css_path):
            self.send_error(404, "CSS not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/css; charset=utf-8")
        self.end_headers()
        with open(css_path, "rb") as file_handle:
            self.wfile.write(file_handle.read())

    def show_info_page(self, title, message, action_text="Return to Login", action_href="/"):
        self.send_html(info_page(title, message, action_text, action_href))

    def do_GET(self):
        try:
            path, query = self.parse_request_context()
            if path in ["/", "/admin"]:
                self.show_login_form()
            elif path == "/static/style.css":
                self.serve_static_css()
            elif path == "/student":
                self.show_student_home(query)
            elif path == "/student_submit":
                self.show_student_portal(query)
            elif path == "/question_paper":
                self.show_question_materials(query)
            elif path == "/question_paper_file":
                self.serve_question_paper_file(query)
            elif path == "/admin_panel":
                if not self.is_admin_authenticated(query):
                    self.send_error(401, "Admin login required")
                    return
                self.show_admin_panel(query)
            elif path == "/admin_students":
                if not self.is_admin_authenticated(query):
                    self.send_error(401, "Admin login required")
                    return
                self.show_admin_students(query)
            elif path == "/admin_dashboard":
                if not self.is_admin_authenticated(query):
                    self.send_error(401, "Admin login required")
                    return
                self.show_admin_dashboard(query)
            elif path == "/export_credentials":
                if not self.is_admin_authenticated(query):
                    self.send_error(401, "Admin login required")
                    return
                self.export_credentials_excel()
            else:
                self.send_error(404, "Not Found")
        except Exception:
            self.send_error(500, "Unexpected server error")

    def do_POST(self):
        try:
            form = cgi.FieldStorage(
                fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST"}
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
                    self.send_error(403, "Invalid username or password")
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
                    self.send_error(401, "Session expired. Please login again.")
                    return
                if str(form.getvalue("confirm_submit", "")) != "yes":
                    self.send_error(400, "Please confirm submission before uploading.")
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

            elif action == "update_settings":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.send_error(401, "Admin login required")
                    return
                CONFIG["max_files"] = int(form.getvalue("max_files", 4))
                self.redirect(self.admin_url("/admin_students", admin_token) + "#actions")

            elif action == "update_paper_settings":
                admin_token = str(form.getvalue("admin_token", "")).strip()
                if not SESSIONS.is_admin_authenticated(admin_token):
                    self.send_error(401, "Admin login required")
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
                    self.send_error(401, "Admin login required")
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
                    self.send_error(401, "Admin login required")
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
                    self.send_error(401, "Admin login required")
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
                    self.send_error(401, "Admin login required")
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
                    self.send_error(401, "Admin login required")
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
                    self.send_error(404, "Student not found.")
                    return
                df.loc[mask, "Paper Type"] = selected_type
                save_data(df)
                self.redirect(self.admin_url("/admin_students", admin_token))
            else:
                self.send_error(400, "Unsupported action")
        except Exception:
            self.send_error(500, "Unexpected server error")

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
            self.send_error(401, "Student login required")
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
            self.send_error(401, "Student login required")
            return

        assigned_paper_type = self.student_assigned_paper_type(roll)
        requested_type = str(self.get_query_value(query, "type", "")).strip().upper()
        if requested_type and requested_type != assigned_paper_type:
            self.send_error(403, "You are not allowed to access other paper types.")
            return

        filename = self.get_query_value(query, "file", "").strip()
        file_path = get_question_paper_file_path_for_type(assigned_paper_type, filename)
        if not file_path:
            self.send_error(404, "Material file not found.")
            return

        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "application/octet-stream"

        as_download = self.get_query_value(query, "download", "") == "1"
        disposition = "attachment" if as_download else "inline"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header(
            "Content-Disposition",
            f'{disposition}; filename="{os.path.basename(file_path)}"',
        )
        self.end_headers()
        with open(file_path, "rb") as file_handle:
            self.wfile.write(file_handle.read())

    def show_upload_page(self, roll, name, token):
        self.send_html(
            student_upload_page(
                roll=roll,
                name=name,
                token=token,
                max_files=CONFIG["max_files"],
                allowed_ext_csv=", ".join(sorted(self.current_allowed_extensions())),
            )
        )

    def show_student_home(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        if not self.is_student_authenticated(roll, token):
            self.send_error(401, "Session expired. Please login again.")
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
            self.send_error(404, "Student not found")
            return
        name = str(user.iloc[0]["Student Name"])
        self.send_html(
            student_home_page(
                name=name,
                roll=roll,
                view_qp_url=self.student_url("/question_paper", roll, token),
                submit_url=self.student_url("/student_submit", roll, token),
            )
        )

    def show_student_portal(self, query):
        roll = str(self.get_query_value(query, "roll", "")).strip()
        token = str(self.get_query_value(query, "token", "")).strip()
        if not self.is_student_authenticated(roll, token):
            self.send_error(401, "Session expired. Please login again.")
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
            self.send_error(404, "Student not found")
            return
        self.show_upload_page(roll, user.iloc[0]["Student Name"], token)

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
                f"<tr><td>{idx + 1}</td><td>{roll_str}</td><td>{row['Student Name']}</td>"
                f"<td>{student_password}</td>"
                f"<td><form method='POST' class='form-row'>"
                f"<input type='hidden' name='action' value='set_student_paper_type'>"
                f"<input type='hidden' name='admin_token' value='{admin_token}'>"
                f"<input type='hidden' name='target_roll' value='{roll_str}'>"
                f"<select name='paper_type'>{options_html}</select>"
                f"<input type='submit' value='Set' class='btn btn-secondary'>"
                f"</form></td>"
                f"<td>{status}</td><td>{last_ip}</td>"
                f"<td class='submission-files-cell'>{files_html}</td>"
                f"<td><form method='POST' class='inline-form'>"
                f"<input type='hidden' name='action' value='reset_user'>"
                f"<input type='hidden' name='admin_token' value='{admin_token}'>"
                f"<input type='hidden' name='target_roll' value='{roll_str}'>"
                f"<input type='submit' value='Reset' class='btn btn-dark'></form></td></tr>"
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
            )
        )

    def show_admin_dashboard(self, query):
        admin_token = self.get_query_value(query, "token", "")
        df = load_data()
        logs = load_logs()
        rows = ""
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

            status = "Submitted" if student_submission_files(roll_str) else "Pending"
            status_class = "status-green" if status == "Submitted" else "status-red"
            rows += (
                f"<tr><td>{student_name}</td><td>{roll_str}</td><td>{last_ip}</td>"
                f"<td>{last_time}</td><td><span class='{status_class}'>{status}</span></td></tr>"
            )

        self.send_html(
            admin_dashboard_page(
                navbar_html=self.render_admin_navbar(admin_token),
                rows_html=rows,
                refresh_seconds=5,
            )
        )

    def show_login_form(self):
        self.send_html(login_page())

    def redirect(self, path):
        self.send_response(303)
        self.send_header("Location", path)
        self.end_headers()


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def run_server():
    ensure_directories()
    with ReusableTCPServer(("", PORT), SecureLabHandler) as httpd:
        print(f"Portal Live: http://localhost:{PORT}")
        httpd.serve_forever()
