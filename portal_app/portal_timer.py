"""Centralized exam timer and late-submission request management."""
import json
import os
import time
from threading import RLock

_TIMER_LOCK = RLock()
_LATE_LOCK = RLock()

LOGS_DIR = "logs"
TIMER_STATE_FILE = os.path.join(LOGS_DIR, "exam_timer.json")
LATE_REQUESTS_FILE = os.path.join(LOGS_DIR, "late_requests.json")
EXTRA_TIME_SECONDS = 180  # 3 minutes extra time when approved

# In-memory timer state.
# end_time is a wall-clock epoch; it is extended when the timer is resumed
# after a pause, so seconds_remaining = end_time - time.time() is always accurate.
_TIMER: dict = {
    "start_time": None,   # epoch float or None
    "end_time": None,     # epoch float or None
    "is_paused": False,
    "paused_at": None,    # epoch float when pause began, else None
}

# Late-submission requests keyed by roll number string.
_LATE_REQUESTS: dict = {}


# ─── Persistence ───────────────────────────────────────────────────────────────

def _load_timer() -> None:
    global _TIMER
    if not os.path.exists(TIMER_STATE_FILE):
        return
    try:
        with open(TIMER_STATE_FILE, "r", encoding="utf-8") as fh:
            saved = json.load(fh)
        for key in ("start_time", "end_time", "is_paused", "paused_at"):
            if key in saved:
                _TIMER[key] = saved[key]
    except Exception:
        pass


