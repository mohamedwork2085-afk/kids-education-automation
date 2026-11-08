import json
import os
from pathlib import Path
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
OUT.mkdir(exist_ok=True)
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("Missing GEMINI_API_KEY GitHub secret.")

MODEL = os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
client = genai.Client(api_key=API_KEY)

prompt = """
اكتب حلقة وثائقية عربية أصلية لقناة DARK FILES AI عن لغز تاريخي أو ظاهرة غريبة موثقة.
الأسلوب: تشويق هادئ، سرد مصري طبيعي مفهوم، من غير مبالغة أو ادعاء أن الخيال حقيقة.
اختر موضوعاً له مصادر عامة معروفة. لا تخترع أسماء باحثين أو تواريخ أو اقتباسات.
لو المعلومة غير مؤكدة قل ذلك بوضوح داخل السرد. لا تقدم نظريات المؤامرة كحقائق.
أخرج JSON فقط بالشكل التالي:
{
 "title": "عنوان عربي جذاب",
 "description": "وصف مختصر للحلقة",
 "topic_visual_search": "عبارة بحث إنجليزية قصيرة للصور",
 "scenes": [
  {"narration":"فقرة الراوي بالمصري من 55 إلى 85 كلمة","visual_search":"عبارة بحث إنجليزية دقيقة للصورة"}
 ],
 "short_title":"عنوان قصير",
 "short_narration":"نص تشويقي مستقل مدته 35 إلى 55 ثانية بالمصري",
 "sources":[{"name":"اسم مصدر معروف","url":"رابط مباشر أو صفحة مؤسسة موثوقة"}]
}
اجعل الحلقة الطويلة كافية تقريباً لـ 6 إلى 8 دقائق، واكتب 10 إلى 12 مشهداً.
كل مشهد يكمل الذي قبله. تجنب وصف مشاهد دموية أو عنف صريح.
لا تكتب Markdown ولا أي نص خارج JSON.
"""

response = client.models.generate_content(
    model=MODEL,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.65,
        max_output_tokens=12000
    )
)
raw = (response.text or "").strip()
fence = chr(96) * 3
raw = raw.replace(fence + "json", "").replace(fence, "").strip()
data = json.loads(raw)

if not data.get("title") or len(data.get("scenes", [])) < 6:
    raise SystemExit("Gemini returned an incomplete episode. Please rerun.")
for scene in data["scenes"]:
    if not scene.get("narration") or not scene.get("visual_search"):
        raise SystemExit("A scene is missing narration or visual_search.")

(OUT / "episode.json").write_text(
    json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("Generated:", data["title"])
print("Scenes:", len(data["scenes"]))
