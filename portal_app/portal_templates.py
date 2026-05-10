import html
import json


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
                const backBtn = document.createElement("button");
                backBtn.className = "page-back";
                backBtn.textContent = "Back";
                backBtn.addEventListener("click", function() {{
                    if (window.history.length > 1) {{
                        window.history.back();
                    }} else {{
                        window.location.href = "/";
                    }}
                }});
                document.body.appendChild(backBtn);

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

                const credit = document.createElement("div");
                credit.className = "dev-credit";
                credit.setAttribute("aria-hidden", "true");
                credit.textContent = "by ayyzenn";
                document.body.appendChild(credit);
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
            <div class="card center-card center-card-wide align-left">
                <h2 class="title">{title}</h2>
                <p class="muted">{message}</p>
                <div class="error-detail-box">
                    <div class="small muted"><b>Error details</b></div>
                    <div class="error-detail-text">{alert_text}</div>
                </div>
                <a class="btn-link btn-primary" href="{retry_href}">Retry Upload</a>
            </div>
        </body>
        """,
    )


def upload_success_page(roll, uploaded_files):
    items = "".join(f"{name}<br>" for name in uploaded_files)
    file_count = len(uploaded_files)
    file_names_inline = ", ".join(uploaded_files)
    file_label = "file" if file_count == 1 else "files"
    return _page(
        "Submission Successful",
        f"""
        <body class="bg-center">
            <div class="card center-card center-card-wide align-left">
                <h2 class="title">Submission Successful</h2>
                <p class="muted">
                    Your final submission has been received.
                </p>
                <div class="success-summary-box">
                    <div><b>Roll No.:</b> {roll}</div>
                    <div><b>Files Submitted:</b> {file_count} {file_label}</div>
                    <div><b>File Name(s):</b> {file_names_inline}</div>
                </div>
                <p class="small muted">Your session has been closed for security.</p>
                <a class="btn-link btn-primary" href="/">Return to Login</a>
            </div>
        </body>
        """,
    )


LOGIN_NOTICE_TEXT = {
    "invalid": "Incorrect username or password. Please check both fields and try again.",
    "session": "Your session expired or you are not signed in. Please log in again.",
    "data": (
        "Student list could not be loaded. Ensure students.xlsx exists in the server folder, "
        "is not open in Excel elsewhere, and is a valid .xlsx file."
    ),
    "assets": "A required site file is missing on the server. Ask your administrator to reinstall or redeploy the portal.",
}


def login_page(notice: str = ""):
    notice_key = (notice or "").strip().lower()
    banner_html = ""
    if notice_key in LOGIN_NOTICE_TEXT:
        banner_html = (
            f'<div class="login-notice login-notice-error" role="alert">'
            f"{html.escape(LOGIN_NOTICE_TEXT[notice_key])}"
            f"</div>"
        )

    return _page(
        "Assessment Submission Portal",
        f"""
        <body class="bg-center">
            <div class="login-shell">
                <div class="card login-info-card">
                    <h2 class="title">Assessment Submission Portal</h2>
                    <p class="muted">
                        Login with your assigned credentials to view question materials and submit your final files.
                    </p>
                    <div class="info-box">
                        <div><b>Student username format:</b> Roll number</div>
                        <div class="small muted">Example: <b>20P-0051</b></div>
                    </div>
                    <div class="small muted">Admin users sign in with the administrator username and password.</div>
                </div>

                <div class="card login-card">
                    <h3 class="title">Sign In</h3>
                    {banner_html}
                    <form method="POST" class="login-form">
                        <input type="hidden" name="action" value="login">
                        <label for="login-username"><b>Username</b></label>
                        <input id="login-username" class="w-full" name="username" placeholder="Enter your username" required>

                        <label for="login-password"><b>Password</b></label>
                        <input id="login-password" class="w-full" type="password" name="password" placeholder="Enter your password" required>

                        <label class="small muted">
                            <input id="show-password-toggle" type="checkbox">
                            Show password
                        </label>

                        <input class="btn btn-primary w-full" type="submit" value="Login">
                    </form>
                </div>
            </div>
            <script>
                (function() {{
                    const input = document.getElementById("login-password");
                    const toggle = document.getElementById("show-password-toggle");
                    if (!input || !toggle) return;
                    toggle.addEventListener("change", function() {{
                        input.type = toggle.checked ? "text" : "password";
                    }});
                }})();
            </script>
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


def student_home_page(name, roll, view_qp_url, submit_url, games_url, instructions=""):
    return _page(
        "Student Portal",
        f"""
        <body class="bg-soft">
            <div class="container-student container-games">
                <div class="panel-head">
                    <h2 class="title">Student Assessment Portal</h2>
                    <p class="muted text-on-dark no-margin">Welcome, {name} ({roll})</p>
                </div>
                <div id="home-timer-bar" class="home-timer-bar home-timer-bar-hidden">
                    <span id="home-timer-icon" class="home-timer-icon">&#9201;</span>
                    <span id="home-timer-text" class="home-timer-text">Loading timer...</span>
                </div>
                <div class="panel-body">
                    <div class="form-row justify-end">
                        <a class="btn-link btn-teal" href="{games_url}">Play Game</a>
                        <a class="btn-link btn-danger" href="/">Logout</a>
                    </div>
                    <div class="info-box" style="margin-bottom:12px;">
                        {html.escape(instructions) if instructions else "Step 1: View question paper and attached materials.<br>Step 2: Prepare your solution and submit final files."}
                    </div>
                    <div class="form-row">
                        <a class="btn-link btn-purple" href="{view_qp_url}">View Materials</a>
                        <a class="btn-link btn-primary" href="{submit_url}">Submit Solution</a>
                    </div>
                </div>
            </div>
            <script>
                (function () {{
                    const roll = {json.dumps(roll)};
                    const token = {json.dumps("")};
                    // token not available on home page - use public timer
                    const bar = document.getElementById("home-timer-bar");
                    const text = document.getElementById("home-timer-text");
                    const icon = document.getElementById("home-timer-icon");

                    function fmt(s) {{
                        if (s === null || s === undefined) return "--:--";
                        const h = Math.floor(s / 3600);
                        const m = Math.floor((s % 3600) / 60);
                        const sc = s % 60;
                        if (h > 0) return h + ":" + String(m).padStart(2,"0") + ":" + String(sc).padStart(2,"0");
                        return String(m).padStart(2,"0") + ":" + String(sc).padStart(2,"0");
                    }}

                    async function pollTimer() {{
                        try {{
                            const resp = await fetch("/api/timer", {{cache: "no-store"}});
                            if (!resp.ok) return;
                            const d = await resp.json();
                            bar.classList.remove("home-timer-bar-hidden","home-timer-active","home-timer-warn","home-timer-crit","home-timer-ended","home-timer-before");
                            if (d.phase === "not_set") {{ bar.classList.add("home-timer-bar-hidden"); return; }}
                            bar.classList.remove("home-timer-bar-hidden");
                            if (d.phase === "before_exam") {{
                                bar.classList.add("home-timer-before");
                                text.textContent = "Exam starts in " + fmt(d.seconds_until_start) + (d.is_paused ? " (paused)" : "");
                                icon.textContent = "⏳";
                            }} else if (d.phase === "active") {{
                                const rem = d.seconds_remaining;
                                if (rem <= 300) {{ bar.classList.add("home-timer-crit"); icon.textContent = "🔴"; }}
                                else if (rem <= 600) {{ bar.classList.add("home-timer-warn"); icon.textContent = "⚠️"; }}
                                else {{ bar.classList.add("home-timer-active"); icon.textContent = "⏱️"; }}
                                text.textContent = (d.is_paused ? "PAUSED — " : "") + "Time remaining: " + fmt(rem);
                            }} else if (d.phase === "extra_time") {{
                                bar.classList.add("home-timer-crit");
                                text.textContent = "Extra time: " + fmt(d.seconds_remaining);
                                icon.textContent = "⏰";
                            }} else {{
                                bar.classList.add("home-timer-ended");
                                text.textContent = "Submission time has ended.";
                                icon.textContent = "🔒";
                            }}
                        }} catch (e) {{}}
                    }}
                    pollTimer();
                    setInterval(pollTimer, 3000);
                }})();
            </script>
        </body>
        """,
    )


