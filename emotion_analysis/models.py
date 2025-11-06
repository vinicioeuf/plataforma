from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class AudioRecording(models.Model):
    """
    Modelo para armazenar gravações de áudio dos usuários
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='audio_recordings',
        verbose_name='Usuário'
    )
    title = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Descrição'
    )
    audio_file = models.FileField(
        upload_to='audio_recordings/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'ogg', 'webm', 'm4a'])],
        verbose_name='Arquivo de Áudio'
    )
    duration = models.FloatField(
        null=True,
        blank=True,
        help_text='Duração em segundos',
        verbose_name='Duração'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gravação de Áudio'
        verbose_name_plural = 'Gravações de Áudio'

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class EmotionAnalysis(models.Model):
    """
    Modelo para armazenar os resultados da análise de emoção
    """
    EMOTION_CHOICES = [
        ('alegria', 'Alegria'),
        ('tristeza', 'Tristeza'),
        ('raiva', 'Raiva'),
        ('medo', 'Medo'),
        ('surpresa', 'Surpresa'),
        ('nojo', 'Nojo'),
        ('neutro', 'Neutro'),
    ]

    recording = models.OneToOneField(
        AudioRecording,
        on_delete=models.CASCADE,
        related_name='emotion_analysis',
        verbose_name='Gravação'
    )
    dominant_emotion = models.CharField(
        max_length=20,
        choices=EMOTION_CHOICES,
        verbose_name='Emoção Dominante'
    )
    confidence = models.FloatField(
        help_text='Confiança da análise (0-1)',
        verbose_name='Confiança'
    )
    emotions_data = models.JSONField(
        help_text='Dados detalhados de todas as emoções detectadas',
        verbose_name='Dados das Emoções'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Analisado em'
    )

    class Meta:
        ordering = ['-analyzed_at']
        verbose_name = 'Análise de Emoção'
        verbose_name_plural = 'Análises de Emoções'

    def __str__(self):
        return f"Análise de '{self.recording.title}' - {self.dominant_emotion}"

    def get_emotion_display_name(self):
        """Retorna o nome amigável da emoção"""
        return dict(self.EMOTION_CHOICES).get(self.dominant_emotion, self.dominant_emotion)

    def get_confidence_percentage(self):
        """Retorna a confiança em porcentagem"""
        return round(self.confidence * 100, 2)
