"""
Main entry point. Run as:
    python main.py --folder-index 0

For a given folder_index (0-6, matching the 7 subfolders under the Drive
parent folder), this will:
  1. Find the next not-yet-uploaded video in that folder
  2. Download it
  3. Apply watermark(s) + outro clip
  4. Upload it to YouTube (public)
  5. Update data/tracking.json with the result
  6. Regenerate docs/data.json for the dashboard
"""

import argparse
import json
import os
import shutil
import sys
import traceback

from scripts import drive_client, youtube_client, watermark, tracking, dashboard_generator

CONFIG_PATH = "config.json"
TMP_DIR = "tmp_work"


def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def initialize_folders_if_needed(data, drive_service, parent_id):
    if data.get("initialized"):
        return
    folders = drive_client.list_subfolders(drive_service, parent_id)
    if not folders:
        raise RuntimeError("No subfolders found under drive_parent_folder_id")
    for idx, folder in enumerate(folders):
        tracking.ensure_folder_entry(data, idx, folder["id"], folder["name"])
    data["initialized"] = True


def build_title(template, video_name):
    num = drive_client.extract_number(video_name)
    return template.replace("{num}", str(num))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder-index", type=int, required=True)
    args = parser.parse_args()

    os.makedirs(TMP_DIR, exist_ok=True)
    config = load_config()
    data = tracking.load()

    drive_service = drive_client.get_drive_service()
    initialize_folders_if_needed(data, drive_service, config["drive_parent_folder_id"])

    key = str(args.folder_index)
    if key not in data["folders"]:
        print(f"No folder configured at index {args.folder_index}, skipping.")
        tracking.save(data)
        return

    entry = data["folders"][key]

    if entry.get("completed"):
        print(f"Folder '{entry['folder_name']}' already fully uploaded. Skipping.")
        tracking.save(data)
        return

    videos = drive_client.list_videos_in_folder(drive_service, entry["folder_id"])
    position = entry["next_position"]

    if position >= len(videos):
        entry["completed"] = True
        print(f"Folder '{entry['folder_name']}' has no more videos. Marking completed.")
        tracking.save(data)
        dashboard_generator.generate(config, data)
        return

    video = videos[position]
    video_name = video["name"]
    print(f"Processing '{video_name}' from folder '{entry['folder_name']}'...")

    raw_path = os.path.join(TMP_DIR, "raw.mp4")
    watermarked_path = os.path.join(TMP_DIR, "watermarked.mp4")
    final_path = os.path.join(TMP_DIR, "final.mp4")

    try:
        drive_client.download_file(drive_service, video["id"], raw_path)

        watermark.process_video(
            input_path=raw_path,
            watermarked_path=watermarked_path,
            final_path=final_path,
            wm_config=config["watermark"],
            outro_path=config["outro_video"],
            tmp_dir=TMP_DIR,
        )

        youtube_service = youtube_client.get_youtube_service()
        title = build_title(config["title_template"], video_name)
        response = youtube_client.upload_video(
            youtube_service,
            final_path,
            title=title,
            description=config["description_template"],
            tags=config["tags"],
        )

        entry["next_position"] = position + 1
        entry["uploaded_count"] = entry.get("uploaded_count", 0) + 1
        tracking.record_success(data, args.folder_index, video_name, response["id"])
        print(f"Uploaded successfully: https://youtube.com/watch?v={response['id']}")

    except Exception as e:
        traceback.print_exc()
        tracking.record_failure(data, args.folder_index, video_name, e)
        print(f"FAILED to process '{video_name}': {e}")

    finally:
        tracking.save(data)
        shutil.rmtree(TMP_DIR, ignore_errors=True)
        try:
            youtube_service = youtube_client.get_youtube_service()
            channel_stats = youtube_client.get_channel_stats(youtube_service)
        except Exception:
            channel_stats = None
        dashboard_generator.generate(config, data, channel_stats)


if __name__ == "__main__":
    sys.exit(main())
