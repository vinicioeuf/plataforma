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
    
    # Configuração de perfil
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    
    # Telepsicologia
    path('consultations/', views.consultations, name='consultations'),
    path('consultations/schedule/', views.schedule_consultation, name='schedule_consultation'),
    path('consultations/<int:consultation_id>/', views.consultation_detail, name='consultation_detail'),
    path('consultations/<int:consultation_id>/message/', views.send_message, name='send_message'),
    
    # Jogos
    path('games/', views.games_menu, name='games_menu'),
    path('games/memory/', views.memory_game, name='memory_game'),
    path('games/breathing/', views.breathing_exercise, name='breathing_exercise'),
    path('games/color-matching/', views.color_matching_game, name='color_matching_game'),
    path('games/save-score/', views.save_game_score, name='save_game_score'),
    
    # Confessionário Virtual
    path('journal/save/', views.save_journal_entry, name='save_journal_entry'),
]
