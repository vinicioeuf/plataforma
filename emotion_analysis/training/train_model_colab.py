"""Script de treinamento para o modelo de reconhecimento de emoções.
Copie para o Google Colab, ajuste os caminhos do Google Drive conforme necessário
(Dataset e pasta de saída), execute a célula inteira e os artefatos do modelo
serão salvos na pasta static/modelo do projeto.
"""

import os
import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

import librosa
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from joblib import dump
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from tensorflow.keras import callbacks, layers, models, optimizers, regularizers
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.layers import TimeDistributed

# -------------------- Configurações principais -------------------- #

@dataclass
class TrainingConfig:
    dataset_path: str = "/content/drive/MyDrive/RAVDESS"
    output_dir: str = "/content/drive/MyDrive/plataforma/static/modelo"
    sample_rate: int = 22050
    n_mfcc: int = 64
    max_pad_len: int = 216  # divisível por 8 após as camadas de pooling
    augmentations_per_file: int = 2
    noise_factor: float = 0.006
    stretch_range: Tuple[float, float] = (0.88, 1.12)
    pitch_steps: Tuple[int, int] = (-2, 2)
    test_size: float = 0.2
    random_seed: int = 42
    batch_size: int = 32
    epochs: int = 120
    base_learning_rate: float = 3e-4


# Dicionário oficial do RAVDESS
EMOTION_MAP = {
    "01": "neutro",
    "02": "calmo",
    "03": "feliz",
    "04": "triste",
    "05": "raivoso",
    "06": "medroso",
    "07": "desgosto",
    "08": "surpreso",
}


CONFIG = TrainingConfig()
random.seed(CONFIG.random_seed)
np.random.seed(CONFIG.random_seed)

MODEL_PATH = os.path.join(CONFIG.output_dir, "modelo_emocoes.keras")
ENCODER_PATH = os.path.join(CONFIG.output_dir, "label_encoder.joblib")
HISTORY_PLOT = os.path.join(CONFIG.output_dir, "training_history.png")
CONFUSION_PLOT = os.path.join(CONFIG.output_dir, "confusion_matrix.png")


# -------------------- Utilidades de áudio -------------------- #

def load_audio(path: str, sr: int) -> Tuple[np.ndarray, int]:
    audio, sample_rate = librosa.load(path, sr=sr)
    return audio, sample_rate


def pad_or_trim(feature: np.ndarray, target_len: int) -> np.ndarray:
    current_len = feature.shape[1]
    if current_len < target_len:
        pad_width = target_len - current_len
        feature = np.pad(feature, ((0, 0), (0, pad_width)), mode="constant")
    else:
        feature = feature[:, :target_len]
    return feature


def compute_mfcc_stack(audio: np.ndarray, sr: int, cfg: TrainingConfig) -> np.ndarray:
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=cfg.n_mfcc)
    mfcc = pad_or_trim(mfcc, cfg.max_pad_len)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)
    stacked = np.stack([mfcc, delta, delta2], axis=-1)
    mean = np.mean(stacked, axis=(0, 1), keepdims=True)
    std = np.std(stacked, axis=(0, 1), keepdims=True) + 1e-8
    stacked = (stacked - mean) / std
    return stacked.astype(np.float32)


def add_noise(audio: np.ndarray, factor: float) -> np.ndarray:
    noise = np.random.randn(len(audio))
    augmented = audio + factor * noise
    return augmented.astype(np.float32)


def stretch_audio(audio: np.ndarray, rate: float) -> np.ndarray:
    stretched = librosa.effects.time_stretch(audio, rate)
    return stretched.astype(np.float32)


def shift_pitch(audio: np.ndarray, sr: int, steps: int) -> np.ndarray:
    shifted = librosa.effects.pitch_shift(audio, sr=sr, n_steps=steps)
    return shifted.astype(np.float32)


