"""
Motor de gamificação: regras de XP, conquistas e alertas de dificuldade,
mantendo as rotas enxutas.

Ponto de entrada: `process_session(student, session)`, chamado logo depois
que uma pergunta é salva.

As chaves dos dicionários devolvidos (xp_total, nivel_nome, conquistas...)
seguem em português porque são o contrato com os templates e o front-end.
"""

import unicodedata
from collections.abc import Callable, Iterable
from datetime import date, timedelta

from .extensions import db
from .models import AlertaDificuldade, Aluno, AlunoConquista, Conquista, Sessao

# ── Regras de pontuação ──────────────────────────────────────────────────
XP_PER_QUESTION = 10

# Quantas perguntas no mesmo assunto disparam um alerta de dificuldade.
DIFFICULTY_ALERT_THRESHOLD = 3

# Quantas sessões numa trilha equivalem a 100% dela.
TRACK_SESSION_GOAL = 5

# O banco guarda o nome do ícone ('alvo', 'fogo'...); o emoji fica só na tela.
ACHIEVEMENT_EMOJI = {
    'alvo': '🎯',
    'corrida': '🏃',
    'mapa': '🗺️',
    'estrela': '⭐',
    'fogo': '🔥',
    'musculo': '💪',
    'coroa': '👑',
    'medalha': '🏅',
}


def emoji_for(icon: str | None) -> str:
    """Traduz o nome do ícone guardado no banco para um emoji.

    Ícones desconhecidos ou vazios viram um troféu genérico.
    """
    return ACHIEVEMENT_EMOJI.get(icon or '', '🏆')


# ══════════════════════════════════════════════════════════════════════════
# ASSUNTO — normalização usada para agrupar perguntas parecidas
# ══════════════════════════════════════════════════════════════════════════
def normalize(text: str | None) -> str:
    """Minúsculo, sem acento e sem espaço sobrando.

    Sem isso, "Chaves Estrangeiras" e "chaves estrangeiras" contariam como
    assuntos diferentes.
    """
    if not text:
        return ''

    unaccented = unicodedata.normalize('NFKD', text)
    unaccented = ''.join(c for c in unaccented if not unicodedata.combining(c))
    return ' '.join(unaccented.lower().split())


# ══════════════════════════════════════════════════════════════════════════
# CRITÉRIOS DAS CONQUISTAS
# ══════════════════════════════════════════════════════════════════════════
def _longest_streak(dates: Iterable[date]) -> int:
    """Maior sequência de dias seguidos em que o aluno estudou."""
    days = sorted(set(dates))
    if not days:
        return 0

    longest = current = 1
    for previous, following in zip(days, days[1:], strict=False):
        if following - previous == timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    return longest


def _student_sessions(student: Aluno) -> list[Sessao]:
    return Sessao.query.filter_by(aluno_id=student.id).all()


def _build_context(student: Aluno, all_sessions: list[Sessao]) -> dict:
    """Números do aluno usados pelos critérios das conquistas.

    Conta apenas as sessões que valeram XP: perguntas barradas pelo guardrail
    ficam no histórico, mas não valem como estudo. Se valessem, daria para
    destravar conquistas fazendo justamente perguntas proibidas.
    """
    sessions = [session for session in all_sessions if (session.xp_ganho or 0) > 0]

    sessions_per_track: dict[int, int] = {}
    for session in sessions:
        if session.trilha_id is not None:
            sessions_per_track[session.trilha_id] = sessions_per_track.get(session.trilha_id, 0) + 1

    return {
        'total_sessoes': len(sessions),
        'trilhas_distintas': len(sessions_per_track),
        'total_avaliacoes': sum(1 for s in sessions if s.avaliacao is not None),
        'dias_consecutivos': _longest_streak(s.criado_em.date() for s in sessions),
        'pontos_xp': student.pontos_xp,
        'tem_trilha_completa': any(
            total >= TRACK_SESSION_GOAL for total in sessions_per_track.values()
        ),
    }


# Cada critério guardado na tabela conquistas vira uma regra aqui.
CRITERIA: dict[str, Callable[[dict], bool]] = {
    'PRIMEIRA_PERGUNTA':   lambda c: c['total_sessoes'] >= 1,
    'SESSOES_10':          lambda c: c['total_sessoes'] >= 10,
    'TRILHAS_5':           lambda c: c['trilhas_distintas'] >= 5,
    'AVALIACOES_5':        lambda c: c['total_avaliacoes'] >= 5,
    'DIAS_CONSECUTIVOS_3': lambda c: c['dias_consecutivos'] >= 3,
    'XP_500':              lambda c: c['pontos_xp'] >= 500,
    'XP_1000':             lambda c: c['pontos_xp'] >= 1000,
    'TRILHA_COMPLETA':     lambda c: c['tem_trilha_completa'],
}


