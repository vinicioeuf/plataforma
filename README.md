# EmotionAI - Plataforma de Análise de Emoções por Voz

## 📋 Descrição

Plataforma web desenvolvida em Django e Bootstrap para análise de emoções através de gravações de áudio. Este projeto foi desenvolvido como parte de um Trabalho de Conclusão de Curso (TCC) e permite que usuários gravem ou façam upload de áudios para identificar emoções presentes na voz.

## ✨ Funcionalidades

- 🎤 **Gravação de Áudio**: Grave áudios diretamente pelo navegador
- 📤 **Upload de Arquivos**: Envie arquivos de áudio existentes (MP3, WAV, OGG, WebM, M4A)
- 🔐 **Sistema de Autenticação**: Registro, login e logout de usuários
- 📊 **Dashboard Interativo**: Visualize estatísticas e histórico de análises
- 😊 **Análise de Emoções**: Identifica 7 emoções principais (Alegria, Tristeza, Raiva, Medo, Surpresa, Nojo, Neutro)
- 📜 **Histórico**: Acesse todas as suas gravações e análises anteriores
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
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

5. **Execute as migrações do banco de dados**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crie um superusuário (admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Execute o servidor de desenvolvimento**
   ```bash
   python manage.py runserver
   ```

8. **Acesse a aplicação**
   - Abra seu navegador e acesse: `http://127.0.0.1:8000`
   - Painel administrativo: `http://127.0.0.1:8000/admin`

## 🎯 Como Usar

### Para Usuários

1. **Cadastro**: Crie uma conta na página de registro
2. **Login**: Faça login com suas credenciais
3. **Gravar Áudio**: 
   - Acesse "Nova Gravação"
   - Escolha entre gravar um áudio ou fazer upload de um arquivo
   - Adicione um título e descrição (opcional)
   - Envie para análise
4. **Visualizar Resultados**: Veja a emoção dominante e a distribuição de todas as emoções
5. **Histórico**: Acesse todas as suas gravações anteriores

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
│   ├── models.py               # Modelos de dados
│   ├── views.py                # Lógica de negócio
│   ├── forms.py                # Formulários
│   ├── urls.py                 # Rotas
│   └── admin.py                # Configuração do admin
├── templates/                   # Templates HTML
│   ├── base.html
│   └── emotion_analysis/
│       ├── home.html
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── record_audio.html
│       ├── analyze_audio.html
│       ├── history.html
│       └── delete_recording.html
├── media/                       # Arquivos de áudio enviados
├── static/                      # Arquivos estáticos (CSS, JS)
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

## 🔒 Segurança

- Autenticação de usuários obrigatória para todas as funcionalidades principais
- Proteção CSRF em todos os formulários
- Validação de tipos de arquivo no upload
- Cada usuário só pode acessar suas próprias gravações

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
