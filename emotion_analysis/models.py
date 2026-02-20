from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import base64


class AudioRecording(models.Model):
    """Modelo para armazenar gravações de áudio dos usuários"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_recordings', verbose_name='Usuário')
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    audio_file = models.FileField(
        upload_to='audio_recordings/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'ogg', 'webm', 'm4a'])],
        verbose_name='Arquivo de Áudio'
    )
    duration = models.FloatField(null=True, blank=True, help_text='Duração em segundos', verbose_name='Duração')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gravação de Áudio'
        verbose_name_plural = 'Gravações de Áudio'

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class EmotionAnalysis(models.Model):
    """Modelo para armazenar os resultados da análise de emoção"""
    EMOTION_CHOICES = [
        ('alegria', 'Alegria'), ('tristeza', 'Tristeza'), ('raiva', 'Raiva'),
        ('medo', 'Medo'), ('surpresa', 'Surpresa'), ('nojo', 'Nojo'), ('neutro', 'Neutro'),
    ]
    recording = models.OneToOneField(AudioRecording, on_delete=models.CASCADE, related_name='emotion_analysis', verbose_name='Gravação')
    dominant_emotion = models.CharField(max_length=20, choices=EMOTION_CHOICES, verbose_name='Emoção Dominante')
    confidence = models.FloatField(help_text='Confiança da análise (0-1)', verbose_name='Confiança')
    emotions_data = models.JSONField(help_text='Dados detalhados de todas as emoções detectadas', verbose_name='Dados das Emoções')
    notes = models.TextField(blank=True, verbose_name='Observações')
    analyzed_at = models.DateTimeField(auto_now_add=True, verbose_name='Analisado em')

    class Meta:
        ordering = ['-analyzed_at']
        verbose_name = 'Análise de Emoção'
        verbose_name_plural = 'Análises de Emoções'

    def __str__(self):
        return f"Análise de '{self.recording.title}' - {self.dominant_emotion}"

    def get_emotion_display_name(self):
        return dict(self.EMOTION_CHOICES).get(self.dominant_emotion, self.dominant_emotion)

    def get_confidence_percentage(self):
        return round(self.confidence * 100, 2)


class UserProfile(models.Model):
    """Perfil estendido do usuário"""
    USER_TYPE_CHOICES = [('patient', 'Paciente'), ('professional', 'Profissional')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='patient')
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True, max_length=500, help_text='Sobre você')
    avatar_emoji = models.CharField(max_length=10, default='😊', help_text='Emoji avatar')
    license_number = models.CharField(max_length=50, blank=True, help_text='Número do registro profissional')
    specialization = models.CharField(max_length=100, blank=True)
    notifications_enabled = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"


class Consultation(models.Model):
    """Modelo para consultas de telepsicologia"""
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'), ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'), ('cancelled', 'Cancelada'),
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
    """Sistema de mensagens entre usuários"""
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

    @staticmethod
    def simple_encrypt(text):
        return base64.b64encode(text.encode()).decode()

    @staticmethod
    def simple_decrypt(encoded):
        try:
            return base64.b64decode(encoded.encode()).decode()
        except Exception:
            return encoded


class GameScore(models.Model):
    """Pontuações dos jogos"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_scores')
    game_name = models.CharField(max_length=100, default='Game')
    score = models.IntegerField()
    time_spent = models.IntegerField(help_text='Tempo em segundos', default=0)
    emotion_before = models.CharField(max_length=20, blank=True)
    emotion_after = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', '-created_at']
        verbose_name = 'Pontuação do Jogo'
        verbose_name_plural = 'Pontuações dos Jogos'

    def __str__(self):
        return f"{self.user.username} - {self.game_name}: {self.score}"


