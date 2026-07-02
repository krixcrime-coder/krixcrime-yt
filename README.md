# KrixCrime YouTube Auto-Uploader

Automatically uploads videos from Google Drive to YouTube, 7 times a day
(one video from each of the 7 source folders), with a watermark and outro
clip applied automatically, plus a live dashboard.

## What this does

Every day, at 7 fixed times (IST), a GitHub Action:
1. Picks the next not-yet-uploaded video from one of your 7 Drive folders
2. Downloads it
3. Adds the circle watermark (top-left, fixed) — and the rectangle logo too, if enabled
4. Appends the 2-second outro clip to the end
5. Uploads it to YouTube as **Public**
6. Updates the dashboard with the result (success or error)

## One-time setup

### 1. Upload this project to your GitHub repo
Upload every file/folder in this zip to `krixcrime-coder/krixcrime-yt`,
keeping the same folder structure (`scripts/`, `assets/`, `data/`, `docs/`,
`.github/workflows/`).

### 2. Confirm your GitHub Secrets are set
You already added these under **Settings → Secrets and variables → Actions**:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REFRESH_TOKEN`

⚠️ Your current refresh token expires in 7 days (because the Google Cloud
OAuth app is still in "Testing" mode). To make it permanent:
1. Go to Google Cloud Console → **APIs & Services → OAuth consent screen**
2. Click **Publish App**
3. Re-generate the refresh token (same Colab steps as before)
4. Update the `GOOGLE_REFRESH_TOKEN` secret with the new value

### 3. Enable GitHub Pages (for the dashboard)
1. Go to your repo → **Settings → Pages**
2. Under "Build and deployment", set **Source: Deploy from a branch**
3. Branch: `main`, Folder: `/docs`
4. Save. Your dashboard will be live at:
   `https://krixcrime-coder.github.io/krixcrime-yt/`

### 5. Set up the Dashboard Control Panel (Settings + Upload Now buttons)
The dashboard can now edit watermark position/size, title/description/tags,
and upload times directly, plus trigger an upload for any folder on demand.
To allow this, the dashboard needs a GitHub token:

1. Go to **github.com/settings/personal-access-tokens/new** (Fine-grained token)
2. Name it anything (e.g. "krixcrime-dashboard")
3. Repository access: **Only select repositories** → choose `krixcrime-yt`
4. Under Permissions, set:
   - **Contents: Read and write**
   - **Actions: Read and write**
5. Generate the token and copy it
6. Open your dashboard → scroll to **Control Panel** → click **Save Changes**
   or **Upload Now** the first time — it will ask you to paste this token
7. It's saved only in that browser's local storage, never committed to the repo
8. Every save/trigger also asks for your 4-digit code (**5677**) as a
   safety check against accidental taps — change this in `docs/index.html`
   (search for `const PIN`) if you want a different code

⚠️ Note: this code is a tap-guard, not real security — anyone with access to
this same browser/device could bypass it and use the saved token. Don't use
this dashboard on a shared or public device.


1. Go to your repo → **Actions** tab
2. Click **YouTube Auto Uploader** → **Run workflow**
3. Leave "folder_index" blank (it'll default to folder 0) or type a number 0-6
4. Watch the run — check the logs for errors
5. Check the dashboard after it finishes

## Editing things later

- **Title / description / tags** — edit `config.json` → `title_template`,
  `description_template`, `tags`. Use `{num}` in the title to insert the
  video's number automatically.
- **Watermark position/size** — edit `config.json` → `watermark` section.
  Positions available: `top_left`, `top_right`, `bottom_left`, `bottom_right`, `center`.
- **Second (rectangle) logo** — set `"rect_enabled": true` in `config.json`
  and pick a position/size for it.
- **Upload times** — editing times requires updating both `config.json`
  (`upload_schedule`) and the cron lines in `.github/workflows/upload.yml`
  (cron times are in UTC = IST minus 5 hours 30 minutes).
- **Outro clip** — replace `assets/outro.mp4` with a new file (keep it short).

## Folder structure

```
config.json                  <- all settings (titles, watermark, schedule)
requirements.txt             <- Python dependencies
main.py                      <- runs one upload cycle
data/tracking.json           <- progress + history (auto-updated, do not edit)
assets/logo_circle.png       <- watermark (always applied, top-left)
assets/logo_rect.png         <- second watermark (currently disabled)
assets/outro.mp4             <- 2-second outro appended to every video
scripts/                     <- all the actual logic
docs/                        <- dashboard (index.html + data.json)
.github/workflows/upload.yml <- the automation schedule
```

## Important note

The tool uploads videos as **Public** automatically and cannot preview
them before upload. Since your Drive folder contains third-party anime
footage, keep in mind YouTube's Content ID system can flag or strike such
uploads regardless of any purchased license — that risk sits with the
channel, not with this tool.
