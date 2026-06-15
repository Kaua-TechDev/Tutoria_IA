from datetime import datetime
from flask_login import UserMixin
import bcrypt

from .extensions import db


# ── Tabela associativa aluno ↔ responsavel ───────────────────────────────
aluno_responsavel = db.Table(
    'aluno_responsavel',
    db.Column('aluno_id',       db.Integer, db.ForeignKey('alunos.id'),       primary_key=True),
    db.Column('responsavel_id', db.Integer, db.ForeignKey('responsaveis.id'), primary_key=True),
)


# ── Níveis e XP ─────────────────────────────────────────────────────────
_NIVEIS = [
    (0,    1, 'Iniciante'),
    (100,  2, 'Aprendiz'),
    (300,  3, 'Intermediario'),
    (600,  4, 'Avancado'),
    (1000, 5, 'Mestre'),
]


# ════════════════════════════════════════════════════════════════════════
# ALUNO
# ════════════════════════════════════════════════════════════════════════
class Aluno(UserMixin, db.Model):
    __tablename__ = 'alunos'

    id         = db.Column(db.Integer,     primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    matricula  = db.Column(db.String(20),  nullable=False, unique=True)
    email      = db.Column(db.String(100), unique=True)
    senha_hash = db.Column(db.String(255), nullable=False, default='')
    segmento   = db.Column(
        db.Enum('FUNDAMENTAL_I', 'FUNDAMENTAL_II', 'MEDIO', 'TECNICO'),
        nullable=False
    )
    pontos_xp  = db.Column(db.Integer, nullable=False, default=0)
    nivel      = db.Column(db.Integer, nullable=False, default=1)
    ativo      = db.Column(db.Enum('ativo', 'ausente'), nullable=False, default='ativo')
    criado_em  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamentos
    responsaveis = db.relationship('Responsavel', secondary=aluno_responsavel,
                                   back_populates='alunos')
    sessoes      = db.relationship('Sessao',           backref='aluno', lazy=True)
    conquistas   = db.relationship('AlunoConquista',   backref='aluno', lazy=True)
    alertas      = db.relationship('AlertaDificuldade', backref='aluno', lazy=True)

    # ── Flask-Login: ID prefixado para diferenciar de Responsavel ──────
    def get_id(self):
        return f'a-{self.id}'

    # ── Senha ───────────────────────────────────────────────────────────
    def set_senha(self, senha: str):
        """Gera hash bcrypt e salva em senha_hash."""
        self.senha_hash = bcrypt.hashpw(
            senha.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_senha(self, senha: str) -> bool:
        """Verifica se a senha fornecida bate com o hash armazenado."""
        return bcrypt.checkpw(
            senha.encode('utf-8'),
            self.senha_hash.encode('utf-8')
        )

    # ── Gamificação ─────────────────────────────────────────────────────
    @property
    def nivel_nome(self) -> str:
        """Retorna o nome do nível atual do aluno."""
        nome = 'Iniciante'
        for xp_min, _, n in _NIVEIS:
            if self.pontos_xp >= xp_min:
                nome = n
        return nome

    def xp_para_proximo_nivel(self) -> int:
        """Retorna quantos XP faltam para o próximo nível. 0 se já for Mestre."""
        for xp_min, _, _ in _NIVEIS:
            if self.pontos_xp < xp_min:
                return xp_min - self.pontos_xp
        return 0  # nível máximo

    def adicionar_xp(self, quantidade: int):
        """Soma XP e atualiza o nível automaticamente."""
        self.pontos_xp += quantidade
        for xp_min, nivel_num, _ in reversed(_NIVEIS):
            if self.pontos_xp >= xp_min:
                self.nivel = nivel_num
                break

    def __repr__(self):
        return f'<Aluno {self.matricula} — {self.nome}>'


# ════════════════════════════════════════════════════════════════════════
# RESPONSAVEL
# ════════════════════════════════════════════════════════════════════════
class Responsavel(UserMixin, db.Model):
    __tablename__ = 'responsaveis'

    id         = db.Column(db.Integer,     primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(100), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False, default='')
    telefone   = db.Column(db.String(20))
    criado_em  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    alunos = db.relationship('Aluno', secondary=aluno_responsavel,
                             back_populates='responsaveis')

    def get_id(self):
        return f'r-{self.id}'

    def set_senha(self, senha: str):
        self.senha_hash = bcrypt.hashpw(
            senha.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_senha(self, senha: str) -> bool:
        return bcrypt.checkpw(
            senha.encode('utf-8'),
            self.senha_hash.encode('utf-8')
        )

    def __repr__(self):
        return f'<Responsavel {self.email}>'


# ════════════════════════════════════════════════════════════════════════
# TRILHA
# ════════════════════════════════════════════════════════════════════════
class Trilha(db.Model):
    __tablename__ = 'trilhas'

    id         = db.Column(db.Integer,     primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    descricao  = db.Column(db.Text)
    disciplina = db.Column(db.String(100), nullable=False)
    segmento   = db.Column(
        db.Enum('FUNDAMENTAL_I', 'FUNDAMENTAL_II', 'MEDIO', 'TECNICO'),
        nullable=False
    )
    ativo      = db.Column(db.Enum('ativo', 'ausente'), nullable=False, default='ativo')
    criado_em  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sessoes = db.relationship('Sessao', backref='trilha', lazy=True)

    def __repr__(self):
        return f'<Trilha {self.nome}>'


# ════════════════════════════════════════════════════════════════════════
# SESSAO
# ════════════════════════════════════════════════════════════════════════
class Sessao(db.Model):
    __tablename__ = 'sessoes'

    id               = db.Column(db.Integer,     primary_key=True)
    aluno_id         = db.Column(db.Integer,     db.ForeignKey('alunos.id'),  nullable=False)
    trilha_id        = db.Column(db.Integer,     db.ForeignKey('trilhas.id'), nullable=True)
    disciplina       = db.Column(db.String(100), nullable=False)
    assunto          = db.Column(db.String(255), nullable=True)
    pergunta         = db.Column(db.Text,        nullable=False)
    resposta_ia      = db.Column(db.Text)
    sugestao_pratica = db.Column(db.Text)
    avaliacao        = db.Column(db.SmallInteger)   # 1 a 5 estrelas
    xp_ganho         = db.Column(db.Integer, nullable=False, default=10)
    criado_em        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Sessao {self.id} — aluno {self.aluno_id}>'


# ════════════════════════════════════════════════════════════════════════
# CONQUISTA
# ════════════════════════════════════════════════════════════════════════
class Conquista(db.Model):
    __tablename__ = 'conquistas'

    id        = db.Column(db.Integer,     primary_key=True)
    nome      = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    icone     = db.Column(db.String(50))
    xp_bonus  = db.Column(db.Integer, nullable=False, default=0)
    criterio  = db.Column(db.String(100))

    alunos = db.relationship('AlunoConquista', backref='conquista', lazy=True)

    def __repr__(self):
        return f'<Conquista {self.nome}>'


# ════════════════════════════════════════════════════════════════════════
# ALUNO_CONQUISTA
# ════════════════════════════════════════════════════════════════════════
class AlunoConquista(db.Model):
    __tablename__ = 'aluno_conquistas'

    aluno_id        = db.Column(db.Integer, db.ForeignKey('alunos.id'),      primary_key=True)
    conquista_id    = db.Column(db.Integer, db.ForeignKey('conquistas.id'),  primary_key=True)
    desbloqueado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<AlunoConquista aluno={self.aluno_id} conquista={self.conquista_id}>'


# ════════════════════════════════════════════════════════════════════════
# ALERTA DE DIFICULDADE
# ════════════════════════════════════════════════════════════════════════
class AlertaDificuldade(db.Model):
    __tablename__ = 'alertas_dificuldade'

    id              = db.Column(db.Integer,     primary_key=True)
    aluno_id        = db.Column(db.Integer,     db.ForeignKey('alunos.id'), nullable=False)
    assunto         = db.Column(db.String(200), nullable=False)
    total_perguntas = db.Column(db.Integer,     nullable=False, default=3)
    resolvido       = db.Column(db.Boolean,     nullable=False, default=False)
    criado_em       = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<AlertaDificuldade aluno={self.aluno_id} assunto={self.assunto}>'
