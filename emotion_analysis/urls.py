from django.urls import path
from . import views

urlpatterns = [
    # Páginas públicas
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Área autenticada
    path('dashboard/', views.dashboard, name='dashboard'),
    path('record/', views.record_audio, name='record_audio'),
    path('analyze/<int:recording_id>/', views.analyze_audio, name='analyze_audio'),
    path('process-analysis/<int:recording_id>/', views.process_emotion_analysis, name='process_emotion_analysis'),
    path('history/', views.history, name='history'),
    path('delete/<int:recording_id>/', views.delete_recording, name='delete_recording'),
]
