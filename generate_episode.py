
import os
import time
from pathlib import Path
from google import genai
from google.genai import types

# =========================
# إعداد Gemini
# =========================

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=180000,
        retry_options=types.HttpRetryOptions(
            attempts=1
        )
    )
)

MODEL = "gemini-3.5-flash-lite"

# =========================
# دالة الاتصال وإعادة المحاولة
# =========================

def ask_gemini(prompt, task_name="Gemini request"):

    max_attempts = 4

    for attempt in range(1, max_attempts + 1):

        try:
            print(
                f"{task_name}: attempt {attempt}/{max_attempts}",
                flush=True
            )

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=9000,
                    temperature=0.6
                )
            )

            if response.text:
                print("Gemini response received successfully.", flush=True)
                return response.text

            raise RuntimeError("Gemini returned an empty response")

        except Exception as error:

            print(f"Request failed: {error}", flush=True)

            if attempt == max_attempts:
                raise

            wait_time = attempt * 15

            print(
                f"Waiting {wait_time} seconds before retry...",
                flush=True
            )

            time.sleep(wait_time)


# =========================
# تجهيز مجلد النتائج
# =========================

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

draft_path = output_dir / "draft.txt"
episode_path = output_dir / "episode.txt"
review_path = output_dir / "review_info.txt"


# =========================
# المرحلة الأولى: كتابة الحلقة
# =========================

writing_prompt = """
أنت كاتب ومعدّ برامج تعليمية محترف للأطفال.

اكتب حلقة أصلية باللغة العربية الفصحى المبسطة
المفهومة للأطفال من عمر 5 إلى 9 سنوات.

شروط الحلقة:
- من 900 إلى 1100 كلمة منطوقة تقريباً.
- 8 مشاهد مترابطة بتسلسل قصصي واضح.
- مدة مستهدفة 8 إلى 10 دقائق حسب سرعة الراوي.
- اختر موضوعاً تعليمياً مناسباً بنفسك.
- ابدأ بلغز أو سؤال يجذب الطفل.
- اجعل المقدم يتحدث إلى الطفل مباشرة.
- أضف أسئلة تفاعلية ووقفات للتفكير.
- أضف تجربة آمنة يمكن تنفيذها بمساعدة شخص بالغ.
- كل مشهد يقدم معلومة جديدة.
- لا تكرر الفكرة نفسها لزيادة طول الحلقة.
- اكتب وصفاً بصرياً مفصلاً لكل مشهد.
- اكتب نص الراوي كاملاً دون اختصار.
- ميّز بوضوح بين الحقائق العلمية والقصص التخيلية.
- لا تخترع أحداثاً تاريخية أو علمية.
- لا تستخدم تشبيهاً قد يجعل الطفل يفهم المعلومة بشكل خاطئ.
- اختم بتلخيص وتحدٍ بسيط للطفل.

لكل مشهد اكتب:
1. عنوان المشهد.
2. وصف الصورة والحركة.
3. نص الراوي كاملاً.
4. المؤثرات الصوتية المقترحة.

في النهاية أضف:
- عنوان الحلقة.
- العمر المستهدف.
- الهدف التعليمي.
- قائمة الحقائق العلمية التي اعتمدت عليها.
"""

print("Writing first draft...", flush=True)

draft = ask_gemini(
    writing_prompt,
    task_name="Writing first draft"
)

draft_path.write_text(
    draft,
    encoding="utf-8"
)

print("Draft saved successfully.", flush=True)


# =========================
# المرحلة الثانية: المراجعة العلمية
# =========================

review_prompt = f"""
أنت مراجع علمي ومحرر متخصص في برامج الأطفال.

راجع الحلقة التالية مراجعة دقيقة.

المطلوب:
1. اكتشف الأخطاء العلمية والتاريخية.
2. اكتشف المعلومات المضللة أو التشبيهات غير الدقيقة.
3. صحح كل خطأ داخل نص الحلقة نفسه.
4. حافظ على القصة والتشويق والأسلوب المناسب للأطفال.
5. لا تضف حقائق غير متأكد منها.
6. لا تحذف المشاهد أو تختصر الحلقة بشدة.
7. حافظ على طول قريب من 900 إلى 1100 كلمة منطوقة.
8. تأكد أن التجارب آمنة ومفهومة.
9. لا تدّع أن المدة 8 إلى 10 دقائق إلا إذا كان حجم النص مناسباً فعلاً.
10. إذا كانت معلومة غير مؤكدة، أعد صياغتها بحذر أو احذفها.

أعد كتابة الحلقة كاملة بعد التصحيح.
لا تكتب تقريراً فقط؛ أريد النسخة النهائية كاملة.

الحلقة:

{draft}
"""

print("Reviewing and correcting the episode...", flush=True)

final_episode = ask_gemini(
    review_prompt,
    task_name="Reviewing episode"
)


# =========================
# المرحلة الثالثة: حفظ الحلقة النهائية
# =========================

word_count = len(final_episode.split())

episode_path.write_text(
    final_episode,
    encoding="utf-8"
)

review_path.write_text(
    f"Model: {MODEL}\n"
    f"Final word count: {word_count}\n"
    "Scientific review: Completed\n"
    "Note: Word count is an estimate, not a measured narration duration.\n",
    encoding="utf-8"
)

print("\n================================")
print("FINAL EPISODE GENERATED!")
print(f"Approximate word count: {word_count}")
print(f"Saved to: {episode_path}")
print("================================", flush=True)
