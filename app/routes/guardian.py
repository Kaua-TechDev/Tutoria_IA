"""Rotas do responsável: painel, detalhes de cada aluno e dashboard.

Toda consulta é restrita aos alunos vinculados ao responsável logado.
"""

from datetime import date, datetime, timedelta

from flask import Blueprint, abort, render_template
from flask_login import current_user
from sqlalchemy import func

from ..extensions import db
from ..gamificacao import TRACK_SESSION_GOAL, student_state
from ..models import (
    LEVEL_NAMES,
    AlertaDificuldade,
    AlunoConquista,
    Responsavel,
    Sessao,
    Trilha,
)
from .access import role_required
from .student import student_achievements

guardian_bp = Blueprint('guardian', __name__)


def _format_date(value: datetime | None) -> str:
    """Formata datas para exibição no painel."""
    if value is None:
        return 'Nenhuma atividade registrada'
    return value.strftime('%d/%m/%Y às %H:%M')


def _calculate_progress(total_sessions: int) -> int:
    """Progresso da trilha em %, limitado a 100."""
    if total_sessions <= 0:
        return 0
    return min(int((total_sessions / TRACK_SESSION_GOAL) * 100), 100)


def _current_guardian() -> Responsavel:
    return current_user._get_current_object()


@guardian_bp.route('/painel')
@role_required(Responsavel)
def panel() -> str:
    """Exibe um resumo dos alunos vinculados ao responsável."""
    students = _current_guardian().alunos
    ids = [student.id for student in students]

    # Duas consultas agregadas no lugar de três consultas por aluno.
    session_stats = {
        student_id: (count, last)
        for student_id, count, last in (
            db.session.query(Sessao.aluno_id, func.count(Sessao.id), func.max(Sessao.criado_em))
            .filter(Sessao.aluno_id.in_(ids))
            .group_by(Sessao.aluno_id)
        )
    }
    open_alerts_by_student = dict(
        db.session.query(AlertaDificuldade.aluno_id, func.count(AlertaDificuldade.id))
        .filter(AlertaDificuldade.aluno_id.in_(ids), AlertaDificuldade.resolvido.is_(False))
        .group_by(AlertaDificuldade.aluno_id)
        .all()
    )

    panel_students = []
    for student in sorted(students, key=lambda s: s.nome.lower()):
        session_count, last_activity = session_stats.get(student.id, (0, None))
        panel_students.append({
            'aluno': student,
            'total_sessoes': session_count,
            'ultima_atividade': last_activity,
            'ultima_atividade_formatada': _format_date(last_activity),
            'alertas_abertos': open_alerts_by_student.get(student.id, 0),
        })

    last_dates = [item['ultima_atividade'] for item in panel_students if item['ultima_atividade']]
    overall_last_activity = max(last_dates, default=None)

    stats = {
        'total_alunos': len(panel_students),
        'total_sessoes': sum(item['total_sessoes'] for item in panel_students),
        'total_xp': sum(student.pontos_xp for student in students),
        'total_alertas': sum(item['alertas_abertos'] for item in panel_students),
        'ultima_atividade': overall_last_activity,
        'ultima_atividade_formatada': _format_date(overall_last_activity),
    }

    return render_template(
        'guardian/panel.html',
        responsavel=current_user,
        alunos_painel=panel_students,
        estatisticas=stats,
    )


@guardian_bp.route('/painel/aluno/<int:aluno_id>')
@role_required(Responsavel)
def student_details(aluno_id: int) -> str:
    """Mostra trilhas, sessões, conquistas e alertas de um aluno vinculado."""
    student = next(
        (linked for linked in _current_guardian().alunos if linked.id == aluno_id),
        None,
    )

    # 404 para alunos de outros responsáveis: não revela quais IDs existem.
    if student is None:
        abort(404)

    sessions = (
        Sessao.query
        .filter_by(aluno_id=student.id)
        .order_by(Sessao.criado_em.desc())
        .all()
    )

    alerts = (
        AlertaDificuldade.query
        .filter_by(aluno_id=student.id)
        .order_by(
            AlertaDificuldade.resolvido.asc(),
            AlertaDificuldade.criado_em.desc(),
        )
        .all()
    )

    available_tracks = (
        Trilha.query
        .filter_by(segmento=student.segmento, ativo='ativo')
        .order_by(Trilha.disciplina, Trilha.nome)
        .all()
    )

    sessions_by_track: dict[int, list[Sessao]] = {}
    for session in sessions:
        if session.trilha_id is not None:
            sessions_by_track.setdefault(session.trilha_id, []).append(session)

    track_progress = []
    for track in available_tracks:
        track_sessions = sessions_by_track.get(track.id, [])
        last_session = track_sessions[0].criado_em if track_sessions else None
        progress = _calculate_progress(len(track_sessions))

        track_progress.append({
            'trilha': track,
            'total_sessoes': len(track_sessions),
            'xp': sum(session.xp_ganho or 0 for session in track_sessions),
            'progresso': progress,
            'concluida': progress >= 100,
            'ultima_sessao': last_session,
            'ultima_sessao_formatada': _format_date(last_session),
        })

    last_activity = sessions[0].criado_em if sessions else None

    stats = {
        'total_sessoes': len(sessions),
        'trilhas_iniciadas': sum(1 for item in track_progress if item['total_sessoes'] > 0),
        'trilhas_concluidas': sum(1 for item in track_progress if item['concluida']),
        'alertas_abertos': sum(1 for alert in alerts if not alert.resolvido),
        'ultima_atividade': last_activity,
        'ultima_atividade_formatada': _format_date(last_activity),
    }

    return render_template(
        'guardian/student_details.html',
        responsavel=current_user,
        aluno=student,
        sessoes=sessions,
        alertas=alerts,
        trilhas_progresso=track_progress,
        estatisticas=stats,
        meta_sessoes_trilha=TRACK_SESSION_GOAL,
        gamificacao=student_state(student),
        conquistas=student_achievements(student),
    )


