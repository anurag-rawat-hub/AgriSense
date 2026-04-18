import os

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from io import BytesIO
from PIL import Image
import requests

app = FastAPI()

# Add CORS middleware to allow the frontend to call this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (e.g., your Django frontend)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TARGET_SIZE = (256, 256)
TF_SERVING_BASE_URL = os.getenv(
    "TF_SERVING_BASE_URL", "http://localhost:8501/v1/models"
)

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

@app.get("/ping")
async def ping():
    return "Server is online"

def read_file_as_image(data) -> np.ndarray:
    image = Image.open(BytesIO(data)).convert("RGB")
    image = image.resize(TARGET_SIZE)
    return np.array(image)

@app.post("/predict/{plant_type}")
async def predict(plant_type: str, file: UploadFile = File(...)):
    if plant_type not in MODEL_MAPPING:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plant type. Choose from: {list(MODEL_MAPPING.keys())}",
        )

    image = read_file_as_image(await file.read())
    img_batch = np.expand_dims(image, axis=0)

    model_name = MODEL_MAPPING[plant_type]
    endpoint = f"{TF_SERVING_BASE_URL}/{model_name}:predict"

    payload = {"instances": img_batch.tolist()}
    
    try:
        response = requests.post(endpoint, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
         raise HTTPException(
            status_code=500, detail=f"Error connecting to TF Serving: {str(e)}"
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500, detail=f"TF Serving returned {response.status_code}: {response.text}"
        )

    prediction = np.array(response.json()["predictions"][0])

    # Correctly pull the list of names for THIS specific plant
    plant_classes = CLASS_MAPPING[plant_type]

    predicted_class = plant_classes[np.argmax(prediction)]

    confidence = np.max(prediction)

    return {
        "plant": plant_type,
        "class": predicted_class,
        "confidence": round(float(confidence), 4),
    }

if __name__ == "__main__":
    import uvicorn
    # Assuming this runs alongside Django, you might want to run it on 8001
    # or if you stop Django, run on 8000.
    uvicorn.run(app, host="localhost", port=8001)
