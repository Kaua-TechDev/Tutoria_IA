from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Aluno, Trilha, Sessao
from ..ia_service import responder_pergunta

# Sem url_prefix: a rota "/" fica direto na raiz do site.
chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/')
@login_required
def index():
    # Somente Aluno pode ver a tela de chat. Responsável é redirecionado
    # para o painel dele (construído na Semana 4).
    if not isinstance(current_user, Aluno):
        return painel_responsavel()

    trilhas = Trilha.query.filter_by(
        segmento=current_user.segmento, ativo='ativo'
    ).all()

    return render_template('chat/index.html', aluno=current_user, trilhas=trilhas)


@chat_bp.route('/chat/perguntar', methods=['POST'])
@login_required
def perguntar():
    if not isinstance(current_user, Aluno):
        abort(403)

    dados = request.get_json(silent=True) or {}
    disciplina = (dados.get('disciplina') or '').strip()
    pergunta = (dados.get('pergunta') or '').strip()
    trilha_id = dados.get('trilha_id')

    if not disciplina or not pergunta:
        return jsonify({'erro': 'Informe a disciplina e a pergunta.'}), 400

    resultado = responder_pergunta(
        disciplina=disciplina,
        pergunta=pergunta,
        segmento=current_user.segmento,
    )

    # Mesmo quando o guardrail bloqueia, registramos a sessão para o
    # histórico e para os alertas de dificuldade (Semana 5) — só não
    # concedemos XP nesse caso.
    xp_ganho = 0 if resultado['bloqueado'] else 10

    sessao = Sessao(
        aluno_id=current_user.id,
        trilha_id=trilha_id if trilha_id else None,
        disciplina=disciplina,
        assunto=None,
        pergunta=pergunta,
        resposta_ia=resultado['explicacao'],
        sugestao_pratica=resultado['sugestao_pratica'],
        xp_ganho=xp_ganho,
    )
    db.session.add(sessao)
    db.session.commit()

    return jsonify({
        'explicacao': resultado['explicacao'],
        'sugestao_pratica': resultado['sugestao_pratica'],
        'bloqueado': resultado['bloqueado'],
    })


def painel_responsavel():
    # Placeholder da Semana 3: a tela completa do responsável (filhos
    # vinculados, stats, histórico) é implementada na Semana 4.
    return render_template('chat/painel_responsavel_em_construcao.html', responsavel=current_user)
