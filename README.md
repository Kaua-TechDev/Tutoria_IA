# Tutória

Tutor de trilhas de estudo com IA — projeto da disciplina Introdução à Inteligência
Artificial, Curso Técnico em Informática.

Stack: Python · Flask · SQLAlchemy · SQLite (ou MySQL) · OpenAI · Chart.js

## Integrantes

- Kauã
- Antônio
- Thainá
- Samuel

## Entregas

| Semana | Data       | Entrega                              | Status    |
|--------|------------|--------------------------------------|-----------|
| S1     | 01/06/2026 | Banco de dados — schema MySQL        | Entregue  |
| S2     | 08/06/2026 | Estrutura Flask + SQLAlchemy         | Entregue  |
| S3     | 15/06/2026 | MVP — autenticação + chat com IA     | Entregue  |
| S4     | 22/06/2026 | Trilhas e painel do responsável      | Entregue  |
| S5     | 29/06/2026 | Gamificação + dashboard              | Entregue  |

## Como rodar

Requisito: Python 3.10 ou superior. **Não precisa instalar MySQL** — o projeto
usa SQLite por padrão e cria o banco sozinho.

### Windows (jeito mais rápido)

```powershell
.\iniciar_windows.bat
```

O script cria o ambiente virtual, instala as dependências, gera o `.env`, cria o
banco de demonstração e sobe o servidor.

### Manual (qualquer sistema)

```bash
python -m venv venv
venv\Scripts\activate          # Linux/Mac: source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env         # Linux/Mac: cp .env.example .env

python db/inicializar_sqlite.py
python run.py
```

Acesse **http://localhost:5000**.

### Logins de teste

| Perfil       | Login                   | Senha      |
|--------------|-------------------------|------------|
| Aluno        | `2026001` (matrícula)   | `teste123` |
| Responsável  | `maria.lima@email.com`  | `teste123` |

Para recriar o banco do zero: `python db/inicializar_sqlite.py --reset`

## Variáveis de ambiente

O `.env` **não vai para o GitHub** (está no `.gitignore`). Copie o `.env.example`
e preencha:

| Variável         | Para que serve                                                  |
|------------------|-----------------------------------------------------------------|
| `OPENAI_API_KEY` | Chave da OpenAI. **Em branco = modo de demonstração**, sem IA.   |
| `SECRET_KEY`     | Chave de sessão do Flask.                                        |
| `DATABASE_URL`   | Em branco = SQLite. Para MySQL, veja abaixo.                     |

O chat **nunca derruba a aplicação**: se a chave estiver vazia, inválida ou a
internet cair, ele responde em modo local e continua registrando a pergunta e
concedendo XP.

### Usando MySQL em vez de SQLite

```bash
pip install PyMySQL
```

E no `.env`:

```
DATABASE_URL=mysql+pymysql://root:senha@localhost/tutor_trilhas
```

Depois rode `db/schema.sql` e `db/seed.sql` no MySQL.

## Estrutura

```
tutoria/
├── app/
│   ├── __init__.py        -- app factory, escolhe SQLite ou MySQL
│   ├── models.py          -- 8 tabelas + regras de XP e nível
│   ├── ia_service.py      -- OpenAI, guardrails e perfis por segmento
│   ├── gamificacao.py     -- XP, conquistas e alertas (Semana 5)
│   ├── routes/
│   │   ├── auth.py        -- login e logout
│   │   └── chat.py        -- chat, painel, detalhes e dashboard
│   ├── static/js/         -- Chart.js local (funciona sem internet)
│   └── templates/
├── db/
│   ├── schema.sql         -- MySQL (Semana 1)
│   ├── seed.sql           -- MySQL (Semana 1)
│   └── inicializar_sqlite.py  -- cria e popula o SQLite
├── .env.example
└── run.py
```

## As funcionalidades

### Autenticação e chat com IA (Semana 3)

