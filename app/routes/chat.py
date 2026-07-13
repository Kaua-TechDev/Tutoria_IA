from datetime import date, timedelta

from flask import Blueprint, render_template, request, jsonify, abort, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from ..extensions import db
from ..models import (
    AlertaDificuldade,
    Aluno,
    AlunoConquista,
    Conquista,
    Responsavel,
    Sessao,
    Trilha,
)
from ..ia_service import responder_pergunta
from ..gamificacao import (
    META_SESSOES_TRILHA,
    XP_POR_PERGUNTA,
    emoji_de,
    estado_do_aluno,
    processar_sessao,
    avaliar_conquistas,
)


# Sem url_prefix: as rotas ficam diretamente na raiz do site.
chat_bp = Blueprint('chat', __name__)


def _formatar_data(data):
    """Formata datas para exibição no painel."""
    if data is None:
        return 'Nenhuma atividade registrada'
    return data.strftime('%d/%m/%Y às %H:%M')


def _calcular_progresso(total_sessoes):
    """Calcula o progresso da trilha no MVP, limitado a 100%."""
    if total_sessoes <= 0:
        return 0
    return min(int((total_sessoes / META_SESSOES_TRILHA) * 100), 100)


def _conquistas_do_aluno(aluno):
    """Todas as conquistas, marcando quais o aluno já desbloqueou.

    As bloqueadas também vão para a tela (em cinza), para o aluno ver o que
    ainda falta.
    """
    desbloqueadas = {
        vinculo.conquista_id: vinculo.desbloqueado_em
        for vinculo in AlunoConquista.query.filter_by(aluno_id=aluno.id).all()
    }

    return [
        {
            'nome': conquista.nome,
            'descricao': conquista.descricao,
            'emoji': emoji_de(conquista.icone),
            'xp_bonus': conquista.xp_bonus,
            'desbloqueada': conquista.id in desbloqueadas,
            'desbloqueado_em': desbloqueadas.get(conquista.id),
        }
        for conquista in Conquista.query.order_by(Conquista.id).all()
    ]


# ══════════════════════════════════════════════════════════════════════════
# ALUNO — chat e gamificação
# ══════════════════════════════════════════════════════════════════════════
@chat_bp.route('/')
@login_required
def index():
    """Mostra o chat para alunos e direciona responsáveis ao painel."""
    if isinstance(current_user, Responsavel):
        return redirect(url_for('chat.painel_responsavel'))

    if not isinstance(current_user, Aluno):
        abort(403)

    trilhas = (
        Trilha.query
        .filter_by(segmento=current_user.segmento, ativo='ativo')
        .order_by(Trilha.disciplina, Trilha.nome)
        .all()
    )

    return render_template(
        'chat/index.html',
        aluno=current_user,
        trilhas=trilhas,
        gamificacao=estado_do_aluno(current_user),
        conquistas=_conquistas_do_aluno(current_user),
    )


