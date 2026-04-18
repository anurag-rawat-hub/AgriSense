#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DHT.h"

// =================CONFIG=================
const char* ssid = "wifi_name";
const char* password = "password";

// Your computer's local IP address where Django is running
// Make sure you start django with: python manage.py runserver 0.0.0.0:8000
const char* serverName = "http://10.135.96.3:8000/sensor/";
// ========================================

// DHT11 setup
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Analog pins
#define MQ135_PIN 34
#define SOIL_MOISTURE_PIN 35

void setup() {
  Serial.begin(115200);
  
  dht.begin();
  
  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // 1. Read Sensors
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  
  int gas_value = analogRead(MQ135_PIN);
  
  // Soil moisture calibration: 0 in water, 4095 dry on ESP32 (usually)
  // Let's convert to a rough percentage (0-100%)
  int raw_moisture = analogRead(SOIL_MOISTURE_PIN);
  float moisture_percent = map(raw_moisture, 4095, 0, 0, 100);
  if (moisture_percent < 0) moisture_percent = 0;
  if (moisture_percent > 100) moisture_percent = 100;

  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }

  // 2. Output to Serial
  Serial.printf("Temp: %.2f C, Hum: %.2f %%, Gas: %d, Moisture: %.2f %%\n", t, h, gas_value, moisture_percent);

  // 3. Send HTTP POST request
  if(WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverName);
    http.addHeader("Content-Type", "application/json");

    // Create JSON Document
    StaticJsonDocument<200> doc;
    doc["temperature"] = t;
    doc["humidity"] = h;
    doc["gas"] = gas_value;
    doc["moisture"] = moisture_percent;

    String jsonStr;
    serializeJson(doc, jsonStr);

    int httpResponseCode = http.POST(jsonStr);

    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }

  // Wait 10 seconds before sending next reading
  delay(10000);
}