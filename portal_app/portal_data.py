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
    if "Paper Type" not in df.columns:
        df["Paper Type"] = ""

    df["Roll No."] = df["Roll No."].fillna("").astype(str)
    df["Student Name"] = df["Student Name"].fillna("").astype(str)
    df["Password"] = df["Password"].fillna("").astype(str)
    df["Paper Type"] = df["Paper Type"].fillna("").astype(str).str.upper().str.strip()
    return df


def paper_type_labels(count: int) -> list[str]:
    safe_count = max(1, min(26, int(count)))
    return [chr(ord("A") + idx) for idx in range(safe_count)]


def assign_default_paper_types(df: pd.DataFrame, paper_types: list[str]) -> pd.DataFrame:
    if not paper_types:
        paper_types = ["A"]
    for idx in df.index:
        df.at[idx, "Paper Type"] = paper_types[idx % len(paper_types)]
    return df


def ensure_valid_paper_types(df: pd.DataFrame, paper_types: list[str]) -> pd.DataFrame:
    if not paper_types:
        paper_types = ["A"]
    valid = set(paper_types)
    for idx in df.index:
        current = str(df.at[idx, "Paper Type"]).upper().strip()
        if current not in valid:
            df.at[idx, "Paper Type"] = paper_types[idx % len(paper_types)]
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


def _paper_type_dir(paper_type: str) -> str:
    safe_type = str(paper_type or "A").upper().strip()[:1] or "A"
    return os.path.join(QUESTION_PAPER_DIR, f"type_{safe_type.lower()}")


def latest_question_paper_path(paper_type: str = "A") -> Optional[str]:
    paper_dir = _paper_type_dir(paper_type)
    if not os.path.isdir(paper_dir):
        return None
    files = []
    for name in os.listdir(paper_dir):
        path = os.path.join(paper_dir, name)
        if os.path.isfile(path):
            files.append(path)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def list_question_paper_files(paper_type: str = "A") -> list[dict]:
    paper_dir = _paper_type_dir(paper_type)
    if not os.path.isdir(paper_dir):
        return []

    files = []
    for name in os.listdir(paper_dir):
        path = os.path.join(paper_dir, name)
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
    return get_question_paper_file_path_for_type("A", filename)


def get_question_paper_file_path_for_type(paper_type: str, filename: str) -> Optional[str]:
    safe_name = os.path.basename(str(filename or "").strip())
    if not safe_name:
        return None
    paper_dir = _paper_type_dir(paper_type)
    path = os.path.join(paper_dir, safe_name)
    if os.path.isfile(path):
        return path
    return None


def save_question_paper(uploaded_file) -> str:
    target_dir = _paper_type_dir("A")
    os.makedirs(target_dir, exist_ok=True)
    safe_name = os.path.basename(uploaded_file.filename)
    target_path = os.path.join(target_dir, safe_name)
    with open(target_path, "wb") as out:
        out.write(uploaded_file.file.read())
    return target_path


def save_question_paper_files(uploaded_items) -> int:
    target_dir = _paper_type_dir("A")
    os.makedirs(target_dir, exist_ok=True)
    saved_count = 0
    for item in uploaded_items:
        filename = getattr(item, "filename", "")
        if not filename:
            continue
        safe_name = os.path.basename(filename)
        if not safe_name:
            continue
        target_path = os.path.join(target_dir, safe_name)
        with open(target_path, "wb") as out:
            out.write(item.file.read())
        saved_count += 1
    return saved_count


def save_question_paper_file_for_type(paper_type: str, uploaded_item) -> bool:
    filename = getattr(uploaded_item, "filename", "")
    if not filename:
        return False
    safe_name = os.path.basename(filename)
    if not safe_name:
        return False

    target_dir = _paper_type_dir(paper_type)
    os.makedirs(target_dir, exist_ok=True)

    # Keep only one active paper file per type.
    for old_name in os.listdir(target_dir):
        old_path = os.path.join(target_dir, old_name)
        if os.path.isfile(old_path):
            os.remove(old_path)

    target_path = os.path.join(target_dir, safe_name)
    with open(target_path, "wb") as out:
        out.write(uploaded_item.file.read())
    return True


def _unique_target_path(base_dir: str, filename: str) -> str:
    name, ext = os.path.splitext(filename)
    candidate = os.path.join(base_dir, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(base_dir, f"{name}_{counter}{ext}")
        counter += 1
    return candidate


def save_question_paper_files_for_type(paper_type: str, uploaded_items) -> int:
    target_dir = _paper_type_dir(paper_type)
    os.makedirs(target_dir, exist_ok=True)

    items = uploaded_items if isinstance(uploaded_items, list) else [uploaded_items]
    saved_count = 0
    for item in items:
        filename = getattr(item, "filename", "")
        if not filename:
            continue
        safe_name = os.path.basename(filename)
        if not safe_name:
            continue
        target_path = _unique_target_path(target_dir, safe_name)
        with open(target_path, "wb") as out:
            out.write(item.file.read())
        saved_count += 1
    return saved_count
