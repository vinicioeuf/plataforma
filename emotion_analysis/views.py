import json
import logging
import random

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta, datetime

from .forms import AudioRecordingForm, RegisterForm
from .models import (
    AudioRecording, EmotionAnalysis, UserProfile, Consultation, Message,
    GameScore, JournalEntry, JournalLike, Achievement, EmotionalProgress,
    Friendship, ChatMessage, Notification, SupportGroup, GroupMessage,
    moderate_content,
)
from .recommendations import ACTION_PLANS

logger = logging.getLogger(__name__)


# ===== HELPERS =====

def check_achievements(user):
    """Verifica e desbloqueia conquistas automaticamente"""
    unlocked = []
    checks = {
        'first_recording': AudioRecording.objects.filter(user=user).exists(),
        'first_game': GameScore.objects.filter(user=user).exists(),
        'breathing_master': GameScore.objects.filter(user=user, game_name='Breathing Exercise').count() >= 5,
        'memory_champion': GameScore.objects.filter(user=user, game_name='Memory Game', score__gte=80).exists(),
        'color_wizard': GameScore.objects.filter(user=user, game_name='Color Matching', score__gte=100).exists(),
        'emotion_explorer': EmotionAnalysis.objects.filter(recording__user=user).values('dominant_emotion').distinct().count() >= 5,
        'journal_writer': JournalEntry.objects.filter(user=user).count() >= 5,
        'friend_maker': Friendship.objects.filter(Q(sender=user) | Q(receiver=user), status='accepted').count() >= 3,
    }
    for atype, condition in checks.items():
        if condition and not Achievement.objects.filter(user=user, achievement_type=atype).exists():
            Achievement.objects.create(user=user, achievement_type=atype)
            unlocked.append(atype)
            Notification.objects.create(
                user=user, notification_type='achievement',
                title='🏆 Nova Conquista!',
                message=f'Você desbloqueou: {dict(Achievement.ACHIEVEMENT_TYPES).get(atype, atype)}',
                link='/dashboard/'
            )
    return unlocked


def create_notification(user, ntype, title, message, link=''):
    """Criar notificação para usuário"""
    Notification.objects.create(user=user, notification_type=ntype, title=title, message=message, link=link)


# ===== AUTH VIEWS =====

