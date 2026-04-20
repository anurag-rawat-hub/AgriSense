import os
import httpx
import numpy as np
from io import BytesIO
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Response, HTTPException
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

app = FastAPI()

AI_URL = os.getenv("AI_URL", "http://localhost:11434/v1")
AI_MODEL = os.getenv("AI_MODEL", "llama3")
AI_KEY = os.getenv("AI_KEY", "ollama")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TARGET_SIZE = (256, 256)
TF_SERVING_BASE_URL = os.getenv(
    "TF_SERVING_BASE_URL", "http://localhost:8501/v1/models"
)

ai_client = OpenAI(base_url=AI_URL, api_key=AI_KEY)


LANG_MAPPING = {
    "hi": "English",
    "hello": "English",
    "namaskar": "Hindi",
    "namaskara": "Kannada",
    "vanakkam": "Tamil",
    "namaste": "Hindi",
}

MODEL_MAPPING = {
    "potato": "potato_model",
    "tomato": "tomato_model",
    "pepper": "bell_pepper_model",
}

CLASS_MAPPING = {
    "potato": ["Early Blight", "Late Blight", "Healthy"],
    "tomato": [
        "Bacterial Spot",
        "Early Blight",
        "Late Blight",
        "Leaf Mold",
        "Septoria Leaf Spot",
        "Spider Mites",
        "Target Spot",
        "Yellow Leaf Curl Virus",
        "Mosaic Virus",
        "Healthy",
    ],
    "pepper": ["Bacterial Spot", "Healthy"],
}

# user_sessions structure: { "phone_number": {"crop": "potato", "lang": "Hindi"} }
user_sessions = {}


def read_file_as_image(data: bytes) -> np.ndarray:
    image = Image.open(BytesIO(data)).convert("RGB").resize(TARGET_SIZE)
    img_array = np.array(image).astype(np.float32) / 255.0
    return img_array


async def get_ai_recommendation(plant_type: str, disease: str, language: str):

    prompt = f"""You are an agriculture specialist. A farmer's {plant_type} has {disease}. 
    Give direct, actionable treatment advice. Max 8 lines. 
    IMPORTANT: Respond ONLY in {language}."""

    try:
        response = ai_client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Service error: {str(e)}"


@app.post("/whatsapp")
async def whatsapp_webhook(
    Body: str = Form(None), MediaUrl0: str = Form(None), From: str = Form(...)
):
    twiml_res = MessagingResponse()
    user_input = Body.strip().lower() if Body else ""

    if user_input in LANG_MAPPING:
        detected_lang = LANG_MAPPING[user_input]
        user_sessions[From] = {"lang": detected_lang, "crop": None}

        greetings = {
            "Hindi": "नमस्ते! AgriSense में आपका स्वागत है। 🌿\nकृपया फसल चुनें:\n1. Potato\n2. Tomato\n3. Pepper",
            "Kannada": "ನಮಸ್ಕಾರ! AgriSense ಗೆ ಸುಸ್ವಾಗತ. 🌿\nದಯವಿಟ್ಟು ಬೆಳೆಯನ್ನು ಆರಿಸಿ:\n1. Potato\n2. Tomato\n3. Pepper",
            "English": "Welcome to AgriSense! 🌿\nSelect a crop to analyze:\n1. Potato\n2. Tomato\n3. Pepper",
        }
        twiml_res.message(greetings.get(detected_lang, greetings["English"]))
        return Response(content=str(twiml_res), media_type="application/xml")

    crops = {
        "1": "potato",
        "2": "tomato",
        "3": "pepper",
        "potato": "potato",
        "tomato": "tomato",
        "pepper": "pepper",
    }

    if user_input in crops:
        selected = crops[user_input]
        if From not in user_sessions:
            user_sessions[From] = {"lang": "English", "crop": selected}
        else:
            user_sessions[From]["crop"] = selected

        lang = user_sessions[From]["lang"]
        prompt_text = "Please upload a photo of the leaf."
        if lang == "Hindi":
            prompt_text = "कृपया पत्ती की फोटो अपलोड करें।"
        elif lang == "Kannada":
            prompt_text = "ದಯವಿಟ್ಟು ಎಲೆಯ ಫೋಟೋವನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ."

        twiml_res.message(f"*{selected.capitalize()}* - {prompt_text}")
        return Response(content=str(twiml_res), media_type="application/xml")

    # image processing
    if MediaUrl0:
        session = user_sessions.get(From)
        if not session or not session.get("crop"):
            twiml_res.message(
                "Please type 'Hi' or 'Namaste' to start and select a crop."
            )
            return Response(content=str(twiml_res), media_type="application/xml")

        plant_type = session["crop"]
        lang = session["lang"]

        try:
            async with httpx.AsyncClient() as client:
                image_res = await client.get(
                    MediaUrl0,
                    auth=(TWILIO_SID, TWILIO_TOKEN),
                    follow_redirects=True,
                    timeout=15.0,
                )

            if image_res.status_code != 200:
                twiml_res.message("Error downloading image.")
                return Response(content=str(twiml_res), media_type="application/xml")

            image = read_file_as_image(image_res.content)
            img_batch = np.expand_dims(image, axis=0)

            model_name = MODEL_MAPPING[plant_type]
            endpoint = f"{TF_SERVING_BASE_URL}/{model_name}:predict"

            async with httpx.AsyncClient() as client:
                tf_res = await client.post(
                    endpoint, json={"instances": img_batch.tolist()}
                )

            if tf_res.status_code == 200:
                predictions = np.array(tf_res.json()["predictions"][0])
                disease = CLASS_MAPPING[plant_type][np.argmax(predictions)]

                if "healthy" in disease.lower():
                    ai_advice = (
                        "Healthy plant!"
                        if lang == "English"
                        else "आपका पौधा स्वस्थ है!"
                        if lang == "Hindi"
                        else "ನಿಮ್ಮ ಗಿಡ ಆರೋಗ್ಯವಾಗಿದೆ!"
                    )
                else:
                    ai_advice = await get_ai_recommendation(plant_type, disease, lang)

                twiml_res.message(
                    f"🌿 *{plant_type.upper()}*\n*Result:* {disease}\n\n*Advice ({lang}):*\n{ai_advice}"
                )
            else:
                twiml_res.message("Prediction server error.")

        except Exception as e:
            twiml_res.message("Processing failed. Please send a clear leaf photo.")

    else:
        twiml_res.message("Please send a greeting like 'Hi' or 'Namaskar' to begin.")

    return Response(content=str(twiml_res), media_type="application/xml")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
