import os
import asyncio
import random
import re
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
        # Retries are handled below so we can switch models deliberately.
        retry_options=types.HttpRetryOptions(attempts=1)
    )
)

PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"
MODELS = (PRIMARY_MODEL, FALLBACK_MODEL)
VOICE = "ar-EG-ShakirNeural"
MAX_ATTEMPTS_PER_MODEL = 3
RETRY_DELAYS_SECONDS = (5, 15)


def is_temporary_error(error):
    """Return True only for errors that may succeed on a later attempt/model."""
    message = str(error).lower()

    # Authentication, permission, and model-name/configuration errors are not
    # fixed by retrying or switching models, so surface them immediately.
    permanent_markers = (
        "api key not valid",
        "invalid api key",
        "unauthenticated",
        "permission denied",
        "forbidden",
        "model not found",
        "not_found",
        "does not exist",
        "unsupported model",
    )
    if any(marker in message for marker in permanent_markers):
        return False

    status = getattr(error, "code", None)
    if status is None:
        status = getattr(error, "status_code", None)
    if status is None:
        status = getattr(error, "status", None)

    try:
        status = int(status)
    except (TypeError, ValueError):
        status = None

    if status in (408, 429, 500, 502, 503, 504):
        return True

    temporary_markers = (
        "unavailable",
        "resource_exhausted",
        "resource exhausted",
        "rate limit",
        "too many requests",
        "timed out",
        "timeout",
        "temporarily",
        "connection reset",
        "service unavailable",
        "internal server error",
    )
    return any(marker in message for marker in temporary_markers)


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

    last_error = None

    for model in MODELS:
        print(f"Using Gemini model: {model}")

        for attempt in range(1, MAX_ATTEMPTS_PER_MODEL + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=9000,
                        temperature=0.2
                    )
                )

                narration = response.text
                if narration and narration.strip():
                    print(f"Narration extracted successfully with {model}.")
                    return narration.strip()

                raise RuntimeError(
                    f"Gemini returned an empty narration response ({model})"
                )

            except Exception as error:
                last_error = error
                print(
                    f"{model} attempt {attempt}/{MAX_ATTEMPTS_PER_MODEL} "
                    f"failed: {error}"
                )

                # Do not retry permanent errors or silently hide configuration
                # problems by trying a different model.
                if not is_temporary_error(error):
                    raise

                if attempt < MAX_ATTEMPTS_PER_MODEL:
                    delay = RETRY_DELAYS_SECONDS[attempt - 1]
                    delay += random.uniform(0, 2)
                    print(f"Temporary error. Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)

        if model != FALLBACK_MODEL:
            print(
                f"{model} is still unavailable after retries. "
                f"Switching to fallback model: {FALLBACK_MODEL}"
            )

    raise RuntimeError(
        "Both Gemini models failed to extract narration. "
        f"Last error: {last_error}"
    ) from last_error


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

    # Save the text before TTS so it remains available if audio generation fails.
    narration_path = output_dir / "narration.txt"
    narration_path.write_text(narration, encoding="utf-8")
    print(f"Narration saved: {narration_path}")

    print("Generating Arabic voice...")
    asyncio.run(create_audio(narration))

    print("Audio generated successfully!")
    print("Saved: output/narration.mp3")


if __name__ == "__main__":
    main()
