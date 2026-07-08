# Tutoria

Tutor de trilhas de estudo com IA — projeto da disciplina Introdução à Inteligência Artificial, Curso Técnico em Informática.

Stack: Python · Flask · MySQL · OpenAI

## Integrantes

- Kauã
- Antônio
- José
- Thainá
- Samuel

## Entregas

| Semana | Data       | Entrega                              | Status         |
|--------|------------|--------------------------------------|----------------|
| S1     | 01/06/2026 | Banco de dados — schema MySQL        | Entregue       |
| S2     | 08/06/2026 | Estrutura Flask + SQLAlchemy         | Em andamento   |
| S3     | 15/06/2026 | MVP — autenticacao + chat com IA     | Entregue       |
| S4     | 22/06/2026 | Trilhas e painel do responsavel      | Aguardando     |
| S5     | 29/06/2026 | Gamificacao + dashboard              | Entrega final  |

## Estrutura

```
tutoria/
├── db/
│   ├── schema.sql   -- cria o banco e as tabelas
│   └── seed.sql     -- dados iniciais e registros de teste
├── app/             -- criado na semana 2
├── .env.example
├── .gitignore
└── README.md
```

## Como rodar o banco

Requisito: MySQL instalado e rodando.

```bash
mysql -u root -p

source db/schema.sql
source db/seed.sql

USE tutor_trilhas;
SHOW TABLES;
SELECT COUNT(*) FROM conquistas;  -- 8
SELECT COUNT(*) FROM trilhas;     -- 8
```

## Variaveis de ambiente

Crie um arquivo `.env` na raiz (nao suba para o GitHub):

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=tutor_trilhas
OPENAI_API_KEY=sk-...
SECRET_KEY=chave_secreta_flask
```

## Criterios de aceite — Semana 1

- [ ] `SHOW TABLES` retorna as 8 tabelas
- [ ] `DESCRIBE alunos` mostra `senha_hash VARCHAR(255)` e `segmento ENUM`
- [ ] INSERT com `aluno_id` inexistente em `sessoes` gera erro de FK
- [ ] `SELECT COUNT(*) FROM conquistas` retorna 8
- [ ] `SELECT COUNT(*) FROM trilhas` retorna 8
- [ ] DER entregue

## Como rodar o servidor (Semana 3 em diante)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# preencha o .env com DB_*, OPENAI_API_KEY e SECRET_KEY
python run.py
```

Acesse http://localhost:5000 — sem login, deve redirecionar para `/auth/login`.

Login de teste (dados do seed.sql, senha real é o placeholder — troque
depois com `set_senha()` no `flask shell` se quiser logar de verdade):

```
Matricula: 2026001  (Ana Lima — TECNICO)
```

## Criterios de aceite — Semana 3

- [ ] Login com matricula/senha valida redireciona para `/`
- [ ] Acesso a `/` sem login redireciona para `/auth/login`
- [ ] `POST /chat/perguntar` retorna JSON com `explicacao` e `sugestao_pratica`
- [ ] Pergunta sobre "mensalidades" ativa o guardrail — IA recusa e redireciona
- [ ] Pergunta academica com segmento TECNICO retorna resposta tecnica sem codigo pronto
- [ ] Sessao e salva na tabela `sessoes` do MySQL apos cada pergunta
