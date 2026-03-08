
import yt_dlp
import uuid

def search_youtube(query):
    ydl_opts = {
        "quiet": True,
        "skip_download": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(f"ytsearch20:{query}", download=False)
    return data["entries"]


def get_video_info(url):
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)


def download_video(url):
    name = f"{uuid.uuid4()}.mp4"
    ydl_opts = {
        "format": "best",
        "outtmpl": name,
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return name


def download_audio(url):
    name = f"{uuid.uuid4()}.mp3"
    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": name,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    title = info.get("title","audio")
    return name, title
