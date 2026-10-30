# Tutoria IA

[![CI](https://github.com/Kaua-TechDev/Tutoria_IA/actions/workflows/ci.yml/badge.svg)](https://github.com/Kaua-TechDev/Tutoria_IA/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Flask](https://img.shields.io/badge/flask-3.0-lightgrey)

Tutor educacional com IA generativa. O aluno tira dúvidas num chat que adapta a linguagem ao seu nível de ensino, ganha XP e conquistas por estudar, e o responsável acompanha o progresso — e as dificuldades recorrentes — num painel próprio.

---

## Funcionalidades

### Chat com IA adaptativo
- Respostas da OpenAI em JSON estruturado: explicação, exercício prático e o tema da dúvida
- **Guardrails em duas camadas:** filtro determinístico por palavra-chave (sem custo de token) e regras no prompt de sistema para os casos que o filtro não prevê
- **Perfis por segmento:** Fundamental I, Fundamental II, Médio e Técnico têm tom e profundidade próprios
- **Resiliência:** timeout, rate limit, erro de rede ou chave inválida caem numa resposta local — a pergunta continua registrada e valendo XP. Sem chave configurada, o app roda inteiro em modo demonstração

### Gamificação
- XP por pergunta e cinco níveis com progressão automática
- 8 conquistas com critérios distintos (sequência de dias, trilhas concluídas, avaliações...), avaliadas até estabilizar — o bônus de uma pode liberar a seguinte
- **Alerta de dificuldade:** três perguntas sobre o mesmo tema avisam o responsável

### Painel do responsável
- Resumo, histórico e progresso por trilha de cada aluno vinculado
- Dashboard com 4 gráficos (Chart.js): engajamento diário, volume por disciplina, distribuição por nível e ranking de XP
- Cada responsável enxerga **somente** os alunos vinculados a ele

---

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12+, Flask 3, SQLAlchemy 2 |
| IA | OpenAI API (`gpt-4o-mini` por padrão) |
| Banco | SQLite (padrão) ou MySQL |
| Autenticação | Flask-Login, bcrypt, Flask-WTF (CSRF), Flask-Limiter |
| Frontend | Jinja2, Tailwind CSS, Chart.js |
| Qualidade | pytest, ruff, GitHub Actions |

---

## Arquitetura

```
├── app/
│   ├── __init__.py          # App factory, headers de segurança, páginas de erro
│   ├── extensions.py        # db, CSRF, rate limiter, login manager
│   ├── models.py            # 8 tabelas + regras de nível e senha
│   ├── ia_service.py        # OpenAI: guardrails, perfis, fallback local
│   ├── gamificacao.py       # XP, conquistas e alertas de dificuldade
│   ├── routes/
│   │   ├── access.py        # Decorator de controle de acesso por papel
│   │   ├── auth.py          # Login e logout
│   │   ├── student.py       # Chat e avaliação das respostas
│   │   └── guardian.py      # Painel, detalhes do aluno e dashboard
│   ├── templates/
│   └── static/
├── db/
│   ├── schema.sql           # Schema MySQL
│   └── init_db.py           # Cria as tabelas e os dados de demonstração
├── docs/                    # Diagrama entidade-relacionamento
├── tests/                   # Testes de models, serviço de IA e rotas
├── config.py                # Configuração por ambiente (dev, test, prod)
└── run.py
```

**Fluxo de uma pergunta:** `POST /chat/perguntar` → validação → `ia_service.answer_question()` (guardrail → OpenAI ou fallback) → sessão salva → `gamificacao.process_session()` (XP, conquistas, alerta) → um único commit → JSON para o front-end.

---

## Como rodar

**Pré-requisito:** Python 3.12+

```bash
git clone https://github.com/Kaua-TechDev/Tutoria_IA.git
cd Tutoria_IA

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # opcional: preencha OPENAI_API_KEY
python db/init_db.py            # cria o banco com dados de demonstração
python run.py
```

Acesse `http://localhost:5000`. No Windows, `iniciar_windows.bat` faz todos os passos.

| Papel | Login | Senha |
|---|---|---|
| Aluno | matrícula `2026001` | `teste123` |
| Responsável | `maria.lima@email.com` | `teste123` |

### Testes e lint

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

---

## Variáveis de ambiente

Todas são opcionais em desenvolvimento; o `.env.example` explica cada uma.

| Variável | Descrição |
|---|---|
| `APP_ENV` | `development` (padrão) ou `production` |
| `SECRET_KEY` | Assina os cookies de sessão. Obrigatória em produção |
| `DATABASE_URL` | URL do banco (padrão: SQLite em `instance/`) |
| `OPENAI_API_KEY` | Chave da OpenAI. Sem ela, modo demonstração |
| `OPENAI_MODEL` | Modelo usado (padrão: `gpt-4o-mini`) |
| `OPENAI_TIMEOUT` | Segundos de espera pela API (padrão: 20) |
| `OPENAI_MAX_RETRIES` | Novas tentativas em falhas temporárias (padrão: 2) |
| `PORT` | Porta do servidor local (padrão: 5000) |
| `RATELIMIT_STORAGE_URI` | Storage do rate limit (padrão: memória; use Redis com vários workers) |

---

## Segurança

- Senhas com bcrypt; login com tempo constante, sem revelar quais matrículas ou e-mails existem
- CSRF em todos os formulários e chamadas JSON; logout apenas por POST
- Rate limit no login (força bruta) e no chat (custo da API por aluno)
- Autorização por papel em todas as rotas; recursos de outros usuários respondem 404
- Cookies `HttpOnly` e `SameSite=Lax`; em produção, `Secure` e HSTS
- Headers `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e `Permissions-Policy`
- Tamanho máximo de pergunta e de requisição, limitando abuso e custo de tokens
- Conteúdo da IA sempre inserido como texto no DOM, nunca como HTML

---

## Decisões técnicas

- **Fallback em vez de erro:** a IA é uma dependência externa; quando falha, o aluno recebe uma resposta útil e o progresso não se perde
- **Guardrail por palavra-chave antes da API:** bloqueio determinístico, instantâneo e sem custo; o prompt de sistema cobre o restante
- **Agregações no banco:** painel e dashboard usam `GROUP BY` em vez de carregar sessões na memória
- **Gamificação sem commit:** as regras só fazem `flush`; a rota decide quando gravar, então uma falha desfaz tudo de uma vez
- **SQLite por padrão, MySQL via `DATABASE_URL`:** roda localmente sem infraestrutura
- **Chart.js servido localmente:** sem dependência de CDN para os gráficos

---

## Autores

- **Kauã Ernesto** — [@Kaua-TechDev](https://github.com/Kaua-TechDev)
- [@samfernandes](https://github.com/samfernandes)

---

## Licença

[MIT](LICENSE)
