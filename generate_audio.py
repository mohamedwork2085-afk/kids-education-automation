
import os
import asyncio
import time
from pathlib import Path

import edge_tts
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(
    api_key=API_KEY,
    http_options=types.HttpOptions(
        timeout=180000,
        retry_options=types.HttpRetryOptions(
            attempts=4,
            initial_delay=2,
            max_delay=15
        )
    )
)

MODEL = "gemini-3.5-flash-lite"
VOICE = "ar-EG-ShakirNeural"


def extract_narration(episode):
    prompt = f"""
استخرج من الحلقة التالية نص الراوي الذي سيُنطق بصوت فقط.

قواعد مهمة:
- احتفظ بكل الكلام الذي يقوله الراوي.
- احذف عناوين المشاهد وأوصاف الصور والحركة.
- احذف تعليمات المؤثرات الصوتية.
- لا تلخص ولا تعيد كتابة الجمل.
- حافظ على ترتيب المشاهد.
- لا تضف مقدمة أو تعليقاً من عندك.
- أخرج النص المنطوق فقط.

الحلقة:
{episode}
"""

    for attempt in range(1, 4):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=9000,
                    temperature=0.2
                )
            )

            if response.text:
                return response.text

            raise RuntimeError("Empty narration response")

        except Exception as error:
            print(f"Extraction attempt {attempt} failed: {error}")

            if attempt == 3:
                raise

            time.sleep(attempt * 10)


async def create_audio(text):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+0%",
        volume="+0%"
    )

    await communicate.save("output/narration.mp3")


def main():
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    episode_path = output_dir / "episode.txt"

    if not episode_path.exists():
        raise FileNotFoundError("output/episode.txt not found")

    episode = episode_path.read_text(encoding="utf-8")

    print("Extracting narrator text...")
    narration = extract_narration(episode)

    if len(narration.split()) < 100:
        raise RuntimeError("Extracted narration is too short")

    (output_dir / "narration.txt").write_text(
        narration,
        encoding="utf-8"
    )

    print("Generating Arabic voice...")
    asyncio.run(create_audio(narration))

    print("Audio generated successfully!")
    print("Saved: output/narration.mp3")


if __name__ == "__main__":
    main()
