# 🚀 GUIA RÁPIDO - Plataforma de Saúde Mental v2.0

## ⚡ Início Rápido

### 1. Instalar e Executar
```bash
# Entrar no diretório
cd f:\xampp\htdocs\plataforma

# Ativar ambiente virtual
.venv\Scripts\activate

# Instalar dependências (se necessário)
pip install -r requirements.txt

# Executar migrações
python manage.py migrate

# Iniciar servidor
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000**

### 2. Criar Contas para Teste

#### Conta Paciente
1. Clique em "Registro"
2. Preencha dados
3. Após login, vá em "Meu Perfil"
4. Selecione "Paciente"
5. Salve

#### Conta Profissional
1. Clique em "Registro"
2. Preencha dados
3. Após login, vá em "Meu Perfil"
4. Selecione "Profissional"
5. Adicione: Número de Registro, Especialização
6. Salve

---

## 🎮 Jogos

### Acessar Jogos
Após login: **Dashboard** → **Jogos** → Escolha um jogo

### Jogo da Memória 🧠
- **Tempo**: Ilimitado
- **Objetivo**: Encontrar os 6 pares
- **Score**: 100 - (tentativas × 2)
- **Dica**: Preste atenção na posição das cartas

### Exercício de Respiração 🫁
- **Duração**: ~2 minutos
- **Ciclos**: 4 completos
- **Objetivo**: Relaxar e aliviar stress
- **Sequência**: Inspire (4s) → Segure (4s) → Expire (4s) → Pausa (2s)

### Jogo de Cores 🎨
- **Tempo**: 30 segundos
- **Objetivo**: Máximo de acertos
- **Pontos**: +10 por acerto
- **Mecânica**: Clique na cor que combina com o texto

---

## 👨‍⚕️ Telepsicologia

### Para Pacientes

#### Agendar Consulta
1. **Dashboard** → **Consultas**
2. Clique **"Agendar Consulta"**
3. Selecione um profissional
4. Escolha data, hora, e descreva o motivo
5. Envie o formulário

#### Participar de Consulta
1. **Consultas** → Selecione a consulta
2. Use o **chat** para se comunicar
3. Compartilhe suas emoções e dúvidas

#### Ver Histórico
- Todas as consultas aparecem em **Consultas**
- Filtro automático por status

### Para Profissionais

#### Gerenciar Consultas
1. **Dashboard** → Ver **"Consultas Hoje"**
2. **Consultas** → Todas as solicitações
3. Clique na consulta para aceitar/rejeitar

#### Atender Paciente
1. Acesse a consulta no horário agendado
2. Use **chat** para comunicação
3. Adicione **anotações** sobre a consulta
4. Marque como **concluída** ao terminar

#### Acompanhar Resultados
- Ver análises de emoção dos pacientes
- Acompanhar scores de jogos
- Histórico completo de comunicações

---

## 📊 Análise de Emoções

### Gravar/Upload de Áudio
1. **Dashboard** → **Nova Gravação**
2. Escolha: Gravar OU Fazer Upload
3. Adicione título e descrição
4. Envie para análise

### Ver Resultados
1. **Histórico** → Selecione gravação
2. Veja:
   - Emoção dominante
   - Confiança da análise
   - Distribuição de todas as emoções
   - Recomendações

### Acompanhar Progresso
- **Dashboard** mostra:
  - Total de gravações
  - Emoção dominante
  - Gráfico de tendências
  - Gravações recentes

---

## 🔐 Segurança

### Suas Informações
- Apenas você acessa seus dados
- Profissionais só veem info de seus pacientes
- Conversas são privadas
- Áudios são criptografados

### Logout
Sempre clique em **"Sair"** ao terminar
- Especialmente em computadores compartilhados

---

## 📱 Acessar de Qualquer Lugar

### Computador
- Abra: `http://127.0.0.1:8000`

### Celular/Tablet (mesma rede)
- Abra: `http://[SEU_IP]:8000`
- Exemplo: `http://192.168.1.100:8000`

### Pela Internet (após configuração)
- Configure hostname em `settings.py`
- Deploy em servidor dedicado

---

## ⚙️ Configurações Úteis

### Perfil
- **Meu Perfil** → Atualize dados pessoais
- Tipo de usuário
- Contato (telefone)
- Para profissionais: registro e especialização

### Notificações
- Ativar/desativar notificações de consultas
- (Pendente de implementação WebSocket)

### Dashboard
- Mostra dados personalizados por tipo
- Atalhos para principais funcionalidades

---

## 🆘 Solução de Problemas

### Servidor não inicia
```bash
# Verificar se porta 8000 está em uso
netstat -ano | findstr :8000

# Matar processo
taskkill /PID [PID] /F

# Ou usar outra porta
python manage.py runserver 8001
```

### Erro de migração
```bash
# Refazer migrações
python manage.py migrate zero
python manage.py migrate
```

### Cache
```bash
# Limpar cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Arquivo não encontrado
- Confirme que arquivo está em `media/audio_recordings/`
- Verifique permissões

---

## 📚 URLs Principais

| Funcionalidade | URL | Descrição |
|---|---|---|
| Home | `/` | Página inicial |
| Dashboard | `/dashboard/` | Painel principal |
| Jogos | `/games/` | Menu de jogos |
| Memória | `/games/memory/` | Jogo da memória |
| Respiração | `/games/breathing/` | Exercício de respiração |
| Cores | `/games/color-matching/` | Jogo de cores |
| Consultas | `/consultations/` | Lista de consultas |
| Agendar | `/consultations/schedule/` | Agendar consulta |
| Análise | `/record/` | Gravar/upload de áudio |
| Histórico | `/history/` | Histórico de gravações |
| Perfil | `/profile/setup/` | Configuração de perfil |
| Admin | `/admin/` | Painel administrativo |

---

## 💡 Dicas

### Melhor Experiência
- Use navegador moderno (Chrome, Edge, Firefox)
- Tela mínima de 1024x768 pixels
- Conexão internet estável para uploads

### Jogos
- Jogo da Memória: ótimo para concentração
- Respiração: faça antes de dormir
- Cores: desafie amigos

### Consultas
- Agende com antecedência
- Teste audio/video antes
- Tenha papel para anotações

### Análise
- Grave em ambiente calmo
- Qualidade de áudio melhor = resultados melhores
- Revise tendências de emoções

---

## 📞 Contato/Suporte

Para problemas técnicos:
1. Verifique CHANGELOG.md
2. Consulte documentação em README.md
3. Abra issue no GitHub

---

**Última atualização**: 03/02/2026 v2.0
**Status**: ✅ Pronto para Uso