def random_augmentation(audio: np.ndarray, sr: int, cfg: TrainingConfig) -> np.ndarray:
    augmented = audio.copy()
    applied = False

    if cfg.noise_factor > 0 and random.random() < 0.7:
        augmented = add_noise(augmented, cfg.noise_factor)
        applied = True

    if random.random() < 0.7:
        rate = random.uniform(*cfg.stretch_range)
        augmented = stretch_audio(augmented, rate)
        applied = True

    if random.random() < 0.7:
        steps = random.randint(*cfg.pitch_steps)
        if steps != 0:
            augmented = shift_pitch(augmented, sr, steps)
            applied = True

    if not applied and cfg.noise_factor > 0:
        augmented = add_noise(augmented, cfg.noise_factor)

    return augmented


# -------------------- Carregamento do dataset -------------------- #

def list_dataset_files(dataset_path: str) -> Tuple[List[str], List[str]]:
    audio_paths: List[str] = []
    labels: List[str] = []
    for root, _, files in os.walk(dataset_path):
        for filename in files:
            if not filename.lower().endswith(".wav"):
                continue
            parts = filename.split("-")
            if len(parts) < 3:
                continue
            label_key = parts[2][:2]
            label = EMOTION_MAP.get(label_key)
            if not label:
                continue
            audio_paths.append(os.path.join(root, filename))
            labels.append(label)
    if not audio_paths:
        raise ValueError("Nenhum arquivo .wav encontrado. Verifique o caminho do dataset.")
    return audio_paths, labels


