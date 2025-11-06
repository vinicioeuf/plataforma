"""Utilities to load the emotion model and run predictions on audio files."""

from __future__ import annotations

import io
import json
import logging
import subprocess
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Dict

import h5py
import imageio_ffmpeg
import joblib
import librosa
import numpy as np
import tensorflow as tf
from django.conf import settings
from sklearn.exceptions import InconsistentVersionWarning

# Keep warnings scoped to the label encoder load only.
import warnings

logger = logging.getLogger(__name__)


MODEL_RELATIVE_PATH = Path('static/modelo/modelo_emocoes.keras')
ENCODER_RELATIVE_PATH = Path('static/modelo/label_encoder.joblib')

CANONICAL_EMOTIONS = [
	'alegria',
	'tristeza',
	'raiva',
	'medo',
	'surpresa',
	'nojo',
	'neutro',
]

RAW_TO_CANONICAL = {
	'calmo': 'neutro',
	'desgosto': 'nojo',
	'feliz': 'alegria',
	'medroso': 'medo',
	'neutro': 'neutro',
	'raivoso': 'raiva',
	'surpreso': 'surpresa',
	'triste': 'tristeza',
}


class AudioProcessingError(Exception):
	"""Custom exception used when the analysis pipeline fails."""


def _resolve_artifact(path: Path) -> Path:
	"""Return an absolute path for the given artifact and ensure it exists."""

	absolute = Path(settings.BASE_DIR) / path
	if not absolute.exists():
		raise AudioProcessingError(f"Arquivo de modelo não encontrado: {absolute}")
	return absolute


def _normalise_layer_config(seq_config: Dict) -> Dict:
	"""Tweak Keras 3 config so TensorFlow 2.15 (tf.keras) can rebuild it."""

	# Sequential dtype is stored as a dictionary in the Keras 3 archive.
	dtype = seq_config.get('dtype')
	if isinstance(dtype, dict):
		seq_config['dtype'] = dtype.get('config', {}).get('name', 'float32')

	for layer in seq_config.get('layers', []):
		cfg = layer.get('config', {})
		# Legacy tf.keras expects batch_input_shape instead of batch_shape.
		if 'batch_shape' in cfg:
			cfg['batch_input_shape'] = cfg.pop('batch_shape')
		dtype = cfg.get('dtype')
		if isinstance(dtype, dict):
			cfg['dtype'] = dtype.get('config', {}).get('name', 'float32')
	return seq_config


def _rehydrate_model(weights_bytes: bytes, seq_config: Dict) -> tf.keras.Model:
	"""Build a tf.keras model from a Sequential config and manual weights."""

	model = tf.keras.Sequential.from_config(seq_config)
	build_shape = seq_config.get('build_input_shape')
	if build_shape:
		model.build(tuple(build_shape))

	with h5py.File(io.BytesIO(weights_bytes), 'r') as weights_file:
		layer_store = weights_file['layers']
		for layer in model.layers:
			if layer.name not in layer_store:
				continue
			store = layer_store[layer.name]

			def _read_vars(group: h5py.Group) -> list[np.ndarray]:
				keys = sorted(group.keys(), key=lambda k: int(k))
				return [group[key][()] for key in keys]

			weights = []
			if 'vars' in store and len(store['vars']) > 0:
				weights = _read_vars(store['vars'])
			elif 'cell' in store:
				weights = _read_vars(store['cell']['vars'])

			if weights:
				layer.set_weights(weights)

	return model


@lru_cache(maxsize=1)
def load_model() -> tf.keras.Model:
	"""Load and cache the TensorFlow model from the Keras 3 archive."""

	model_path = _resolve_artifact(MODEL_RELATIVE_PATH)
	with zipfile.ZipFile(model_path) as archive:
		config = json.loads(archive.read('config.json'))
		seq_config = _normalise_layer_config(config['config'])
		weights_bytes = archive.read('model.weights.h5')

	model = _rehydrate_model(weights_bytes, seq_config)
	logger.info('Modelo de emoções carregado com sucesso.')
	return model


@lru_cache(maxsize=1)
def load_label_encoder():
	"""Load and cache the label encoder used during model training."""

	encoder_path = _resolve_artifact(ENCODER_RELATIVE_PATH)
	with warnings.catch_warnings():
		warnings.simplefilter('ignore', category=InconsistentVersionWarning)
		encoder = joblib.load(encoder_path)
	return encoder


def _error_details(exc: Exception) -> str:
	message = str(exc).strip()
	return message or exc.__class__.__name__


