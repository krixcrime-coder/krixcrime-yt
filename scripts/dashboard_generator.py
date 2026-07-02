"""Builds docs/data.json which the static dashboard (docs/index.html) reads."""

import json
from collections import defaultdict

OUTPUT_PATH = "docs/data.json"


def generate(config, tracking_data, channel_stats=None):
    total_uploaded = sum(f.get("uploaded_count", 0) for f in tracking_data["folders"].values())

    daily = defaultdict(lambda: {"success": 0, "failed": 0, "errors": []})
    for entry in tracking_data["history"]:
        day = entry["date"][:10]
        if entry["status"] == "success":
            daily[day]["success"] += 1
        else:
            daily[day]["failed"] += 1
            daily[day]["errors"].append({
                "video": entry["video_name"],
                "error": entry["error"],
            })

    daily_report = [
        {"date": day, **stats} for day, stats in sorted(daily.items(), reverse=True)
    ]

    folders_summary = []
    for idx, f in sorted(tracking_data["folders"].items(), key=lambda kv: int(kv[0])):
        folders_summary.append({
            "folder_index": int(idx),
            "folder_name": f["folder_name"],
            "uploaded_count": f.get("uploaded_count", 0),
            "next_position": f.get("next_position", 0),
            "completed": f.get("completed", False),
        })

    history_recent = list(reversed(tracking_data["history"]))[:100]

    output = {
        "channel": channel_stats or {
            "title": config.get("channel_holder_name", "Unknown"),
            "logo": "",
            "subscribers": "N/A",
            "total_videos": "N/A",
            "channel_url": "",
        },
        "channel_holder_name": config.get("channel_holder_name", ""),
        "total_uploaded_by_tool": total_uploaded,
        "folders": folders_summary,
        "daily_report": daily_report,
        "history_recent": history_recent,
        "watermark_config": config.get("watermark", {}),
        "upload_schedule": config.get("upload_schedule", []),
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
