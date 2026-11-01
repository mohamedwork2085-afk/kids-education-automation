import os
from pathlib import Path
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=api_key)

prompt = """
أنت كاتب ومعدّ برامج تعليمية محترف للأطفال.

اكتب حلقة تعليمية أصلية باللغة العربية البسيطة المناسبة للأطفال من 5 إلى 9 سنوات.

الشروط:
- مدة الحلقة من 8 إلى 10 دقائق.
- موضوع الحلقة: اختر بنفسك موضوعاً علمياً أو تعليمياً ممتعاً.
- ابدأ بمقدمة تشد انتباه الطفل.
- اشرح المعلومة بطريقة سهلة وبأمثلة من الحياة اليومية.
- اجعل الأحداث مترابطة وفيها تشويق وأسئلة للطفل.
- قسّم الحلقة إلى 8 مشاهد متتابعة.
- اكتب نص الراوي كاملاً لكل مشهد.
- اقترح وصفاً بصرياً لكل مشهد ليسهل تحويله إلى رسوم متحركة.
- تأكد من صحة المعلومات علمياً.
- لا تستخدم معلومات مخيفة أو محتوى غير مناسب للأطفال.
- اختم بمراجعة بسيطة لما تعلمه الطفل.

اكتب النتيجة بهذا الترتيب:
عنوان الحلقة
الفئة العمرية
الهدف التعليمي
نص الحلقة مقسماً إلى 8 مشاهد
خاتمة الحلقة
"""

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=prompt
)

episode = response.text

if not episode:
    raise RuntimeError("Gemini returned an empty response")

Path("output").mkdir(exist_ok=True)
Path("output/episode.txt").write_text(episode, encoding="utf-8")

print("Episode generated successfully!")
print(episode)
