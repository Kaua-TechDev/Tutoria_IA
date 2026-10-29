# Tutoria IA

Sistema de tutoria educacional com inteligência artificial, construído com Python e Flask. Permite que estudantes interajam com um tutor adaptativo via chat, enquanto responsáveis acompanham o progresso em tempo real.

---

## Visão Geral

O projeto resolve um problema concreto: estudantes que não têm acesso a tutores humanos personalizados. A solução usa LLMs para criar um assistente que adapta o tom e o conteúdo ao perfil de cada aluno, com guardrails para manter o foco pedagógico e um sistema de gamificação para engajamento.

---

## Stack

- **Backend:** Python 3.10+, Flask, SQLAlchemy  
- **IA:** OpenAI API (GPT) com guardrails e perfis por segmento  
- **Banco de dados:** SQLite (padrão) ou MySQL  
- **Frontend:** HTML/CSS + Chart.js (dashboards)  
- **Autenticação:** Flask sessions com controle de papéis (aluno / responsável)

---

## Funcionalidades

### Chat com IA adaptativo
- Integração com a API da OpenAI para respostas em linguagem natural
- **Guardrails:** o modelo é instruído a redirecionar perguntas fora do escopo educacional (ex: mensalidades, assuntos pessoais)
- **Perfis por segmento:** o prompt base muda de acordo com o perfil do aluno, adaptando linguagem e nível de dificuldade

### Sistema de gamificação
- XP acumulado por interações e progresso nas trilhas
- Sistema de níveis com progressão automática
- 8 conquistas desbloqueáveis com critérios distintos
- Alertas automáticos ao responsável quando o aluno apresenta dificuldades recorrentes

### Painel do responsável
- Acesso restrito: cada responsável vê apenas os alunos vinculados ao seu perfil
- Dashboard com 4 gráficos em Chart.js: atividade semanal, conquistas, nível atual e alertas

### Banco de dados
- 8 tabelas com relacionamentos entre usuários, trilhas, sessões de chat, XP, conquistas e alertas
- Schema documentado em `db/schema.sql` com seed para testes

---

## Arquitetura

```
tutoria/
├── app/
│   ├── __init__.py       # App factory — seleciona SQLite ou MySQL
│   ├── models.py         # 8 tabelas + regras de XP e nível
│   ├── ia_service.py     # Integração OpenAI, guardrails, perfis por segmento
│   ├── gamificacao.py    # Motor de XP, conquistas e alertas
│   └── routes/
│       ├── auth.py       # Login e logout
│       └── chat.py       # Chat, painel, detalhes e dashboard
├── db/
│   ├── schema.sql
│   ├── seed.sql
│   └── inicializar_sqlite.py
├── .env.example
└── run.py
```

---

## Como rodar

**Pré-requisito:** Python 3.10+

```bash
# Clone o repositório
git clone https://github.com/Kaua-TechDev/Tutoria_IA.git
cd Tutoria_IA

# Crie o ambiente virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env e adicione sua OPENAI_API_KEY
# Sem a chave, o sistema roda em modo demo com respostas locais

# Inicialize o banco de dados
python db/inicializar_sqlite.py

# Inicie a aplicação
python run.py
```

Acesse em `http://localhost:5000`

**Contas de teste:**
| Papel | Credencial | Senha |
|---|---|---|
| Aluno | matrícula `2026001` | `teste123` |
| Responsável | `maria.lima@email.com` | `teste123` |

---

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `OPENAI_API_KEY` | Chave da API da OpenAI. Sem ela, o sistema entra em modo demo |
| `SECRET_KEY` | Chave secreta do Flask para sessões |
| `DATABASE_URL` | URL do banco (padrão: SQLite local) |

---

## Decisões técnicas

- **SQLite por padrão:** facilita rodar localmente sem dependências externas; MySQL disponível para produção via variável de ambiente
- **App factory pattern:** permite criar instâncias separadas por ambiente (dev/test/prod)
- **Guardrails no prompt:** ao invés de pós-processamento, as restrições são definidas no system prompt do modelo, reduzindo latência e mantendo consistência
- **Chart.js local:** biblioteca servida estaticamente para evitar dependência de CDN externo
