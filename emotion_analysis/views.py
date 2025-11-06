import json
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import audio_processing
from .forms import AudioRecordingForm, RegisterForm
from .models import AudioRecording, EmotionAnalysis
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
    
    context = {
        'recordings': recordings,
        'total_recordings': total_recordings,
        'emotion_stats': emotion_stats,
        'recent_analyses': recent_analyses,
        'analysis_total': analyses.count(),
        'dominant_emotion': dominant_emotion,
        'dominant_emotion_count': dominant_emotion_count,
        'emotion_labels_json': json.dumps(emotion_labels, ensure_ascii=False),
        'emotion_values_json': json.dumps(emotion_values)
    }
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

    try:
        resultado = audio_processing.analyze_recording(recording)
    except audio_processing.AudioProcessingError as exc:
        logger.warning('Falha controlada na análise de áudio: %s', exc)
        return JsonResponse({
            'success': False,
            'error': str(exc),
        }, status=400)
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception('Erro inesperado ao processar o áudio id=%s', recording_id)
        return JsonResponse({
            'success': False,
            'error': 'Erro ao processar o áudio. Tente novamente mais tarde.',
        }, status=500)

    analysis, created = EmotionAnalysis.objects.update_or_create(
        recording=recording,
        defaults={
            'dominant_emotion': resultado['dominant_emotion'],
            'confidence': resultado['confidence'],
            'emotions_data': resultado['emotions_data']
        }
    )

    return JsonResponse({
        'success': True,
        'dominant_emotion': analysis.get_emotion_display_name(),
        'confidence': analysis.get_confidence_percentage(),
        'emotions_data': resultado['emotions_data']
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