@chat_bp.route('/chat/perguntar', methods=['POST'])
@login_required
def perguntar():
    """Recebe a pergunta, consulta a IA, salva a sessão e aplica a gamificação."""
    if not isinstance(current_user, Aluno):
        abort(403)

    dados = request.get_json(silent=True) or {}
    disciplina = str(dados.get('disciplina') or '').strip()
    pergunta = str(dados.get('pergunta') or '').strip()
    trilha_id = dados.get('trilha_id')

    if not disciplina or not pergunta:
        return jsonify({'erro': 'Informe a disciplina e a pergunta.'}), 400

    trilha = None

    if trilha_id not in (None, ''):
        try:
            trilha_id = int(trilha_id)
        except (TypeError, ValueError):
            return jsonify({'erro': 'A trilha informada é inválida.'}), 400

        trilha = db.session.get(Trilha, trilha_id)

        if trilha is None:
            return jsonify({'erro': 'Trilha não encontrada.'}), 404

        if trilha.segmento != current_user.segmento:
            return jsonify({
                'erro': 'Essa trilha não pertence ao segmento do aluno.'
            }), 403

    try:
        resultado = responder_pergunta(
            disciplina=disciplina,
            pergunta=pergunta,
            segmento=current_user.segmento,
        )

        bloqueado = bool(resultado.get('bloqueado', False))

        # Pergunta barrada pelo guardrail entra no histórico, mas não vale XP.
        sessao = Sessao(
            aluno_id=current_user.id,
            trilha_id=trilha.id if trilha else None,
            disciplina=disciplina,
            assunto=resultado.get('assunto') or None,
            pergunta=pergunta,
            resposta_ia=resultado.get('explicacao', ''),
            sugestao_pratica=resultado.get('sugestao_pratica', ''),
            xp_ganho=0 if bloqueado else XP_POR_PERGUNTA,
        )

        db.session.add(sessao)
        db.session.flush()   # a sessão precisa existir para entrar nas contagens

        progresso = processar_sessao(current_user, sessao)

        db.session.commit()

        return jsonify({
            'sessao_id': sessao.id,
            'bloqueado': bloqueado,
            'assunto': sessao.assunto,
            'explicacao': resultado.get('explicacao', ''),
            'sugestao_pratica': resultado.get('sugestao_pratica', ''),
            **progresso,
        })

    except Exception:
        db.session.rollback()
        return jsonify({
            'erro': (
                'Não foi possível processar a pergunta agora. '
                'Tente novamente em alguns instantes.'
            )
        }), 500


@chat_bp.route('/chat/avaliar', methods=['POST'])
@login_required
def avaliar():
    """Registra a nota de 1 a 5 que o aluno deu para uma resposta.

    Alimenta a conquista "Avaliador" e a média de satisfação do dashboard.
    """
    if not isinstance(current_user, Aluno):
        abort(403)

    dados = request.get_json(silent=True) or {}

    try:
        sessao_id = int(dados.get('sessao_id'))
        nota = int(dados.get('nota'))
    except (TypeError, ValueError):
        return jsonify({'erro': 'Avaliação inválida.'}), 400

    if not 1 <= nota <= 5:
        return jsonify({'erro': 'A nota deve ficar entre 1 e 5.'}), 400

    sessao = db.session.get(Sessao, sessao_id)

    if sessao is None or sessao.aluno_id != current_user.id:
        abort(403)

    try:
        sessao.avaliacao = nota
        db.session.flush()

        conquistas = avaliar_conquistas(current_user)
        db.session.commit()

        resposta = estado_do_aluno(current_user)
        resposta['conquistas'] = conquistas
        return jsonify(resposta)

    except Exception:
        db.session.rollback()
        return jsonify({'erro': 'Não foi possível salvar a avaliação.'}), 500


