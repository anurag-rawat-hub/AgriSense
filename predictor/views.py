import requests
import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt

from .ml_model import predict_image
from .utils import get_ai_recommendation


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

        if 'image' not in request.FILES:
            return JsonResponse({"error": "No image uploaded"}, status=400)

        image = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        file_path = fs.path(filename)

        print(" Image saved:", file_path)

        try:
            #  ML Prediction
            result = predict_image(file_path)

            if not result:
                return JsonResponse({"error": "ML model failed"}, status=500)

            print("🧠 Result:", result)

        except Exception as e:
            print("❌ ML ERROR:", str(e))
            return JsonResponse({"error": "ML prediction failed"}, status=500)

        try:
            # AI Recommendation
            ai_output = get_ai_recommendation(
                result.get("crop", "Unknown"),
                result.get("disease", "Unknown")
            )

        except Exception as e:
            print("❌ AI ERROR:", str(e))
            ai_output = "AI unavailable"

        return JsonResponse({
            "crop": result.get("crop"),
            "disease": result.get("disease"),
            "confidence": result.get("confidence"),
            "ai": ai_output
        })

    return JsonResponse({"error": "Invalid request"}, status=405)
from .models import SensorData
import json

@csrf_exempt
def sensor_data(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            sensor = SensorData.objects.create(
                temperature=data.get("temperature"),
                humidity=data.get("humidity"),
                gas=data.get("gas"),
                moisture=data.get("moisture")
            )

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"})


@csrf_exempt
def ask_ai(request):
    import requests   #  force import inside function

    if request.method == "POST":
        data = json.loads(request.body)
        question = data.get("question")

        try:
            res = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": question,
                    "stream": False
                }
            )

            result = res.json()
            answer = result.get("response", "No response")

        except Exception as e:
            print("ERROR:", e)
            answer = "AI not available"

        return JsonResponse({"answer": answer})