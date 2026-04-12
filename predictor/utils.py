import requests

def get_ai_recommendation(crop, disease,sensor=None):
    if sensor:
        sensor_info = f"""
        Temperature: {sensor.temperature}
        Humidity: {sensor.humidity}
        Gas: {sensor.gas}
        Soil Moisture: {sensor.moisture}
        """

    prompt = f"""
    Crop: {crop}
    Disease: {disease}

    Give:
    1. Treatment
    2. Fertilizer suggestion
    3. Yield improvement tips
    4. Yield prediction
    """

    import requests

def get_ai_recommendation(crop, disease):
    prompt = f"""
    Crop: {crop}
    Disease: {disease}

    Give:
    1. Treatment
    2. Fertilizer suggestion
    3. Yield improvement tips
    4. Yield prediction
    """

    try:
        res = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1:8b",
                "prompt": prompt,
                "stream": False
            }
        )

        data = res.json()

        # ✅ SAFE ACCESS
        if "response" in data:
            return data["response"]
        else:
            return f"⚠️ Ollama Error: {data}"

    except Exception as e:
        return f"❌ Connection Error: {str(e)}"