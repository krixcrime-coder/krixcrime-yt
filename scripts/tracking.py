"""Reads/writes data/tracking.json which stores per-folder progress and
the full upload history used to build the dashboard."""

import json
from datetime import datetime, timezone

TRACKING_PATH = "data/tracking.json"


def load():
    with open(TRACKING_PATH, "r") as f:
        return json.load(f)


def save(data):
    with open(TRACKING_PATH, "w") as f:
        json.dump(data, f, indent=2)


def ensure_folder_entry(data, folder_index, folder_id, folder_name):
    key = str(folder_index)
    if key not in data["folders"]:
        data["folders"][key] = {
            "folder_id": folder_id,
            "folder_name": folder_name,
            "next_position": 0,   # index into the sorted video list
            "uploaded_count": 0,
            "completed": False,
        }
    return data["folders"][key]


def record_success(data, folder_index, video_name, youtube_id):
    now = datetime.now(timezone.utc).isoformat()
    data["history"].append({
        "date": now,
        "folder_index": folder_index,
        "video_name": video_name,
        "status": "success",
        "youtube_link": f"https://youtube.com/watch?v={youtube_id}",
        "error": None,
    })


def record_failure(data, folder_index, video_name, error_message):
    now = datetime.now(timezone.utc).isoformat()
    data["history"].append({
        "date": now,
        "folder_index": folder_index,
        "video_name": video_name,
        "status": "failed",
        "youtube_link": None,
        "error": str(error_message)[:500],
    })
