
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

OUTPUT = Path("output")
AUDIO = OUTPUT / "narration.mp3"
VIDEO = OUTPUT / "final_video.mp4"

WIDTH, HEIGHT = 1280, 720

if not AUDIO.exists():
    raise FileNotFoundError("narration.mp3 not found")

# تقسيم نص الراوي إلى مشاهد
text = (OUTPUT / "narration.txt").read_text(encoding="utf-8")
paragraphs = [
    p.strip() for p in re.split(r"\n+", text)
    if len(p.strip()) > 30
]

if not paragraphs:
    raise RuntimeError("No narration scenes found")

# خط عربي
font_paths = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
]

font_path = next(
    (p for p in font_paths if Path(p).exists()),
    None
)

if not font_path:
    raise RuntimeError("Arabic font not found")

font = ImageFont.truetype(font_path, 42)

def create_scene(index, paragraph):
    image = Image.new("RGB", (WIDTH, HEIGHT), (20, 35, 75))
    draw = ImageDraw.Draw(image)

    # خلفية زخرفية بسيطة
    draw.ellipse((850, -180, 1450, 420), fill=(45, 85, 140))
    draw.ellipse((-200, 480, 350, 1050), fill=(35, 65, 115))

    draw.text(
        (WIDTH // 2, 100),
        f"رحلة المعرفة - المشهد {index + 1}",
        font=font,
        fill="white",
        anchor="mm"
    )

    # تقسيم الكلام إلى أسطر
    words = paragraph.split()
    lines = []
    current = ""

    for word in words:
        test = current + " " + word
        if draw.textlength(test, font=font) > 1050:
            lines.append(current)
            current = word
        else:
            current = test

    if current:
        lines.append(current)

    y = 300
    for line in lines[:5]:
        draw.text(
            (WIDTH // 2, y),
            line,
            font=font,
            fill=(255, 230, 150),
            anchor="mm",
            direction="rtl"
        )
        y += 65

    path = OUTPUT / f"scene_{index + 1}.png"
    image.save(path)
    return path


def main():
    OUTPUT.mkdir(exist_ok=True)

    audio = AudioFileClip(str(AUDIO))
    total_duration = audio.duration

    # توزيع مدة الصوت على المشاهد حسب طول النص
    weights = [max(len(p.split()), 1) for p in paragraphs]
    total_words = sum(weights)

    clips = []

    for i, paragraph in enumerate(paragraphs):
        duration = total_duration * weights[i] / total_words
        image_path = create_scene(i, paragraph)

        clip = (
            ImageClip(str(image_path))
            .with_duration(duration)
        )

        clips.append(clip)

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

    print("VIDEO CREATED:", VIDEO)


if __name__ == "__main__":
    main()
