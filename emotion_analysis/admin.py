from django.contrib import admin
from .models import AudioRecording, EmotionAnalysis

@admin.register(AudioRecording)
class AudioRecordingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'created_at', 'duration']
    list_filter = ['created_at', 'user']
    search_fields = ['title', 'user__username']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'title', 'description')
        }),
        ('Arquivo de Áudio', {
            'fields': ('audio_file', 'duration')
        }),
        ('Metadados', {
            'fields': ('created_at',)
        }),
    )

@admin.register(EmotionAnalysis)
class EmotionAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'recording', 'get_user', 'dominant_emotion', 'confidence', 'analyzed_at']
    list_filter = ['analyzed_at', 'dominant_emotion']
    search_fields = ['recording__title', 'recording__user__username', 'dominant_emotion']
    readonly_fields = ['analyzed_at']
    
    def get_user(self, obj):
        return obj.recording.user.username
    get_user.short_description = 'Usuário'
    
    fieldsets = (
        ('Gravação', {
            'fields': ('recording',)
        }),
        ('Resultado da Análise', {
            'fields': ('dominant_emotion', 'confidence', 'emotions_data')
        }),
        ('Observações', {
            'fields': ('notes', 'analyzed_at')
        }),
    )
