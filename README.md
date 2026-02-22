# EmotionAI - Plataforma de Análise de Emoções por Voz

## 📋 Descrição

Plataforma web desenvolvida em Django e Bootstrap para análise de emoções através de gravações de áudio. Este projeto foi desenvolvido como parte de um Trabalho de Conclusão de Curso (TCC) e permite que usuários gravem ou façam upload de áudios para identificar emoções presentes na voz.

## ✨ Funcionalidades

### Análise de Emoções
- 🎤 **Gravação de Áudio**: Grave áudios diretamente pelo navegador
- 📤 **Upload de Arquivos**: Envie arquivos de áudio existentes (MP3, WAV, OGG, WebM, M4A)
- 😊 **Análise de Emoções**: Identifica 7 emoções principais (Alegria, Tristeza, Raiva, Medo, Surpresa, Nojo, Neutro)
- 📜 **Histórico**: Acesse todas as suas gravações e análises anteriores
- 📊 **Dashboard Interativo**: Visualize estatísticas e histórico de análises

### Telepsicologia (NOVO)
- 👨‍⚕️ **Sistema de Consultas**: Pacientes podem agendar consultas com profissionais de saúde mental
- 💬 **Chat de Consulta**: Comunicação em tempo real entre paciente e profissional durante consultas
- 📅 **Agendamento de Consultas**: Sistema inteligente para agendar consultas
- 👥 **Perfis de Usuário**: Tipos de usuário diferentes (Paciente e Profissional)
- 📋 **Histórico de Consultas**: Acompanhe todas as consultas passadas e futuras

### Jogos Interativos (NOVO)
- 🧠 **Jogo da Memória**: Teste sua memória com um clássico jogo de cartas
- 🫁 **Exercício de Respiração**: Exercício guiado para relaxamento e redução do stress
- 🎨 **Jogo de Cores**: Combine cores rapidamente para aumentar a pontuação
- 🏆 **Sistema de Scores**: Acompanhe seus melhores scores em todos os jogos

### Gerais
- 🔐 **Sistema de Autenticação**: Registro, login e logout de usuários
- 🎨 **Interface Responsiva**: Design moderno com Bootstrap 5

## 🛠️ Tecnologias Utilizadas

- **Backend**: Django 4.2.7
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Banco de Dados**: SQLite (desenvolvimento)
- **Ícones**: Bootstrap Icons

## 📦 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou baixe o projeto**
   ```bash
   cd plataforma
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**
   - Windows:
     venv\Scripts\activate
     ```
4. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```
5. **Execute as migrações do banco de dados**
   ```bash
   python manage.py makemigrations
   python manage.py migrate

