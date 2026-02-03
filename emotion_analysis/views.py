import json
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta, datetime

# from . import audio_processing  # Comentado temporariamente
from .forms import AudioRecordingForm, RegisterForm
from .models import AudioRecording, EmotionAnalysis, UserProfile, Consultation, Message, GameScore, JournalEntry
from .recommendations import ACTION_PLANS


logger = logging.getLogger(__name__)


def home(request):
    """Página inicial"""
    return render(request, 'emotion_analysis/home.html')


def register(request):
    """Página de registro de usuário"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo(a)!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    
    return render(request, 'emotion_analysis/register.html', {'form': form})


def user_login(request):
    """Página de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bem-vindo de volta, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'emotion_analysis/login.html')


@login_required
def user_logout(request):
    """Logout do usuário"""
    logout(request)
    messages.success(request, 'Você saiu da sua conta com sucesso.')
    return redirect('home')


@login_required
def dashboard(request):
    """Dashboard principal do usuário"""
    # Obter ou criar perfil do usuário
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    recordings = AudioRecording.objects.filter(user=request.user).order_by('-created_at')[:5]
    total_recordings = AudioRecording.objects.filter(user=request.user).count()
    
    # Estatísticas de emoções
    analyses = EmotionAnalysis.objects.filter(recording__user=request.user)
    emotion_stats = {}
    for analysis in analyses:
        emotion = analysis.get_emotion_display_name()
        emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1
    emotion_labels = list(emotion_stats.keys())
    emotion_values = list(emotion_stats.values())
    dominant_emotion = None
    dominant_emotion_count = 0
    if emotion_stats:
        dominant_emotion = max(emotion_stats, key=emotion_stats.get)
        dominant_emotion_count = emotion_stats.get(dominant_emotion, 0)
    recent_analyses = analyses.select_related('recording').order_by('-analyzed_at')[:5]
    
    # Dados específicos por tipo de usuário
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
    }
    
    if profile.user_type == 'professional':
        # Dados para profissionais
        today = timezone.now().date()
        context.update({
            'consultations_today': Consultation.objects.filter(
                professional=request.user,
                scheduled_datetime__date=today
            ).count(),
            'total_patients': Consultation.objects.filter(
                professional=request.user
            ).values('patient').distinct().count(),
            'recent_consultations': Consultation.objects.filter(
                professional=request.user
            ).order_by('-scheduled_datetime')[:5],
        })
    else:
        # Dados para pacientes
        context.update({
            'recent_games': GameScore.objects.filter(
                user=request.user
            ).order_by('-created_at')[:3],
            'next_consultation': Consultation.objects.filter(
                patient=request.user,
                scheduled_datetime__gte=timezone.now(),
                status='scheduled'
            ).order_by('scheduled_datetime').first(),
        })
    
    return render(request, 'emotion_analysis/dashboard.html', context)


@login_required
def record_audio(request):
    """Página para gravar ou fazer upload de áudio"""
    if request.method == 'POST':
        form = AudioRecordingForm(request.POST, request.FILES)
        if form.is_valid():
            recording = form.save(commit=False)
            recording.user = request.user
            recording.save()
            messages.success(request, 'Áudio enviado com sucesso!')
            return redirect('analyze_audio', recording_id=recording.id)
    else:
        form = AudioRecordingForm()
    
    return render(request, 'emotion_analysis/record_audio.html', {'form': form})


@login_required
def analyze_audio(request, recording_id):
    """Página para análise de áudio"""
    recording = get_object_or_404(AudioRecording, id=recording_id, user=request.user)
    
    # Verifica se já existe uma análise
    try:
        analysis = recording.emotion_analysis
    except EmotionAnalysis.DoesNotExist:
        analysis = None
    action_plan = None
    if analysis:
        action_plan = ACTION_PLANS.get(analysis.dominant_emotion)
    
    context = {
        'recording': recording,
        'analysis': analysis,
        'action_plan': action_plan
    }
    return render(request, 'emotion_analysis/analyze_audio.html', context)


@login_required
@require_POST
def process_emotion_analysis(request, recording_id):
    """
    Endpoint para processar a análise de emoção
    AQUI VOCÊ ADICIONARÁ SEU SCRIPT DE ANÁLISE DE EMOÇÕES
    """
    recording = get_object_or_404(AudioRecording, id=recording_id, user=request.user)

    # Análise temporária simulada (remover quando implementar audio_processing)
    import random
    emotions = ['alegria', 'tristeza', 'raiva', 'medo', 'surpresa', 'nojo', 'neutro']
    dominant_emotion = random.choice(emotions)
    confidence = round(random.uniform(0.6, 0.95), 2)
    emotions_data = {emotion: round(random.uniform(0.1, 0.9), 2) for emotion in emotions}
    
    analysis, created = EmotionAnalysis.objects.update_or_create(
        recording=recording,
        defaults={
            'dominant_emotion': dominant_emotion,
            'confidence': confidence,
            'emotions_data': emotions_data
        }
    )

    return JsonResponse({
        'success': True,
        'dominant_emotion': analysis.get_emotion_display_name(),
        'confidence': analysis.get_confidence_percentage(),
        'emotions_data': emotions_data
    })


@login_required
def history(request):
    """Página de histórico de gravações e análises"""
    recordings = AudioRecording.objects.filter(user=request.user)
    return render(request, 'emotion_analysis/history.html', {'recordings': recordings})


@login_required
def delete_recording(request, recording_id):
    """Deletar uma gravação"""
    recording = get_object_or_404(AudioRecording, id=recording_id, user=request.user)
    
    if request.method == 'POST':
        recording.delete()
        messages.success(request, 'Gravação excluída com sucesso!')
        return redirect('history')
    
    return render(request, 'emotion_analysis/delete_recording.html', {'recording': recording})