def student_games_page(name, roll, token):
    return _page(
        "Mini Games",
        f"""
        <body class="bg-soft">
            <div class="container-student">
                <div class="panel-head">
                    <h2 class="title">Mini Games Corner</h2>
                    <p class="muted text-on-dark no-margin">Have fun, {name} ({roll})</p>
                </div>
                <div class="panel-body">
                    <div class="form-row justify-end">
                        <a class="btn-link btn-secondary" href="/student?roll={roll}&token={token}">Back</a>
                        <a class="btn-link btn-danger" href="/">Logout</a>
                    </div>
                    <p class="muted">
                        Choose a game below.
                    </p>
                    <div class="game-tabs" role="tablist" aria-label="Game selector">
                        <button class="btn btn-purple game-tab-btn" id="tab-snake" data-game="snake" aria-selected="true">Snake</button>
                        <button class="btn btn-teal game-tab-btn" id="tab-flappy" data-game="flappy" aria-selected="false">Flappy Bird</button>
                        <button class="btn btn-dark game-tab-btn" id="tab-pacman" data-game="pacman" aria-selected="false">Pacman</button>
                    </div>

                    <section class="game-panel" id="game-panel-snake">
                        <div class="game-layout">
                            <div class="game-main">
                                <h3 class="section-title">Snake</h3>
                                <p class="small muted">Controls: Arrow keys. Press <b>Space</b> to restart after game over.</p>
                                <div class="game-scoreboard" aria-live="polite">
                                    <div class="score-chip">
                                        <span class="score-chip-label">Score</span>
                                        <span class="score-chip-value" id="snake-score">0</span>
                                    </div>
                                    <div class="score-chip score-chip-best">
                                        <span class="score-chip-label">High Score</span>
                                        <span class="score-chip-value" id="snake-high-score">0</span>
                                    </div>
                                </div>
                                <canvas id="snake-canvas" class="game-canvas" width="560" height="560"></canvas>
                            </div>
                            <div class="leaderboard-wrap">
                                <h4 class="leaderboard-title">Snake Leaderboard</h4>
                                <ol id="snake-leaderboard" class="leaderboard-list">
                                    <li class="leaderboard-empty">No scores yet. Be the first to score.</li>
                                </ol>
                            </div>
                        </div>
                    </section>

                    <section class="game-panel" id="game-panel-flappy" hidden>
                        <div class="game-layout">
                            <div class="game-main">
                                <h3 class="section-title">Flappy Bird</h3>
                                <p class="small muted">Controls: Press <b>Space</b> to flap. Press <b>Space</b> again after game over to restart.</p>
                                <div class="game-scoreboard" aria-live="polite">
                                    <div class="score-chip">
                                        <span class="score-chip-label">Score</span>
                                        <span class="score-chip-value" id="flappy-score">0</span>
                                    </div>
                                    <div class="score-chip score-chip-best">
                                        <span class="score-chip-label">High Score</span>
                                        <span class="score-chip-value" id="flappy-high-score">0</span>
                                    </div>
                                </div>
                                <canvas id="flappy-canvas" class="game-canvas game-canvas-wide" width="860" height="420"></canvas>
                            </div>
                            <div class="leaderboard-wrap">
                                <h4 class="leaderboard-title">Flappy Bird Leaderboard</h4>
                                <ol id="flappy-leaderboard" class="leaderboard-list">
                                    <li class="leaderboard-empty">No scores yet. Be the first to score.</li>
                                </ol>
                            </div>
                        </div>
                    </section>

                    <section class="game-panel" id="game-panel-pacman" hidden>
                        <div class="game-layout">
                            <div class="game-main">
                                <h3 class="section-title">Pacman</h3>
                                <p class="small muted">Controls: Arrow keys. Collect all dots. Avoid the ghost. Press <b>Space</b> to restart after game over.</p>
                                <div class="game-scoreboard" aria-live="polite">
                                    <div class="score-chip">
                                        <span class="score-chip-label">Score</span>
                                        <span class="score-chip-value" id="pacman-score">0</span>
                                    </div>
                                    <div class="score-chip score-chip-best">
                                        <span class="score-chip-label">High Score</span>
                                        <span class="score-chip-value" id="pacman-high-score">0</span>
                                    </div>
                                    <div class="score-chip">
                                        <span class="score-chip-label">Level</span>
                                        <span class="score-chip-value" id="pacman-level">1</span>
                                    </div>
                                </div>
                                <canvas id="pacman-canvas" class="game-canvas" width="560" height="560"></canvas>
                            </div>
                            <div class="leaderboard-wrap">
                                <h4 class="leaderboard-title">Pacman Leaderboard</h4>
                                <ol id="pacman-leaderboard" class="leaderboard-list">
                                    <li class="leaderboard-empty">No scores yet. Be the first to score.</li>
                                </ol>
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            <script>
                (function () {{
                    const studentRoll = "{roll}";
                    const studentToken = "{token}";
                    const tabButtons = document.querySelectorAll(".game-tab-btn");
                    const panels = {{
                        snake: document.getElementById("game-panel-snake"),
                        flappy: document.getElementById("game-panel-flappy"),
                        pacman: document.getElementById("game-panel-pacman"),
                    }};
                    const leaderboardEls = {{
                        snake: document.getElementById("snake-leaderboard"),
                        flappy: document.getElementById("flappy-leaderboard"),
                        pacman: document.getElementById("pacman-leaderboard"),
                    }};
                    let activeGame = "snake";

                    function showGame(name) {{
                        activeGame = name;
                        panels.snake.hidden = name !== "snake";
                        panels.flappy.hidden = name !== "flappy";
                        panels.pacman.hidden = name !== "pacman";
                        tabButtons.forEach(function (btn) {{
                            const isActive = btn.getAttribute("data-game") === name;
                            btn.setAttribute("aria-selected", isActive ? "true" : "false");
                            btn.classList.toggle("btn-primary", isActive);
                        }});
                    }}

                    tabButtons.forEach(function (btn) {{
                        btn.addEventListener("click", function () {{
                            showGame(btn.getAttribute("data-game"));
                        }});
                    }});

                    showGame("snake");

                    function leaderboardItemClass(rank) {{
                        if (rank === 1) return "leaderboard-item rank-gold";
                        if (rank === 2) return "leaderboard-item rank-silver";
                        if (rank === 3) return "leaderboard-item rank-bronze";
                        return "leaderboard-item";
                    }}

                    function escapeHtml(value) {{
                        return String(value)
                            .replaceAll("&", "&amp;")
                            .replaceAll("<", "&lt;")
                            .replaceAll(">", "&gt;")
                            .replaceAll('"', "&quot;")
                            .replaceAll("'", "&#39;");
                    }}

                    function renderLeaderboard(game, rows) {{
                        const list = leaderboardEls[game];
                        if (!list) return;
                        if (!rows || rows.length === 0) {{
                            list.innerHTML = '<li class="leaderboard-empty">No scores yet. Be the first to score.</li>';
                            return;
                        }}
                        list.innerHTML = rows
                            .map(function (row) {{
                                const displayName = row.name ? row.name + " (" + row.roll + ")" : row.roll;
                                return (
                                    '<li class="' +
                                    leaderboardItemClass(Number(row.rank || 0)) +
                                    '">' +
                                    '<span class="leader-rank">#' + Number(row.rank || 0) + "</span>" +
                                    '<span class="leader-name">' + escapeHtml(displayName) + "</span>" +
                                    '<span class="leader-score">' + Number(row.score || 0) + "</span>" +
                                    "</li>"
                                );
                            }})
                            .join("");
                    }}

                    async function refreshLeaderboard(game) {{
                        try {{
                            const resp = await fetch(
                                "/game_leaderboard?roll=" +
                                    encodeURIComponent(studentRoll) +
                                    "&token=" +
                                    encodeURIComponent(studentToken) +
                                    "&game=" +
                                    encodeURIComponent(game),
                                {{ cache: "no-store" }}
                            );
                            if (!resp.ok) return;
                            const data = await resp.json();
                            if (!data || !data.ok) return;
                            renderLeaderboard(game, data.leaders || []);
                        }} catch (error) {{}}
                    }}

                    async function pushScore(game, score) {{
                        if (!Number.isFinite(score) || score < 1) return;
                        try {{
                            await fetch("/", {{
                                method: "POST",
                                headers: {{ "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" }},
                                body:
                                    "action=submit_game_score" +
                                    "&roll_no=" +
                                    encodeURIComponent(studentRoll) +
                                    "&auth_token=" +
                                    encodeURIComponent(studentToken) +
                                    "&game=" +
                                    encodeURIComponent(game) +
                                    "&score=" +
                                    encodeURIComponent(String(score)),
                            }});
                        }} catch (error) {{}}
                        refreshLeaderboard(game);
                    }}

                    // Snake game
                    const snakeCanvas = document.getElementById("snake-canvas");
                    const snakeCtx = snakeCanvas.getContext("2d");
                    const snakeScoreEl = document.getElementById("snake-score");
                    const snakeHighScoreEl = document.getElementById("snake-high-score");
                    const snakeHighScoreKey = "portal_game_snake_high_score";
                    let snakeHighScore = Number(localStorage.getItem(snakeHighScoreKey) || "0");
                    const snakeGrid = 21;
                    const snakeTile = snakeCanvas.width / snakeGrid;
                    let snakeDirection = {{ x: 1, y: 0 }};
                    let snakeNextDirection = {{ x: 1, y: 0 }};
                    let snakeBody = [{{ x: 9, y: 10 }}];
                    let snakeFood = {{ x: 15, y: 10 }};
                    let snakeScore = 0;
                    let snakeGameOver = false;
                    snakeHighScoreEl.textContent = String(snakeHighScore);

                    function snakeReset() {{
                        snakeDirection = {{ x: 1, y: 0 }};
                        snakeNextDirection = {{ x: 1, y: 0 }};
                        snakeBody = [{{ x: 9, y: 10 }}];
                        snakeFood = {{ x: 15, y: 10 }};
                        snakeScore = 0;
                        snakeGameOver = false;
                        snakeScoreEl.textContent = "0";
                    }}

                    function snakePlaceFood() {{
                        while (true) {{
                            const fx = Math.floor(Math.random() * snakeGrid);
                            const fy = Math.floor(Math.random() * snakeGrid);
                            if (!snakeBody.some(function (s) {{ return s.x === fx && s.y === fy; }})) {{
                                snakeFood = {{ x: fx, y: fy }};
                                return;
                            }}
                        }}
                    }}

                    function snakeStep() {{
                        if (snakeGameOver) return;
                        snakeDirection = snakeNextDirection;
                        const head = snakeBody[0];
                        const next = {{ x: head.x + snakeDirection.x, y: head.y + snakeDirection.y }};

                        if (next.x < 0 || next.y < 0 || next.x >= snakeGrid || next.y >= snakeGrid) {{
                            snakeGameOver = true;
                            return;
                        }}
                        if (snakeBody.some(function (s) {{ return s.x === next.x && s.y === next.y; }})) {{
                            snakeGameOver = true;
                            return;
                        }}

                        snakeBody.unshift(next);
                        if (next.x === snakeFood.x && next.y === snakeFood.y) {{
                            snakeScore += 1;
                            snakeScoreEl.textContent = String(snakeScore);
                            if (snakeScore > snakeHighScore) {{
                                snakeHighScore = snakeScore;
                                snakeHighScoreEl.textContent = String(snakeHighScore);
                                localStorage.setItem(snakeHighScoreKey, String(snakeHighScore));
                            }}
                            pushScore("snake", snakeScore);
                            snakePlaceFood();
                        }} else {{
                            snakeBody.pop();
                        }}
                    }}

                    function snakeDraw() {{
                        snakeCtx.fillStyle = "#0f172a";
                        snakeCtx.fillRect(0, 0, snakeCanvas.width, snakeCanvas.height);

                        snakeCtx.fillStyle = "#22c55e";
                        snakeBody.forEach(function (s) {{
                            snakeCtx.fillRect(s.x * snakeTile + 1, s.y * snakeTile + 1, snakeTile - 2, snakeTile - 2);
                        }});

                        snakeCtx.fillStyle = "#ef4444";
                        snakeCtx.fillRect(
                            snakeFood.x * snakeTile + 2,
                            snakeFood.y * snakeTile + 2,
                            snakeTile - 4,
                            snakeTile - 4
                        );

                        if (snakeGameOver) {{
                            snakeCtx.fillStyle = "rgba(0, 0, 0, 0.45)";
                            snakeCtx.fillRect(0, 0, snakeCanvas.width, snakeCanvas.height);
                            snakeCtx.fillStyle = "#ffffff";
                            snakeCtx.font = "bold 26px sans-serif";
                            snakeCtx.fillText("Game Over", 130, 195);
                            snakeCtx.font = "14px sans-serif";
                            snakeCtx.fillText("Press Space to restart", 132, 220);
                        }}
                    }}

                    setInterval(function () {{
                        snakeStep();
                        snakeDraw();
                    }}, 110);

                    // Flappy game
                    const flappyCanvas = document.getElementById("flappy-canvas");
                    const flappyCtx = flappyCanvas.getContext("2d");
                    const flappyScoreEl = document.getElementById("flappy-score");
                    const flappyHighScoreEl = document.getElementById("flappy-high-score");
                    const flappyHighScoreKey = "portal_game_flappy_high_score";
                    let flappyHighScore = Number(localStorage.getItem(flappyHighScoreKey) || "0");
                    flappyHighScoreEl.textContent = String(flappyHighScore);
                    const flappyState = {{
                        birdY: 150,
                        birdVY: 0,
                        gravity: 0.38,
                        flapLift: -6.4,
                        pipes: [],
                        frame: 0,
                        score: 0,
                        alive: true,
                    }};

                    function flappyReset() {{
                        flappyState.birdY = 150;
                        flappyState.birdVY = 0;
                        flappyState.pipes = [];
                        flappyState.frame = 0;
                        flappyState.score = 0;
                        flappyState.alive = true;
                        flappyScoreEl.textContent = "0";
                    }}

                    function flappySpawnPipe() {{
                        const gap = 110;
                        const topHeight = 40 + Math.floor(Math.random() * 150);
                        flappyState.pipes.push({{
                            x: flappyCanvas.width + 20,
                            w: 56,
                            top: topHeight,
                            bottomY: topHeight + gap,
                            passed: false,
                        }});
                    }}

                    function flappyStep() {{
                        if (!flappyState.alive) return;
                        flappyState.frame += 1;
                        flappyState.birdVY += flappyState.gravity;
                        flappyState.birdY += flappyState.birdVY;

                        if (flappyState.frame % 95 === 0) {{
                            flappySpawnPipe();
                        }}

                        const birdX = 115;
                        const birdSize = 18;

                        flappyState.pipes.forEach(function (p) {{
                            p.x -= 2.4;
                            const inX = birdX + birdSize > p.x && birdX - birdSize < p.x + p.w;
                            const hitTop = flappyState.birdY - birdSize < p.top;
                            const hitBottom = flappyState.birdY + birdSize > p.bottomY;
                            if (inX && (hitTop || hitBottom)) {{
                                flappyState.alive = false;
                            }}
                            if (!p.passed && p.x + p.w < birdX) {{
                                p.passed = true;
                                flappyState.score += 1;
                                flappyScoreEl.textContent = String(flappyState.score);
                                if (flappyState.score > flappyHighScore) {{
                                    flappyHighScore = flappyState.score;
                                    flappyHighScoreEl.textContent = String(flappyHighScore);
                                    localStorage.setItem(flappyHighScoreKey, String(flappyHighScore));
                                }}
                                pushScore("flappy", flappyState.score);
                            }}
                        }});

                        flappyState.pipes = flappyState.pipes.filter(function (p) {{ return p.x + p.w > -5; }});

                        if (flappyState.birdY > flappyCanvas.height - 8 || flappyState.birdY < 8) {{
                            flappyState.alive = false;
                        }}
                    }}

                    function flappyDraw() {{
                        flappyCtx.fillStyle = "#0ea5e9";
                        flappyCtx.fillRect(0, 0, flappyCanvas.width, flappyCanvas.height);

                        flappyCtx.fillStyle = "#16a34a";
                        flappyState.pipes.forEach(function (p) {{
                            flappyCtx.fillRect(p.x, 0, p.w, p.top);
                            flappyCtx.fillRect(p.x, p.bottomY, p.w, flappyCanvas.height - p.bottomY);
                        }});

                        flappyCtx.fillStyle = "#f59e0b";
                        flappyCtx.beginPath();
                        flappyCtx.arc(115, flappyState.birdY, 13, 0, Math.PI * 2);
                        flappyCtx.fill();

                        if (!flappyState.alive) {{
                            flappyCtx.fillStyle = "rgba(0, 0, 0, 0.35)";
                            flappyCtx.fillRect(0, 0, flappyCanvas.width, flappyCanvas.height);
                            flappyCtx.fillStyle = "#ffffff";
                            flappyCtx.font = "bold 28px sans-serif";
                            flappyCtx.fillText("Game Over", 180, 145);
                            flappyCtx.font = "14px sans-serif";
                            flappyCtx.fillText("Press Space to restart", 188, 170);
                        }}
                    }}

                    setInterval(function () {{
                        flappyStep();
                        flappyDraw();
                    }}, 16);

                    // Pacman game
                    const pacmanCanvas = document.getElementById("pacman-canvas");
                    const pacmanCtx = pacmanCanvas.getContext("2d");
                    const pacmanScoreEl = document.getElementById("pacman-score");
                    const pacmanHighScoreEl = document.getElementById("pacman-high-score");
                    const pacmanLevelEl = document.getElementById("pacman-level");
                    const pacmanHighScoreKey = "portal_game_pacman_high_score";
                    let pacmanHighScore = Number(localStorage.getItem(pacmanHighScoreKey) || "0");
                    pacmanHighScoreEl.textContent = String(pacmanHighScore);
                    const pacmanGrid = 20;
                    const pacmanTile = pacmanCanvas.width / pacmanGrid;
                    let pacmanWalls = new Set();
                    let pacmanDots = new Set();
                    let pacmanPowerDots = new Set();
                    let pacmanPlayer = {{ x: 1, y: 1 }};
                    let pacmanGhost = {{ x: 18, y: 18 }};
                    let pacmanDir = {{ x: 1, y: 0 }};
                    let pacmanNextDir = {{ x: 1, y: 0 }};
                    let pacmanGhostDir = {{ x: -1, y: 0 }};
                    let pacmanScore = 0;
                    let pacmanGameOver = false;
                    let pacmanWon = false;
                    let pacmanFrightenedTicks = 0;
                    let pacmanLevel = 1;

                    function pacmanKey(x, y) {{
                        return String(x) + "," + String(y);
                    }}

                    function pacmanBuildMap() {{
                        pacmanWalls = new Set();
                        pacmanDots = new Set();
                        pacmanPowerDots = new Set();
                        const mazeVariant = Math.floor(Math.random() * 4);
                        for (let y = 0; y < pacmanGrid; y += 1) {{
                            for (let x = 0; x < pacmanGrid; x += 1) {{
                                const border = x === 0 || y === 0 || x === pacmanGrid - 1 || y === pacmanGrid - 1;
                                const pillarA = x === (4 + (mazeVariant % 2)) && y >= 2 && y <= 17 && y !== 9 && y !== 10;
                                const pillarB = x === 10 && y >= 2 && y <= 17 && y !== (4 + (mazeVariant % 3)) && y !== (13 + (mazeVariant % 2));
                                const pillarC = x === (14 + (mazeVariant === 3 ? -1 : 0)) && y >= 2 && y <= 17 && y !== 7 && y !== 12;
                                const barTop = y === (6 + (mazeVariant === 2 ? 1 : 0)) && x >= 7 && x <= 12 && x !== (8 + mazeVariant % 3);
                                const barBottom = y === (13 + (mazeVariant === 1 ? -1 : 0)) && x >= 7 && x <= 12 && x !== (10 + mazeVariant % 3);
                                const zigA = mazeVariant >= 2 && (x + y) % 11 === 0 && x > 2 && x < 17 && y > 2 && y < 17;
                                const safeZone = (x <= 2 && y <= 2) || (x >= pacmanGrid - 3 && y >= pacmanGrid - 3);
                                if (border || ((pillarA || pillarB || pillarC || barTop || barBottom || zigA) && !safeZone)) {{
                                    pacmanWalls.add(pacmanKey(x, y));
                                }} else {{
                                    pacmanDots.add(pacmanKey(x, y));
                                }}
                            }}
                        }}
                        pacmanDots.delete(pacmanKey(1, 1));
                        pacmanDots.delete(pacmanKey(18, 18));
                        [[1, 18], [18, 1], [3, 10], [16, 10]].forEach(function (p) {{
                            const k = pacmanKey(p[0], p[1]);
                            if (!pacmanWalls.has(k)) {{
                                pacmanDots.delete(k);
                                pacmanPowerDots.add(k);
                            }}
                        }});
                        // Classic side tunnel.
                        pacmanWalls.delete(pacmanKey(0, 10));
                        pacmanWalls.delete(pacmanKey(19, 10));
                    }}

                    function pacmanReset() {{
                        pacmanBuildMap();
                        pacmanPlayer = {{ x: 1, y: 1 }};
                        pacmanGhost = {{ x: 18, y: 18 }};
                        pacmanDir = {{ x: 1, y: 0 }};
                        pacmanNextDir = {{ x: 1, y: 0 }};
                        pacmanGhostDir = {{ x: -1, y: 0 }};
                        pacmanScore = 0;
                        pacmanGameOver = false;
                        pacmanWon = false;
                        pacmanFrightenedTicks = 0;
                        pacmanScoreEl.textContent = "0";
                        pacmanLevel = 1;
                        pacmanLevelEl.textContent = "1";
                    }}

                    function pacmanAdvanceLevel() {{
                        pacmanLevel += 1;
                        pacmanLevelEl.textContent = String(pacmanLevel);
                        pacmanBuildMap();
                        pacmanPlayer = {{ x: 1, y: 1 }};
                        pacmanGhost = {{ x: 18, y: 18 }};
                        pacmanDir = {{ x: 1, y: 0 }};
                        pacmanNextDir = {{ x: 1, y: 0 }};
                        pacmanGhostDir = {{ x: -1, y: 0 }};
                        pacmanFrightenedTicks = 0;
                    }}

                    function pacmanTryMove(entity, dir) {{
                        if (!dir || (dir.x === 0 && dir.y === 0)) return false;
                        const nx = entity.x + dir.x;
                        const ny = entity.y + dir.y;
                        if (ny < 0 || ny >= pacmanGrid) return false;
                        if (ny === 10 && nx < 0) {{
                            entity.x = pacmanGrid - 1;
                            return true;
                        }}
                        if (ny === 10 && nx >= pacmanGrid) {{
                            entity.x = 0;
                            return true;
                        }}
                        if (nx < 0 || nx >= pacmanGrid) return false;
                        if (pacmanWalls.has(pacmanKey(nx, ny))) return false;
                        entity.x = nx;
                        entity.y = ny;
                        return true;
                    }}

                    function pacmanStepGhost() {{
                        const choices = [
                            {{ x: 1, y: 0 }},
                            {{ x: -1, y: 0 }},
                            {{ x: 0, y: 1 }},
                            {{ x: 0, y: -1 }},
                        ];
                        let valid = choices.filter(function (c) {{
                            const nx = pacmanGhost.x + c.x;
                            const ny = pacmanGhost.y + c.y;
                            if (ny < 0 || ny >= pacmanGrid) return false;
                            if (ny === 10 && (nx < 0 || nx >= pacmanGrid)) return true;
                            if (nx < 0 || nx >= pacmanGrid) return false;
                            return !pacmanWalls.has(pacmanKey(nx, ny));
                        }});
                        if (!valid.length) return;

                        const reverse = {{ x: -pacmanGhostDir.x, y: -pacmanGhostDir.y }};
                        const nonReverse = valid.filter(function (v) {{
                            return !(v.x === reverse.x && v.y === reverse.y);
                        }});
                        if (nonReverse.length) valid = nonReverse;

                        valid.sort(function (a, b) {{
                            const da = Math.abs(pacmanGhost.x + a.x - pacmanPlayer.x) + Math.abs(pacmanGhost.y + a.y - pacmanPlayer.y);
                            const db = Math.abs(pacmanGhost.x + b.x - pacmanPlayer.x) + Math.abs(pacmanGhost.y + b.y - pacmanPlayer.y);
                            if (pacmanFrightenedTicks > 0) return db - da;
                            return da - db;
                        }});

                        const best = valid[0];
                        if (pacmanTryMove(pacmanGhost, best)) {{
                            pacmanGhostDir = best;
                        }}
                    }}

                    function pacmanUpdate() {{
                        if (pacmanGameOver || pacmanWon) return;
                        if (pacmanTryMove({{ x: pacmanPlayer.x, y: pacmanPlayer.y }}, pacmanNextDir)) {{
                            pacmanDir = {{ x: pacmanNextDir.x, y: pacmanNextDir.y }};
                        }}
                        pacmanTryMove(pacmanPlayer, pacmanDir);

                        const dotKey = pacmanKey(pacmanPlayer.x, pacmanPlayer.y);
                        if (pacmanDots.has(dotKey)) {{
                            pacmanDots.delete(dotKey);
                            pacmanScore += 1;
                            pacmanScoreEl.textContent = String(pacmanScore);
                            if (pacmanScore > pacmanHighScore) {{
                                pacmanHighScore = pacmanScore;
                                pacmanHighScoreEl.textContent = String(pacmanHighScore);
                                localStorage.setItem(pacmanHighScoreKey, String(pacmanHighScore));
                            }}
                            pushScore("pacman", pacmanScore);
                        }}
                        if (pacmanPowerDots.has(dotKey)) {{
                            pacmanPowerDots.delete(dotKey);
                            pacmanScore += 5;
                            pacmanFrightenedTicks = 20;
                            pacmanScoreEl.textContent = String(pacmanScore);
                            if (pacmanScore > pacmanHighScore) {{
                                pacmanHighScore = pacmanScore;
                                pacmanHighScoreEl.textContent = String(pacmanHighScore);
                                localStorage.setItem(pacmanHighScoreKey, String(pacmanHighScore));
                            }}
                            pushScore("pacman", pacmanScore);
                        }}

                        if (pacmanPlayer.x === pacmanGhost.x && pacmanPlayer.y === pacmanGhost.y) {{
                            if (pacmanFrightenedTicks > 0) {{
                                pacmanScore += 10;
                                pacmanScoreEl.textContent = String(pacmanScore);
                                pacmanGhost = {{ x: 18, y: 18 }};
                                pacmanGhostDir = {{ x: -1, y: 0 }};
                                pacmanFrightenedTicks = 0;
                                pushScore("pacman", pacmanScore);
                            }} else {{
                                pacmanGameOver = true;
                            }}
                        }}
                        if (pacmanDots.size === 0 && pacmanPowerDots.size === 0) {{
                            pacmanAdvanceLevel();
                        }}
                        if (pacmanFrightenedTicks > 0) pacmanFrightenedTicks -= 1;
                    }}

                    function pacmanDraw() {{
                        pacmanCtx.fillStyle = "#020617";
                        pacmanCtx.fillRect(0, 0, pacmanCanvas.width, pacmanCanvas.height);

                        pacmanCtx.fillStyle = "#334155";
                        pacmanWalls.forEach(function (k) {{
                            const parts = k.split(",");
                            const x = Number(parts[0]);
                            const y = Number(parts[1]);
                            pacmanCtx.fillRect(x * pacmanTile, y * pacmanTile, pacmanTile, pacmanTile);
                        }});

                        pacmanCtx.fillStyle = "#f8fafc";
                        pacmanDots.forEach(function (k) {{
                            const parts = k.split(",");
                            const x = Number(parts[0]);
                            const y = Number(parts[1]);
                            pacmanCtx.beginPath();
                            pacmanCtx.arc(x * pacmanTile + pacmanTile / 2, y * pacmanTile + pacmanTile / 2, pacmanTile * 0.12, 0, Math.PI * 2);
                            pacmanCtx.fill();
                        }});
                        pacmanCtx.fillStyle = "#a78bfa";
                        pacmanPowerDots.forEach(function (k) {{
                            const parts = k.split(",");
                            const x = Number(parts[0]);
                            const y = Number(parts[1]);
                            pacmanCtx.beginPath();
                            pacmanCtx.arc(x * pacmanTile + pacmanTile / 2, y * pacmanTile + pacmanTile / 2, pacmanTile * 0.21, 0, Math.PI * 2);
                            pacmanCtx.fill();
                        }});

                        pacmanCtx.fillStyle = "#facc15";
                        pacmanCtx.beginPath();
                        pacmanCtx.arc(
                            pacmanPlayer.x * pacmanTile + pacmanTile / 2,
                            pacmanPlayer.y * pacmanTile + pacmanTile / 2,
                            pacmanTile * 0.38,
                            0.2 * Math.PI,
                            1.8 * Math.PI
                        );
                        pacmanCtx.lineTo(pacmanPlayer.x * pacmanTile + pacmanTile / 2, pacmanPlayer.y * pacmanTile + pacmanTile / 2);
                        pacmanCtx.fill();

                        pacmanCtx.fillStyle = pacmanFrightenedTicks > 0 ? "#60a5fa" : "#ef4444";
                        pacmanCtx.beginPath();
                        pacmanCtx.arc(
                            pacmanGhost.x * pacmanTile + pacmanTile / 2,
                            pacmanGhost.y * pacmanTile + pacmanTile / 2,
                            pacmanTile * 0.34,
                            0,
                            Math.PI * 2
                        );
                        pacmanCtx.fill();

                        if (pacmanGameOver || pacmanWon) {{
                            pacmanCtx.fillStyle = "rgba(0, 0, 0, 0.45)";
                            pacmanCtx.fillRect(0, 0, pacmanCanvas.width, pacmanCanvas.height);
                            pacmanCtx.fillStyle = "#ffffff";
                            pacmanCtx.font = "bold 30px sans-serif";
                            pacmanCtx.fillText(pacmanWon ? "You Win!" : "Game Over", 190, 260);
                            pacmanCtx.font = "14px sans-serif";
                            pacmanCtx.fillText("Press Space to restart", 200, 286);
                        }}
                    }}

                    setInterval(function () {{
                        pacmanUpdate();
                        pacmanDraw();
                    }}, 120);

                    setInterval(function () {{
                        if (pacmanGameOver || pacmanWon) return;
                        pacmanStepGhost();
                        if (pacmanPlayer.x === pacmanGhost.x && pacmanPlayer.y === pacmanGhost.y) {{
                            if (pacmanFrightenedTicks > 0) {{
                                pacmanScore += 10;
                                pacmanScoreEl.textContent = String(pacmanScore);
                                pacmanGhost = {{ x: 18, y: 18 }};
                                pacmanGhostDir = {{ x: -1, y: 0 }};
                                pacmanFrightenedTicks = 0;
                                pushScore("pacman", pacmanScore);
                            }} else {{
                                pacmanGameOver = true;
                            }}
                        }}
                        pacmanDraw();
                    }}, 260);

                    document.addEventListener("keydown", function (event) {{
                        const key = event.key;
                        if (activeGame === "snake") {{
                            if (key === "ArrowUp" || key === "ArrowDown" || key === "ArrowLeft" || key === "ArrowRight" || key === " ") {{
                                event.preventDefault();
                            }}
                            if (key === "ArrowUp" && snakeDirection.y !== 1) snakeNextDirection = {{ x: 0, y: -1 }};
                            if (key === "ArrowDown" && snakeDirection.y !== -1) snakeNextDirection = {{ x: 0, y: 1 }};
                            if (key === "ArrowLeft" && snakeDirection.x !== 1) snakeNextDirection = {{ x: -1, y: 0 }};
                            if (key === "ArrowRight" && snakeDirection.x !== -1) snakeNextDirection = {{ x: 1, y: 0 }};
                            if (key === " " && snakeGameOver) snakeReset();
                        }}

                        if (activeGame === "flappy" && key === " ") {{
                            event.preventDefault();
                            if (!flappyState.alive) {{
                                flappyReset();
                            }} else {{
                                flappyState.birdVY = flappyState.flapLift;
                            }}
                        }}

                        if (activeGame === "pacman") {{
                            if (key === "ArrowUp" || key === "ArrowDown" || key === "ArrowLeft" || key === "ArrowRight" || key === " ") {{
                                event.preventDefault();
                            }}
                            if (key === "ArrowUp") pacmanNextDir = {{ x: 0, y: -1 }};
                            if (key === "ArrowDown") pacmanNextDir = {{ x: 0, y: 1 }};
                            if (key === "ArrowLeft") pacmanNextDir = {{ x: -1, y: 0 }};
                            if (key === "ArrowRight") pacmanNextDir = {{ x: 1, y: 0 }};
                            if (key === " " && (pacmanGameOver || pacmanWon)) pacmanReset();
                        }}
                    }});

                    snakeReset();
                    flappyReset();
                    pacmanReset();
                    snakeDraw();
                    flappyDraw();
                    pacmanDraw();
                    refreshLeaderboard("snake");
                    refreshLeaderboard("flappy");
                    refreshLeaderboard("pacman");
                    setInterval(function () {{
                        refreshLeaderboard(activeGame);
                    }}, 15000);
                }})();
            </script>
        </body>
        """,
    )