def evaluate_achievements(
    student: Aluno, sessions: list[Sessao] | None = None
) -> list[dict]:
    """Desbloqueia as conquistas que o aluno passou a merecer.

    Repete até estabilizar porque o bônus de XP de uma conquista pode
    desbloquear a próxima (o bônus do Maratonista pode levar o aluno aos
    500 XP e liberar o Dedicado de uma vez). As sessões não mudam entre as
    voltas, então são lidas uma vez só; `sessions` permite reaproveitar uma
    leitura já feita por quem chamou.

    Não faz commit. Devolve so as conquistas desbloqueadas nesta chamada,
    no formato {nome, descricao, emoji, xp_bonus}.
    """
    owned = {
        link.conquista_id
        for link in AlunoConquista.query.filter_by(aluno_id=student.id).all()
    }

    if sessions is None:
        sessions = _student_sessions(student)

    achievements = Conquista.query.all()
    unlocked = []

    # Limite de voltas: uma por conquista, para nunca virar loop infinito.
    for _ in range(len(CRITERIA) + 1):
        context = _build_context(student, sessions)
        new_ones = []

        for achievement in achievements:
            if achievement.id in owned:
                continue

            criterion = CRITERIA.get(achievement.criterio)
            if criterion is None or not criterion(context):
                continue

            db.session.add(
                AlunoConquista(aluno_id=student.id, conquista_id=achievement.id)
            )
            owned.add(achievement.id)

            if achievement.xp_bonus:
                student.add_xp(achievement.xp_bonus)

            new_ones.append({
                'nome': achievement.nome,
                'descricao': achievement.descricao,
                'emoji': emoji_for(achievement.icone),
                'xp_bonus': achievement.xp_bonus,
            })

        if not new_ones:
            break

        unlocked.extend(new_ones)

    return unlocked


# ══════════════════════════════════════════════════════════════════════════
# ALERTAS DE DIFICULDADE
# ══════════════════════════════════════════════════════════════════════════
def check_difficulty(
    student: Aluno, topic: str | None, sessions: list[Sessao] | None = None
) -> dict | None:
    """Abre (ou atualiza) um alerta quando o aluno insiste no mesmo assunto.

    A partir de DIFFICULTY_ALERT_THRESHOLD perguntas sobre o mesmo tema, o
    responsável passa a ver o aviso no painel. Se o alerta já existe e está
    aberto, só atualizamos a contagem — não criamos um alerta duplicado.

    Devolve o alerta apenas quando ele é criado agora (para avisar na tela).
    """
    key = normalize(topic)
    if not key:
        return None

    if sessions is None:
        sessions = _student_sessions(student)

    repetitions = sum(1 for session in sessions if normalize(session.assunto) == key)

    if repetitions < DIFFICULTY_ALERT_THRESHOLD:
        return None

    open_alert = next(
        (
            alert
            for alert in AlertaDificuldade.query.filter_by(
                aluno_id=student.id, resolvido=False
            ).all()
            if normalize(alert.assunto) == key
        ),
        None,
    )

    if open_alert is not None:
        open_alert.total_perguntas = repetitions
        return None

    alert = AlertaDificuldade(
        aluno_id=student.id,
        assunto=topic,
        total_perguntas=repetitions,
        resolvido=False,
    )
    db.session.add(alert)

    return {'assunto': topic, 'total_perguntas': repetitions}


# ══════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════
def student_state(student: Aluno) -> dict:
    """Resumo da gamificação usado pela barra de XP e pelo cabecalho da tela."""
    return {
        'xp_total': student.pontos_xp,
        'nivel': student.nivel,
        'nivel_nome': student.level_name,
        'progresso_nivel': student.level_progress(),
        'xp_para_proximo': student.xp_to_next_level(),
    }


def process_session(student: Aluno, session: Sessao) -> dict:
    """Aplica XP, conquistas e alertas depois que uma pergunta é registrada.

    Soma o XP da sessão, desbloqueia conquistas e verifica alertas de
    dificuldade. Devolve o estado do aluno mais xp_ganho, subiu_de_nivel,
    conquistas e alerta.

    Espera que `session` já tenha sido adicionada à sessão do SQLAlchemy e que
    um flush tenha ocorrido, para que ela entre nas contagens. Não faz commit:
    quem chama decide a hora de gravar.
    """
    level_before = student.nivel

    if session.xp_ganho:
        student.add_xp(session.xp_ganho)

    sessions = _student_sessions(student)
    achievements = evaluate_achievements(student, sessions)
    alert = check_difficulty(student, session.assunto, sessions)

    result = student_state(student)
    result.update({
        'xp_ganho': session.xp_ganho,
        'subiu_de_nivel': student.nivel > level_before,
        'conquistas': achievements,
        'alerta': alert,
    })
    return result