def build_feature_set(
    paths: Sequence[str],
    labels: Sequence[str],
    cfg: TrainingConfig,
    augment: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    features: List[np.ndarray] = []
    y: List[str] = []
    for path, label in zip(paths, labels):
        try:
            audio, sr = load_audio(path, cfg.sample_rate)
            features.append(compute_mfcc_stack(audio, sr, cfg))
            y.append(label)
            if augment:
                for _ in range(cfg.augmentations_per_file):
                    augmented_audio = random_augmentation(audio, sr, cfg)
                    features.append(compute_mfcc_stack(augmented_audio, sr, cfg))
                    y.append(label)
        except Exception as exc:
            print(f"Falha ao processar {path}: {exc}")
    X = np.stack(features)
    y_array = np.array(y)
    return X, y_array


# -------------------- Modelo -------------------- #

def build_model(input_shape: Tuple[int, int, int], num_classes: int) -> models.Model:
    inputs = layers.Input(shape=input_shape)

    x = layers.Conv2D(64, (3, 3), padding="same", kernel_regularizer=regularizers.l2(1e-4))(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(64, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.SpatialDropout2D(0.2)(x)

    x = layers.Conv2D(128, (3, 3), padding="same", kernel_regularizer=regularizers.l2(1e-4))(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv2D(128, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.SpatialDropout2D(0.3)(x)

    x = layers.Conv2D(256, (3, 3), padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.SpatialDropout2D(0.35)(x)

    x = layers.Permute((2, 1, 3))(x)
    x = TimeDistributed(layers.Flatten())(x)

    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Bidirectional(layers.LSTM(64))(x)
    x = layers.Dropout(0.4)(x)

    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.4)(x)

    outputs = layers.Dense(num_classes, activation="softmax")(x)
    model = models.Model(inputs=inputs, outputs=outputs)
    return model


def make_callbacks(cfg: TrainingConfig) -> List[callbacks.Callback]:
    os.makedirs(cfg.output_dir, exist_ok=True)
    monitor_metric = "val_accuracy"
    return [
        callbacks.ModelCheckpoint(
            MODEL_PATH,
            monitor=monitor_metric,
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
        callbacks.ReduceLROnPlateau(
            monitor=monitor_metric,
            mode="max",
            factor=0.5,
            patience=6,
            min_lr=1e-6,
            verbose=1,
        ),
        callbacks.EarlyStopping(
            monitor=monitor_metric,
            mode="max",
            patience=12,
            restore_best_weights=True,
            verbose=1,
        ),
    ]


# -------------------- Fluxo de treinamento -------------------- #

def main(cfg: TrainingConfig) -> None:
    os.makedirs(cfg.output_dir, exist_ok=True)

    print("Carregando caminhos do dataset...")
    paths, labels = list_dataset_files(cfg.dataset_path)
    print(f"Total de arquivos válidos: {len(paths)}")

    train_paths, test_paths, train_labels, test_labels = train_test_split(
        paths,
        labels,
        test_size=cfg.test_size,
        stratify=labels,
        random_state=cfg.random_seed,
    )

    print("Gerando features para o conjunto de treino (com aumento de dados)...")
    X_train, y_train = build_feature_set(train_paths, train_labels, cfg, augment=True)

    print("Gerando features para o conjunto de teste...")
    X_test, y_test = build_feature_set(test_paths, test_labels, cfg, augment=False)

    print(f"Dimensão X_train: {X_train.shape}")
    print(f"Dimensão X_test: {X_test.shape}")

    label_encoder = LabelEncoder()
    y_train_int = label_encoder.fit_transform(y_train)
    y_test_int = label_encoder.transform(y_test)

    y_train_cat = to_categorical(y_train_int)
    y_test_cat = to_categorical(y_test_int)

    class_weights = compute_class_weight(
        class_weight="balanced",
        classes=np.unique(y_train_int),
        y=y_train_int,
    )
    class_weights_dict = dict(enumerate(class_weights))
    print("Class weights:", class_weights_dict)

    model = build_model(X_train.shape[1:], y_train_cat.shape[1])
    model.compile(
        optimizer=optimizers.Adam(learning_rate=cfg.base_learning_rate),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    history = model.fit(
        X_train,
        y_train_cat,
        validation_data=(X_test, y_test_cat),
        epochs=cfg.epochs,
        batch_size=cfg.batch_size,
        callbacks=make_callbacks(cfg),
        class_weight=class_weights_dict,
        verbose=1,
    )

    print("Carregando o melhor modelo salvo...")
    best_model = models.load_model(MODEL_PATH)
    dump(label_encoder, ENCODER_PATH)
    print(f"Modelo salvo em {MODEL_PATH}")
    print(f"LabelEncoder salvo em {ENCODER_PATH}")

    loss, acc = best_model.evaluate(X_test, y_test_cat, verbose=0)
    print(f"Acurácia no conjunto de teste: {acc * 100:.2f}%")

    y_pred_probs = best_model.predict(X_test)
    y_pred = np.argmax(y_pred_probs, axis=1)
    report = classification_report(y_test_int, y_pred, target_names=label_encoder.classes_)
    print("\nRelatório de Classificação:\n", report)

    cm = confusion_matrix(y_test_int, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=label_encoder.classes_,
        yticklabels=label_encoder.classes_,
    )
    plt.ylabel("Verdadeiro")
    plt.xlabel("Predito")
    plt.title("Matriz de Confusão")
    plt.tight_layout()
    plt.savefig(CONFUSION_PLOT, dpi=150)
    plt.close()
    print(f"Matriz de confusão salva em {CONFUSION_PLOT}")

    plt.figure(figsize=(9, 4))
    plt.plot(history.history["accuracy"], label="Treino")
    plt.plot(history.history["val_accuracy"], label="Validação")
    plt.plot(history.history["loss"], label="Loss treino")
    plt.plot(history.history["val_loss"], label="Loss validação")
    plt.xlabel("Épocas")
    plt.title("Evolução do Treinamento")
    plt.legend()
    plt.tight_layout()
    plt.savefig(HISTORY_PLOT, dpi=150)
    plt.close()
    print(f"Histórico de treinamento salvo em {HISTORY_PLOT}")


if __name__ == "__main__":
    main(CONFIG)
