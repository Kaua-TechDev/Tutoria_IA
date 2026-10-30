"""
Modelos do banco. Tabelas e colunas seguem em português porque espelham o
schema (db/schema.sql); métodos e helpers Python estão em inglês.
"""

import re
from datetime import UTC, datetime

import bcrypt
from flask_login import UserMixin

from .extensions import db

_BCRYPT_HASH = re.compile(r'\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}')

SEGMENTS = ('FUNDAMENTAL_I', 'FUNDAMENTAL_II', 'MEDIO', 'TECNICO')
STATUSES = ('ativo', 'ausente')

# Hash válido de uma senha aleatória, usado quando o login não encontra o
# usuário: o bcrypt roda do mesmo jeito e o tempo de resposta não denuncia
# quais matrículas ou e-mails existem.
_DUMMY_HASH = bcrypt.hashpw(b'tutoria-dummy-password', bcrypt.gensalt()).decode()


def utcnow() -> datetime:
    """Horário UTC sem fuso, no mesmo formato que o banco guarda."""
    return datetime.now(UTC).replace(tzinfo=None)


def verify_dummy_password(password: str) -> None:
    """Gasta o mesmo tempo de um check_password para usuários inexistentes."""
    bcrypt.checkpw(password.encode('utf-8'), _DUMMY_HASH.encode('utf-8'))


# ── Tabela associativa aluno ↔ responsável ───────────────────────────────
aluno_responsavel = db.Table(
    'aluno_responsavel',
    db.Column('aluno_id',       db.Integer, db.ForeignKey('alunos.id', ondelete='CASCADE'),       primary_key=True),
    db.Column('responsavel_id', db.Integer, db.ForeignKey('responsaveis.id', ondelete='CASCADE'), primary_key=True),
)


# ── Níveis e XP ─────────────────────────────────────────────────────────
LEVELS = [
    (0,    1, 'Iniciante'),
    (100,  2, 'Aprendiz'),
    (300,  3, 'Intermediario'),
    (600,  4, 'Avancado'),
    (1000, 5, 'Mestre'),
]

LEVEL_NAMES = [name for _, _, name in LEVELS]