@guardian_bp.route('/dashboard')
@role_required(Responsavel)
def dashboard() -> str:
    """Dashboard dos alunos vinculados. Monta os dados dos quatro gráficos.

    Os números saem de consultas agregadas no banco, sem carregar as sessões
    na memória.
    """
    students = sorted(_current_guardian().alunos, key=lambda s: s.nome)
    ids = [student.id for student in students]
    own_sessions = Sessao.aluno_id.in_(ids)

    # ── Gráfico 1: engajamento — sessões por dia nos últimos 14 dias ──────
    today = date.today()
    last_days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    first_day = datetime.combine(last_days[0], datetime.min.time())

    day_column = func.date(Sessao.criado_em)
    # SQLite devolve a data como texto e o MySQL como date; str() iguala os dois.
    sessions_per_day = {
        str(day): total
        for day, total in (
            db.session.query(day_column, func.count(Sessao.id))
            .filter(own_sessions, Sessao.criado_em >= first_day)
            .group_by(day_column)
        )
    }

    engagement_chart = {
        'labels': [day.strftime('%d/%m') for day in last_days],
        'valores': [sessions_per_day.get(day.isoformat(), 0) for day in last_days],
    }

    # ── Gráfico 2: volume de perguntas por disciplina ─────────────────────
    sessions_by_subject = (
        db.session.query(Sessao.disciplina, func.count(Sessao.id).label('total'))
        .filter(own_sessions)
        .group_by(Sessao.disciplina)
        .order_by(func.count(Sessao.id).desc())
        .all()
    )

    subjects_chart = {
        'labels': [name for name, _ in sessions_by_subject],
        'valores': [total for _, total in sessions_by_subject],
    }

    # ── Gráfico 3: distribuição por nível ─────────────────────────────────
    level_counts = {name: 0 for name in LEVEL_NAMES}
    for student in students:
        level_counts[student.level_name] += 1

    levels_chart = {
        'labels': LEVEL_NAMES,
        'valores': [level_counts[name] for name in LEVEL_NAMES],
    }

    # ── Gráfico 4: desempenho — ranking de XP (top 5) ─────────────────────
    ranking = sorted(students, key=lambda s: s.pontos_xp, reverse=True)[:5]

    ranking_chart = {
        'labels': [student.nome.split(' ')[0] for student in ranking],
        'valores': [student.pontos_xp for student in ranking],
    }

    # ── Cartões de resumo ─────────────────────────────────────────────────
    total_sessions, average_rating = (
        db.session.query(func.count(Sessao.id), func.avg(Sessao.avaliacao))
        .filter(own_sessions)
        .one()
    )

    open_alerts_filter = (
        AlertaDificuldade.aluno_id.in_(ids),
        AlertaDificuldade.resolvido.is_(False),
    )

    stats = {
        'total_alunos': len(students),
        'total_sessoes': total_sessions,
        'xp_medio': round(sum(s.pontos_xp for s in students) / len(students)) if students else 0,
        'media_avaliacao': round(float(average_rating), 1) if average_rating else 0,
        'total_conquistas': AlunoConquista.query.filter(AlunoConquista.aluno_id.in_(ids)).count(),
        'alertas_abertos': AlertaDificuldade.query.filter(*open_alerts_filter).count(),
    }

    alerts = (
        AlertaDificuldade.query
        .filter(*open_alerts_filter)
        .order_by(AlertaDificuldade.total_perguntas.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'guardian/dashboard.html',
        responsavel=current_user,
        estatisticas=stats,
        grafico_engajamento=engagement_chart,
        grafico_disciplinas=subjects_chart,
        grafico_niveis=levels_chart,
        grafico_ranking=ranking_chart,
        alertas=alerts,
    )
