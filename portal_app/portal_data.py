import os
from typing import Optional

import pandas as pd

from .portal_config import EXCEL_FILE, LOG_FILE, QUESTION_PAPER_DIR, UPLOAD_BASE_DIR
from .portal_security import generate_password


def ensure_directories() -> None:
    os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
    os.makedirs(QUESTION_PAPER_DIR, exist_ok=True)


def normalize_student_data(df: pd.DataFrame) -> pd.DataFrame:
    if "Roll No." not in df.columns and "Roll Number" in df.columns:
        df = df.rename(columns={"Roll Number": "Roll No."})
    if "Student Name" not in df.columns and "Name" in df.columns:
        df = df.rename(columns={"Name": "Student Name"})

    if "Roll No." not in df.columns:
        df["Roll No."] = ""
    if "Student Name" not in df.columns:
        df["Student Name"] = ""
    if "Password" not in df.columns:
        df["Password"] = ""

    df["Roll No."] = df["Roll No."].fillna("").astype(str)
    df["Student Name"] = df["Student Name"].fillna("").astype(str)
    df["Password"] = df["Password"].fillna("").astype(str)
    return df


def load_data() -> pd.DataFrame:
    if not os.path.exists(EXCEL_FILE):
        pd.DataFrame(
            {"Roll No.": ["101"], "Student Name": ["Student 1"], "Password": [""]}
        ).to_excel(EXCEL_FILE, index=False)

    df = normalize_student_data(pd.read_excel(EXCEL_FILE))
    missing_pw_mask = df["Password"].astype(str).str.strip() == ""
    if missing_pw_mask.any():
        for idx in df[missing_pw_mask].index:
            df.at[idx, "Password"] = generate_password()
        df.to_excel(EXCEL_FILE, index=False)
    return df


def save_data(df: pd.DataFrame) -> None:
    df.to_excel(EXCEL_FILE, index=False)


def load_logs() -> pd.DataFrame:
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        return pd.DataFrame(columns=["Roll No.", "IP Address"])

    logs = pd.read_csv(LOG_FILE)
    if "Roll No." not in logs.columns:
        logs["Roll No."] = ""
    if "IP Address" not in logs.columns:
        logs["IP Address"] = "Unknown"
    return logs


def log_submission(roll: str, ip: str) -> None:
    log_entry = pd.DataFrame(
        [{"Timestamp": pd.Timestamp.now(), "Roll No.": str(roll), "IP Address": ip}]
    )
    header = not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0
    log_entry.to_csv(LOG_FILE, mode="a", index=False, header=header)


def has_student_submitted(roll: str) -> bool:
    return os.path.exists(os.path.join(UPLOAD_BASE_DIR, str(roll)))


def student_submission_files(roll: str) -> list[str]:
    student_path = os.path.join(UPLOAD_BASE_DIR, str(roll))
    try:
        if os.path.exists(student_path):
            return os.listdir(student_path)
    except OSError:
        return []
    return []


def save_student_files(roll: str, file_items, allowed_extensions: set[str]) -> int:
    student_dir = os.path.join(UPLOAD_BASE_DIR, str(roll))
    os.makedirs(student_dir, exist_ok=True)
    uploaded_count = 0
    for item in file_items:
        if hasattr(item, "filename") and item.filename:
            ext = os.path.splitext(item.filename)[1].lower()
            if ext in allowed_extensions:
                filepath = os.path.join(student_dir, os.path.basename(item.filename))
                with open(filepath, "wb") as out:
                    out.write(item.file.read())
                uploaded_count += 1
    return uploaded_count


def latest_question_paper_path() -> Optional[str]:
    if not os.path.isdir(QUESTION_PAPER_DIR):
        return None
    files = []
    for name in os.listdir(QUESTION_PAPER_DIR):
        path = os.path.join(QUESTION_PAPER_DIR, name)
        if os.path.isfile(path):
            files.append(path)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def list_question_paper_files() -> list[dict]:
    if not os.path.isdir(QUESTION_PAPER_DIR):
        return []

    files = []
    for name in os.listdir(QUESTION_PAPER_DIR):
        path = os.path.join(QUESTION_PAPER_DIR, name)
        if os.path.isfile(path):
            files.append(
                {
                    "name": name,
                    "path": path,
                    "size_bytes": os.path.getsize(path),
                    "modified_ts": os.path.getmtime(path),
                }
            )
    files.sort(key=lambda x: x["modified_ts"], reverse=True)
    return files


def get_question_paper_file_path(filename: str) -> Optional[str]:
    safe_name = os.path.basename(str(filename or "").strip())
    if not safe_name:
        return None
    path = os.path.join(QUESTION_PAPER_DIR, safe_name)
    if os.path.isfile(path):
        return path
    return None


def save_question_paper(uploaded_file) -> str:
    os.makedirs(QUESTION_PAPER_DIR, exist_ok=True)
    safe_name = os.path.basename(uploaded_file.filename)
    target_path = os.path.join(QUESTION_PAPER_DIR, safe_name)
    with open(target_path, "wb") as out:
        out.write(uploaded_file.file.read())
    return target_path


def save_question_paper_files(uploaded_items) -> int:
    os.makedirs(QUESTION_PAPER_DIR, exist_ok=True)
    saved_count = 0
    for item in uploaded_items:
        filename = getattr(item, "filename", "")
        if not filename:
            continue
        safe_name = os.path.basename(filename)
        if not safe_name:
            continue
        target_path = os.path.join(QUESTION_PAPER_DIR, safe_name)
        with open(target_path, "wb") as out:
            out.write(item.file.read())
        saved_count += 1
    return saved_count
