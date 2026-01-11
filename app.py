from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
import shutil

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def ffmpeg_installed():
    return shutil.which("ffmpeg") is not None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    quality = request.form.get("quality")

    file_id = str(uuid.uuid4())
    output = f"{DOWNLOAD_FOLDER}/{file_id}.%(ext)s"

    has_ffmpeg = ffmpeg_installed()

    ydl_opts = {
        "outtmpl": output,
        "quiet": True,
        "noplaylist": True,
    }

    # ---------- FORMAT SELECTION ----------
    if quality == "360":
        # Always progressive
        ydl_opts["format"] = "best[height<=360][ext=mp4]"

    elif quality == "720":
        if has_ffmpeg:
            ydl_opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]"
        else:
            # Progressive 720p ONLY
            ydl_opts["format"] = "best[height<=720][ext=mp4]"

    elif quality == "1080":
        if not has_ffmpeg:
            return "1080p requires FFmpeg installed", 400
        ydl_opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]"

    elif quality == "audio":
        if not has_ffmpeg:
            return "MP3 requires FFmpeg installed", 400
        ydl_opts["format"] = "bestaudio"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

    if quality == "audio":
        file_path = file_path.replace(".webm", ".mp3").replace(".m4a", ".mp3")

    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path)
    )



if __name__ == "__main__":
    app.run(debug=True)