def student_upload_page(roll, name, token, max_files, allowed_ext_csv, instructions=""):
    return _page(
        "Student Submission Portal",
        f"""
        <body class="bg-soft">
            <!-- ── Sticky exam timer bar ── -->
            <div id="exam-timer-bar" class="exam-timer-sticky exam-timer-bar-hidden">
                <span id="exam-timer-icon" class="exam-timer-icon">&#9201;</span>
                <span id="exam-timer-text" class="exam-timer-label">Loading timer…</span>
                <span id="exam-timer-display" class="exam-timer-display"></span>
            </div>

            <!-- ── 10-minute warning banner ── -->
            <div id="warn-10" class="exam-warn-banner exam-warn-banner-hidden" role="alert">
                <b>&#9888; Only 10 minutes remaining.</b>
                Please organise your files, verify your roll number, and review submission
                instructions carefully before final submission.
            </div>

            <!-- ── 5-minute critical alert ── -->
            <div id="warn-5" class="exam-warn-banner exam-warn-critical exam-warn-banner-hidden" role="alert">
                <b>&#128721; Only 5 minutes remaining.</b>
                Submission portal will close soon. Submit immediately.
            </div>

            <div class="container-student">
                <div class="panel-head">
                    <h2 class="title">Submission Portal</h2>
                    <p class="muted text-on-dark no-margin">Welcome, {name} ({roll})</p>
                </div>
                <div class="panel-body">
                    <div class="form-row justify-end">
                        <a class="btn-link btn-secondary" href="/student?roll={roll}&token={token}">Back</a>
                        <a class="btn-link btn-danger" href="/">Logout</a>
                    </div>
                    <div class="info-box info-box-blue">
                        You can upload up to {max_files} file(s). <br> <b>Allowed types:</b> {allowed_ext_csv}.
                    </div>

                    <!-- ── Submission ended overlay ── -->
                    <div id="submission-locked-notice" class="submission-locked-notice" style="display:none;">
                        <div class="locked-icon">&#128274;</div>
                        <h3 class="locked-title">Submission Time Has Ended</h3>
                        <p class="locked-body" id="locked-body-text">
                            The submission window is closed. Contact your teacher if you need extra time.
                        </p>
                        <div id="late-request-section" class="late-request-section">
                            <button id="late-request-btn" class="btn btn-primary" onclick="doRequestExtraTime()">
                                Request Extra Time from Teacher
                            </button>
                            <div id="late-request-status" class="late-request-status" style="display:none;"></div>
                        </div>
                    </div>

                    <form id="upload-form" method="POST" enctype="multipart/form-data"
                          onsubmit="return validateUpload();">
                        <input type="hidden" name="action" value="upload">
                        <input type="hidden" name="roll_no" value="{roll}">
                        <input type="hidden" name="auth_token" value="{token}">
                        <label><b>Select Files</b></label><br>
                        <input id="student-lab-files" type="file" name="lab_files" multiple required
                               data-preview-target="student-file-preview">
                        <div id="student-file-preview" class="file-preview-list file-preview-empty">No files selected yet.</div>
                        <div id="empty-file-warn" class="exam-warn-banner" style="display:none;margin-top:6px;">
                            <b>&#9888; One or more selected files are empty (0 bytes).</b>
                            Remove them before submitting — empty files will not be accepted.
                        </div><br>
                        <label class="muted">
                            <input type="checkbox" name="confirm_submit" value="yes" required>
                            I confirm this is my final submission.
                        </label><br><br>
                        <input id="submit-btn" class="btn btn-primary" type="submit" value="Submit Final Files">
                    </form>
                </div>
            </div>

            <!-- ── Standalone file-preview script (no timer dependencies) ── -->
            <script>
                (function () {{
                    var fileInput = document.getElementById("student-lab-files");
                    var preview   = document.getElementById("student-file-preview");
                    var emptyWarn = document.getElementById("empty-file-warn");
                    if (!fileInput || !preview) return;

                    function fmtSize(bytes) {{
                        if (bytes === 0) return "⚠️ EMPTY";
                        if (bytes < 1024) return bytes + " B";
                        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
                        return (bytes / 1048576).toFixed(2) + " MB";
                    }}

                    function getExt(name) {{
                        var dot = name.lastIndexOf(".");
                        return dot > 0 ? name.substring(dot) : "(no ext)";
                    }}

                    function updatePreview() {{
                        var files = Array.from(fileInput.files || []);
                        if (files.length === 0) {{
                            preview.classList.add("file-preview-empty");
                            preview.innerHTML = "No files selected yet.";
                            if (emptyWarn) emptyWarn.style.display = "none";
                            var sb = document.getElementById("submit-btn");
                            if (sb) sb.disabled = false;
                            return;
                        }}
                        var hasEmpty = false;
                        preview.classList.remove("file-preview-empty");
                        preview.innerHTML = files.map(function (f, idx) {{
                            var empty = (f.size === 0);
                            if (empty) hasEmpty = true;
                            var ext   = getExt(f.name);
                            var size  = fmtSize(f.size);
                            var rowCls = empty ? "file-preview-empty-file" : "";
                            return "<div class='file-preview-row " + rowCls + "'>" +
                                "<span class='fp-num'>" + (idx + 1) + ".</span>" +
                                "<span class='fp-name'>" + String(f.name) + "</span>" +
                                "<span class='fp-ext'>" + ext + "</span>" +
                                "<span class='file-size-badge" + (empty ? " file-size-empty" : "") + "'>" + size + "</span>" +
                                "</div>";
                        }}).join("");
                        if (emptyWarn) emptyWarn.style.display = hasEmpty ? "" : "none";
                        var sb = document.getElementById("submit-btn");
                        if (sb) sb.disabled = hasEmpty;
                    }}

                    fileInput.addEventListener("change", updatePreview);
                }})();
            </script>

            <script>
                (function () {{
                    const _roll = {json.dumps(roll)};
                    const _token = {json.dumps(token)};
                    let _warned10 = false;
                    let _warned5 = false;
                    let _locked = false;
                    let _lateStatus = null; // null | "pending" | "approved" | "rejected"

                    const timerBar = document.getElementById("exam-timer-bar");
                    const timerIcon = document.getElementById("exam-timer-icon");
                    const timerLabel = document.getElementById("exam-timer-text");
                    const timerDisplay = document.getElementById("exam-timer-display");
                    const warn10 = document.getElementById("warn-10");
                    const warn5 = document.getElementById("warn-5");
                    const lockNotice = document.getElementById("submission-locked-notice");
                    const uploadForm = document.getElementById("upload-form");
                    const submitBtn = document.getElementById("submit-btn");
                    const lockedBody = document.getElementById("locked-body-text");
                    const lateSection = document.getElementById("late-request-section");
                    const lateBtn = document.getElementById("late-request-btn");
                    const lateStatusDiv = document.getElementById("late-request-status");

                    // ── Pre-submit validation ─────────────────────────────────
                    window.validateUpload = function() {{
                        const fileInput = document.getElementById("student-lab-files");
                        const files = Array.from((fileInput && fileInput.files) || []);
                        const emptyFiles = files.filter(function(f) {{ return f.size === 0; }});
                        if (emptyFiles.length > 0) {{
                            alert("Cannot submit: " + emptyFiles.length + " empty file(s) selected.\n" +
                                  "Remove empty files before submitting.");
                            return false;
                        }}
                        return confirm("Are you sure you want to submit? You will not be able to upload again.");
                    }};

                    function fmt(s) {{
                        if (s === null || s === undefined) return "";
                        const h = Math.floor(s / 3600);
                        const m = Math.floor((s % 3600) / 60);
                        const sc = s % 60;
                        if (h > 0) return h + ":" + String(m).padStart(2, "0") + ":" + String(sc).padStart(2, "0");
                        return String(m).padStart(2, "0") + ":" + String(sc).padStart(2, "0");
                    }}

                    function beep() {{
                        try {{
                            const ctx = new (window.AudioContext || window.webkitAudioContext)();
                            const osc = ctx.createOscillator();
                            const gain = ctx.createGain();
                            osc.connect(gain);
                            gain.connect(ctx.destination);
                            osc.frequency.value = 880;
                            gain.gain.setValueAtTime(0.4, ctx.currentTime);
                            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);
                            osc.start(ctx.currentTime);
                            osc.stop(ctx.currentTime + 0.6);
                        }} catch (e) {{}}
                    }}

                    function lockForm(message) {{
                        if (_locked) return;
                        _locked = true;
                        if (uploadForm) {{
                            uploadForm.querySelectorAll("input,select,textarea,button").forEach(function (el) {{
                                el.disabled = true;
                            }});
                        }}
                        if (lockNotice) lockNotice.style.display = "";
                        if (lockedBody && message) lockedBody.textContent = message;
                    }}

                    function unlockForm() {{
                        if (!_locked) return;
                        _locked = false;
                        if (uploadForm) {{
                            uploadForm.querySelectorAll("input,select,textarea,button").forEach(function (el) {{
                                el.disabled = false;
                            }});
                        }}
                        if (lockNotice) lockNotice.style.display = "none";
                    }}

                    function setTimerBar(cls, iconText, labelText, displayText) {{
                        timerBar.className = "exam-timer-sticky " + cls;
                        if (timerIcon) timerIcon.textContent = iconText;
                        if (timerLabel) timerLabel.textContent = labelText;
                        if (timerDisplay) timerDisplay.textContent = displayText || "";
                    }}

                    function showLateRequestSection(status) {{
                        _lateStatus = status;
                        if (!lateSection) return;
                        if (status === "pending") {{
                            if (lateBtn) lateBtn.style.display = "none";
                            if (lateStatusDiv) {{
                                lateStatusDiv.style.display = "";
                                lateStatusDiv.className = "late-request-status late-status-pending";
                                lateStatusDiv.textContent = "⌛ Request submitted. Waiting for teacher approval…";
                            }}
                        }} else if (status === "approved") {{
                            if (lateBtn) lateBtn.style.display = "none";
                            if (lateStatusDiv) {{
                                lateStatusDiv.style.display = "";
                                lateStatusDiv.className = "late-request-status late-status-approved";
                                lateStatusDiv.textContent = "Extra time approved! Please submit now.";
                            }}
                        }} else if (status === "rejected") {{
                            if (lateBtn) lateBtn.style.display = "none";
                            if (lateStatusDiv) {{
                                lateStatusDiv.style.display = "";
                                lateStatusDiv.className = "late-request-status late-status-rejected";
                                lateStatusDiv.textContent = "Extra time request was rejected by teacher.";
                            }}
                        }} else {{
                            if (lateBtn) lateBtn.style.display = "";
                            if (lateStatusDiv) lateStatusDiv.style.display = "none";
                        }}
                    }}

                    function updateTimerUI(d) {{
                        const phase = d.phase;
                        const rem = d.seconds_remaining;
                        const paused = d.is_paused;

                        if (phase === "not_set") {{
                            timerBar.className = "exam-timer-sticky exam-timer-bar-hidden";
                            return;
                        }}

                        if (phase === "before_exam") {{
                            setTimerBar("exam-timer-before", "⏳", "Exam starts in:", fmt(d.seconds_until_start) + (paused ? " (paused)" : ""));
                            if (warn10) warn10.classList.add("exam-warn-banner-hidden");
                            if (warn5) warn5.classList.add("exam-warn-banner-hidden");
                            return;
                        }}

                        if (phase === "extra_time") {{
                            setTimerBar("exam-timer-crit", "⏰", "Extra submission time:", fmt(rem));
                            unlockForm();
                            if (lockNotice) lockNotice.style.display = "none";
                            showLateRequestSection("approved");
                            return;
                        }}

                        if (phase === "ended") {{
                            setTimerBar("exam-timer-ended", "🔒", "Submission closed", "");
                            lockForm("The submission window has closed. You may request extra time below.");
                            // Check for pending late request via current status
                            if (lateSection && _lateStatus === null) {{
                                showLateRequestSection(null);
                            }}
                            return;
                        }}

                        // phase === "active"
                        if (rem !== null && rem <= 300 && !_warned5) {{
                            _warned5 = true;
                            if (warn5) warn5.classList.remove("exam-warn-banner-hidden");
                            beep();
                        }}
                        if (rem !== null && rem <= 600 && !_warned10) {{
                            _warned10 = true;
                            if (warn10) warn10.classList.remove("exam-warn-banner-hidden");
                        }}
                        if (warn5) {{
                            if (rem !== null && rem <= 300) warn5.classList.remove("exam-warn-banner-hidden");
                        }}
                        if (warn10) {{
                            if (rem !== null && rem <= 600 && rem > 300) warn10.classList.remove("exam-warn-banner-hidden");
                            else if (rem !== null && rem <= 300) warn10.classList.add("exam-warn-banner-hidden");
                        }}

                        if (rem !== null && rem <= 300) {{
                            setTimerBar("exam-timer-crit", "🔴", "Time remaining:", fmt(rem) + (paused ? " ⏸" : ""));
                        }} else if (rem !== null && rem <= 600) {{
                            setTimerBar("exam-timer-warn", "⚠️", "Time remaining:", fmt(rem) + (paused ? " ⏸" : ""));
                        }} else {{
                            setTimerBar("exam-timer-active", "⏱️", "Time remaining:", fmt(rem) + (paused ? " ⏸" : ""));
                        }}

                        if (_locked && _lateStatus !== "approved") {{
                            unlockForm();
                        }}
                    }}

                    async function pollTimer() {{
                        try {{
                            const url = "/api/student_timer?roll=" + encodeURIComponent(_roll) + "&token=" + encodeURIComponent(_token);
                            const resp = await fetch(url, {{cache: "no-store"}});
                            if (!resp.ok) return;
                            const d = await resp.json();
                            updateTimerUI(d);

                            // Sync late request status from timer
                            if (d.phase === "ended" && _lateStatus === null) {{
                                // Check if there's already a pending request
                            }} else if (d.phase === "extra_time" && _lateStatus !== "approved") {{
                                showLateRequestSection("approved");
                            }}
                        }} catch (e) {{}}
                    }}

                    window.doRequestExtraTime = async function () {{
                        if (lateBtn) lateBtn.disabled = true;
                        try {{
                            const resp = await fetch("/api/request_extra_time", {{
                                method: "POST",
                                headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
                                body: "roll_no=" + encodeURIComponent(_roll) + "&auth_token=" + encodeURIComponent(_token),
                            }});
                            const data = await resp.json();
                            if (data.ok) {{
                                showLateRequestSection(data.status || "pending");
                            }} else {{
                                if (lateBtn) lateBtn.disabled = false;
                            }}
                        }} catch (e) {{
                            if (lateBtn) lateBtn.disabled = false;
                        }}
                    }};

                    pollTimer();
                    setInterval(pollTimer, 2000);
                }})();
            </script>
        </body>
        """,
    )


