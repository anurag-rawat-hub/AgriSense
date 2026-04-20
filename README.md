<h1 align="center">🌾 Smart Crop Disease Detection & Advisory System</h1>

<h4 align="center">🥇 1st Place – TECHNOTSAV (AIoT & Robotics), VVCE Mysuru</h4>

<br>

<h6 align="center">
An AI-powered agriculture solution designed to help farmers detect crop diseases early, receive actionable recommendations, and improve yield using Machine Learning + IoT.
</h6>

<br>

<h2>✨ Features</h2>

🌿 <b>Crop & Disease Detection</b><br>
Detects crop type and diseases using CNN-based models.
<br><br>

🤖 <b>AI-Powered Advisory System</b><br>
Uses LLM (LLaMA 3.1 via Ollama) to generate smart recommendations.
<br><br>

📊 <b>Yield Prediction</b><br>
Predicts crop yield based on environmental and crop conditions.
<br><br>

🌡️ <b>Real-Time IoT Monitoring</b><br>
Collects data from:<br>
Temperature & Humidity (DHT11)<br>
Air Quality (MQ135)<br>
Soil Moisture Sensor
<br><br>

📲 <b>WhatsApp Integration</b><br>
Sends recommendations in regional languages for better accessibility.

<br><br>

<h2>📸 Demo & Screenshots</h2>

<p align="center">
  <img src="images/leaf-detection.jpg" width="45%">
  <img src="images/dashboard.jpg" width="45%">
</p>

<p align="center">
  <img src="images/assistant.jpg" width="45%">
  <img src="images/ai-advice.jpg" width="45%">
</p>

<p align="center">
  <img src="images/whatsapp.jpg" width="40%">
</p>

<br>

<h2>🛠️ Tech Stack</h2>

<b>Backend:</b> FastAPI / Django<br>
<b>AI/ML:</b> TensorFlow (CNN Models), LLaMA 3.1 (Ollama)<br>
<b>IoT:</b> ESP32, DHT11, MQ135, Soil Moisture Sensor<br>
<b>Frontend:</b> HTML, CSS, JavaScript<br>
<b>Integration:</b> WhatsApp API

<br><br>

<h2>⚙️ Workflow</h2>

User uploads leaf image → CNN Model detects disease → Backend processes data → AI Agent generates recommendations → IoT data is integrated → Final output sent via WhatsApp
