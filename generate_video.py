
import re
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

OUTPUT = Path("output")
AUDIO = OUTPUT / "narration.mp3"
NARRATION = OUTPUT / "narration.txt"
VIDEO = OUTPUT / "final_video.mp4"

WIDTH, HEIGHT = 1280, 720
SCENE_COUNT = 8

def arabic(text):
    return get_display(arabic_reshaper.reshape(text))

def split_into_scenes(text):
    words = text.split()

    if len(words) < 40:
        raise RuntimeError("Narration is too short")

    scenes = []
    for i in range(SCENE_COUNT):
        start = i * len(words) // SCENE_COUNT
        end = (i + 1) * len(words) // SCENE_COUNT
        scenes.append(" ".join(words[start:end]))

    return scenes

def create_scene(index, content, font):
    image = Image.new("RGB", (WIDTH, HEIGHT), (22, 39, 78))
    draw = ImageDraw.Draw(image)

    # زخارف كرتونية بسيطة
    draw.ellipse((900, -180, 1450, 370), fill=(48, 91, 145))
    draw.ellipse((-180, 500, 350, 1030), fill=(40, 72, 125))
    draw.rounded_rectangle(
        (75, 175, 1205, 610),
        radius=35,
        fill=(32, 55, 100)
    )

    title_font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34
    )

    draw.text(
        (WIDTH // 2, 105),
        arabic(f"رحلة المعرفة - المشهد {index + 1}"),
        font=title_font,
        fill="white",
        anchor="mm"
    )

    # تقسيم الكلام لأسطر مع الحفاظ على اتجاه العربية
    lines = []
    current = ""

    for word in content.split():
        candidate = (current + " " + word).strip()
        visual = arabic(candidate)

        if draw.textlength(visual, font=font) > 1000 and current:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    # عرض أول 7 أسطر
    visible_lines = lines[:7]
    line_height = 57
    start_y = 390 - (len(visible_lines) * line_height) // 2

    for i, line in enumerate(visible_lines):
        draw.text(
            (WIDTH // 2, start_y + i * line_height),
            arabic(line),
            font=font,
            fill=(255, 235, 175),
            anchor="mm"
        )

    path = OUTPUT / f"scene_{index + 1}.png"
    image.save(path)
    return path

def main():
    OUTPUT.mkdir(exist_ok=True)

    if not AUDIO.exists() or not NARRATION.exists():
        raise FileNotFoundError("Narration text or audio is missing")

    narration = NARRATION.read_text(encoding="utf-8")
    scenes = split_into_scenes(narration)

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        39
    )

    audio = AudioFileClip(str(AUDIO))
    clips = []

    weights = [max(len(scene.split()), 1) for scene in scenes]
    total_words = sum(weights)

    for i, scene in enumerate(scenes):
        print(f"Creating scene {i + 1}/{SCENE_COUNT}", flush=True)

        duration = audio.duration * weights[i] / total_words
        image_path = create_scene(i, scene, font)

        clips.append(
            ImageClip(str(image_path)).with_duration(duration)
        )

    video = concatenate_videoclips(clips, method="compose")
    video = video.with_audio(audio)

    video.write_videofile(
        str(VIDEO),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast"
    )

    audio.close()
    video.close()

    print("VIDEO CREATED SUCCESSFULLY!", flush=True)

if __name__ == "__main__":
    main()