class Achievement(models.Model):
    """Sistema de conquistas"""
    ACHIEVEMENT_TYPES = [
        ('first_recording', 'Primeira Gravação'), ('first_game', 'Primeiro Jogo'),
        ('breathing_master', 'Mestre da Respiração'), ('memory_champion', 'Campeão da Memória'),
        ('color_wizard', 'Mago das Cores'), ('emotion_explorer', 'Explorador de Emoções'),
        ('journal_writer', 'Escritor do Diário'), ('social_butterfly', 'Borboleta Social'),
        ('week_streak', 'Sequência Semanal'), ('gratitude_guru', 'Guru da Gratidão'),
        ('reflection_master', 'Mestre da Reflexão'), ('friend_maker', 'Fazedor de Amigos'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement_type = models.CharField(max_length=50, choices=ACHIEVEMENT_TYPES)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'achievement_type']
        ordering = ['-unlocked_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_achievement_type_display()}"

    @staticmethod
    def get_icon(achievement_type):
        icons = {
            'first_recording': '🎙️', 'first_game': '🎮', 'breathing_master': '🫁',
            'memory_champion': '🧠', 'color_wizard': '🎨', 'emotion_explorer': '🔍',
            'journal_writer': '📝', 'social_butterfly': '🦋', 'week_streak': '🔥',
            'gratitude_guru': '🙏', 'reflection_master': '💭', 'friend_maker': '🤝',
        }
        return icons.get(achievement_type, '⭐')


class EmotionalProgress(models.Model):
    """Progresso emocional do usuário"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emotional_progress')
    date = models.DateField(default=timezone.now)
    overall_mood = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text='Humor geral 1-5')
    dominant_emotion = models.CharField(max_length=20, blank=True)
    activities_count = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    journal_entries_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date} - Humor: {self.overall_mood}"


class JournalEntry(models.Model):
    """Entrada do diário/confessionário virtual"""
    VISIBILITY_CHOICES = [
        ('private', 'Privado'), ('friends', 'Apenas Amigos'),
        ('public', 'Público'), ('anonymous', 'Anônimo'),
    ]
    ENTRY_TYPE_CHOICES = [('text', 'Texto'), ('audio', 'Áudio')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    content = models.TextField(help_text='Conteúdo do desabafo/reflexão')
    audio_file = models.FileField(
        upload_to='journal_audio/%Y/%m/%d/', blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'ogg', 'webm', 'm4a'])],
    )
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES, default='text')
    mood_rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True, help_text='Humor de 1 a 5')
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    is_flagged = models.BooleanField(default=False, help_text='Marcado pela moderação')
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Entrada do Diário'
        verbose_name_plural = 'Entradas do Diário'

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%d/%m/%Y')}: {self.content[:50]}..."

    def get_display_author(self):
        if self.visibility == 'anonymous':
            return 'Anônimo'
        return self.user.get_full_name() or self.user.username

    def is_visible_to(self, user):
        if self.user == user:
            return True
        if self.visibility in ('public', 'anonymous'):
            return True
        if self.visibility == 'friends':
            return Friendship.are_friends(self.user, user)
        return False


class JournalLike(models.Model):
    """Curtidas em entradas do diário"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_likes')
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'entry']


class Friendship(models.Model):
    """Sistema de amizades"""
    STATUS_CHOICES = [
        ('pending', 'Pendente'), ('accepted', 'Aceita'),
        ('rejected', 'Rejeitada'), ('blocked', 'Bloqueada'),
    ]
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_sent')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['sender', 'receiver']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} ({self.status})"

    @staticmethod
    def are_friends(user1, user2):
        return Friendship.objects.filter(
            models.Q(sender=user1, receiver=user2) | models.Q(sender=user2, receiver=user1),
            status='accepted'
        ).exists()

    @staticmethod
    def get_friends(user):
        friendships = Friendship.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user),
            status='accepted'
        )
        friends = []
        for f in friendships:
            friends.append(f.receiver if f.sender == user else f.sender)
        return friends


class ChatMessage(models.Model):
    """Mensagens de chat privado entre amigos"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sent')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_received')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Chat: {self.sender.username} → {self.receiver.username}"


class Notification(models.Model):
    """Sistema de notificações"""
    NOTIFICATION_TYPES = [
        ('friend_request', 'Solicitação de Amizade'), ('friend_accepted', 'Amizade Aceita'),
        ('new_message', 'Nova Mensagem'), ('achievement', 'Conquista Desbloqueada'),
        ('journal_like', 'Curtida no Diário'), ('consultation', 'Consulta'), ('system', 'Sistema'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class SupportGroup(models.Model):
    """Grupos de apoio"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    emoji = models.CharField(max_length=10, default='💬')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, related_name='support_groups', blank=True)
    is_active = models.BooleanField(default=True)
    max_members = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.emoji} {self.name}"


class GroupMessage(models.Model):
    """Mensagens nos grupos de apoio"""
    group = models.ForeignKey(SupportGroup, on_delete=models.CASCADE, related_name='group_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        author = 'Anônimo' if self.is_anonymous else self.sender.username
        return f"{author} em {self.group.name}: {self.content[:50]}"


def moderate_content(text):
    """Moderação automática de conteúdo"""
    banned_words = []  # Adicionar palavras impróprias aqui
    text_lower = text.lower()
    for word in banned_words:
        if word in text_lower:
            return True, word
    return False, None
