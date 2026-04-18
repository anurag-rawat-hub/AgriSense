import requests

def get_ai_recommendation(crop, disease, sensor=None):
    if sensor:
        sensor_block = f"""Current Sensor Readings:
- Temperature   : {getattr(sensor, 'temperature', 'N/A')} °C
- Humidity      : {getattr(sensor, 'humidity', 'N/A')} %
- Soil Moisture : {getattr(sensor, 'moisture', 'N/A')}
- Gas Level     : {getattr(sensor, 'gas', 'N/A')} ppm"""
    else:
        sensor_block = "Sensor data not available."

    prompt = f"""You are an expert agronomist AI assistant. Analyze the crop disease and sensor data below, then give precise, actionable advice.

Crop    : {crop}
Disease : {disease}

{sensor_block}

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
        if "response" in data:
            return data["response"]
        else:
            return f"Ollama Error: {data}"
    except Exception as e:
        return f"Connection Error: {str(e)}"