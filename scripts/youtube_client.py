"""Handles all YouTube interactions: uploading videos and fetching channel stats."""

import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def get_youtube_service():
    creds = Credentials(
        None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video(service, file_path, title, description, tags):
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "24",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
    return response


def get_channel_stats(service):
    resp = service.channels().list(part="snippet,statistics", mine=True).execute()
    item = resp["items"][0]
    return {
        "title": item["snippet"]["title"],
        "logo": item["snippet"]["thumbnails"]["high"]["url"],
        "subscribers": item["statistics"].get("subscriberCount", "0"),
        "total_videos": item["statistics"].get("videoCount", "0"),
        "channel_url": f"https://www.youtube.com/channel/{item['id']}",
    }