def _save_timer() -> None:
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(TIMER_STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(_TIMER, fh)
    except Exception:
        pass


def _load_late_requests() -> None:
    global _LATE_REQUESTS
    if not os.path.exists(LATE_REQUESTS_FILE):
        return
    try:
        with open(LATE_REQUESTS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            _LATE_REQUESTS = data
    except Exception:
        pass


def _save_late_requests() -> None:
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)
        with open(LATE_REQUESTS_FILE, "w", encoding="utf-8") as fh:
            json.dump(_LATE_REQUESTS, fh)
    except Exception:
        pass


# ─── Timer controls ────────────────────────────────────────────────────────────

def get_timer_status() -> dict:
    """Return current timer state as a JSON-safe dict."""
    with _TIMER_LOCK:
        now = time.time()
        start = _TIMER.get("start_time")
        end = _TIMER.get("end_time")
        is_paused = bool(_TIMER.get("is_paused"))
        paused_at = _TIMER.get("paused_at")

        # When paused, the clock is frozen at paused_at; compare against that.
        ref = paused_at if (is_paused and paused_at is not None) else now

        if start is None or end is None:
            return {
                "phase": "not_set",
                "start_time": None,
                "end_time": None,
                "is_paused": is_paused,
                "seconds_remaining": None,
                "seconds_until_start": None,
                "server_time": now,
            }

        if ref < start:
            return {
                "phase": "before_exam",
                "start_time": start,
                "end_time": end,
                "is_paused": is_paused,
                "seconds_remaining": None,
                "seconds_until_start": max(0, int(start - ref)),
                "server_time": now,
            }

        if ref >= end:
            return {
                "phase": "ended",
                "start_time": start,
                "end_time": end,
                "is_paused": is_paused,
                "seconds_remaining": 0,
                "seconds_until_start": None,
                "server_time": now,
            }

        return {
            "phase": "active",
            "start_time": start,
            "end_time": end,
            "is_paused": is_paused,
            "seconds_remaining": max(0, int(end - ref)),
            "seconds_until_start": None,
            "server_time": now,
        }


def set_exam_times(start_epoch: float, end_epoch: float) -> None:
    with _TIMER_LOCK:
        _TIMER["start_time"] = float(start_epoch)
        _TIMER["end_time"] = float(end_epoch)
        _TIMER["is_paused"] = False
        _TIMER["paused_at"] = None
        _save_timer()


def reset_timer() -> None:
    with _TIMER_LOCK:
        _TIMER["start_time"] = None
        _TIMER["end_time"] = None
        _TIMER["is_paused"] = False
        _TIMER["paused_at"] = None
        _save_timer()


def pause_timer() -> bool:
    """Pause the exam clock. Returns True if state changed."""
    with _TIMER_LOCK:
        if _TIMER.get("is_paused"):
            return False
        _TIMER["is_paused"] = True
        _TIMER["paused_at"] = time.time()
        _save_timer()
        return True


def resume_timer() -> bool:
    """Resume the exam clock, extending end_time by the pause duration.
    Returns True if state changed."""
    with _TIMER_LOCK:
        if not _TIMER.get("is_paused"):
            return False
        paused_at = _TIMER.get("paused_at")
        if paused_at is not None and _TIMER.get("end_time") is not None:
            pause_duration = time.time() - paused_at
            _TIMER["end_time"] = _TIMER["end_time"] + pause_duration
            # Also extend start_time if the exam hasn't started yet.
            if _TIMER.get("start_time") is not None and paused_at < _TIMER["start_time"]:
                _TIMER["start_time"] = _TIMER["start_time"] + pause_duration
        _TIMER["is_paused"] = False
        _TIMER["paused_at"] = None
        _save_timer()
        return True


def is_submission_locked() -> bool:
    """True if the global exam has ended (for all students without extra time)."""
    return get_timer_status()["phase"] == "ended"


# ─── Student-specific timer ────────────────────────────────────────────────────

def get_student_timer_status(roll: str) -> dict:
    """Return timer status for a specific student, accounting for extra time."""
    base = get_timer_status()
    late_status = None
    now = time.time()
    with _LATE_LOCK:
        req = _LATE_REQUESTS.get(str(roll))
        if req is not None:
            status = req.get("status")
            if status == "approved":
                extra_end = req.get("extra_end_time")
                if extra_end is not None and now < extra_end:
                    late_status = "approved"
                else:
                    # Approval window has expired; student may request again.
                    late_status = None
            else:
                late_status = status

    result = dict(base)
    result["late_request_status"] = late_status

    if req is not None and req.get("status") == "approved":
        extra_end = req.get("extra_end_time")
        if extra_end is not None:
            if now < extra_end:
                result["phase"] = "extra_time"
                result["seconds_remaining"] = max(0, int(extra_end - now))
                result["extra_end_time"] = extra_end
                return result

    return result


def is_submission_locked_for_student(roll: str) -> bool:
    """True if this student's submission window has ended (no valid extra time)."""
    phase = get_student_timer_status(str(roll)).get("phase", "not_set")
    return phase == "ended"


# ─── Late requests ─────────────────────────────────────────────────────────────

def add_late_request(roll: str, name: str) -> bool:
    """Register a late-submission request. Returns False if one already exists."""
    with _LATE_LOCK:
        key = str(roll)
        existing = _LATE_REQUESTS.get(key)
        if existing is not None:
            # Allow fresh request if prior approval window has already expired.
            if existing.get("status") == "approved":
                extra_end = existing.get("extra_end_time")
                if extra_end is not None and time.time() >= extra_end:
                    _LATE_REQUESTS[key] = {
                        "roll": str(roll),
                        "name": str(name),
                        "requested_at": time.time(),
                        "status": "pending",
                        "extra_end_time": None,
                    }
                    _save_late_requests()
                    return True
            return False
        _LATE_REQUESTS[key] = {
            "roll": str(roll),
            "name": str(name),
            "requested_at": time.time(),
            "status": "pending",
            "extra_end_time": None,
        }
        _save_late_requests()
        return True


def approve_late_request(roll: str) -> bool:
    with _LATE_LOCK:
        req = _LATE_REQUESTS.get(str(roll))
        if req is None:
            return False
        req["status"] = "approved"
        req["extra_end_time"] = time.time() + EXTRA_TIME_SECONDS
        req["approved_at"] = time.time()
        _save_late_requests()
        return True


def reject_late_request(roll: str) -> bool:
    with _LATE_LOCK:
        req = _LATE_REQUESTS.get(str(roll))
        if req is None:
            return False
        req["status"] = "rejected"
        req["rejected_at"] = time.time()
        _save_late_requests()
        return True


def get_late_requests() -> list:
    with _LATE_LOCK:
        return list(_LATE_REQUESTS.values())


def get_late_request_status(roll: str) -> "str | None":
    """Return status for a late request ('pending'/'approved'/'rejected'), or None."""
    with _LATE_LOCK:
        req = _LATE_REQUESTS.get(str(roll))
        return req.get("status") if req is not None else None


def clear_late_request(roll: str) -> bool:
    """Remove a late-request entry entirely. Returns True if an entry was removed."""
    with _LATE_LOCK:
        key = str(roll)
        if key not in _LATE_REQUESTS:
            return False
        del _LATE_REQUESTS[key]
        _save_late_requests()
        return True


def cleanup_stale_late_requests(submitted_rolls: set) -> int:
    """Remove late requests for students who have no submission files and whose
    extra-time window (if any) has already expired.  Returns number removed."""
    now = time.time()
    with _LATE_LOCK:
        to_remove = []
        for roll, req in _LATE_REQUESTS.items():
            if roll in submitted_rolls:
                continue  # student submitted — keep record
            status = req.get("status")
            if status == "pending":
                continue  # waiting for teacher decision — always keep
            if status == "rejected":
                continue  # keep rejected state visible to student/admin
            if status == "approved":
                extra_end = req.get("extra_end_time")
                if extra_end is not None and now < extra_end:
                    continue  # still inside extra-time window — keep
            # approved+expired with no submission — remove
            to_remove.append(roll)
        if not to_remove:
            return 0
        for roll in to_remove:
            del _LATE_REQUESTS[roll]
        _save_late_requests()
        return len(to_remove)


# Initialise persistent state on module import.
_load_timer()
_load_late_requests()
