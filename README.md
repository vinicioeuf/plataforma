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

# EmotionAI — Plataforma de Análise de Emoções por Voz

Este repositório contém uma aplicação Django para gravação, upload e
análise de áudio com foco em detecção de emoções na fala. O objetivo
desse `README` é preparar o projeto para publicação Open Source e permitir
que desenvolvedores contribuam e executem localmente.

Links úteis:
- Código principal do app de análise: [emotion_analysis](emotion_analysis/)
- Script de exemplo de análise de modelo: [emotion_analysis/analise_modelo.py](emotion_analysis/analise_modelo.py)
- Arquivo de dependências: [requirements.txt](requirements.txt)

## Sumário
- Descrição
- Requisitos
- Instalação rápida
- Executando localmente
- Treinamento / usar modelo pré-treinado
- Testes e estilo de código
- Como contribuir
- Licença e considerações de privacidade

## Descrição

Plataforma web (Django) para gravação/upload de áudios, análise de emoções
e recursos adicionais (telepsicologia, jogos). A lógica de análise é
modular: você pode integrar seu próprio modelo de áudio (veja
[emotion_analysis/analise_modelo.py](emotion_analysis/analise_modelo.py)).

## Requisitos

- Python 3.8+
- FFmpeg (opcional, para conversões de áudio em alguns ambientes)
- Para desenvolvimento local: pip, virtualenv

Instale dependências com:

```bash
python -m venv .venv
source .venv/Scripts/activate    # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt
```

## Instalação rápida

1. Clone o repositório e entre na pasta:

```bash
git clone <REPO_URL>
cd plataforma
```

2. Configure e ative o ambiente virtual (veja comandos acima).

3. Rode migrações e crie um superusuário:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

4. Inicie o servidor de desenvolvimento:

```bash
python manage.py runserver
```

Abra `http://127.0.0.1:8000` no navegador.

## Treinamento / Como usar o modelo de análise

O repositório contém um exemplo de pipeline de treinamento em
[emotion_analysis/analise_modelo.py](emotion_analysis/analise_modelo.py). Esse
script mostra como extrair MFCCs, treinar um `MLPClassifier` e testar em
gravação local. Pontos importantes:

- O script baixa dataset via `kagglehub` (é preciso configurar credenciais).
- As dependências para treinamento incluem `librosa`, `scikit-learn`,
  `sounddevice`, `scipy`.
- Para produzir um artefato reutilizável (modelo salvo), adapte o script
  para salvar o modelo com `joblib.dump` ou `keras.models.save_model`.

Sugestão de comando para treinar/gerar modelo (exemplo):

```bash
python emotion_analysis/analise_modelo.py
# Após treinar, salve o modelo e adicione o arquivo em static/modelo/ ou
# em um bucket privado se preferir não commitar modelos grandes.
```

Integração com a aplicação Django:

- Implemente a função de processamento em [emotion_analysis/views.py](emotion_analysis/views.py)
  para carregar o modelo e retornar o dicionário de resultado esperado
  (dominant_emotion, confidence, emotions_data).

## Uso em produção

- Use um banco de dados robusto (Postgres/MySQL) e configure `ALLOWED_HOSTS`.
- Proteja as chaves/segredos com variáveis de ambiente.
- Armazene modelos grandes fora do repo (S3/Blob storage) e carregue-os
  na inicialização do serviço.

## Testes e estilo de código

Sugere-se adicionar testes unitários e linters. Comandos úteis:

```bash
pip install -r requirements.txt  # inclui pytest, flake8, black se desejado
pytest
flake8 .
black .
```

## Como contribuir

1. Fork do repositório
2. Crie uma branch descritiva: `git checkout -b feat/minha-melhora`
3. Adicione testes e siga o estilo do projeto
4. Faça commits pequenos e descritivos
5. Abra um Pull Request explicando a mudança

Guia de revisão mínima para PRs:

- Inclua descrição do problema/solução
- Inclua testes para bugs corrigidos ou funcionalidades novas
- Verifique se o código segue `black`/`flake8`

Modelos e dados:

- Não commite datasets grandes nem modelos binários. Use [git-lfs](https://git-lfs.github.com/)
  ou armazenamento externo.

Código sensível e credenciais:

- Nunca coloque chaves ou tokens no repositório. Use variáveis de ambiente
  e um arquivo `.env` ignorado pelo git.

## Licença

Recomenda-se uma licença permissiva para incentivar contribuições e uso.
Uma opção comum é a `MIT License`. Para adicionar a licença:

1. Crie um arquivo `LICENSE` contendo o texto da MIT License.
2. Adicione um cabeçalho curto no `README.md` indicando a escolha.

Exemplo de cabeçalho de licença no topo do repositório:

```
MIT License — consulte o arquivo LICENSE para detalhes.
```

Se preferir outra licença (Apache-2.0, GPLv3) escolha conforme necessidade.

## Privacidade e conformidade

- Os áudios podem conter dados pessoais sensíveis. Antes de publicar ou
  processar dados de usuários reais, verifique requisitos legais locais
  (LGPD, GDPR) e adapte termos/consentimento.
- Para deploy público, adicione uma política de privacidade clara e
  mecanismos para remoção de dados pessoais.

## Contato e suporte

Abra uma issue para relatar problemas ou discutir melhorias.

---

Se desejar, posso:

- Adicionar um arquivo `CONTRIBUTING.md` com checklists e modelos de PR.
- Gerar um `LICENSE` com texto MIT.
- Criar um `requirements-dev.txt` com `pytest`, `flake8`, `black`.

---

Arquivo alterado por este patch: [README.md](README.md)
