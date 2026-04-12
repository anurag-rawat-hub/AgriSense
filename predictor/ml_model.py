import torch
from torchvision import transforms
from PIL import Image

# Dummy labels (replace with real trained model)
CROPS = ["Tomato", "Potato", "Corn"]
DISEASES = ["Healthy", "Leaf Blight", "Rust"]

def predict_image(image_path):
    try:
        return {
            "crop": "Tomato",
            "disease": "Leaf Blight",
            "confidence": 0.92
        }
    except:
        return None   # ✅ important