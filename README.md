# TÚTORA — Tutor de Trilhas de Estudo com IA

Disciplina **Introdução à Inteligência Artificial**  
Curso Técnico em Informática — Colégio Castelo  
Stack: `Python` · `Flask` · `MySQL` · `OpenAI`

---

## Cronograma de Entregas

| Semana | Data       | Entrega                              | Status        |
|--------|------------|--------------------------------------|---------------|
| S1     | 01/06/2026 | Banco de Dados — Schema MySQL        | ✅ Entregue   |
| S2     | 08/06/2026 | Estrutura Flask + SQLAlchemy         | ⏳ Em andamento |
| S3     | 15/06/2026 | MVP — Autenticação + Chat com IA     | 🔜 Aguardando |
| S4     | 22/06/2026 | Trilhas, Painel do Responsável       | 🔜 Aguardando |
| S5     | 29/06/2026 | Gamificação + Dashboard (Entrega Final) | 🏁 Final   |

---

## Estrutura do Repositório

```
tutoria/
├── db/
│   ├── schema.sql   ← DDL: cria o banco e as 8 tabelas
│   └── seed.sql     ← DML: dados iniciais e registros de teste
├── app/             ← Será criado na Semana 2
├── .env.example     ← Variáveis de ambiente (modelo)
├── .gitignore
└── README.md
```

---

## Como Rodar o Banco de Dados

### Pré-requisitos
- MySQL instalado e rodando (`mysql --version`)

### Passo a passo

```bash
# 1. Acesse o MySQL
mysql -u root -p

# 2. Execute o schema (cria banco + tabelas)
source db/schema.sql

# 3. Execute o seed (insere dados iniciais e de teste)
source db/seed.sql

# 4. Confirme as tabelas criadas
USE tutor_trilhas;
SHOW TABLES;

# 5. Confirme os dados obrigatórios
SELECT COUNT(*) FROM conquistas;   -- deve retornar 8
SELECT COUNT(*) FROM trilhas;      -- deve retornar 8
```

---

## Critérios de Aceite — Semana 1

- [ ] `SHOW TABLES` retorna as 8 tabelas
- [ ] `DESCRIBE alunos` mostra `senha_hash VARCHAR(255)` e `segmento ENUM`
- [ ] `INSERT` com `aluno_id` inexistente em `sessoes` gera **erro de FK**
- [ ] `SELECT * FROM conquistas` retorna **8 linhas**
- [ ] `SELECT * FROM trilhas` retorna **8 linhas**
- [ ] DER entregue (físico ou digital)

---

## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (nunca suba para o GitHub):

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=tutor_trilhas
OPENAI_API_KEY=sk-...
SECRET_KEY=chave_secreta_flask
```

---

## Integrantes do Grupo

<!-- Adicione os nomes do grupo aqui -->
- Kauã
- Antônio
- Thainá
- Samuel
- José
