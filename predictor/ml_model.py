import os
import tensorflow as tf
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "potato_disease_classifier_v1.keras")

IMAGE_SIZE = 256
CLASS_NAMES = [
    "Potato___Early_blight",
    "Potato___healthy",
    "Potato___Late_blight",
]

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = tf.keras.models.load_model(MODEL_PATH)
            print(f"Loaded model from: {MODEL_PATH}")
        except Exception as e:
            print(f"Error loading model: {e}")
    return _model

def predict_image(img_path):
    """Predict the class of a single image and return a dict."""
    model = get_model()
    if model is None:
        return None
        
    try:
        img = tf.keras.preprocessing.image.load_img(
            img_path, target_size=(IMAGE_SIZE, IMAGE_SIZE)
        )
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0)

        predictions = model.predict(img_array, verbose=0)
        class_idx = np.argmax(predictions[0])
        predicted_class = CLASS_NAMES[class_idx]
        confidence = float(np.max(predictions[0]))

        parts = predicted_class.split("___")
        if len(parts) == 2:
            crop = parts[0]
            disease = parts[1].replace("_", " ")
        else:
            crop = "Unknown"
            disease = predicted_class.replace("_", " ")

        return {
            "crop": crop,
            "disease": disease,
            "confidence": confidence
        }
    except Exception as e:
        print(f"Error predicting image: {e}")
        return None
