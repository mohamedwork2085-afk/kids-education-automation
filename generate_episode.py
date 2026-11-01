import os
import time
from pathlib import Path
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=120000,
        retry_options=types.HttpRetryOptions(
            attempts=4,
            initial_delay=2,
            max_delay=15
        )
    )
)

prompt = """
أنت كاتب ومعدّ برامج تعليمية محترف للأطفال.

اكتب حلقة تعليمية أصلية باللغة العربية البسيطة للأطفال من 5 إلى 9 سنوات.

الشروط:
- مدة الحلقة من 8 إلى 10 دقائق.
- اختر بنفسك موضوعاً علمياً أو تعليمياً ممتعاً.
- ابدأ بمقدمة تشد انتباه الطفل.
- اشرح المعلومات بأمثلة من الحياة اليومية.
- اجعل الأحداث مترابطة ومشوقة.
- قسّم الحلقة إلى 8 مشاهد متتابعة.
- اكتب نص الراوي كاملاً لكل مشهد.
- اقترح وصفاً بصرياً لكل مشهد.
- تأكد من صحة المعلومات.
- اجعل المحتوى آمناً ومناسباً للأطفال.
- اختم بمراجعة بسيطة لما تعلمه الطفل.

اكتب عنوان الحلقة والفئة العمرية والهدف التعليمي،
ثم المشاهد الثمانية والخاتمة.
"""

response = None

for attempt in range(1, 4):
    try:
        print(f"Generating episode, attempt {attempt}/3...")

        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=6000,
                temperature=0.7
            )
        )

        if response.text:
            break

        raise RuntimeError("Gemini returned an empty response")

    except Exception as error:
        print(f"Attempt {attempt} failed: {error}")

        if attempt == 3:
            raise

        time.sleep(attempt * 10)

Path("output").mkdir(exist_ok=True)
Path("output/episode.txt").write_text(
    response.text,
    encoding="utf-8"
)

print("Episode generated successfully!")
print(response.text)
