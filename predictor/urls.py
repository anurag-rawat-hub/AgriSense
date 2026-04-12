from django.urls import path
from . import views

urlpatterns = [
    path('', views.index),
    path('predict/', views.predict),
    path('sensor/', views.sensor_data),
    path('get-sensor-data/', views.get_sensor_data),
    path('dashboard/', views.dashboard),
    path('ai/', views.ai_page),
    path('ask-ai/', views.ask_ai),
]