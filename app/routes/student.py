"""Rotas do aluno: chat com a IA, avaliação das respostas e gamificação."""

import logging

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.wrappers import Response

from ..extensions import db, limiter
from ..gamificacao import (
    XP_PER_QUESTION,
    emoji_for,
    evaluate_achievements,
    process_session,
    student_state,
)
from ..ia_service import answer_question
from ..models import Aluno, AlunoConquista, Conquista, Sessao, Trilha
from .access import role_required

logger = logging.getLogger(__name__)

# Rotas JSON devolvem o corpo sozinho ou acompanhado do status HTTP.
JsonResponse = Response | tuple[Response, int]

# Perguntas mais longas que isso são recusadas: cada caractere vira token
# pago na OpenAI.
MAX_QUESTION_LENGTH = 2000
MAX_SUBJECT_LENGTH = 100

student_bp = Blueprint('student', __name__)


def _current_student() -> Aluno:
    return current_user._get_current_object()


def student_achievements(student: Aluno) -> list[dict]:
    """Todas as conquistas, marcando quais o aluno já desbloqueou.

    As bloqueadas também vão para a tela (em cinza), para o aluno ver o que
    ainda falta.
    """
    unlocked = {
        link.conquista_id: link.desbloqueado_em
        for link in AlunoConquista.query.filter_by(aluno_id=student.id).all()
    }

    return [
        {
            'nome': achievement.nome,
            'descricao': achievement.descricao,
            'emoji': emoji_for(achievement.icone),
            'xp_bonus': achievement.xp_bonus,
            'desbloqueada': achievement.id in unlocked,
            'desbloqueado_em': unlocked.get(achievement.id),
        }
        for achievement in Conquista.query.order_by(Conquista.id).all()
    ]


@student_bp.route('/')
@login_required
def index() -> str | Response:
    """Mostra o chat para alunos e direciona responsáveis ao painel."""
    if current_user.is_guardian:
        return redirect(url_for('guardian.panel'))

    student = _current_student()
    tracks = (
        Trilha.query
        .filter_by(segmento=student.segmento, ativo='ativo')
        .order_by(Trilha.disciplina, Trilha.nome)
        .all()
    )

    return render_template(
        'student/chat.html',
        aluno=student,
        trilhas=tracks,
        gamificacao=student_state(student),
        conquistas=student_achievements(student),
    )


@student_bp.route('/chat/perguntar', methods=['POST'])
@role_required(Aluno)
@limiter.limit('20 per minute; 300 per day', key_func=lambda: current_user.get_id())
def ask() -> JsonResponse:
    """Recebe a pergunta, consulta a IA, salva a sessão e aplica a gamificação."""
    student = _current_student()
    payload = request.get_json(silent=True) or {}
    subject = str(payload.get('disciplina') or '').strip()
    question = str(payload.get('pergunta') or '').strip()
    track_id = payload.get('trilha_id')

    if not subject or not question:
        return jsonify({'erro': 'Informe a disciplina e a pergunta.'}), 400

    if len(subject) > MAX_SUBJECT_LENGTH:
        return jsonify({'erro': 'Disciplina inválida.'}), 400

    if len(question) > MAX_QUESTION_LENGTH:
        return jsonify({
            'erro': f'A pergunta pode ter no máximo {MAX_QUESTION_LENGTH} caracteres.'
        }), 400

    track = None

    if track_id not in (None, ''):
        try:
            track_id = int(track_id)
        except (TypeError, ValueError):
            return jsonify({'erro': 'A trilha informada é inválida.'}), 400

        track = db.session.get(Trilha, track_id)

        if track is None:
            return jsonify({'erro': 'Trilha não encontrada.'}), 404

        if track.segmento != student.segmento:
            return jsonify({
                'erro': 'Essa trilha não pertence ao segmento do aluno.'
            }), 403

    try:
        result = answer_question(
            subject=subject,
            question=question,
            segment=student.segmento,
        )

        blocked = bool(result.get('bloqueado', False))

        # Pergunta barrada pelo guardrail entra no histórico, mas não vale XP.
        session = Sessao(
            aluno_id=student.id,
            trilha_id=track.id if track else None,
            disciplina=subject,
            assunto=result.get('assunto') or None,
            pergunta=question,
            resposta_ia=result.get('explicacao', ''),
            sugestao_pratica=result.get('sugestao_pratica', ''),
            xp_ganho=0 if blocked else XP_PER_QUESTION,
        )

        db.session.add(session)
        db.session.flush()   # a sessão precisa existir para entrar nas contagens

        progress = process_session(student, session)

        db.session.commit()

    except Exception:
        db.session.rollback()
        logger.exception('Falha ao processar pergunta do aluno %s', student.id)
        return jsonify({
            'erro': (
                'Não foi possível processar a pergunta agora. '
                'Tente novamente em alguns instantes.'
            )
        }), 500

    return jsonify({
        'sessao_id': session.id,
        'bloqueado': blocked,
        'assunto': session.assunto,
        'explicacao': result.get('explicacao', ''),
        'sugestao_pratica': result.get('sugestao_pratica', ''),
        **progress,
    })


@student_bp.route('/chat/avaliar', methods=['POST'])
@role_required(Aluno)
@limiter.limit('60 per minute', key_func=lambda: current_user.get_id())
def rate() -> JsonResponse:
    """Registra a nota de 1 a 5 que o aluno deu para uma resposta.

    Alimenta a conquista "Avaliador" e a média de satisfação do dashboard.
    """
    student = _current_student()
    payload = request.get_json(silent=True) or {}

    try:
        session_id = int(payload.get('sessao_id'))
        score = int(payload.get('nota'))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Avaliação inválida.'}), 400

    if not 1 <= score <= 5:
        return jsonify({'erro': 'A nota deve ficar entre 1 e 5.'}), 400

    session = db.session.get(Sessao, session_id)

    # 404 também para sessões de outros alunos: não revela quais IDs existem.
    if session is None or session.aluno_id != student.id:
        return jsonify({'erro': 'Sessão não encontrada.'}), 404

    try:
        session.avaliacao = score
        db.session.flush()

        achievements = evaluate_achievements(student)
        db.session.commit()

    except Exception:
        db.session.rollback()
        logger.exception('Falha ao salvar avaliação da sessão %s', session_id)
        return jsonify({'erro': 'Não foi possível salvar a avaliação.'}), 500

    response = student_state(student)
    response['conquistas'] = achievements
    return jsonify(response)