# ===== VIEWS DE TELEPSICOLOGIA =====

@login_required
def consultations(request):
    """Lista de consultas"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.user_type == 'professional':
        consultations = Consultation.objects.filter(professional=request.user)
    else:
        consultations = Consultation.objects.filter(patient=request.user)
    
    consultations = consultations.order_by('-scheduled_datetime')
    
    context = {
        'consultations': consultations,
        'profile': profile,
        'professionals': User.objects.filter(userprofile__user_type='professional') if profile.user_type == 'patient' else None,
    }
    
    return render(request, 'emotion_analysis/consultations.html', context)


@login_required
def schedule_consultation(request):
    """Agendar nova consulta"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.user_type != 'patient':
        messages.error(request, 'Apenas pacientes podem agendar consultas.')
        return redirect('consultations')
    
    if request.method == 'POST':
        professional_id = request.POST.get('professional')
        title = request.POST.get('title', 'Consulta')
        description = request.POST.get('description', '')
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        
        try:
            professional = User.objects.get(id=professional_id, userprofile__user_type='professional')
            scheduled_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            scheduled_datetime = timezone.make_aware(scheduled_datetime)
            
            consultation = Consultation.objects.create(
                patient=request.user,
                professional=professional,
                title=title,
                description=description,
                scheduled_datetime=scheduled_datetime,
            )
            
            messages.success(request, 'Consulta agendada com sucesso!')
            return redirect('consultations')
            
        except (User.DoesNotExist, ValueError) as e:
            messages.error(request, 'Erro ao agendar consulta. Verifique os dados informados.')
    
    professionals = User.objects.filter(userprofile__user_type='professional')
    return render(request, 'emotion_analysis/schedule_consultation.html', {'professionals': professionals})


@login_required
def consultation_detail(request, consultation_id):
    """Detalhes da consulta"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.user_type == 'professional':
        consultation = get_object_or_404(Consultation, id=consultation_id, professional=request.user)
    else:
        consultation = get_object_or_404(Consultation, id=consultation_id, patient=request.user)
    
    messages = Message.objects.filter(
        consultation=consultation
    ).order_by('created_at')
    
    context = {
        'consultation': consultation,
        'messages': messages,
        'profile': profile,
    }
    
    return render(request, 'emotion_analysis/consultation_detail.html', context)


@login_required
def send_message(request, consultation_id):
    """Enviar mensagem na consulta"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if profile.user_type == 'professional':
        consultation = get_object_or_404(Consultation, id=consultation_id, professional=request.user)
        recipient = consultation.patient
    else:
        consultation = get_object_or_404(Consultation, id=consultation_id, patient=request.user)
        recipient = consultation.professional
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Message.objects.create(
                sender=request.user,
                recipient=recipient,
                consultation=consultation,
                content=content
            )
            messages.success(request, 'Mensagem enviada!')
        
        return redirect('consultation_detail', consultation_id=consultation_id)
    
    return redirect('consultation_detail', consultation_id=consultation_id)


# ===== VIEWS DE JOGOS =====

@login_required
def games_menu(request):
    """Página inicial dos jogos"""
    recent_scores = GameScore.objects.filter(user=request.user).order_by('-created_at')[:5]
    best_scores = GameScore.objects.filter(user=request.user).order_by('-score')[:5]
    
    context = {
        'top_games': best_scores,
    }
    
    return render(request, 'emotion_analysis/games/games_menu.html', context)


@login_required
def memory_game(request):
    """Jogo da Memória"""
    return render(request, 'emotion_analysis/games/memory_game.html')


@login_required
def breathing_exercise(request):
    """Exercício de Respiração"""
    return render(request, 'emotion_analysis/games/breathing_exercise.html')


@login_required
def color_matching_game(request):
    """Jogo de Combinação de Cores"""
    return render(request, 'emotion_analysis/games/color_matching.html')


@login_required
@require_POST
def save_game_score(request):
    """Salvar pontuação do jogo"""
    try:
        # Aceitar tanto JSON quanto POST
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        game_name = data.get('game_name', 'Unknown Game')
        score = int(data.get('score', 0))
        time_spent = int(data.get('time_spent', 0))
        
        GameScore.objects.create(
            user=request.user,
            game_name=game_name,
            score=score,
            time_spent=time_spent,
        )
        
        return JsonResponse({'success': True, 'message': 'Pontuação salva!'})
    
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def profile_setup(request):
    """Configuração do perfil do usuário"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        phone = request.POST.get('phone', '')
        birth_date = request.POST.get('birth_date')
        license_number = request.POST.get('license_number', '')
        specialization = request.POST.get('specialization', '')
        
        profile.user_type = user_type
        profile.phone = phone
        if birth_date:
            profile.birth_date = birth_date
        if user_type == 'professional':
            profile.license_number = license_number
            profile.specialization = specialization
        
        profile.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('dashboard')
    
    return render(request, 'emotion_analysis/profile_setup.html', {'profile': profile})


@login_required
@require_POST
def save_journal_entry(request):
    """Salvar entrada do confessionário virtual"""
    try:
        # Aceitar tanto JSON quanto POST
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        content = data.get('content', '').strip()
        mood_rating = data.get('mood_rating', None)
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Conteúdo não pode estar vazio'})
        
        from .models import JournalEntry
        entry = JournalEntry.objects.create(
            user=request.user,
            content=content,
            mood_rating=int(mood_rating) if mood_rating else None,
        )
        
        return JsonResponse({
            'success': True, 
            'message': 'Entrada salva com segurança! 💝',
            'entry_date': entry.created_at.strftime('%d/%m/%Y %H:%M')
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