def admin_home_page(navbar_html, current_paper_name, current_paper_time, students_url, admin_token):
    return admin_home_page_multi(
        navbar_html=navbar_html,
        students_url=students_url,
        admin_token=admin_token,
        paper_types=["A"],
        paper_rows_html=f"<tr><td>A</td><td>{current_paper_name}</td><td>{current_paper_time}</td></tr>",
    )


def admin_home_page_multi(navbar_html, students_url, admin_token, paper_types, paper_rows_html):
    file_inputs_html = "".join(
        f"""
        <div class="upload-type-item">
            <label class="small muted"><b>Paper Type {paper_type}</b></label>
            <input id="qp-files-{paper_type.lower()}" type="file" name="question_paper_file_{paper_type}" multiple required data-preview-target="qp-preview-{paper_type.lower()}">
            <div id="qp-preview-{paper_type.lower()}" class="file-preview-list file-preview-empty">No files selected yet.</div>
        </div>
        """
        for paper_type in paper_types
    )

    return _page(
        "Admin Panel",
        f"""
        <body class="bg-soft">
            {navbar_html}
            <main class="container-sm">
                <div class="card admin-hero-card">
                    <h2 class="title">Admin Home</h2>
                    <p class="muted">Use this page for paper setup, question material upload, and exam timer configuration.</p>
                </div>

                <!-- ── Exam Timer Setup ── -->
                <div class="card admin-section-card">
                    <h3 class="section-title">&#9201; Exam Timer</h3>
                    <p class="small muted">Set start and end times to control the student submission window.
                       The timer syncs in real-time across all connected students.</p>
                    <div id="current-timer-status" class="timer-status-display">
                        <span class="small muted">Loading timer status…</span>
                    </div>
                    <form method="POST" class="timer-set-form">
                        <input type="hidden" name="action" value="set_exam_timer">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <div class="timer-inputs-row">
                            <div class="timer-input-group">
                                <label class="small muted"><b>Exam Start</b></label>
                                <input type="datetime-local" name="exam_start" id="exam-start-input" required>
                            </div>
                            <div class="timer-input-group">
                                <label class="small muted"><b>Exam End</b></label>
                                <input type="datetime-local" name="exam_end" id="exam-end-input" required>
                            </div>
                        </div>
                        <div class="form-row timer-btn-row">
                            <input class="btn btn-primary" type="submit" value="Set Timer">
                            <button type="button" class="btn btn-secondary" id="timer-pause-btn" onclick="togglePause()">Pause</button>
                            <button type="button" class="btn btn-red" onclick="doResetTimer()">Reset Timer</button>
                        </div>
                    </form>
                    <form id="reset-timer-form" method="POST" style="display:none;">
                        <input type="hidden" name="action" value="reset_timer_full">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                    </form>
                </div>

                <div class="card admin-section-card">
                    <h3 class="section-title">Paper Type Setup</h3>
                    <p class="small muted">Set how many paper variants you want to run (A, B, C ...).</p>
                    <form method="POST" class="form-row form-row-tight">
                        <input type="hidden" name="action" value="update_paper_settings">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <label class="small muted" for="question-paper-count"><b>Number of Paper Types</b></label>
                        <input id="question-paper-count" class="paper-count-input" type="number" name="question_paper_count" min="1" max="26" value="{len(paper_types)}">
                        <input class="btn btn-primary" type="submit" value="Apply">
                    </form>
                    <div class="info-box">
                        <div class="small muted"><b>Current Paper Types:</b> {", ".join(paper_types)}</div>
                        <div class="small muted">Each type is saved in a separate folder under <code>question_paper/</code>.</div>
                        <div class="small muted">You can upload multiple files per type (question PDF + datasets + any extra material).</div>
                    </div>
                </div>

                <div class="card admin-section-card">
                    <h3 class="section-title">Upload Question Paper Materials</h3>
                    <div class="table-wrap">
                        <table>
                            <tr><th>Paper Type</th><th>Latest File</th><th>Last Updated</th></tr>
                            {paper_rows_html}
                        </table>
                    </div>
                    <form method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="action" value="upload_question_paper">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <div class="upload-type-grid">
                            {file_inputs_html}
                        </div>
                        <input class="btn btn-primary" type="submit" value="Upload Materials">
                    </form>
                </div>
            </main>
            <script>
                (function () {{
                    // ── File previews ──────────────────────────────────────────
                    const inputs = document.querySelectorAll(".upload-type-item input[type='file'][data-preview-target]");
                    inputs.forEach(function (input) {{
                        const targetId = input.getAttribute("data-preview-target");
                        const preview = document.getElementById(targetId);
                        if (!preview) return;
                        input.addEventListener("change", function () {{
                            const files = Array.from(input.files || []);
                            if (files.length === 0) {{
                                preview.classList.add("file-preview-empty");
                                preview.innerHTML = "No files selected yet.";
                                return;
                            }}
                            preview.classList.remove("file-preview-empty");
                            preview.innerHTML = files.map(function (f, idx) {{
                                return "<div>" + (idx + 1) + ". " + String(f.name) + "</div>";
                            }}).join("");
                        }});
                    }});

                    // ── Timer status display ──────────────────────────────────
                    const adminToken = {json.dumps(admin_token)};
                    const pauseBtn = document.getElementById("timer-pause-btn");
                    const statusDiv = document.getElementById("current-timer-status");
                    const startInput = document.getElementById("exam-start-input");
                    const endInput = document.getElementById("exam-end-input");

                    function fmt(s) {{
                        if (s === null || s === undefined) return "--:--";
                        const h = Math.floor(s / 3600);
                        const m = Math.floor((s % 3600) / 60);
                        const sc = s % 60;
                        if (h > 0) return h + ":" + String(m).padStart(2,"0") + ":" + String(sc).padStart(2,"0");
                        return String(m).padStart(2,"0") + ":" + String(sc).padStart(2,"0");
                    }}

                    function epochToLocal(epoch) {{
                        if (!epoch) return "";
                        const d = new Date(epoch * 1000);
                        const pad = n => String(n).padStart(2,"0");
                        return d.getFullYear() + "-" + pad(d.getMonth()+1) + "-" + pad(d.getDate()) +
                               "T" + pad(d.getHours()) + ":" + pad(d.getMinutes());
                    }}

                    async function fetchTimerAndUpdate() {{
                        try {{
                            const resp = await fetch("/api/timer", {{cache: "no-store"}});
                            if (!resp.ok) return;
                            const d = await resp.json();
                            // Update pause button label
                            if (pauseBtn) pauseBtn.textContent = d.is_paused ? "Resume" : "Pause";
                            // Populate date inputs if not currently focused
                            if (startInput && !document.activeElement === startInput && d.start_time) {{
                                startInput.value = epochToLocal(d.start_time);
                            }}
                            if (endInput && !document.activeElement === endInput && d.end_time) {{
                                endInput.value = epochToLocal(d.end_time);
                            }}
                            // Update status pill
                            let cls = "timer-pill-notset";
                            let label = "No timer set";
                            if (d.phase === "before_exam") {{ cls = "timer-pill-before"; label = "Starts in " + fmt(d.seconds_until_start) + (d.is_paused ? " ⏸" : ""); }}
                            else if (d.phase === "active") {{ cls = "timer-pill-active"; label = "Active — " + fmt(d.seconds_remaining) + " remaining" + (d.is_paused ? " ⏸ PAUSED" : ""); }}
                            else if (d.phase === "extra_time") {{ cls = "timer-pill-active"; label = "Extra time — " + fmt(d.seconds_remaining); }}
                            else if (d.phase === "ended") {{ cls = "timer-pill-ended"; label = "Exam ended"; }}
                            if (statusDiv) statusDiv.innerHTML = "<span class='timer-pill " + cls + "'>" + label + "</span>";
                        }} catch (e) {{}}
                    }}

                    window.togglePause = async function () {{
                        try {{
                            const resp = await fetch("/api/timer", {{cache: "no-store"}});
                            const current = await resp.json();
                            const action = current.is_paused ? "resume" : "pause";
                            await fetch("/api/timer_control", {{
                                method: "POST",
                                headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
                                body: "admin_token=" + encodeURIComponent(adminToken) + "&action=" + action,
                            }});
                            fetchTimerAndUpdate();
                        }} catch (e) {{}}
                    }};

                    window.doResetTimer = function () {{
                        if (!confirm("Reset the exam timer? Students will no longer see a countdown.")) return;
                        document.getElementById("reset-timer-form").submit();
                    }};

                    fetchTimerAndUpdate();
                    setInterval(fetchTimerAndUpdate, 4000);
                }})();
            </script>
        </body>
        """,
    )


