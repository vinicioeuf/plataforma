"""analise_modelo.py

Script de exemplo para treinar e testar um modelo de reconhecimento
de emoções a partir de arquivos de áudio (baseado no dataset RAVDESS).

Fluxo principal:
1. Baixa/verifica o dataset RAVDESS via `kagglehub`.
2. Extrai características (MFCC) dos arquivos de áudio.
3. Treina um classificador MLP com as emoções selecionadas.
4. Avalia o modelo e plota a matriz de confusão.
5. Permite gravação de voz em tempo real para prever a emoção.

Notas:
- Este arquivo foi documentado para facilitar leitura e manutenção.
- Dependências principais: librosa, numpy, sounddevice, scipy,
  scikit-learn, matplotlib, seaborn, kagglehub.

Uso:
    python analise_modelo.py

"""

import os
import glob
import librosa
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import kagglehub

# 1. Download do Dataset (Seu código original)
print("Baixando/Verificando o dataset RAVDESS...")
dataset_path = kagglehub.dataset_download("uwrfkaggler/ravdess-emotional-speech-audio")
print("Caminho do dataset:", dataset_path)

# Dicionário de emoções do padrão RAVDESS
# O 3º número no nome do arquivo RAVDESS representa a emoção
# Mapeamento entre códigos do arquivo RAVDESS e rótulos em português.
emotions_dict = {
    '01': 'neutro',
    '02': 'calmo',
    '03': 'feliz',
    '04': 'triste',
    '05': 'irritado',
    '06': 'assustado',
    '07': 'nojo',
    '08': 'surpreso'
}

# Subconjunto de emoções usadas para treino/avaliação (simplificação).
observed_emotions = ['feliz', 'triste', 'irritado', 'neutro']

# 2. Função de Extração de Características (MFCC)
def extract_feature(file_name):
    """Extrai características (MFCC) de um arquivo de áudio.

    Carrega o arquivo com `librosa.load` (preservando a taxa original) e
    calcula os MFCCs com `n_mfcc=40`. Retorna a média dos coeficientes ao
    longo do tempo, resultando em um vetor fixo (40 dimensões).

    Args:
        file_name (str): Caminho para o arquivo de áudio (*.wav).

    Returns:
        numpy.ndarray: Vetor 1D com a média dos 40 coeficientes MFCC.
    """
    # Carrega o áudio e a taxa de amostragem
    X, sample_rate = librosa.load(file_name, sr=None)
    # Extrai os MFCCs (40 coeficientes) e tira a média temporal
    mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=40).T, axis=0)
    return mfccs

# 3. Carregando os Dados
def load_data(test_size=0.2):
    x, y = [], []
    # Busca por todos os arquivos .wav nas subpastas (Actor_01, Actor_02, etc.)
    for file in glob.glob(os.path.join(dataset_path, "**", "*.wav"), recursive=True):
        file_name = os.path.basename(file)
        # O padrão do RAVDESS é algo como 03-01-02-01-02-01-01.wav
        emotion_code = file_name.split("-")[2]
        emotion = emotions_dict[emotion_code]

        if emotion not in observed_emotions:
            continue

        feature = extract_feature(file)
        x.append(feature)
        y.append(emotion)

    return train_test_split(np.array(x), y, test_size=test_size, random_state=9)

print("\nExtraindo características dos áudios (isso pode levar alguns minutos)...")
X_train, X_test, y_train, y_test = load_data(test_size=0.25)
print(f'Características extraídas: {X_train.shape[0]} amostras de treino e {X_test.shape[0]} amostras de teste.')

# 4. Treinando o Modelo (Rede Neural MLP)
print("\nTreinando o modelo de Inteligência Artificial...")
# Configuração do MLPClassifier: hiperparâmetros escolhidos como exemplo.
model = MLPClassifier(alpha=0.01, batch_size=256, epsilon=1e-08,
                      hidden_layer_sizes=(300,), learning_rate='adaptive', max_iter=500)
model.fit(X_train, y_train)

# 5. Avaliação e Matriz de Confusão
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f'\nAcurácia do Modelo: {accuracy*100:.2f}%')
print("\nRelatório de Classificação:\n", classification_report(y_test, y_pred))

# Plotando a Matriz de Confusão

cm = confusion_matrix(y_test, y_pred, labels=observed_emotions)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=observed_emotions, yticklabels=observed_emotions)
plt.title('Matriz de Confusão - Reconhecimento de Emoções')
plt.ylabel('Emoção Real')
plt.xlabel('Emoção Prevista')
plt.show()

# 6. Gravando Áudio e Testando em Tempo Real
def record_and_predict():
    fs = 22050  # Taxa de amostragem padrão
    seconds = 4  # Duração da gravação
    print("\n" + "=" * 50)
    print("🎤 PREPARE-SE PARA FALAR!")
    print(f"Gravando por {seconds} segundos... Fale uma frase de forma neutra, feliz, triste ou irritada.")

    # Grava o áudio do microfone
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()  # Espera a gravação terminar
    print("Gravação concluída!")

    # Salva temporariamente
    temp_filename = "gravacao_teste.wav"
    write(temp_filename, fs, myrecording)

    # Extrai características e prevê
    features = extract_feature(temp_filename)
    prediction = model.predict([features])

    print(f"\n🧠 A emoção identificada na sua fala foi: **{prediction[0].upper()}**")
    print("=" * 50 + "\n")

# Chame a função para testar sua voz!
record_and_predict()