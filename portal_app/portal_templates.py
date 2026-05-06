import html


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


def student_home_page(name, roll, view_qp_url, submit_url, games_url):
    return _page(
        "Student Portal",
        f"""
        <body class="bg-soft">
            <div class="container-student container-games">
                <div class="panel-head">
                    <h2 class="title">Student Assessment Portal</h2>
                    <p class="muted text-on-dark no-margin">Welcome, {name} ({roll})</p>
                </div>
                <div class="panel-body">
                    <div class="form-row justify-end">
                        <a class="btn-link btn-teal" href="{games_url}">Play Game</a>
                        <a class="btn-link btn-danger" href="/">Logout</a>
                    </div>
                    <p class="muted">
                        Step 1: View question paper and attached materials.<br>
                        Step 2: Prepare your solution and submit final files.
                    </p>
                    <div class="form-row">
                        <a class="btn-link btn-purple" href="{view_qp_url}">View Materials</a>
                        <a class="btn-link btn-primary" href="{submit_url}">Submit Solution</a>
                    </div>
                </div>
            </div>
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
                    }};
                    const leaderboardEls = {{
                        snake: document.getElementById("snake-leaderboard"),
                        flappy: document.getElementById("flappy-leaderboard"),
                    }};
                    let activeGame = "snake";

                    function showGame(name) {{
                        activeGame = name;
                        panels.snake.hidden = name !== "snake";
                        panels.flappy.hidden = name !== "flappy";
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
                    }});

                    snakeReset();
                    flappyReset();
                    snakeDraw();
                    flappyDraw();
                    refreshLeaderboard("snake");
                    refreshLeaderboard("flappy");
                    setInterval(function () {{
                        refreshLeaderboard(activeGame);
                    }}, 15000);
                }})();
            </script>
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
                    <p class="muted text-on-dark no-margin">Welcome, {name} ({roll})</p>
                </div>
                <div class="panel-body">
                    <div class="form-row justify-end">
                        <a class="btn-link btn-secondary" href="/student?roll={roll}&token={token}">Back</a>
                        <a class="btn-link btn-danger" href="/">Logout</a>
                    </div>
                    <div class="info-box info-box-blue">
                        <b>Instructions:</b> You can upload up to {max_files} file(s). Allowed types: {allowed_ext_csv}.
                    </div>
                    <form method="POST" enctype="multipart/form-data" onsubmit="return confirm('Are you sure you want to submit? You will not be able to upload again.');">
                        <input type="hidden" name="action" value="upload">
                        <input type="hidden" name="roll_no" value="{roll}">
                        <input type="hidden" name="auth_token" value="{token}">
                        <label><b>Select Files</b></label><br>
                        <input id="student-lab-files" type="file" name="lab_files" multiple required>
                        <div id="student-file-preview" class="file-preview-list file-preview-empty">No files selected yet.</div><br>
                        <label class="muted">
                            <input type="checkbox" name="confirm_submit" value="yes" required>
                            I confirm this is my final submission.
                        </label><br><br>
                        <input class="btn btn-primary" type="submit" value="Submit Final Files">
                    </form>
                </div>
            </div>
            <script>
                (function () {{
                    const input = document.getElementById("student-lab-files");
                    const preview = document.getElementById("student-file-preview");
                    if (!input || !preview) return;
                    input.addEventListener("change", function () {{
                        const files = Array.from(input.files || []);
                        if (files.length === 0) {{
                            preview.classList.add("file-preview-empty");
                            preview.innerHTML = "No files selected yet.";
                            return;
                        }}
                        preview.classList.remove("file-preview-empty");
                        preview.innerHTML = files
                            .map(function (f, idx) {{
                                return "<div>" + (idx + 1) + ". " + String(f.name) + "</div>";
                            }})
                            .join("");
                    }});
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
                    <p class="muted">Use this page for paper setup and question material upload. Other controls are available in the navbar.</p>
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
                    const inputs = document.querySelectorAll(".upload-type-item input[type='file'][data-preview-target]");
                    if (!inputs.length) return;
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
                            preview.innerHTML = files
                                .map(function (f, idx) {{
                                    return "<div>" + (idx + 1) + ". " + String(f.name) + "</div>";
                                }})
                                .join("");
                        }});
                    }});
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
                    <p class="small muted">Use this carefully. It updates passwords immediately.</p>
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
                    <h3 class="section-title">Student Credentials & Status</h3>
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
        </body>
        """,
    )


def admin_dashboard_page(
    navbar_html,
    rows_html,
    refresh_seconds=5,
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
                <div class="card admin-section-card">
                    <h2 class="title">Submission Dashboard</h2>
                    <p class="small muted">Summary updates every {refresh_seconds}s with page refresh. Filter choice is remembered until you close the tab.</p>
                    <div class="dashboard-stats" role="region" aria-label="Submission counts">
                        <div class="stat-tile">
                            <div class="stat-tile-value">{total_count}</div>
                            <div class="stat-tile-label">Total students</div>
                        </div>
                        <div class="stat-tile stat-tile-submitted">
                            <div class="stat-tile-value">{submitted_count}</div>
                            <div class="stat-tile-label">Submitted</div>
                        </div>
                        <div class="stat-tile stat-tile-pending">
                            <div class="stat-tile-value">{pending_count}</div>
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
                    </div>
                    <div class="table-wrap table-wrap-sticky">
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
                    const STORAGE_KEY = "portal_dashboard_filter";
                    const tbody = document.getElementById("dashboard-tbody");
                    const sel = document.getElementById("dash-filter");
                    const showing = document.getElementById("dash-showing");
                    const total = {total_count};
                    if (!tbody || !sel || !showing) return;

                    function applyFilter() {{
                        const mode = sel.value;
                        const rows = tbody.querySelectorAll("tr.dashboard-row");
                        let visible = 0;
                        rows.forEach(function(tr) {{
                            const st = tr.getAttribute("data-status") || "";
                            const ok = mode === "all" || mode === st;
                            tr.style.display = ok ? "" : "none";
                            if (ok) visible += 1;
                        }});
                        if (mode === "all") {{
                            showing.textContent = "Showing all " + total + " students.";
                        }} else {{
                            const label = mode === "submitted" ? "submitted" : "pending";
                            showing.textContent = "Showing " + visible + " of " + total + " (" + label + " only).";
                        }}
                    }}

                    try {{
                        const saved = sessionStorage.getItem(STORAGE_KEY);
                        if (saved === "all" || saved === "submitted" || saved === "pending") {{
                            sel.value = saved;
                        }}
                    }} catch (e) {{}}

                    sel.addEventListener("change", function() {{
                        try {{ sessionStorage.setItem(STORAGE_KEY, sel.value); }} catch (e) {{}}
                        applyFilter();
                    }});
                    applyFilter();
                }})();
            </script>
        </body>
        """,
        auto_refresh_seconds=refresh_seconds,
    )