Aluno entra com matrícula, responsável com e-mail. A IA adapta a explicação ao
segmento do aluno (do Fundamental I ao Técnico) e devolve sempre uma explicação
mais um exercício prático.

**Guardrails:** perguntas sobre mensalidade, boletos ou tentativas de burlar as
instruções são recusadas — e **não valem XP**.

### Trilhas e painel do responsável (Semana 4)

O responsável vê só os alunos vinculados a ele (acessar outro aluno devolve 403),
com progresso por trilha, histórico de sessões e alertas.

### Gamificação e dashboard (Semana 5)

**XP e níveis.** Cada pergunta respondida vale 10 XP. São cinco níveis —
Iniciante, Aprendiz, Intermediário, Avançado e Mestre — e a barra de progresso
anima na tela a cada ponto ganho.

**Conquistas.** As 8 medalhas do banco desbloqueiam sozinhas, avaliadas por
`app/gamificacao.py` a cada pergunta:

| Conquista | Critério | Bônus |
|-----------|----------|-------|
| 🎯 Primeira Pergunta | 1ª sessão | +20 XP |
| 🏃 Maratonista | 10 sessões | +50 XP |
| 🗺️ Explorador | 5 trilhas diferentes | +40 XP |
| ⭐ Avaliador | avaliar 5 respostas | +15 XP |
| 🔥 Persistente | 3 dias seguidos | +30 XP |
| 💪 Dedicado | 500 XP | +60 XP |
| 👑 Mestre do Conhecimento | 1000 XP | +100 XP |
| 🏅 Trilheiro | completar uma trilha | +45 XP |

Ao desbloquear, uma notificação aparece na tela e a medalha acende na barra
lateral, sem recarregar a página. O bônus de uma conquista pode desbloquear a
seguinte na mesma jogada.

**Alertas de dificuldade.** A IA rotula o assunto de cada pergunta. Quando o aluno
faz **3 perguntas sobre o mesmo assunto**, um alerta é aberto automaticamente e
passa a aparecer no painel e no dashboard do responsável.

**Dashboard gerencial.** Quatro gráficos em Chart.js:

1. **Engajamento** — perguntas por dia nos últimos 14 dias
2. **Disciplinas mais procuradas** — onde a turma mais tem dúvida
3. **Distribuição por nível** — quantos alunos em cada faixa de XP
4. **Ranking de XP** — os cinco alunos com mais pontos

O Chart.js é servido da pasta `app/static/js/`, então **os gráficos funcionam sem
internet** — a apresentação não depende do wi-fi da escola.

## Critérios de aceite

### Semana 1
- [x] `SHOW TABLES` retorna as 8 tabelas
- [x] `SELECT COUNT(*) FROM conquistas` retorna 8
- [x] `SELECT COUNT(*) FROM trilhas` retorna 8
- [x] DER entregue

### Semana 3
- [x] Login com matrícula válida redireciona para `/`
- [x] Acesso a `/` sem login redireciona para `/auth/login`
- [x] `POST /chat/perguntar` retorna JSON com `explicacao` e `sugestao_pratica`
- [x] Pergunta sobre "mensalidades" ativa o guardrail e não concede XP
- [x] Sessão é salva no banco após cada pergunta

### Semana 4
- [x] Responsável vê apenas os alunos vinculados a ele
- [x] Acessar um aluno não vinculado retorna 403
- [x] Detalhes do aluno mostram XP, nível, trilhas, sessões e alertas

### Semana 5
- [x] Cada pergunta respondida concede 10 XP e anima a barra de progresso
- [x] Subir de nível dispara notificação na tela
- [x] As 8 conquistas desbloqueiam sozinhas pelos critérios do banco
- [x] Conquista desbloqueada mostra notificação e acende a medalha
- [x] 3 perguntas no mesmo assunto abrem um alerta automático
- [x] O alerta aparece no painel e no dashboard do responsável
- [x] O dashboard mostra os 4 gráficos em Chart.js