def home(request):
    return render(request, 'emotion_analysis/home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo(a)!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'emotion_analysis/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.is_online = True
            profile.save()
            messages.success(request, f'Bem-vindo de volta, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    return render(request, 'emotion_analysis/login.html')


@login_required
def user_logout(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.is_online = False
    profile.last_seen = timezone.now()
    profile.save()
    logout(request)
    messages.success(request, 'Você saiu da sua conta com sucesso.')
    return redirect('home')


# ===== DASHBOARD =====

@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    recordings = AudioRecording.objects.filter(user=request.user).order_by('-created_at')[:5]
    total_recordings = AudioRecording.objects.filter(user=request.user).count()

    analyses = EmotionAnalysis.objects.filter(recording__user=request.user)
    emotion_stats = {}
    for analysis in analyses:
        emotion = analysis.get_emotion_display_name()
        emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1
    emotion_labels = list(emotion_stats.keys())
    emotion_values = list(emotion_stats.values())
    dominant_emotion = max(emotion_stats, key=emotion_stats.get) if emotion_stats else None
    dominant_emotion_count = emotion_stats.get(dominant_emotion, 0) if dominant_emotion else 0
    recent_analyses = analyses.select_related('recording').order_by('-analyzed_at')[:5]

    # Achievements
    user_achievements = Achievement.objects.filter(user=request.user)
    total_achievements = len(Achievement.ACHIEVEMENT_TYPES)

    # Notifications
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    # Friends
    friends_count = Friendship.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user), status='accepted'
    ).count()
    pending_requests = Friendship.objects.filter(receiver=request.user, status='pending').count()

    # Journal entries
    recent_journal = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:3]

    # Games total
    total_games = GameScore.objects.filter(user=request.user).count()

    context = {
        'recordings': recordings,
        'total_recordings': total_recordings,
        'emotion_stats': emotion_stats,
        'recent_analyses': recent_analyses,
        'analysis_total': analyses.count(),
        'dominant_emotion': dominant_emotion,
        'dominant_emotion_count': dominant_emotion_count,
        'emotion_labels_json': json.dumps(emotion_labels, ensure_ascii=False),
        'emotion_values_json': json.dumps(emotion_values),
        'profile': profile,
        'user_achievements': user_achievements,
        'total_achievements': total_achievements,
        'unread_notifications': unread_notifications,
        'friends_count': friends_count,
        'pending_requests': pending_requests,
        'recent_journal': recent_journal,
        'total_games': total_games,
    }

    if profile.user_type == 'professional':
        today = timezone.now().date()
        context.update({
            'consultations_today': Consultation.objects.filter(professional=request.user, scheduled_datetime__date=today).count(),
            'total_patients': Consultation.objects.filter(professional=request.user).values('patient').distinct().count(),
            'recent_consultations': Consultation.objects.filter(professional=request.user).order_by('-scheduled_datetime')[:5],
        })
    else:
        context.update({
            'recent_games': GameScore.objects.filter(user=request.user).order_by('-created_at')[:3],
            'next_consultation': Consultation.objects.filter(
                patient=request.user, scheduled_datetime__gte=timezone.now(), status='scheduled'
            ).order_by('scheduled_datetime').first(),
        })

    # Check achievements
    check_achievements(request.user)

    return render(request, 'emotion_analysis/dashboard.html', context)


# ===== AUDIO =====

@login_required
def record_audio(request):
    if request.method == 'POST':
        form = AudioRecordingForm(request.POST, request.FILES)
        if form.is_valid():
            recording = form.save(commit=False)
            recording.user = request.user
            recording.save()
            check_achievements(request.user)
            messages.success(request, 'Áudio enviado com sucesso!')
            return redirect('analyze_audio', recording_id=recording.id)
    else:
        form = AudioRecordingForm()
    return render(request, 'emotion_analysis/record_audio.html', {'form': form})


@login_required
def analyze_audio(request, recording_id):
    recording = get_object_or_404(AudioRecording, id=recording_id, user=request.user)
    try:
        analysis = recording.emotion_analysis
    except EmotionAnalysis.DoesNotExist:
        analysis = None
    action_plan = ACTION_PLANS.get(analysis.dominant_emotion) if analysis else None
    return render(request, 'emotion_analysis/analyze_audio.html', {
        'recording': recording, 'analysis': analysis, 'action_plan': action_plan
    })


@login_required
@require_POST
def process_emotion_analysis(request, recording_id):
    recording = get_object_or_404(AudioRecording, id=recording_id, user=request.user)
    emotions = ['alegria', 'tristeza', 'raiva', 'medo', 'surpresa', 'nojo', 'neutro']
    dominant_emotion = random.choice(emotions)
    confidence = round(random.uniform(0.6, 0.95), 2)
    emotions_data = {e: round(random.uniform(0.1, 0.9), 2) for e in emotions}

    analysis, created = EmotionAnalysis.objects.update_or_create(
        recording=recording,
        defaults={'dominant_emotion': dominant_emotion, 'confidence': confidence, 'emotions_data': emotions_data}
    )
    check_achievements(request.user)
    return JsonResponse({
        'success': True,
        'dominant_emotion': analysis.get_emotion_display_name(),
        'confidence': analysis.get_confidence_percentage(),
        'emotions_data': emotions_data
    })


@login_required
def history(request):
    recordings = AudioRecording.objects.filter(user=request.user)
    journal_entries = JournalEntry.objects.filter(user=request.user).order_by('-created_at')[:10]
    game_scores = GameScore.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'emotion_analysis/history.html', {
        'recordings': recordings, 'journal_entries': journal_entries, 'game_scores': game_scores
    })