class PasswordMixin:
    """Hash e verificação de senha com bcrypt, comum a alunos e responsáveis."""

    senha_hash: str

    def set_password(self, password: str) -> None:
        """Gera hash bcrypt e salva em senha_hash."""
        self.senha_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verifica se a senha fornecida bate com o hash armazenado.

        Hash mal formado (ex.: placeholder de carga manual) conta como senha
        errada. O formato é validado antes porque alguns hashes truncados
        derrubam o bcrypt com um panic que não é ValueError.
        """
        if not _BCRYPT_HASH.fullmatch(self.senha_hash or ''):
            return False
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.senha_hash.encode('utf-8')
            )
        except ValueError:
            return False


# ════════════════════════════════════════════════════════════════════════
# ALUNO
# ════════════════════════════════════════════════════════════════════════
class Aluno(PasswordMixin, UserMixin, db.Model):
    __tablename__ = 'alunos'

    is_guardian = False

    id         = db.Column(db.Integer,     primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    matricula  = db.Column(db.String(20),  nullable=False, unique=True)
    email      = db.Column(db.String(100), unique=True)
    senha_hash = db.Column(db.String(255), nullable=False, default='')
    segmento   = db.Column(db.Enum(*SEGMENTS, name='segmento'), nullable=False)
    pontos_xp  = db.Column(db.Integer, nullable=False, default=0)
    nivel      = db.Column(db.Integer, nullable=False, default=1)
    ativo      = db.Column(db.Enum(*STATUSES, name='status'), nullable=False, default='ativo')
    criado_em  = db.Column(db.DateTime, nullable=False, default=utcnow)

    # Relacionamentos
    responsaveis = db.relationship('Responsavel', secondary=aluno_responsavel,
                                   back_populates='alunos')
    sessoes      = db.relationship('Sessao',           backref='aluno', lazy=True)
    conquistas   = db.relationship('AlunoConquista',   backref='aluno', lazy=True)
    alertas      = db.relationship('AlertaDificuldade', backref='aluno', lazy=True)

    # ── Flask-Login: ID prefixado para diferenciar de Responsavel ──────
    def get_id(self) -> str:
        return f'a-{self.id}'

    # ── Gamificação ─────────────────────────────────────────────────────
    @property
    def level_name(self) -> str:
        """Retorna o nome do nível atual do aluno."""
        name = LEVEL_NAMES[0]
        for xp_min, _, level_label in LEVELS:
            if self.pontos_xp >= xp_min:
                name = level_label
        return name

    def xp_to_next_level(self) -> int:
        """Retorna quantos XP faltam para o próximo nível. 0 se já for Mestre."""
        for xp_min, _, _ in LEVELS:
            if self.pontos_xp < xp_min:
                return xp_min - self.pontos_xp
        return 0  # nível máximo

    def level_progress(self) -> int:
        """Percentual (0 a 100) já percorrido DENTRO do nível atual.

        É o número que a barra de XP anima na tela. Um aluno com 150 XP está
        no nível Aprendiz (começa em 100, vai até 300), então já andou
        50 de 200 pontos da faixa — ou seja, 25%.
        """
        range_start = 0
        range_end = None

        for xp_min, _, _ in LEVELS:
            if self.pontos_xp >= xp_min:
                range_start = xp_min
            elif range_end is None:
                range_end = xp_min

        if range_end is None:
            return 100  # nível máximo: barra cheia

        covered = self.pontos_xp - range_start
        range_size = range_end - range_start

        return max(0, min(100, round(covered / range_size * 100)))

    def add_xp(self, amount: int) -> None:
        """Soma XP e atualiza o nível automaticamente."""
        self.pontos_xp += amount
        for xp_min, level_number, _ in reversed(LEVELS):
            if self.pontos_xp >= xp_min:
                self.nivel = level_number
                break

    def __repr__(self) -> str:
        return f'<Aluno {self.matricula} — {self.nome}>'


# ════════════════════════════════════════════════════════════════════════
# RESPONSÁVEL
# ════════════════════════════════════════════════════════════════════════
class Responsavel(PasswordMixin, UserMixin, db.Model):
    __tablename__ = 'responsaveis'

    is_guardian = True

    id         = db.Column(db.Integer,     primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(100), nullable=False, unique=True)
    senha_hash = db.Column(db.String(255), nullable=False, default='')
    telefone   = db.Column(db.String(20))
    criado_em  = db.Column(db.DateTime, nullable=False, default=utcnow)

    alunos = db.relationship('Aluno', secondary=aluno_responsavel,
                             back_populates='responsaveis')

    def get_id(self) -> str:
        return f'r-{self.id}'

    def __repr__(self) -> str:
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
    segmento   = db.Column(db.Enum(*SEGMENTS, name='segmento'), nullable=False, index=True)
    ativo      = db.Column(db.Enum(*STATUSES, name='status'), nullable=False, default='ativo')
    criado_em  = db.Column(db.DateTime, nullable=False, default=utcnow)

    sessoes = db.relationship('Sessao', backref='trilha', lazy=True)

    def __repr__(self) -> str:
        return f'<Trilha {self.nome}>'


# ════════════════════════════════════════════════════════════════════════
# SESSÃO
# ════════════════════════════════════════════════════════════════════════
class Sessao(db.Model):
    __tablename__ = 'sessoes'

    id               = db.Column(db.Integer,     primary_key=True)
    aluno_id         = db.Column(db.Integer,     db.ForeignKey('alunos.id', ondelete='CASCADE'),    nullable=False, index=True)
    trilha_id        = db.Column(db.Integer,     db.ForeignKey('trilhas.id', ondelete='SET NULL'), nullable=True,  index=True)
    disciplina       = db.Column(db.String(100), nullable=False)
    assunto          = db.Column(db.String(255), nullable=True)
    pergunta         = db.Column(db.Text,        nullable=False)
    resposta_ia      = db.Column(db.Text)
    sugestao_pratica = db.Column(db.Text)
    avaliacao        = db.Column(db.SmallInteger)   # 1 a 5 estrelas
    xp_ganho         = db.Column(db.Integer, nullable=False, default=10)
    criado_em        = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
        return f'<Conquista {self.nome}>'


# ════════════════════════════════════════════════════════════════════════
# ALUNO_CONQUISTA
# ════════════════════════════════════════════════════════════════════════
class AlunoConquista(db.Model):
    __tablename__ = 'aluno_conquistas'

    aluno_id        = db.Column(db.Integer, db.ForeignKey('alunos.id', ondelete='CASCADE'),     primary_key=True)
    conquista_id    = db.Column(db.Integer, db.ForeignKey('conquistas.id', ondelete='CASCADE'), primary_key=True)
    desbloqueado_em = db.Column(db.DateTime, nullable=False, default=utcnow)

    def __repr__(self) -> str:
        return f'<AlunoConquista aluno={self.aluno_id} conquista={self.conquista_id}>'


# ════════════════════════════════════════════════════════════════════════
# ALERTA DE DIFICULDADE
# ════════════════════════════════════════════════════════════════════════
class AlertaDificuldade(db.Model):
    __tablename__ = 'alertas_dificuldade'

    id              = db.Column(db.Integer,     primary_key=True)
    aluno_id        = db.Column(db.Integer,     db.ForeignKey('alunos.id', ondelete='CASCADE'), nullable=False, index=True)
    assunto         = db.Column(db.String(200), nullable=False)
    total_perguntas = db.Column(db.Integer,     nullable=False, default=3)
    resolvido       = db.Column(db.Boolean,     nullable=False, default=False)
    criado_em       = db.Column(db.DateTime,    nullable=False, default=utcnow)

    def __repr__(self) -> str:
        return f'<AlertaDificuldade aluno={self.aluno_id} assunto={self.assunto}>'