# ══════════════════════════════════════════════════════════════════════════
# RESPONSÁVEL — painel, detalhes e dashboard
# ══════════════════════════════════════════════════════════════════════════
@chat_bp.route('/painel')
@login_required
def painel_responsavel():
    """Exibe um resumo dos alunos vinculados ao responsável."""
    if isinstance(current_user, Aluno):
        return redirect(url_for('chat.index'))

    if not isinstance(current_user, Responsavel):
        abort(403)

    alunos_painel = []
    total_sessoes = 0
    total_xp = 0
    total_alertas = 0
    ultima_atividade_geral = None

    for aluno in current_user.alunos:
        quantidade_sessoes = (
            Sessao.query
            .filter_by(aluno_id=aluno.id)
            .count()
        )

        ultima_atividade = (
            db.session.query(func.max(Sessao.criado_em))
            .filter(Sessao.aluno_id == aluno.id)
            .scalar()
        )

        alertas_abertos = (
            AlertaDificuldade.query
            .filter_by(aluno_id=aluno.id, resolvido=False)
            .count()
        )

        total_sessoes += quantidade_sessoes
        total_xp += aluno.pontos_xp
        total_alertas += alertas_abertos

        if (
            ultima_atividade is not None
            and (
                ultima_atividade_geral is None
                or ultima_atividade > ultima_atividade_geral
            )
        ):
            ultima_atividade_geral = ultima_atividade

        alunos_painel.append({
            'aluno': aluno,
            'total_sessoes': quantidade_sessoes,
            'ultima_atividade': ultima_atividade,
            'ultima_atividade_formatada': _formatar_data(ultima_atividade),
            'alertas_abertos': alertas_abertos,
        })

    alunos_painel.sort(key=lambda item: item['aluno'].nome.lower())

    estatisticas = {
        'total_alunos': len(alunos_painel),
        'total_sessoes': total_sessoes,
        'total_xp': total_xp,
        'total_alertas': total_alertas,
        'ultima_atividade': ultima_atividade_geral,
        'ultima_atividade_formatada': _formatar_data(ultima_atividade_geral),
    }

    return render_template(
        'chat/painel_responsavel.html',
        responsavel=current_user,
        alunos_painel=alunos_painel,
        estatisticas=estatisticas,
    )


@chat_bp.route('/painel/aluno/<int:aluno_id>')
@login_required
def detalhes_aluno(aluno_id):
    """Mostra trilhas, sessões, conquistas e alertas de um aluno vinculado."""
    if not isinstance(current_user, Responsavel):
        abort(403)

    aluno = next(
        (
            aluno_vinculado
            for aluno_vinculado in current_user.alunos
            if aluno_vinculado.id == aluno_id
        ),
        None,
    )

    # Impede o acesso a alunos que não pertencem ao responsável logado.
    if aluno is None:
        abort(403)

    sessoes = (
        Sessao.query
        .filter_by(aluno_id=aluno.id)
        .order_by(Sessao.criado_em.desc())
        .all()
    )

    alertas = (
        AlertaDificuldade.query
        .filter_by(aluno_id=aluno.id)
        .order_by(
            AlertaDificuldade.resolvido.asc(),
            AlertaDificuldade.criado_em.desc(),
        )
        .all()
    )

    trilhas_disponiveis = (
        Trilha.query
        .filter_by(segmento=aluno.segmento, ativo='ativo')
        .order_by(Trilha.disciplina, Trilha.nome)
        .all()
    )

    trilhas_progresso = []

    for trilha in trilhas_disponiveis:
        sessoes_da_trilha = [
            sessao for sessao in sessoes
            if sessao.trilha_id == trilha.id
        ]

        total_sessoes_trilha = len(sessoes_da_trilha)
        xp_trilha = sum(sessao.xp_ganho or 0 for sessao in sessoes_da_trilha)
        ultima_sessao = sessoes_da_trilha[0].criado_em if sessoes_da_trilha else None
        progresso = _calcular_progresso(total_sessoes_trilha)

        trilhas_progresso.append({
            'trilha': trilha,
            'total_sessoes': total_sessoes_trilha,
            'xp': xp_trilha,
            'progresso': progresso,
            'concluida': progresso >= 100,
            'ultima_sessao': ultima_sessao,
            'ultima_sessao_formatada': _formatar_data(ultima_sessao),
        })

    ultima_atividade = sessoes[0].criado_em if sessoes else None

    estatisticas = {
        'total_sessoes': len(sessoes),
        'trilhas_iniciadas': sum(
            1 for item in trilhas_progresso
            if item['total_sessoes'] > 0
        ),
        'trilhas_concluidas': sum(
            1 for item in trilhas_progresso
            if item['concluida']
        ),
        'alertas_abertos': sum(
            1 for alerta in alertas
            if not alerta.resolvido
        ),
        'ultima_atividade': ultima_atividade,
        'ultima_atividade_formatada': _formatar_data(ultima_atividade),
    }

    return render_template(
        'chat/detalhes_aluno.html',
        responsavel=current_user,
        aluno=aluno,
        sessoes=sessoes,
        alertas=alertas,
        trilhas_progresso=trilhas_progresso,
        estatisticas=estatisticas,
        gamificacao=estado_do_aluno(aluno),
        conquistas=_conquistas_do_aluno(aluno),
    )


