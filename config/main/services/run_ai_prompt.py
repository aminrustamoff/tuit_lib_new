from django.conf import settings
from django.utils.html import strip_tags
from google import genai


def build_history_text(history):
    """
    Frontenddan kelgan oxirgi xabarlarni AI prompt ichiga qo'shish uchun tayyorlaydi.
    history formati:
    [
        {"role": "user", "text": "Salom"},
        {"role": "assistant", "text": "Salom! Qanday yordam beray?"}
    ]
    """

    if not history:
        return "Oldingi yozishmalar mavjud emas."

    lines = []

    for item in history[-6:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role", "")
        text = str(item.get("text", "")).strip()

        if not text:
            continue

        # AI javoblari HTML bo'lishi mumkin, tarix uchun text holatiga keltiramiz
        text = strip_tags(text)

        if role == "user":
            role_name = "Foydalanuvchi"
        elif role in ["assistant", "ai", "model"]:
            role_name = "AI"
        else:
            role_name = "Noma'lum"

        lines.append(f"{role_name}: {text}")

    return "\n".join(lines) if lines else "Oldingi yozishmalar mavjud emas."


def run_ai_prompt(prompt, user=None, book_name_list=None, history=None):
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY topilmadi. "
            "Iltimos, environment variable yoki settings.py da GEMINI_API_KEY ni o'rnating. "
            "API key: https://aistudio.google.com/apikey"
        )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
    except Exception as e:
        raise ValueError(f"Gemini client tayyorlanishida xatolik: {str(e)}")

    books_text = (
        ", ".join(book_name_list)
        if book_name_list
        else "Hech qanday kitob mavjud emas."
    )

    history_text = build_history_text(history)

    system_text = (
        "Sen foydalanuvchiga sodda, aniq va foydali javob beradigan yordamchisan. "
        "Foydalanuvchi savoliga javob berishda, agar kerak bo'lsa, quyidagi kitob nomlaridan foydalanib tavsiyalar ber. "
        f"Kitoblar: {books_text} "
        "Agar foydalanuvchi kitob tavsiyasi so'rasa, mavjud kitoblardan birini tavsiya qil. "
        "Agar foydalanuvchi boshqa kitob haqida savol bersa, bu kitob mavjud emasligini ayt va unga aniq shu kitobga o'xshash mavjud kitoblarni tavsiya qil. "
        "Agar foydalanuvchi kitoblardan tashqari savol bersa, unga 'men kitoblar haqida savolga javob berishga ixtisoslashgan yordamchiman, iltimos, kitoblar bilan bog'liq savol bering' deb javob ber. "
        "Agar hech qanday kitob mavjud bo'lmasa, foydalanuvchiga kitoblar mavjud emasligini bildir. "
        "Javobni chiroyli formatlash uchun HTML taglardan foydalan. "
        "Faqat body ichida ishlaydigan oddiy HTML taglardan foydalan: p, br, b, strong, i, ul, ol, li, h3, h4. "
        "script, style, iframe kabi xavfli taglardan foydalanma. "
    )

    full_prompt = f"""
{system_text}

Oldingi yozishmalar:
{history_text}

Hozirgi foydalanuvchi savoli:
{prompt}
"""

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=full_prompt
    )

    return response.text or "AI javob qaytarmadi."