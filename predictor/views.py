import requests
import os
import json
import numpy as np
from io import BytesIO
from PIL import Image

from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt

from .ml_model import predict_image
from .utils import get_ai_recommendation

TARGET_SIZE = (256, 256)
TF_SERVING_BASE_URL = os.getenv("TF_SERVING_BASE_URL", "http://10.135.96.96:8501/v1/models")

MODEL_MAPPING = {
    "tomato": "tomato_model",
    "pepper": "bell_pepper_model",
}

CLASS_MAPPING = {
    "tomato": ["Bacterial Spot", "Early Blight", "Late Blight", "Leaf Mold", "Septoria Leaf Spot", "Spider Mites", "Target Spot", "Yellow Leaf Curl Virus", "Mosaic Virus", "Healthy"],
    "pepper": ["Bacterial Spot", "Healthy"],
}


# Landing Page
def landing(request):
    return render(request, "landing.html")

# Dashboard (Index) Page
def index(request):
    return render(request, "index.html")

def get_sensor_data(request):
    data = SensorData.objects.all().order_by('-created_at')[:20]
    result = []
    for d in data:
        result.append({
            "temperature": d.temperature,
            "humidity": d.humidity,
            "gas": d.gas,
            "moisture": d.moisture,
            "time": d.created_at.strftime("%H:%M")
        })

    return JsonResponse(result, safe=False)

def ai_page(request):
    return render(request, "ai.html")


def dashboard(request):
    return render(request, "dashboard.html")

#  Prediction API
@csrf_exempt
def predict(request):
    if request.method == "POST":
        crop_type = request.POST.get("crop", "potato")
        
        if 'image' not in request.FILES:
            return JsonResponse({"error": "No image uploaded"}, status=400)

        image_file = request.FILES['image']
        
        if crop_type in MODEL_MAPPING:
            # Docker TF Serving Logic
            try:
                img_data = image_file.read()
                image = Image.open(BytesIO(img_data)).convert("RGB")
                image = image.resize(TARGET_SIZE)
                img_array = np.array(image)
                img_batch = np.expand_dims(img_array, axis=0)

                model_name = MODEL_MAPPING[crop_type]
                endpoint = f"{TF_SERVING_BASE_URL}/{model_name}:predict"

                payload = {"instances": img_batch.tolist()}
                response = requests.post(endpoint, json=payload, timeout=10)

                if response.status_code != 200:
                    return JsonResponse({"error": f"TF Serving error: {response.text}"}, status=500)

                prediction = np.array(response.json()["predictions"][0])
                plant_classes = CLASS_MAPPING[crop_type]
                predicted_class = plant_classes[np.argmax(prediction)]
                confidence = np.max(prediction)

                result = {
                    "crop": crop_type.capitalize(),
                    "disease": predicted_class,
                    "confidence": float(confidence)
                }
            except Exception as e:
                print("❌ TF ENGINE ERROR:", str(e))
                return JsonResponse({"error": "TF Serving prediction failed"}, status=500)
        else:
            # Local ML Logic for potato
            fs = FileSystemStorage()
            filename = fs.save(image_file.name, image_file)
            file_path = fs.path(filename)
            try:
                result = predict_image(file_path)
                if not result:
                    return JsonResponse({"error": "ML model failed"}, status=500)
            except Exception as e:
                print("❌ LOCAL ML ERROR:", str(e))
                return JsonResponse({"error": "Local ML prediction failed"}, status=500)

        return JsonResponse({
            "crop": result.get("crop"),
            "disease": result.get("disease"),
            "confidence": result.get("confidence"),
            "ai": ""
        })

    return JsonResponse({"error": "Invalid request"}, status=405)
from .models import SensorData
import json

import time as _time

_last_whatsapp_alert_time = 0
WHATSAPP_COOLDOWN_SECONDS = 600  # 10 minutes — change as needed

def notify_whatsapp(message, phone):
    global _last_whatsapp_alert_time

    now = _time.time()
    if now - _last_whatsapp_alert_time < WHATSAPP_COOLDOWN_SECONDS:
        print(f"⏳ WhatsApp alert skipped — cooldown active ({int(WHATSAPP_COOLDOWN_SECONDS - (now - _last_whatsapp_alert_time))}s remaining)")
        return

    url = "http://10.135.96.96:8001/send-alert"
    payload = {
        "message": str(message),
        "to_phone": str(phone)
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"FastAPI Response: {response.status_code} - {response.text}")
        _last_whatsapp_alert_time = now  # Update timestamp only on successful send attempt
    except Exception as e:
        print(f"Connection failed: {e}")


@csrf_exempt
def sensor_data(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            moisture = data.get("moisture")

            sensor = SensorData.objects.create(
                temperature=data.get("temperature"),
                humidity=data.get("humidity"),
                gas=data.get("gas"),
                moisture=moisture
            )

            # WhatsApp alert if moisture > 2
            try:
                if moisture is not None and int(moisture) >=100:
                    notify_whatsapp(
                        message=f"🚨 Alert: Soil moisture is high ({moisture}%). Check your irrigation system immediately.",
                        phone="+919039128679"
                    )
            except Exception as alert_err:
                print(f"Failed to send WhatsApp alert: {alert_err}")

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"})


@csrf_exempt
def ask_ai(request):
    import requests   #  force import inside function

    if request.method == "POST":
        data = json.loads(request.body)
        
        crop = data.get("crop")
        disease = data.get("disease")
        question = data.get("question")
        
        if crop and disease:
            latest_sensor = SensorData.objects.last()
            temp = getattr(latest_sensor, 'temperature', 'N/A') if latest_sensor else 'N/A'
            humidity = getattr(latest_sensor, 'humidity', 'N/A') if latest_sensor else 'N/A'
            moisture = getattr(latest_sensor, 'moisture', 'N/A') if latest_sensor else 'N/A'
            gas = getattr(latest_sensor, 'gas', 'N/A') if latest_sensor else 'N/A'

            prompt = f"""You are an expert agronomist AI assistant. Analyze the crop disease and sensor data below, then give precise, actionable advice.

Crop    : {crop}
Disease : {disease}

Current Sensor Readings:
- Temperature   : {temp} °C
- Humidity      : {humidity} %
- Soil Moisture : {moisture}
- Gas Level     : {gas} ppm

Using the sensor data above, provide your recommendations strictly in the following format.
You may give up to 3-4 bullet points per section where needed. Keep each point concise (1-2 lines max). No paragraphs.

--- Sensor Summary ---
Briefly describe what the sensor readings indicate about the current growing conditions.

1. Treatment:
- [Specific action for disease control]
- [Product name + purchase link (Amazon/Flipkart style)]

2. Fertilizer Suggestion:
- [Specific fertilizer recommendation based on disease and soil moisture]
- [Product name + purchase link]

3. Yield Improvement Tips:
- [Tip tailored to current temperature and humidity]
- [Tip based on gas/moisture conditions]

4. Yield Prediction:
- [Estimated yield impact given current disease severity and sensor conditions]
"""
        else:
            prompt = question

        try:
            res = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False
                }
            )

            result = res.json()
            answer = result.get("response", "No response")

        except Exception as e:
            print("ERROR:", e)
            answer = "AI not available"

        return JsonResponse({"answer": answer})