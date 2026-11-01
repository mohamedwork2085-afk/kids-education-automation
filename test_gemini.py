import os
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing!")

client = genai.Client(api_key=api_key)

prompt = """
اقترح فكرة حلقة تعليمية ممتعة للأطفال من سن 5 إلى 9 سنوات.
اكتب:
1. عنوان الحلقة.
2. الفكرة التعليمية.
3. ملخص الحلقة في 5 نقاط.
4. معلومة علمية أو تعليمية صحيحة يتعلمها الطفل.

اكتب باللغة العربية البسيطة، واجعل الفكرة ممتعة وآمنة ومناسبة للأطفال.
"""

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents=prompt
)

print("نجح الاتصال بـ Gemini!")
print(response.text)