def question_materials_page(student_name, roll, paper_type, rows_html, back_url):
    return _page(
        "Question Materials",
        f"""
        <body class="bg-soft">
            <main class="container">
                <div class="card">
                    <h2 class="title">Question Materials</h2>
                    <p class="muted">Student: <b>{student_name}</b> ({roll})</p>
                    <p class="muted"><b>Assigned Paper Type:</b> {paper_type}</p>
                    <div class="form-row justify-end">
                        <a class="btn-link btn-secondary" href="{back_url}">Back</a>
                        <a class="btn-link btn-danger" href="/">Logout</a>
                    </div>
                    <div class="table-wrap">
                        <table>
                            <tr>
                                <th>File</th><th>Type</th><th>Size (KB)</th><th>Action</th>
                            </tr>
                            {rows_html}
                        </table>
                    </div>
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
    paper_types,
    current_instructions="",
):
    ext_items = []
    for ext in available_extensions:
        checked = "checked" if ext in selected_extensions else ""
        ext_items.append(
            f'<label class="ext-item"><input type="checkbox" name="allowed_extensions" value="{ext}" {checked}>'
            f'<span class="ext-label">{ext}</span></label>'
        )
    ext_html = "".join(ext_items)

    return _page(
        "Student Management",
        f"""
        <body class="bg-soft">
            {navbar_html}
            <main class="container">
                <div class="card admin-section-card">
                    <h2 class="title">Student Management</h2>
                    <p class="small muted">Configure submission rules, extension policy, password reset, and student status from separate sections.</p>
                </div>

                <div id="actions" class="card admin-section-card">
                    <h3 class="section-title">Submission Rules</h3>
                    <div class="form-row">
                        <form method="POST" class="form-row">
                            <span class="small muted">Max Files</span>
                            <input class="max-files-input" type="number" name="max_files" value="{max_files}">
                            <input type="hidden" name="action" value="update_settings">
                            <input type="hidden" name="admin_token" value="{admin_token}">
                            <input class="btn btn-primary" type="submit" value="Update">
                        </form>
                    </div>
                </div>

                <div class="card admin-section-card">
                    <h3 class="section-title">Submission Instructions</h3>
                    <p class="small muted">These instructions are shown to students on the submission page. Leave blank to use the default.</p>
                    <form method="POST" class="form-row form-col">
                        <input type="hidden" name="action" value="update_instructions">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <textarea name="instructions" rows="4"
                            style="width:100%;box-sizing:border-box;padding:8px;border-radius:6px;border:1px solid var(--border);background:var(--input-bg);color:var(--text);font-size:14px;resize:vertical;"
                            placeholder="Enter instructions for students…">{html.escape(current_instructions)}</textarea>
                        <div style="margin-top:6px;">
                            <input class="btn btn-primary" type="submit" value="Save Instructions">
                        </div>
                    </form>
                </div>

                <div class="card admin-section-card">
                    <h3 class="section-title">Allowed Extensions</h3>
                    <p class="small muted">
                        Tick the small boxes next to each extension you want to allow, then click <b>Apply Extensions</b>.
                    </p>
                    <form method="POST" class="form-row form-col extensions-form">
                        <input type="hidden" name="action" value="update_extensions">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <div class="small muted section-label"><b>Allowed file types</b></div>
                        <div class="ext-grid ext-grid-admin" role="group" aria-label="Allowed file extensions">
                            {ext_html}
                        </div>
                        <input class="btn btn-primary" type="submit" value="Apply Extensions">
                    </form>
                </div>

                <div class="card admin-section-card danger-zone">
                    <h3 class="section-title">Password Reset</h3>
                    <p class="small muted">Individual passwords update instantly (no page reload). Reset All requires confirmation.</p>
                    <form method="POST" class="form-row form-col" onsubmit="return confirm('Are you sure you want to reset passwords for all users?');">
                        <input type="hidden" name="action" value="reset_all_users">
                        <input type="hidden" name="admin_token" value="{admin_token}">
                        <label class="small muted">
                            <input type="checkbox" name="confirm_reset_all" value="yes" required>
                            I understand this will reset every student's password.
                        </label>
                        <input class="btn btn-red" type="submit" value="Reset All Passwords">
                    </form>
                </div>

                <div class="card admin-section-card">
                    <h3 class="section-title">Student Credentials &amp; Status</h3>
                    <div class="table-wrap table-wrap-sticky">
                        <table class="admin-students-table">
                            <colgroup>
                                <col class="col-sno">
                                <col class="col-roll">
                                <col class="col-name">
                                <col class="col-password">
                                <col class="col-paper">
                                <col class="col-status">
                                <col class="col-ip">
                                <col class="col-files">
                                <col class="col-action">
                            </colgroup>
                            <tr>
                                <th>S#</th><th>Roll</th><th>Name</th><th>Password</th><th>Paper Type</th><th>Status</th><th>Last IP</th><th>Files</th><th>Action</th>
                            </tr>
                            {rows_html}
                        </table>
                    </div>
                </div>
            </main>
            <script>
                (function () {{
                    const adminToken = {json.dumps(admin_token)};

                    window.resetPasswordAsync = function (roll, btn) {{
                        if (!confirm("Reset password for " + roll + "?")) return;
                        btn.disabled = true;
                        btn.textContent = "…";
                        const row = btn.closest("tr[data-roll]");
                        fetch("/api/reset_password", {{
                            method: "POST",
                            headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
                            body: "admin_token=" + encodeURIComponent(adminToken) +
                                  "&target_roll=" + encodeURIComponent(roll),
                        }})
                        .then(function (r) {{ return r.json(); }})
                        .then(function (data) {{
                            btn.disabled = false;
                            btn.textContent = "Reset";
                            if (data.ok && row) {{
                                const pwCell = row.querySelector(".pw-cell");
                                if (pwCell) {{
                                    pwCell.textContent = data.new_password;
                                    pwCell.classList.add("pw-flash");
                                    setTimeout(function () {{ pwCell.classList.remove("pw-flash"); }}, 1800);
                                }}
                            }}
                        }})
                        .catch(function () {{
                            btn.disabled = false;
                            btn.textContent = "Reset";
                        }});
                    }};
                }})();
            </script>
        </body>
        """,
    )


def admin_dashboard_page(
    navbar_html,
    rows_html,
    admin_token="",
    submitted_count=0,
    pending_count=0,
    total_count=0,
):
    return _page(
        "Submission Dashboard",
        f"""
        <body class="bg-soft">
            {navbar_html}
            <main class="container">

                <!-- ── Active Exam Timer card ── -->
                <div class="card admin-section-card" id="dash-timer-card">
                    <div class="dash-section-head">
                        <h3 class="section-title no-margin">&#9201; Active Exam Timer</h3>
                        <div id="dash-timer-pill" class="timer-pill timer-pill-notset">Loading…</div>
                    </div>
                    <div class="dash-timer-controls form-row" style="margin-top:10px;">
                        <button class="btn btn-secondary" id="dash-pause-btn" onclick="dashTogglePause()">Pause</button>
                        <span class="small muted" id="dash-timer-detail"></span>
                    </div>
                </div>

                <!-- ── Late Submission Requests card ── -->
                <div class="card admin-section-card" id="dash-late-card">
                    <h3 class="section-title">Late Submission Requests</h3>
                    <div id="dash-late-empty" class="small muted" style="display:none;">No pending requests.</div>
                    <div class="table-wrap" id="dash-late-table-wrap" style="display:none;">
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th><th>Roll</th><th>Submitted</th>
                                    <th>Requested At</th><th>Status</th><th>Action</th>
                                </tr>
                            </thead>
                            <tbody id="dash-late-tbody"></tbody>
                        </table>
                    </div>
                </div>

                <!-- ── Submission Stats / Student Table ── -->
                <div class="card admin-section-card">
                    <h2 class="title">Submission Dashboard</h2>
                    <p class="small muted" id="dash-refresh-note">Auto-refreshes in background every 5 s without disrupting your view.</p>
                    <div class="dashboard-stats" role="region" aria-label="Submission counts">
                        <div class="stat-tile">
                            <div class="stat-tile-value" id="stat-total">{total_count}</div>
                            <div class="stat-tile-label">Total students</div>
                        </div>
                        <div class="stat-tile stat-tile-submitted">
                            <div class="stat-tile-value" id="stat-submitted">{submitted_count}</div>
                            <div class="stat-tile-label">Submitted</div>
                        </div>
                        <div class="stat-tile stat-tile-pending">
                            <div class="stat-tile-value" id="stat-pending">{pending_count}</div>
                            <div class="stat-tile-label">Pending</div>
                        </div>
                    </div>
                    <div class="dashboard-toolbar form-row">
                        <label class="small muted" for="dash-filter"><b>Show</b></label>
                        <select id="dash-filter" class="dashboard-filter" aria-label="Filter dashboard rows">
                            <option value="all">All students</option>
                            <option value="submitted">Submitted only</option>
                            <option value="pending">Pending only</option>
                        </select>
                        <span id="dash-showing" class="small muted"></span>
                        <span id="dash-last-updated" class="small muted" style="margin-left:auto;"></span>
                    </div>
                    <div class="table-wrap table-wrap-sticky" id="dash-table-wrap">
                        <table class="admin-dashboard-table">
                            <thead>
                                <tr>
                                    <th>Name</th><th>Roll</th><th>IP Address</th><th>Timestamp</th><th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="dashboard-tbody">
                                {rows_html}
                            </tbody>
                        </table>
                    </div>
                </div>
            </main>
            <script>
                (function() {{
                    const FILTER_KEY = "portal_dashboard_filter";
                    const adminToken = {json.dumps(admin_token)};
                    const tbody = document.getElementById("dashboard-tbody");
                    const sel = document.getElementById("dash-filter");
                    const showing = document.getElementById("dash-showing");
                    const lastUpdated = document.getElementById("dash-last-updated");
                    const tableWrap = document.getElementById("dash-table-wrap");
                    const pauseBtn = document.getElementById("dash-pause-btn");
                    const timerPill = document.getElementById("dash-timer-pill");
                    const timerDetail = document.getElementById("dash-timer-detail");
                    const lateEmpty = document.getElementById("dash-late-empty");
                    const lateTableWrap = document.getElementById("dash-late-table-wrap");
                    const lateTbody = document.getElementById("dash-late-tbody");

                    let totalCount = {total_count};

                    // ── Filter ────────────────────────────────────────────────
                    function applyFilter() {{
                        const mode = sel ? sel.value : "all";
                        const rows = tbody ? tbody.querySelectorAll("tr.dashboard-row") : [];
                        let visible = 0;
                        rows.forEach(function(tr) {{
                            const st = tr.getAttribute("data-status") || "";
                            const ok = mode === "all" || mode === st;
                            tr.style.display = ok ? "" : "none";
                            if (ok) visible += 1;
                        }});
                        if (!showing) return;
                        if (mode === "all") {{
                            showing.textContent = "Showing all " + totalCount + " students.";
                        }} else {{
                            showing.textContent = "Showing " + visible + " of " + totalCount + " (" + mode + " only).";
                        }}
                    }}

                    try {{
                        const saved = sessionStorage.getItem(FILTER_KEY);
                        if (saved === "all" || saved === "submitted" || saved === "pending") {{
                            if (sel) sel.value = saved;
                        }}
                    }} catch (e) {{}}

                    if (sel) {{
                        sel.addEventListener("change", function() {{
                            try {{ sessionStorage.setItem(FILTER_KEY, sel.value); }} catch (e) {{}}
                            applyFilter();
                        }});
                    }}
                    applyFilter();

                    // ── Escape HTML ───────────────────────────────────────────
                    function esc(s) {{
                        return String(s)
                            .replace(/&/g,"&amp;").replace(/</g,"&lt;")
                            .replace(/>/g,"&gt;").replace(/"/g,"&quot;")
                            .replace(/'/g,"&#39;");
                    }}

                    // ── Build table row HTML ──────────────────────────────────
                    function buildRows(rows) {{
                        return rows.map(function(r) {{
                            const sc = r.status === "submitted" ? "status-green" : "status-red";
                            const label = r.status === "submitted" ? "Submitted" : "Pending";
                            let nameCell;
                            if (r.status === "submitted") {{
                                nameCell = "<span class='dash-folder-link' " +
                                    "onclick='openSubmissionFolder(" + JSON.stringify(esc(r.roll)) + ")' " +
                                    "title='Click to open submission folder on server'>" +
                                    esc(r.name) + "</span>";
                            }} else {{
                                nameCell = esc(r.name);
                            }}
                            return "<tr class='dashboard-row' data-status='" + esc(r.status) + "'>" +
                                "<td>" + nameCell + "</td><td>" + esc(r.roll) + "</td>" +
                                "<td>" + esc(r.ip) + "</td><td>" + esc(r.time) + "</td>" +
                                "<td><span class='" + sc + "'>" + label + "</span></td>" +
                                "</tr>";
                        }}).join("");
                    }}

                    // ── Format seconds ────────────────────────────────────────
                    function fmt(s) {{
                        if (s === null || s === undefined) return "--:--";
                        const h = Math.floor(s / 3600);
                        const m = Math.floor((s % 3600) / 60);
                        const sc = s % 60;
                        if (h > 0) return h + ":" + String(m).padStart(2,"0") + ":" + String(sc).padStart(2,"0");
                        return String(m).padStart(2,"0") + ":" + String(sc).padStart(2,"0");
                    }}

                    // ── Update timer UI ───────────────────────────────────────
                    function updateTimerUI(d) {{
                        if (!timerPill) return;
                        if (pauseBtn) pauseBtn.textContent = d.is_paused ? "Resume" : "Pause";
                        timerPill.className = "timer-pill";
                        if (d.phase === "not_set") {{
                            timerPill.classList.add("timer-pill-notset");
                            timerPill.textContent = "No timer set";
                            if (timerDetail) timerDetail.textContent = "";
                        }} else if (d.phase === "before_exam") {{
                            timerPill.classList.add("timer-pill-before");
                            timerPill.textContent = "Starts in " + fmt(d.seconds_until_start);
                            if (timerDetail) timerDetail.textContent = d.is_paused ? "⏸ Paused" : "";
                        }} else if (d.phase === "active") {{
                            timerPill.classList.add("timer-pill-active");
                            timerPill.textContent = fmt(d.seconds_remaining) + " remaining";
                            if (timerDetail) timerDetail.textContent = d.is_paused ? "⏸ Paused" : "";
                        }} else if (d.phase === "ended") {{
                            timerPill.classList.add("timer-pill-ended");
                            timerPill.textContent = "Exam ended";
                            if (timerDetail) timerDetail.textContent = "";
                        }}
                    }}

                    // ── Build late requests table ─────────────────────────────
                    function updateLateRequests(reqs) {{
                        if (!reqs || reqs.length === 0) {{
                            if (lateEmpty) lateEmpty.style.display = "";
                            if (lateTableWrap) lateTableWrap.style.display = "none";
                            return;
                        }}
                        if (lateEmpty) lateEmpty.style.display = "none";
                        if (lateTableWrap) lateTableWrap.style.display = "";
                        if (!lateTbody) return;
                        lateTbody.innerHTML = reqs.map(function(r) {{
                            const reqTime = r.requested_at ? new Date(r.requested_at * 1000).toLocaleString() : "-";
                            const submittedLabel = r.submitted ? "<span class='status-green'>Yes</span>" : "<span class='status-red'>No</span>";
                            let statusLabel = r.status;
                            let actions = "";
                            if (r.status === "pending") {{
                                statusLabel = "<b class='status-orange'>Pending</b>";
                                actions = "<button class='btn btn-primary btn-xs' onclick='handleRequest(" +
                                    JSON.stringify(esc(r.roll)) + "," + JSON.stringify("approve") + ")'>Approve</button> " +
                                    "<button class='btn btn-red btn-xs' onclick='handleRequest(" +
                                    JSON.stringify(esc(r.roll)) + "," + JSON.stringify("reject") + ")'>Reject</button>";
                            }} else if (r.status === "approved") {{
                                statusLabel = "<span class='status-green'>Approved</span>";
                            }} else {{
                                statusLabel = "<span class='status-red'>Rejected</span>";
                            }}
                            return "<tr>" +
                                "<td>" + esc(r.name) + "</td><td>" + esc(r.roll) + "</td>" +
                                "<td>" + submittedLabel + "</td><td>" + esc(reqTime) + "</td>" +
                                "<td>" + statusLabel + "</td><td>" + actions + "</td>" +
                                "</tr>";
                        }}).join("");
                    }}

                    window.handleRequest = async function(roll, decision) {{
                        try {{
                            const resp = await fetch("/api/handle_late_request", {{
                                method: "POST",
                                headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
                                body: "admin_token=" + encodeURIComponent(adminToken) +
                                      "&roll=" + encodeURIComponent(roll) +
                                      "&decision=" + encodeURIComponent(decision),
                            }});
                            const data = await resp.json();
                            if (data.ok) refreshData();
                        }} catch (e) {{}}
                    }};

                    window.openSubmissionFolder = async function(roll) {{
                        try {{
                            const resp = await fetch(
                                "/admin_open_folder?token=" + encodeURIComponent(adminToken) +
                                "&roll=" + encodeURIComponent(roll),
                                {{cache: "no-store"}}
                            );
                            const data = await resp.json();
                            if (!data.ok) {{
                                alert("Could not open folder: " + (data.error || "Unknown error"));
                            }}
                        }} catch (e) {{
                            alert("Could not reach server.");
                        }}
                    }};

                    window.dashTogglePause = async function() {{
                        try {{
                            const r1 = await fetch("/api/timer", {{cache: "no-store"}});
                            const cur = await r1.json();
                            const act = cur.is_paused ? "resume" : "pause";
                            await fetch("/api/timer_control", {{
                                method: "POST",
                                headers: {{"Content-Type": "application/x-www-form-urlencoded"}},
                                body: "admin_token=" + encodeURIComponent(adminToken) + "&action=" + act,
                            }});
                            refreshData();
                        }} catch (e) {{}}
                    }};

                    // ── Background refresh (scroll-preserving) ────────────────
                    async function refreshData() {{
                        try {{
                            const url = "/admin_dashboard_data?token=" + encodeURIComponent(adminToken);
                            const resp = await fetch(url, {{cache: "no-store"}});
                            if (resp.status === 401) {{
                                // Session expired — redirect to login
                                window.location.href = "/";
                                return;
                            }}
                            if (!resp.ok) return;
                            const data = await resp.json();
                            if (!data.ok) return;

                            // Update stats
                            totalCount = data.total_count;
                            const el = (id) => document.getElementById(id);
                            if (el("stat-total")) el("stat-total").textContent = data.total_count;
                            if (el("stat-submitted")) el("stat-submitted").textContent = data.submitted_count;
                            if (el("stat-pending")) el("stat-pending").textContent = data.pending_count;

                            // Update timer
                            if (data.timer) updateTimerUI(data.timer);

                            // Update late requests
                            if (data.late_requests) updateLateRequests(data.late_requests);

                            // Update student table — preserve scroll position
                            if (tbody && data.rows) {{
                                const scrollTop = tableWrap ? tableWrap.scrollTop : 0;
                                const scrollLeft = tableWrap ? tableWrap.scrollLeft : 0;
                                tbody.innerHTML = buildRows(data.rows);
                                if (tableWrap) {{
                                    tableWrap.scrollTop = scrollTop;
                                    tableWrap.scrollLeft = scrollLeft;
                                }}
                                applyFilter();
                            }}

                            // Update last-refreshed label
                            if (lastUpdated) {{
                                const now = new Date();
                                lastUpdated.textContent = "Updated " + now.toLocaleTimeString();
                            }}
                        }} catch (e) {{ console.error("Dashboard refresh error:", e); }}
                    }}

                    refreshData();
                    setInterval(refreshData, 5000);
                }})();
            </script>
        </body>
        """,
    )
