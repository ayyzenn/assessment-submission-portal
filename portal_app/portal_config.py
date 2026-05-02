PORT = 8080

EXCEL_FILE = "students.xlsx"
UPLOAD_BASE_DIR = "submissions"
LOG_FILE = "submission_logs.csv"
QUESTION_PAPER_DIR = "question_paper"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

PASSWORD_LENGTH = 8
SESSION_TTL_SECONDS = 2 * 60 * 60

ALLOWED_EXTENSIONS = {".txt", ".pdf"} # Allowed extensions for the submissions

AVAILABLE_EXTENSIONS = sorted(
    {
        ".txt", ".md", ".rtf", ".pdf", ".doc", ".docx", ".odt",
        ".csv", ".tsv", ".xls", ".xlsx", ".ods",
        ".ppt", ".pptx",
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
        ".mp3", ".wav", ".aac",
        ".mp4", ".mkv", ".mov", ".avi",
        ".py", ".ipynb", ".sh", ".bat", ".ps1",
        ".c", ".h", ".cpp", ".hpp", ".java", ".js", ".ts", ".go", ".rs", ".php", ".rb",
        ".asm", ".sql", ".json", ".xml", ".yaml", ".yml", ".toml", ".ini",
        ".log", ".cfg",
    }
)

CONFIG = {
    "max_files": 2,
    "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
    "question_paper_count": 1,
}
