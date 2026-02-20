from django.urls import path
from . import views

urlpatterns = [
    # Páginas públicas
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Áudio
    path('record/', views.record_audio, name='record_audio'),
    path('analyze/<int:recording_id>/', views.analyze_audio, name='analyze_audio'),
    path('process-analysis/<int:recording_id>/', views.process_emotion_analysis, name='process_emotion_analysis'),
    path('history/', views.history, name='history'),
    path('delete/<int:recording_id>/', views.delete_recording, name='delete_recording'),

    # Perfil
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
    path('games/emotion-identify/', views.emotion_identify_game, name='emotion_identify_game'),
    path('games/gratitude/', views.gratitude_challenge, name='gratitude_challenge'),
    path('games/reflection/', views.reflection_game, name='reflection_game'),
    path('games/save-score/', views.save_game_score, name='save_game_score'),

    # Confessionário Virtual / Diário
    path('journal/save/', views.save_journal_entry, name='save_journal_entry'),
    path('journal/feed/', views.journal_feed, name='journal_feed'),
    path('journal/like/<int:entry_id>/', views.like_journal_entry, name='like_journal_entry'),
    path('journal/audio/', views.save_journal_audio, name='save_journal_audio'),

    # Amigos
    path('friends/', views.friends_list, name='friends_list'),
    path('friends/request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friends/respond/<int:friendship_id>/', views.respond_friend_request, name='respond_friend_request'),
    path('friends/block/<int:user_id>/', views.block_user, name='block_user'),

    # Chat
    path('chat/<int:user_id>/', views.chat_view, name='chat_view'),
    path('chat/<int:user_id>/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/<int:user_id>/messages/', views.get_chat_messages, name='get_chat_messages'),

    # Notificações
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/count/', views.get_unread_count, name='get_unread_count'),

    # Grupos de Apoio
    path('groups/', views.support_groups, name='support_groups'),
    path('groups/create/', views.create_support_group, name='create_support_group'),
    path('groups/<int:group_id>/join/', views.join_support_group, name='join_support_group'),
    path('groups/<int:group_id>/chat/', views.group_chat, name='group_chat'),
    path('groups/<int:group_id>/send/', views.send_group_message, name='send_group_message'),
]