def _load_waveform(audio_path: Path, sample_rate: int) -> tuple[np.ndarray, int]:
	"""Load audio and return a mono waveform at the desired sample rate."""

	primary_exc: Exception | None = None
	try:
		waveform, sr = librosa.load(audio_path.as_posix(), sr=sample_rate)
		return waveform, sr
	except Exception as exc:  # pragma: no cover - backend dependent
		primary_exc = exc
		logger.debug('librosa não conseguiu ler %s: %s', audio_path, exc)

	try:
		import audioread

		with audioread.audio_open(audio_path.as_posix()) as reader:
			native_sr = reader.samplerate
			channels = reader.channels
			pcm_chunks = [np.frombuffer(buf, dtype=np.int16) for buf in reader]

		if not pcm_chunks:
			return np.array([], dtype=np.float32), sample_rate

		pcm = np.concatenate(pcm_chunks)
		if channels > 1:
			pcm = pcm.reshape(-1, channels).mean(axis=1)

		waveform = pcm.astype(np.float32) / 32768.0
		if native_sr != sample_rate and waveform.size:
			waveform = librosa.resample(waveform, orig_sr=native_sr, target_sr=sample_rate)
		return waveform, sample_rate
	except Exception as exc:  # pragma: no cover - dependent on ffmpeg backend
		logger.debug('audioread não conseguiu ler %s: %s', audio_path, exc)
		if primary_exc is None:
			primary_exc = exc

	try:
		ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
		command = [
			ffmpeg_exe,
			'-hide_banner',
			'-loglevel', 'error',
			'-i', audio_path.as_posix(),
			'-ac', '1',
			'-ar', str(sample_rate),
			'-f', 'f32le',
			'pipe:1',
		]
		completed = subprocess.run(
			command,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			check=False,
		)
		if completed.returncode != 0:
			stderr = completed.stderr.decode('utf-8', errors='ignore').strip()
			raise AudioProcessingError(
				f'FFmpeg não conseguiu converter o áudio ({audio_path.name}): {stderr}'
			)
		waveform = np.frombuffer(completed.stdout, dtype=np.float32)
		return waveform, sample_rate
	except AudioProcessingError:
		raise
	except Exception as exc:  # pragma: no cover - defensive
		reason = _error_details(primary_exc or exc)
		raise AudioProcessingError(
			f'Não foi possível converter o áudio ({audio_path.name}): {reason}'
		) from exc


def _extract_melspectrogram(
	audio_path: Path,
	*,
	sample_rate: int = 22050,
	n_mels: int = 40,
	hop_length: int = 512,
	n_fft: int = 2048,
	target_frames: int = 174,
) -> np.ndarray:
	"""Convert an audio file into the mel-spectrogram tensor expected by the model."""

	waveform, sr = _load_waveform(audio_path, sample_rate)

	if waveform.size == 0:
		raise AudioProcessingError('O arquivo de áudio está vazio ou corrompido.')

	melspec = librosa.feature.melspectrogram(
		y=waveform,
		sr=sr,
		n_fft=n_fft,
		hop_length=hop_length,
		n_mels=n_mels,
	)
	melspec_db = librosa.power_to_db(melspec, ref=np.max)

	# Pad or trim time dimension so the tensor matches the training shape (40, 174).
	if melspec_db.shape[1] < target_frames:
		pad_width = target_frames - melspec_db.shape[1]
		melspec_db = np.pad(melspec_db, ((0, 0), (0, pad_width)), mode='constant')
	else:
		melspec_db = melspec_db[:, :target_frames]

	features = melspec_db.astype(np.float32)
	features = np.expand_dims(features, axis=-1)  # (40, 174, 1)
	features = np.expand_dims(features, axis=0)   # (1, 40, 174, 1)
	return features


def _aggregate_probabilities(raw_labels: np.ndarray, probs: np.ndarray) -> Dict[str, float]:
	"""Remap raw model labels to the canonical ones used in the application."""

	aggregated: Dict[str, float] = {emotion: 0.0 for emotion in CANONICAL_EMOTIONS}
	for label, probability in zip(raw_labels, probs):
		canonical = RAW_TO_CANONICAL.get(label, label)
		if canonical not in aggregated:
			aggregated[canonical] = 0.0
		aggregated[canonical] += float(probability)
	return aggregated


def analyze_audio_file(audio_path: Path) -> Dict[str, object]:
	"""Run the end-to-end prediction pipeline for the supplied audio file."""

	absolute_path = audio_path if audio_path.is_absolute() else Path(audio_path).resolve()
	if not absolute_path.exists():
		raise AudioProcessingError(f"Arquivo de áudio não encontrado: {absolute_path}")

	model = load_model()
	encoder = load_label_encoder()

	features = _extract_melspectrogram(absolute_path)
	predictions = model.predict(features, verbose=0)[0]

	raw_labels = encoder.classes_
	top_raw_label = raw_labels[int(np.argmax(predictions))]
	aggregated = _aggregate_probabilities(raw_labels, predictions)

	dominant_emotion = RAW_TO_CANONICAL.get(top_raw_label, top_raw_label)
	confidence = float(aggregated.get(dominant_emotion, 0.0))

	# Ensure we only return canonical labels in the final payload.
	emotions_data = {
		emotion: float(aggregated.get(emotion, 0.0))
		for emotion in CANONICAL_EMOTIONS
	}

	return {
		'dominant_emotion': dominant_emotion,
		'confidence': confidence,
		'emotions_data': emotions_data,
		'raw_prediction': top_raw_label,
	}


def analyze_recording(recording) -> Dict[str, object]:
	"""Thin wrapper to analyse a Django ``AudioRecording`` instance."""

	audio_file_path = Path(recording.audio_file.path)
	result = analyze_audio_file(audio_file_path)
	logger.debug('Previsão gerada: raw=%s canonical=%s', result['raw_prediction'], result['dominant_emotion'])
	return result