@login_required
def delete_recording(request, recording_id):
    recording = get_object_or_404(AudioRecording, id=recording_id, user=request.user)
    if request.method == 'POST':
        recording.delete()
        messages.success(request, 'Gravação excluída com sucesso!')
        return redirect('history')
    return render(request, 'emotion_analysis/delete_recording.html', {'recording': recording})


# ===== TELEPSICOLOGIA =====

@login_required
def consultations(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.user_type == 'professional':
        consults = Consultation.objects.filter(professional=request.user)
    else:
        consults = Consultation.objects.filter(patient=request.user)
    consults = consults.order_by('-scheduled_datetime')
    return render(request, 'emotion_analysis/consultations.html', {
        'consultations': consults, 'profile': profile,
        'professionals': User.objects.filter(userprofile__user_type='professional') if profile.user_type == 'patient' else None,
    })


@login_required
def schedule_consultation(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.user_type != 'patient':
        messages.error(request, 'Apenas pacientes podem agendar consultas.')
        return redirect('consultations')
    if request.method == 'POST':
        try:
            professional = User.objects.get(id=request.POST.get('professional'), userprofile__user_type='professional')
            dt = datetime.strptime(f"{request.POST.get('date')} {request.POST.get('time')}", "%Y-%m-%d %H:%M")
            Consultation.objects.create(
                patient=request.user, professional=professional,
                title=request.POST.get('title', 'Consulta'),
                description=request.POST.get('description', ''),
                scheduled_datetime=timezone.make_aware(dt),
            )
            create_notification(professional, 'consultation', '📅 Nova Consulta',
                                f'{request.user.get_full_name() or request.user.username} agendou uma consulta.', '/consultations/')
            messages.success(request, 'Consulta agendada com sucesso!')
            return redirect('consultations')
        except (User.DoesNotExist, ValueError):
            messages.error(request, 'Erro ao agendar consulta. Verifique os dados.')
    return render(request, 'emotion_analysis/schedule_consultation.html', {
        'professionals': User.objects.filter(userprofile__user_type='professional')
    })


@login_required
def consultation_detail(request, consultation_id):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.user_type == 'professional':
        consultation = get_object_or_404(Consultation, id=consultation_id, professional=request.user)
    else:
        consultation = get_object_or_404(Consultation, id=consultation_id, patient=request.user)
    msgs = Message.objects.filter(consultation=consultation).order_by('created_at')
    return render(request, 'emotion_analysis/consultation_detail.html', {
        'consultation': consultation, 'chat_messages': msgs, 'profile': profile,
    })


@login_required
def send_message(request, consultation_id):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if profile.user_type == 'professional':
        consultation = get_object_or_404(Consultation, id=consultation_id, professional=request.user)
        recipient = consultation.patient
    else:
        consultation = get_object_or_404(Consultation, id=consultation_id, patient=request.user)
        recipient = consultation.professional
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(sender=request.user, recipient=recipient, consultation=consultation, content=content)
            messages.success(request, 'Mensagem enviada!')
        return redirect('consultation_detail', consultation_id=consultation_id)
    return redirect('consultation_detail', consultation_id=consultation_id)


# ===== GAMES =====

@login_required
def games_menu(request):
    best_scores = GameScore.objects.filter(user=request.user).order_by('-score')[:5]
    total_games = GameScore.objects.filter(user=request.user).count()
    achievements = Achievement.objects.filter(user=request.user)
    return render(request, 'emotion_analysis/games/games_menu.html', {
        'top_games': best_scores, 'total_games': total_games, 'achievements': achievements,
    })


@login_required
def memory_game(request):
    return render(request, 'emotion_analysis/games/memory_game.html')


@login_required
def breathing_exercise(request):
    return render(request, 'emotion_analysis/games/breathing_exercise.html')


@login_required
def color_matching_game(request):
    return render(request, 'emotion_analysis/games/color_matching.html')


@login_required
def emotion_identify_game(request):
    return render(request, 'emotion_analysis/games/emotion_identify.html')


@login_required
def gratitude_challenge(request):
    return render(request, 'emotion_analysis/games/gratitude_challenge.html')


@login_required
def reflection_game(request):
    return render(request, 'emotion_analysis/games/reflection_game.html')


@login_required
@require_POST
def save_game_score(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        game_name = data.get('game_name', 'Unknown Game')
        score = int(data.get('score', 0))
        time_spent = int(data.get('time_spent', 0))
        emotion_before = data.get('emotion_before', '')
        emotion_after = data.get('emotion_after', '')

        GameScore.objects.create(
            user=request.user, game_name=game_name, score=score,
            time_spent=time_spent, emotion_before=emotion_before, emotion_after=emotion_after,
        )
        check_achievements(request.user)
        return JsonResponse({'success': True, 'message': 'Pontuação salva!'})
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ===== PROFILE =====

@login_required
def profile_setup(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.user_type = request.POST.get('user_type', profile.user_type)
        profile.phone = request.POST.get('phone', '')
        profile.bio = request.POST.get('bio', '')
        profile.avatar_emoji = request.POST.get('avatar_emoji', '😊')
        bd = request.POST.get('birth_date')
        if bd:
            profile.birth_date = bd
        if profile.user_type == 'professional':
            profile.license_number = request.POST.get('license_number', '')
            profile.specialization = request.POST.get('specialization', '')
        profile.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('dashboard')
    return render(request, 'emotion_analysis/profile_setup.html', {'profile': profile})


# ===== CONFESSIONÁRIO / JOURNAL =====

@login_required
@require_POST
def save_journal_entry(request):
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        content = data.get('content', '').strip()
        mood_rating = data.get('mood_rating', None)
        visibility = data.get('visibility', 'private')
        entry_type = data.get('entry_type', 'text')

        if not content:
            return JsonResponse({'success': False, 'error': 'Conteúdo não pode estar vazio'})

        # Auto-moderation
        flagged, word = moderate_content(content)

        entry = JournalEntry.objects.create(
            user=request.user, content=content,
            mood_rating=int(mood_rating) if mood_rating else None,
            visibility=visibility, entry_type=entry_type, is_flagged=flagged,
        )
        check_achievements(request.user)
        return JsonResponse({
            'success': True, 'message': 'Entrada salva com segurança! 💝',
            'entry_date': entry.created_at.strftime('%d/%m/%Y %H:%M')
        })
    except Exception as e:
        logger.error(f"Error saving journal entry: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def journal_feed(request):
    """Feed do confessionário - entradas públicas e de amigos"""
    user = request.user
    friends = Friendship.get_friends(user)
    friend_ids = [f.id for f in friends]

    entries = JournalEntry.objects.filter(
        Q(visibility='public') | Q(visibility='anonymous') |
        Q(visibility='friends', user__id__in=friend_ids) |
        Q(user=user)
    ).select_related('user').order_by('-created_at')[:50]

    user_likes = set(JournalLike.objects.filter(user=user).values_list('entry_id', flat=True))

    return render(request, 'emotion_analysis/journal_feed.html', {
        'entries': entries, 'user_likes': user_likes,
    })


@login_required
@require_POST
def like_journal_entry(request, entry_id):
    entry = get_object_or_404(JournalEntry, id=entry_id)
    like, created = JournalLike.objects.get_or_create(user=request.user, entry=entry)
    if created:
        entry.likes_count += 1
        entry.save()
        if entry.user != request.user:
            create_notification(entry.user, 'journal_like', '❤️ Curtida',
                                f'Alguém curtiu seu desabafo.', '/journal/feed/')
    else:
        like.delete()
        entry.likes_count = max(0, entry.likes_count - 1)
        entry.save()
    return JsonResponse({'success': True, 'likes_count': entry.likes_count, 'liked': created})


@login_required
def save_journal_audio(request):
    """Salvar entrada de áudio no confessionário"""
    if request.method == 'POST' and request.FILES.get('audio_file'):
        audio = request.FILES['audio_file']
        content = request.POST.get('content', 'Desabafo por áudio')
        visibility = request.POST.get('visibility', 'private')
        mood = request.POST.get('mood_rating')

        entry = JournalEntry.objects.create(
            user=request.user, content=content, audio_file=audio,
            entry_type='audio', visibility=visibility,
            mood_rating=int(mood) if mood else None,
        )
        check_achievements(request.user)
        messages.success(request, 'Áudio salvo com segurança! 💝')
        return redirect('journal_feed')
    return redirect('dashboard')


# ===== FRIENDS SYSTEM =====

@login_required
def friends_list(request):
    friends = Friendship.get_friends(request.user)
    pending_received = Friendship.objects.filter(receiver=request.user, status='pending')
    pending_sent = Friendship.objects.filter(sender=request.user, status='pending')
    blocked = Friendship.objects.filter(sender=request.user, status='blocked')

    # Search users
    search_query = request.GET.get('q', '')
    search_results = []
    if search_query:
        search_results = User.objects.filter(
            Q(username__icontains=search_query) | Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query)
        ).exclude(id=request.user.id)[:20]

    return render(request, 'emotion_analysis/friends.html', {
        'friends': friends, 'pending_received': pending_received,
        'pending_sent': pending_sent, 'blocked': blocked,
        'search_query': search_query, 'search_results': search_results,
    })


@login_required
@require_POST
def send_friend_request(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target == request.user:
        return JsonResponse({'success': False, 'error': 'Não pode adicionar a si mesmo'})
    # Check if already exists
    existing = Friendship.objects.filter(
        Q(sender=request.user, receiver=target) | Q(sender=target, receiver=request.user)
    ).first()
    if existing:
        if existing.status == 'blocked':
            return JsonResponse({'success': False, 'error': 'Usuário bloqueado'})
        return JsonResponse({'success': False, 'error': 'Solicitação já existe'})
    Friendship.objects.create(sender=request.user, receiver=target, status='pending')
    create_notification(target, 'friend_request', '👋 Solicitação de Amizade',
                        f'{request.user.get_full_name() or request.user.username} quer ser seu amigo!', '/friends/')
    return JsonResponse({'success': True, 'message': 'Solicitação enviada!'})


@login_required
@require_POST
def respond_friend_request(request, friendship_id):
    friendship = get_object_or_404(Friendship, id=friendship_id, receiver=request.user)
    action = request.POST.get('action', '')
    if action == 'accept':
        friendship.status = 'accepted'
        friendship.save()
        create_notification(friendship.sender, 'friend_accepted', '🎉 Amizade Aceita',
                            f'{request.user.get_full_name() or request.user.username} aceitou sua amizade!', '/friends/')
        check_achievements(request.user)
        check_achievements(friendship.sender)
        return JsonResponse({'success': True, 'message': 'Amizade aceita!'})
    elif action == 'reject':
        friendship.status = 'rejected'
        friendship.save()
        return JsonResponse({'success': True, 'message': 'Solicitação recusada.'})
    return JsonResponse({'success': False, 'error': 'Ação inválida'})


@login_required
@require_POST
def block_user(request, user_id):
    target = get_object_or_404(User, id=user_id)
    friendship = Friendship.objects.filter(
        Q(sender=request.user, receiver=target) | Q(sender=target, receiver=request.user)
    ).first()
    if friendship:
        friendship.status = 'blocked'
        friendship.sender = request.user
        friendship.receiver = target
        friendship.save()
    else:
        Friendship.objects.create(sender=request.user, receiver=target, status='blocked')
    return JsonResponse({'success': True, 'message': 'Usuário bloqueado.'})


# ===== CHAT =====

@login_required
def chat_view(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if not Friendship.are_friends(request.user, other_user):
        messages.error(request, 'Vocês precisam ser amigos para conversar.')
        return redirect('friends_list')

    # Mark messages as read
    ChatMessage.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)

    chat_msgs = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')[:100]

    other_profile, _ = UserProfile.objects.get_or_create(user=other_user)

    return render(request, 'emotion_analysis/chat.html', {
        'other_user': other_user, 'other_profile': other_profile, 'chat_messages': chat_msgs,
    })


@login_required
@require_POST
def send_chat_message(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    if not Friendship.are_friends(request.user, other_user):
        return JsonResponse({'success': False, 'error': 'Não são amigos'})
    content = request.POST.get('content', '').strip()
    if not content:
        data = json.loads(request.body) if request.content_type == 'application/json' else {}
        content = data.get('content', '').strip()
    if content:
        ChatMessage.objects.create(sender=request.user, receiver=other_user, content=content)
        create_notification(other_user, 'new_message', '💬 Nova Mensagem',
                            f'{request.user.get_full_name() or request.user.username} enviou uma mensagem.',
                            f'/chat/{request.user.id}/')
    return JsonResponse({'success': True})


@login_required
def get_chat_messages(request, user_id):
    """API para polling de mensagens"""
    other_user = get_object_or_404(User, id=user_id)
    ChatMessage.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    msgs = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')[:100]
    return JsonResponse({'messages': [
        {
            'id': m.id, 'sender': m.sender.username, 'sender_id': m.sender.id,
            'content': m.content, 'is_mine': m.sender == request.user,
            'time': m.created_at.strftime('%H:%M'),
        } for m in msgs
    ]})


# ===== NOTIFICATIONS =====

@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
    return render(request, 'emotion_analysis/notifications.html', {'notifications': notifs})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def get_unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ===== SUPPORT GROUPS =====

@login_required
def support_groups(request):
    groups = SupportGroup.objects.filter(is_active=True)
    my_groups = request.user.support_groups.all()
    return render(request, 'emotion_analysis/support_groups.html', {
        'groups': groups, 'my_groups': my_groups,
    })


@login_required
@require_POST
def create_support_group(request):
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    emoji = request.POST.get('emoji', '💬')
    if name and description:
        group = SupportGroup.objects.create(name=name, description=description, emoji=emoji, creator=request.user)
        group.members.add(request.user)
        messages.success(request, f'Grupo "{name}" criado com sucesso!')
    return redirect('support_groups')


@login_required
@require_POST
def join_support_group(request, group_id):
    group = get_object_or_404(SupportGroup, id=group_id)
    if group.members.count() < group.max_members:
        group.members.add(request.user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Grupo cheio'})


@login_required
def group_chat(request, group_id):
    group = get_object_or_404(SupportGroup, id=group_id)
    if request.user not in group.members.all():
        messages.error(request, 'Você não é membro deste grupo.')
        return redirect('support_groups')
    msgs = GroupMessage.objects.filter(group=group).order_by('created_at')[:100]
    return render(request, 'emotion_analysis/group_chat.html', {'group': group, 'group_messages': msgs})


@login_required
@require_POST
def send_group_message(request, group_id):
    group = get_object_or_404(SupportGroup, id=group_id)
    if request.user not in group.members.all():
        return JsonResponse({'success': False, 'error': 'Não é membro'})
    data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
    content = data.get('content', '').strip()
    is_anonymous = data.get('is_anonymous', False)
    if content:
        flagged, _ = moderate_content(content)
        if not flagged:
            GroupMessage.objects.create(group=group, sender=request.user, content=content, is_anonymous=bool(is_anonymous))
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Conteúdo inapropriado detectado.'})
    return JsonResponse({'success': False, 'error': 'Mensagem vazia'})
