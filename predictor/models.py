from django.db import models

class SensorData(models.Model):
    temperature = models.FloatField()
    humidity = models.FloatField()
    gas = models.FloatField()
    moisture = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)