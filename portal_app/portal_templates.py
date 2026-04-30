def _page(title: str, body_html: str, auto_refresh_seconds: int | None = None) -> str:
    refresh = (
        f'<meta http-equiv="refresh" content="{auto_refresh_seconds}">'
        if auto_refresh_seconds
        else ""
    )
    return f"""
    <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8">
            {refresh}
            <link rel="stylesheet" href="/static/style.css">
            <script>
                (function() {{
                    const saved = localStorage.getItem("portal_theme");
                    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
                    if (saved === "dark" || (!saved && prefersDark)) {{
                        document.documentElement.classList.add("theme-dark");
                    }}
                }})();
            </script>
        </head>
        {body_html}
        <script>
            (function() {{
                const btn = document.createElement("button");
                btn.className = "theme-toggle";
                function isDark() {{
                    return document.documentElement.classList.contains("theme-dark");
                }}
                function setLabel() {{
                    btn.textContent = isDark() ? "Light Mode" : "Dark Mode";
                }}
                btn.addEventListener("click", function() {{
                    document.documentElement.classList.toggle("theme-dark");
                    localStorage.setItem("portal_theme", isDark() ? "dark" : "light");
                    setLabel();
                }});
                setLabel();
                document.body.appendChild(btn);
            }})();
        </script>
    </html>
    """


def info_page(title, message, action_text="Return to Login", action_href="/"):
    return _page(
        title,
        f"""
        <body class="bg-center">
            <div class="card center-card">
                <h2 class="title">{title}</h2>
                <p class="muted">{message}</p>
                <a class="btn-link btn-primary" href="{action_href}">{action_text}</a>
            </div>
        </body>
        """,
    )


def alert_retry_page(title, message, alert_text, retry_href):
    return _page(
        title,
        f"""
        <body class="bg-center">
            <div class="card center-card">
                <h2 class="title">{title}</h2>
                <p class="muted">{message}</p>
                <a class="btn-link btn-primary" href="{retry_href}">Retry Upload</a>
            </div>
            <script>
                alert({alert_text!r});
            </script>
        </body>
        """,
    )


def login_page():
    return _page(
        "Assessment Submission Portal",
        """
        <body class="bg-center">
            <div class="card login-card">
                <h2 class="title">Login Portal</h2>
                <p class="muted">
                    Username is your roll number.
                    <br>e.g., <b>20P-0051</b>
                </p>
                <form method="POST">
                    <input type="hidden" name="action" value="login">
                    <label>Username</label><br>
                    <input class="w-full" name="username" required><br><br>
                    <label>Password</label><br>
                    <input class="w-full" type="password" name="password" required><br><br>
                    <input class="btn btn-primary w-full" type="submit" value="Login">
                </form>
            </div>
        </body>
        """,
    )


def admin_navbar(admin_home_url, students_url, dashboard_url, export_url, logout_url="/"):
    return f"""
    <nav class="navbar">
        <div><b>Admin Panel</b></div>
        <div class="nav-links">
            <a class="btn-link btn-dark" href="{admin_home_url}">Admin Home</a>
            <a class="btn-link btn-secondary" href="{students_url}">Manage Students</a>
            <a class="btn-link btn-purple" target="_blank" rel="noopener noreferrer" href="{dashboard_url}">Dashboard</a>
            <a class="btn-link btn-teal" href="{export_url}">Export Credentials</a>
            <a class="btn-link btn-danger" href="{logout_url}">Logout</a>
        </div>
    </nav>
    """


def student_home_page(name, roll, view_qp_url, submit_url):
    return _page(
        "Student Portal",
        f"""
        <body class="bg-soft">
            <div class="container-student">
                <div class="panel-head">
                    <h2 class="title">Student Assessment Portal</h2>
                    <p class="muted text-on-dark" style="margin:0;">Welcome, {name} ({roll})</p>
                </div>
                <div class="panel-body">
                    <p class="muted">
                        Step 1: View your question paper.<br>
                        Step 2: Prepare your solution and submit final files.
                    </p>
                    <div class="form-row">
                        <a class="btn-link btn-purple" target="_blank" rel="noopener noreferrer" href="{view_qp_url}">View Question Paper</a>
                        <a class="btn-link btn-primary" href="{submit_url}">Submit Solution</a>
                    </div>
                </div>
            </div>
        </body>
        """,
    )