@chat_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard gerencial da turma. Monta os dados dos quatro gráficos."""
    if not isinstance(current_user, Responsavel):
        abort(403)

    alunos = Aluno.query.order_by(Aluno.nome).all()
    sessoes = Sessao.query.all()

    # ── Gráfico 1: engajamento — sessões por dia nos últimos 14 dias ──────
    hoje = date.today()
    ultimos_dias = [hoje - timedelta(days=i) for i in range(13, -1, -1)]

    sessoes_por_dia = {dia: 0 for dia in ultimos_dias}
    for sessao in sessoes:
        dia = sessao.criado_em.date()
        if dia in sessoes_por_dia:
            sessoes_por_dia[dia] += 1

    grafico_engajamento = {
        'labels': [dia.strftime('%d/%m') for dia in ultimos_dias],
        'valores': [sessoes_por_dia[dia] for dia in ultimos_dias],
    }

    # ── Gráfico 2: volume de perguntas por disciplina ─────────────────────
    por_disciplina = {}
    for sessao in sessoes:
        por_disciplina[sessao.disciplina] = por_disciplina.get(sessao.disciplina, 0) + 1

    disciplinas_ordenadas = sorted(
        por_disciplina.items(), key=lambda item: item[1], reverse=True
    )

    grafico_disciplinas = {
        'labels': [nome for nome, _ in disciplinas_ordenadas],
        'valores': [total for _, total in disciplinas_ordenadas],
    }

    # ── Gráfico 3: distribuição da turma por nível ────────────────────────
    faixas = ['Iniciante', 'Aprendiz', 'Intermediario', 'Avancado', 'Mestre']
    contagem_niveis = {faixa: 0 for faixa in faixas}
    for aluno in alunos:
        contagem_niveis[aluno.nivel_nome] = contagem_niveis.get(aluno.nivel_nome, 0) + 1

    grafico_niveis = {
        'labels': faixas,
        'valores': [contagem_niveis[faixa] for faixa in faixas],
    }

    # ── Gráfico 4: desempenho — ranking de XP (top 5) ─────────────────────
    ranking = sorted(alunos, key=lambda a: a.pontos_xp, reverse=True)[:5]

    grafico_ranking = {
        'labels': [aluno.nome.split(' ')[0] for aluno in ranking],
        'valores': [aluno.pontos_xp for aluno in ranking],
    }

    # ── Cartões de resumo ─────────────────────────────────────────────────
    notas = [s.avaliacao for s in sessoes if s.avaliacao is not None]
    media_avaliacao = round(sum(notas) / len(notas), 1) if notas else 0

    total_conquistas = AlunoConquista.query.count()
    alertas_abertos = AlertaDificuldade.query.filter_by(resolvido=False).count()

    estatisticas = {
        'total_alunos': len(alunos),
        'total_sessoes': len(sessoes),
        'xp_medio': round(sum(a.pontos_xp for a in alunos) / len(alunos)) if alunos else 0,
        'media_avaliacao': media_avaliacao,
        'total_conquistas': total_conquistas,
        'alertas_abertos': alertas_abertos,
    }

    alertas = (
        AlertaDificuldade.query
        .filter_by(resolvido=False)
        .order_by(AlertaDificuldade.total_perguntas.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'chat/dashboard.html',
        responsavel=current_user,
        estatisticas=estatisticas,
        grafico_engajamento=grafico_engajamento,
        grafico_disciplinas=grafico_disciplinas,
        grafico_niveis=grafico_niveis,
        grafico_ranking=grafico_ranking,
        alertas=alertas,
    )
