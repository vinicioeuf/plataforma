from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone


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


class UserProfile(models.Model):
    """Perfil estendido do usuário"""
    USER_TYPE_CHOICES = [
        ('patient', 'Paciente'),
        ('professional', 'Profissional'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='patient')
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    # Para profissionais
    license_number = models.CharField(max_length=50, blank=True, help_text='Número do registro profissional')
    specialization = models.CharField(max_length=100, blank=True)
    # Configurações
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


class Consultation(models.Model):
    """Modelo para consultas de telepsicologia"""
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_consultations')
    professional = models.ForeignKey(User, on_delete=models.CASCADE, related_name='professional_consultations')
    title = models.CharField(max_length=200, default='Consulta')
    description = models.TextField(blank=True)
    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.IntegerField(default=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, help_text='Anotações do profissional')
    patient_feedback = models.TextField(blank=True, help_text='Feedback do paciente')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_datetime']
    
    def __str__(self):
        return f"Consulta: {self.patient.get_full_name()} - {self.scheduled_datetime.strftime('%d/%m/%Y %H:%M')}"


class Message(models.Model):
    """Sistema de mensagens entre paciente e profissional"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} → {self.recipient.username}: {self.content[:50]}..."


class GameScore(models.Model):
    """Pontuações dos jogos"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_scores')
    game_name = models.CharField(max_length=100, default='Game')  # Nome do jogo
    score = models.IntegerField()
    time_spent = models.IntegerField(help_text='Tempo em segundos', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-score', '-created_at']
        verbose_name = 'Pontuação do Jogo'
        verbose_name_plural = 'Pontuações dos Jogos'
    
    def __str__(self):
        return f"{self.user.username} - {self.game_name}: {self.score}"


class JournalEntry(models.Model):
    """Entrada do diário/confessionário virtual"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    content = models.TextField(help_text='Conteúdo do desabafo/reflexão')
    mood_rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)], 
        null=True, 
        blank=True,
        help_text='Humor de 1 a 5'
    )
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Entrada do Diário'
        verbose_name_plural = 'Entradas do Diário'
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%d/%m/%Y')}: {self.content[:50]}..."