def student_upload_page(roll, name, token, max_files, allowed_ext_csv):
    return _page(
        "Student Submission Portal",
        f"""
        <body class="bg-soft">
            <div class="container-student">
                <div class="panel-head">
                    <h2 class="title">Submission Portal</h2>
                    <p class="muted text-on-dark" style="margin:0;">Welcome, {name} ({roll})</p>
                </div>
                <div class="panel-body">
                    <div class="info-box info-box-blue">
                        <b>Instructions:</b> You can upload up to {max_files} file(s). Allowed types: {allowed_ext_csv}.
                    </div>
                    <form method="POST" enctype="multipart/form-data" onsubmit="return confirm('Are you sure you want to submit? You will not be able to upload again.');">
                        <input type="hidden" name="action" value="upload">
                        <input type="hidden" name="roll_no" value="{roll}">
                        <input type="hidden" name="auth_token" value="{token}">
                        <label><b>Select Files</b></label><br>
                        <input type="file" name="lab_files" multiple required><br><br>
                        <label class="muted">
                            <input type="checkbox" name="confirm_submit" value="yes" required>
                            I confirm this is my final submission.
                        </label><br><br>
                        <input class="btn btn-primary" type="submit" value="Submit Final Files">
                    </form>
                </div>
            </div>
        </body>
        """,
    )


def admin_home_page(navbar_html, current_paper_name, current_paper_time, students_url, admin_token):
    return _page(
        "Admin Panel",
        f"""
        <body class="bg-soft">
            {navbar_html}
            <main class="container-sm">
                <div class="card">
                    <h2 class="title">Admin Home</h2>
                    <p class="muted">Upload or replace the question paper here.</p>
                    <div class="info-box">
                        <div class="small muted"><b>Current Question Paper:</b> {current_paper_name}</div>
                        <div class="small muted">Last Updated: {current_paper_time}</div>
                    </div>
                    <form method="POST" enctype="multipart/form-data" class="form-row">
                        <input type="hidden" name="action" value="upload_question_paper">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <input type="file" name="question_paper_file" required>
                        <input class="btn btn-primary" type="submit" value="Upload Question Paper">
                    </form>
                    <br>
                    <a class="btn-link btn-secondary" href="{students_url}">Manage Students</a>
                </div>
            </main>
        </body>
        """,
    )


def admin_students_page(
    navbar_html,
    rows_html,
    max_files,
    admin_token,
    export_url,
    available_extensions,
    selected_extensions,
):
    ext_items = []
    for ext in available_extensions:
        checked = "checked" if ext in selected_extensions else ""
        ext_items.append(
            f'<label class="ext-item"><input type="checkbox" name="allowed_extensions" value="{ext}" {checked}> {ext}</label>'
        )
    ext_html = "".join(ext_items)

    return _page(
        "Student Management",
        f"""
        <body class="bg-soft">
            {navbar_html}
            <main class="container">
                <div class="card">
                    <h2 class="title">Student Management</h2>
                    <div class="form-row">
                        <form method="POST" class="form-row">
                            <span class="small muted">Max Files</span>
                            <input type="number" name="max_files" value="{max_files}" style="width:72px;">
                            <input type="hidden" name="action" value="update_settings">
                            <input type="hidden" name="admin_token" value="{admin_token}">
                            <input class="btn btn-primary" type="submit" value="Update">
                        </form>
                        <a class="btn-link btn-teal" href="{export_url}">Export Credentials</a>
                    </div>
                    <br>
                    <form method="POST">
                        <input type="hidden" name="action" value="update_extensions">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <div class="small muted" style="margin-bottom:6px;"><b>Allowed File Extensions</b></div>
                        <div class="ext-grid">
                            {ext_html}
                        </div>
                        <br>
                        <input class="btn btn-primary" type="submit" value="Apply Extensions">
                    </form>
                    <br>
                    <form method="POST" onsubmit="return confirm('Are you sure you want to reset passwords for all users?');">
                        <input type="hidden" name="action" value="reset_all_users">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <label class="small muted">
                            <input type="checkbox" name="confirm_reset_all" value="yes" required>
                            I understand this will reset every student's password.
                        </label><br><br>
                        <input class="btn btn-red" type="submit" value="Reset All Passwords">
                    </form>
                    <br>
                    <div class="table-wrap">
                        <table>
                            <tr>
                                <th>S#</th><th>Roll</th><th>Name</th><th>Password</th><th>Status</th><th>Last IP</th><th>Files</th><th>Action</th>
                            </tr>
                            {rows_html}
                        </table>
                    </div>
                </div>
            </main>
        </body>
        """,
    )


def admin_dashboard_page(navbar_html, rows_html, refresh_seconds=5):
    return _page(
        "Submission Dashboard",
        f"""
        <body class="bg-soft">
            {navbar_html}
            <main class="container">
                <div class="card">
                    <h2 class="title">Submission Dashboard</h2>
                    <div class="table-wrap">
                        <table>
                            <tr>
                                <th>Name</th><th>Roll</th><th>IP Address</th><th>Timestamp</th><th>Status</th>
                            </tr>
                            {rows_html}
                        </table>
                    </div>
                </div>
            </main>
        </body>
        """,
        auto_refresh_seconds=refresh_seconds,
    )
