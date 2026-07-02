"""Applies watermark(s) to a video and appends the outro clip using ffmpeg."""

import json
import subprocess


def _has_audio_stream(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "json", path],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(result.stdout or "{}")
    return bool(data.get("streams"))


def _ensure_audio(outro_path, fixed_outro_path):
    """If the outro clip has no audio track, add a silent one so concat works."""
    if _has_audio_stream(outro_path):
        return outro_path
    subprocess.run([
        "ffmpeg", "-y",
        "-i", outro_path,
        "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-shortest",
        "-c:v", "copy", "-c:a", "aac",
        fixed_outro_path,
    ], check=True)
    return fixed_outro_path

POSITIONS = {
    "top_left": "{m}:{m}",
    "top_right": "main_w-overlay_w-{m}:{m}",
    "bottom_left": "{m}:main_h-overlay_h-{m}",
    "bottom_right": "main_w-overlay_w-{m}:main_h-overlay_h-{m}",
    "center": "(main_w-overlay_w)/2:(main_h-overlay_h)/2",
}


def _overlay_pos(position, margin):
    return POSITIONS.get(position, POSITIONS["top_left"]).format(m=margin)


def apply_watermarks(input_path, output_path, wm_config):
    """
    wm_config is the "watermark" section of config.json.
    Always applies the circle logo. Applies the rect logo too if rect_enabled is true.
    """
    inputs = ["-i", input_path, "-i", wm_config["circle_logo"]]
    filters = [f"[1:v]scale={wm_config['circle_width']}:-1[wm1]"]
    last_video_label = "0:v"
    overlay_chain = f"[{last_video_label}][wm1]overlay={_overlay_pos(wm_config['circle_position'], wm_config['circle_margin'])}"

    if wm_config.get("rect_enabled") and wm_config.get("rect_logo"):
        inputs += ["-i", wm_config["rect_logo"]]
        rect_w = wm_config.get("rect_width") or 150
        filters.append(f"[2:v]scale={rect_w}:-1[wm2]")
        overlay_chain += "[tmp1];[tmp1][wm2]overlay=" + _overlay_pos(
            wm_config["rect_position"], wm_config["rect_margin"]
        )

    filter_complex = ";".join(filters) + ";" + overlay_chain

    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", filter_complex,
        "-codec:a", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def append_outro(input_path, outro_path, output_path, tmp_dir):
    """Concatenates the outro clip onto the end of the input video.
    Handles the case where either clip is missing an audio track."""
    import os

    safe_input = input_path

    if not _has_audio_stream(input_path):
        safe_input = os.path.join(tmp_dir, "main_with_audio.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-shortest", "-c:v", "copy", "-c:a", "aac", safe_input,
        ], check=True)

    safe_outro = _ensure_audio(outro_path, os.path.join(tmp_dir, "outro_with_audio.mp4"))

    cmd = [
        "ffmpeg", "-y",
        "-i", safe_input,
        "-i", safe_outro,
        "-filter_complex",
        "[0:v:0][0:a:0][1:v:0][1:a:0]concat=n=2:v=1:a=1[outv][outa]",
        "-map", "[outv]", "-map", "[outa]",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def process_video(input_path, watermarked_path, final_path, wm_config, outro_path, tmp_dir):
    apply_watermarks(input_path, watermarked_path, wm_config)
    append_outro(watermarked_path, outro_path, final_path, tmp_dir)
