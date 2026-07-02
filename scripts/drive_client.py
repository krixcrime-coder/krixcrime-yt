"""Handles all Google Drive interactions: listing folders, listing videos,
and downloading a specific video file."""

import io
import os
import re

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def get_drive_service():
    creds = Credentials(
        None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def extract_number(name):
    """Pulls the first number out of a filename like 'ERideBay (501).mp4' -> 501"""
    m = re.search(r"\((\d+)\)", name)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 0


def list_subfolders(service, parent_id):
    """Returns subfolders of parent_id, sorted by the number in their name."""
    folders = []
    page_token = None
    while True:
        res = service.files().list(
            q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="nextPageToken, files(id, name)",
            pageSize=100,
            pageToken=page_token,
        ).execute()
        folders.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    folders.sort(key=lambda f: extract_number(f["name"]))
    return folders


def list_videos_in_folder(service, folder_id):
    """Returns all video files in a folder, sorted numerically by filename."""
    files = []
    page_token = None
    while True:
        res = service.files().list(
            q=f"'{folder_id}' in parents and mimeType contains 'video/' and trashed=false",
            fields="nextPageToken, files(id, name)",
            pageSize=1000,
            pageToken=page_token,
        ).execute()
        files.extend(res.get("files", []))
        page_token = res.get("nextPageToken")
        if not page_token:
            break
    files.sort(key=lambda f: extract_number(f["name"]))
    return files


def download_file(service, file_id, dest_path):
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
