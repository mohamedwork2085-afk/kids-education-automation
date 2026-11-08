import asyncio
import json
import os
import re
import subprocess
import textwrap
from pathlib import Path
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
ASSETS = OUT / "assets"
AUDIO = OUT / "audio"
for folder in (OUT, ASSETS, AUDIO):
    folder.mkdir(parents=True, exist_ok=True)

VOICE = os.environ.get("TTS_VOICE") or "ar-EG-ShakirNeural"
HEADERS = {"User-Agent": "DarkFilesAI/1.0 (documentary video project)"}

def run(cmd):
    subprocess.run(cmd, check=True)

def fallback_image(path, label, size=(1920, 1080)):
    image = Image.new("RGB", size, (12, 15, 22))
    draw = ImageDraw.Draw(image)
    w, h = size
    for y in range(h):
        shade = int(12 + 22 * y / h)
        draw.line((0, y, w, y), fill=(shade, shade + 2, shade + 8))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 58)
    except Exception:
        font = ImageFont.load_default()
    lines = textwrap.wrap(label, width=28)
    y = h // 2 - len(lines) * 42
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        draw.text(((w - (box[2] - box[0])) / 2, y), line, fill=(210, 215, 225), font=font)
        y += 88
    image.save(path, quality=90)

def commons_image(query, destination):
    params = {
        "action": "query", "generator": "search", "gsrsearch": query,
        "gsrnamespace": 6, "gsrlimit": 12, "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": 1920, "format": "json"
    }
    try:
        res = requests.get("https://commons.wikimedia.org/w/api.php",
                           params=params, headers=HEADERS, timeout=35)
        res.raise_for_status()
        pages = res.json().get("query", {}).get("pages", {})
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            url = info.get("thumburl") or info.get("url")
            mime = info.get("mime", "")
            if not url or not mime.startswith("image/") or mime in ("image/svg+xml", "image/gif"):
                continue
            download = requests.get(url, headers=HEADERS, timeout=45)
            download.raise_for_status()
            destination.write_bytes(download.content)
            meta = info.get("extmetadata", {})
            def clean(key):
                value = meta.get(key, {}).get("value", "")
                return re.sub("<[^>]+>", "", str(value)).strip()
            return {
                "title": page.get("title", ""),
                "url": info.get("descriptionurl", url),
                "license": clean("LicenseShortName") or "راجع صفحة الملف",
                "artist": clean("Artist") or "غير مذكور"
            }
    except Exception as exc:
        print("Commons lookup failed:", str(exc)[:180])
    fallback_image(destination, query)
    return {"title": "Original fallback graphic", "url": "",
            "license": "Original generated graphic", "artist": "DARK FILES AI"}

async def make_tts(text, path):
    communicate = edge_tts.Communicate(text, voice=VOICE, rate="-4%", pitch="-2Hz")
    await communicate.save(str(path))

def render_clip(image, audio, output, width, height):
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio)
    ], text=True).strip()
    duration = max(3.0, float(probe) + 0.25)
    vf = (
        f"scale={width*1.25}:{height*1.25}:force_original_aspect_ratio=increase,"
        f"crop={width*1.25}:{height*1.25},"
        f"zoompan=z='min(zoom+0.00035,1.12)':d=1:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={width}x{height}:fps=25,format=yuv420p"
    )
    run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-framerate", "25", "-i", str(image), "-i", str(audio),
        "-vf", vf, "-t", str(duration), "-r", "25",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "25",
        "-c:a", "aac", "-b:a", "128k", "-shortest", str(output)
    ])

def concat_clips(clips, destination):
    listing = OUT / "concat.txt"
    lines = []
    for clip in clips:
        escaped = str(clip.resolve()).replace("'", "'\\''")
        lines.append("file '" + escaped + "'")
    listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", str(destination)])

async def main():
    data = json.loads((OUT / "episode.json").read_text(encoding="utf-8"))
    credits = []
    long_clips = []
    for index, scene in enumerate(data["scenes"], 1):
        print("Preparing scene", index, "of", len(data["scenes"]))
        image = ASSETS / ("scene_%02d.jpg" % index)
        audio = AUDIO / ("scene_%02d.mp3" % index)
        credit = commons_image(scene["visual_search"], image)
        credits.append(
            "Scene %d: %s | %s | %s | %s" %
            (index, credit["title"], credit["license"], credit["artist"], credit["url"])
        )
        await make_tts(scene["narration"], audio)
        clip = OUT / ("clip_%02d.mp4" % index)
        render_clip(image, audio, clip, 1920, 1080)
        long_clips.append(clip)

    long_video = OUT / "dark_files_episode_16x9.mp4"
    concat_clips(long_clips, long_video)

    short_audio = AUDIO / "short.mp3"
    await make_tts(data["short_narration"], short_audio)
    short_image = ASSETS / "scene_01.jpg"
    short_video = OUT / "dark_files_short_9x16.mp4"
    render_clip(short_image, short_audio, short_video, 1080, 1920)

    source_lines = [
        "%s - %s" % (source.get("name", ""), source.get("url", ""))
        for source in data.get("sources", [])
    ]
    (OUT / "credits.txt").write_text(
        "DARK FILES AI - Visual sources and licenses\n\n" +
        "\n".join(credits) + "\n\nStory references:\n" +
        "\n".join(source_lines), encoding="utf-8"
    )
    (OUT / "titles.txt").write_text(
        data.get("title", "") + "\n" + data.get("description", "") +
        "\n\nSHORT: " + data.get("short_title", ""), encoding="utf-8"
    )
    print("Finished:", long_video, short_video)

if __name__ == "__main__":
    asyncio.run(main())