6. **Crie um superusuário (admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Execute o servidor de desenvolvimento**
   ```bash
   python manage.py runserver

8. **Acesse a aplicação**
   - Abra seu navegador e acesse: `http://127.0.0.1:8000`
   - Painel administrativo: `http://127.0.0.1:8000/admin`
## 🎯 Como Usar

### Para Pacientes

1. **Cadastro**: Crie uma conta na página de registro
3. **Configurar Perfil**: Acesse "Meu Perfil" e selecione "Paciente" como tipo de usuário
4. **Análise de Emoções**: 
   - Acesse "Nova Gravação"
   - Escolha entre gravar um áudio ou fazer upload de um arquivo
   - Envie para análise
5. **Jogar**: Acesse a seção "Jogos" para se distrair com:
   - Jogo da Memória
   - Exercício de Respiração Guiado
6. **Agendar Consulta**: 
   - Acesse "Consultas" → "Agendar Consulta"
   - Selecione um profissional de saúde mental

   - Escolha data e horário

   - Receba confirmação do profissional
7. **Participar de Consulta**:
   - Acesse a consulta agendada
   - Use o chat para se comunicar com o profissional
   - Compartilhe informações sobre seu estado emocional

### Para Profissionais de Saúde Mental

1. **Cadastro**: Crie uma conta na página de registro
2. **Login**: Faça login com suas credenciais
3. **Configurar Perfil Profissional**: 
   - Acesse "Meu Perfil"
   - Selecione "Profissional" como tipo de usuário
   - Adicione número de registro/crédito
   - Indique sua especialização (Psicólogo, Psiquiatra, etc.)
4. **Gerenciar Consultas**:
   - Acesse "Consultas" para ver todas as solicitações e consultas agendadas
   - Confirme ou rejeite solicitações de consulta
   - Acompanhe seu calendário de consultas
5. **Atender Pacientes**:
   - Acesse a consulta no horário agendado
   - Use o chat para comunicação em tempo real
   - Adicione notas sobre a consulta
   - Marque como concluída ao finalizar

### Para Desenvolvedores - Integrar Script de Análise de Emoções

O local preparado para adicionar seu script de análise está no arquivo:
**`emotion_analysis/views.py`** na função **`process_emotion_analysis`**

```python
# Área marcada para adicionar seu script (linhas 117-140)
# Seu script deve retornar um dicionário com:
resultado = {
    'dominant_emotion': 'alegria',  # ou outra emoção
    'confidence': 0.85,  # valor entre 0 e 1
    'emotions_data': {
        'alegria': 0.85,
        'tristeza': 0.05,
        'raiva': 0.03,
        'medo': 0.02,
        'surpresa': 0.03,
        'nojo': 0.01,
        'neutro': 0.01
    }
}
```

## 📁 Estrutura do Projeto

```
plataforma/
├── config/                      # Configurações do Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── emotion_analysis/            # App principal
│   ├── models.py               # Modelos: AudioRecording, EmotionAnalysis, UserProfile, 
│   │                           #         Consultation, Message, GameScore
│   ├── views.py                # Lógica de negócio (análise, telepsicologia, jogos)
│   ├── forms.py                # Formulários
│   ├── urls.py                 # Rotas
│   └── admin.py                # Configuração do admin
├── templates/                   # Templates HTML
│   ├── base.html               # Template base
│   └── emotion_analysis/
│       ├── home.html           # Página inicial
│       ├── login.html          # Login
│       ├── register.html       # Registro
│       ├── dashboard.html      # Dashboard (paciente/profissional)
│       ├── profile_setup.html  # Configuração de perfil
│       ├── record_audio.html   # Gravação/upload de áudio
│       ├── analyze_audio.html  # Análise de emoções
│       ├── history.html        # Histórico de gravações
│       ├── delete_recording.html # Deletar gravação
│       ├── consultations.html  # Lista de consultas
│       ├── consultation_detail.html # Detalhes da consulta + chat
│       ├── schedule_consultation.html # Agendar consulta
│       └── games/              # Seção de jogos
│           ├── games_menu.html # Menu de jogos
│           ├── memory_game.html # Jogo da memória
│           ├── breathing_exercise.html # Exercício de respiração
│           └── color_matching.html # Jogo de cores
├── media/                       # Arquivos de áudio enviados
├── static/                      # Arquivos estáticos (CSS, JS)
│   ├── css/
│   │   └── main.css            # Estilos personalizados
│   └── modelo/                 # Modelos treinados
├── manage.py
└── requirements.txt
```

## 🗃️ Modelos de Dados

### AudioRecording
- Armazena informações sobre as gravações de áudio
- Campos: user, title, description, audio_file, duration, created_at

### EmotionAnalysis
- Armazena os resultados da análise de emoções
- Campos: recording, dominant_emotion, confidence, emotions_data, notes, analyzed_at

### UserProfile
- Perfil estendido do usuário com tipos diferentes
- Tipos: Paciente e Profissional
- Campos: user, user_type, phone, birth_date, license_number, specialization, notifications_enabled

### Consultation
- Consultas de telepsicologia agendadas
- Estados: Agendada, Em Andamento, Concluída, Cancelada
- Campos: patient, professional, title, description, scheduled_datetime, duration_minutes, status, notes

### Message
- Mensagens entre paciente e profissional
- Campos: sender, recipient, consultation, content, is_read, created_at

### GameScore
- Pontuações dos jogos dos usuários
- Campos: user, game_name, score, time_spent, created_at

## 🔒 Segurança

- Autenticação de usuários obrigatória para todas as funcionalidades principais
- Proteção CSRF em todos os formulários
- Validação de tipos de arquivo no upload
- Cada usuário só pode acessar suas próprias gravações
- Isolamento de dados entre pacientes e profissionais
- Permissões específicas por tipo de usuário

## ✨ Novidades na Versão 2.0

### Sistema de Telepsicologia
- Pacientes podem agendar consultas com profissionais
- Sistema de chat integrado para comunicação durante consultas
- Profissionais podem adicionar notas sobre consultas
- Histórico completo de consultas
- Status de consulta em tempo real

### Sistema de Jogos
- **Jogo da Memória**: 12 cartas para testar concentração (com flip animation)
- **Exercício de Respiração**: 4 ciclos de respiração guiada com animação visual
- **Jogo de Cores**: Combine cores rapidamente com dificuldade progressiva
- Sistema de pontuação automático
- Histórico de scores salvos

### Perfis de Usuário
- Dois tipos de usuário distintos: Paciente e Profissional
- Cada tipo tem funcionalidades específicas
- Profissionais podem adicionar credenciais e especialização

## 🎮 Detalhes dos Jogos

### Jogo da Memória
- 12 cartas com emojis diferentes
- Encontre todos os 6 pares
- Acompanhe tentativas e tempo
- Score baseado em eficiência

### Exercício de Respiração
- Instruções guiadas: Inspire (4s), Segure (4s), Expire (4s), Pausa (2s)
- 4 ciclos completos
- Animação de respiração visual
- Relaxamento garantido

### Jogo de Cores
- 30 segundos para marcar o máximo de pontos
- Combine o texto com a cor correspondente
- Dificuldade aumenta com os acertos
- Pontuação em tempo real

## 🎨 Interface

A interface foi desenvolvida com Bootstrap 5 e inclui:
- Design responsivo para dispositivos móveis
- Gradientes e animações suaves
- Badges coloridos para diferentes emoções
- Ícones do Bootstrap Icons
- Sistema de mensagens (alertas) para feedback ao usuário

## 📝 Notas de Desenvolvimento

- O projeto usa SQLite por padrão (ideal para desenvolvimento)
- Para produção, configure outro banco de dados em `settings.py`
- Lembre-se de alterar o `SECRET_KEY` em produção
- Configure `DEBUG = False` em ambiente de produção
- Os arquivos de mídia são armazenados em `media/audio_recordings/`

## 🤝 Contribuindo

Como este é um projeto de TCC, as contribuições são limitadas. Porém, sugestões e melhorias são sempre bem-vindas!

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos (TCC).

## 👤 Autor

Desenvolvido como parte do Trabalho de Conclusão de Curso.

## 📧 Contato

Para dúvidas ou sugestões, entre em contato através do GitHub.

---

**Nota Importante**: O script de análise de emoções não está incluído. Você deve implementar ou integrar sua própria solução de análise de emoções por voz no local indicado no código.
