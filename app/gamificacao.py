"""
gamificacao.py
──────────────
Semana 5. Concentra as regras de XP, conquistas e alertas de dificuldade,
mantendo as rotas (chat.py) enxutas.

Ponto de entrada: `processar_sessao(aluno, sessao)`, chamado logo depois que
uma pergunta e salva.
"""

import unicodedata
from datetime import timedelta

from .extensions import db
from .models import AlertaDificuldade, AlunoConquista, Conquista, Sessao

# ── Regras de pontuacao ──────────────────────────────────────────────────
XP_POR_PERGUNTA = 10

# Quantas perguntas no mesmo assunto disparam um alerta de dificuldade.
LIMITE_ALERTA_DIFICULDADE = 3

# Quantas sessoes numa trilha equivalem a 100% dela (mesma regra da Semana 4).
META_SESSOES_TRILHA = 5

# O banco guarda o nome do icone ('alvo', 'fogo'...); o emoji fica so na tela.
EMOJI_CONQUISTA = {
    'alvo': '🎯',
    'corrida': '🏃',
    'mapa': '🗺️',
    'estrela': '⭐',
    'fogo': '🔥',
    'musculo': '💪',
    'coroa': '👑',
    'medalha': '🏅',
}


def emoji_de(icone: str) -> str:
    """Traduz o nome do icone guardado no banco para um emoji."""
    return EMOJI_CONQUISTA.get(icone or '', '🏆')


# ══════════════════════════════════════════════════════════════════════════
# ASSUNTO — normalizacao usada para agrupar perguntas parecidas
# ══════════════════════════════════════════════════════════════════════════
def normalizar(texto: str) -> str:
    """Minusculo, sem acento e sem espaco sobrando.

    Sem isso, "Chaves Estrangeiras" e "chaves estrangeiras" contariam como
    assuntos diferentes.
    """
    if not texto:
        return ''

    sem_acento = unicodedata.normalize('NFKD', texto)
    sem_acento = ''.join(c for c in sem_acento if not unicodedata.combining(c))
    return ' '.join(sem_acento.lower().split())


# ══════════════════════════════════════════════════════════════════════════
# CRITERIOS DAS CONQUISTAS
# ══════════════════════════════════════════════════════════════════════════
def _dias_consecutivos(datas) -> int:
    """Maior sequencia de dias seguidos em que o aluno estudou."""
    dias = sorted({d for d in datas})
    if not dias:
        return 0

    maior = atual = 1
    for anterior, seguinte in zip(dias, dias[1:]):
        if seguinte - anterior == timedelta(days=1):
            atual += 1
            maior = max(maior, atual)
        else:
            atual = 1
    return maior


def _contexto(aluno) -> dict:
    """Numeros do aluno usados pelos criterios das conquistas.

    Conta apenas as sessoes que valeram XP: perguntas barradas pelo guardrail
    ficam no historico, mas nao valem como estudo. Se valessem, daria para
    destravar conquistas fazendo justamente perguntas proibidas.
    """
    sessoes = [
        sessao
        for sessao in Sessao.query.filter_by(aluno_id=aluno.id).all()
        if (sessao.xp_ganho or 0) > 0
    ]

    sessoes_por_trilha = {}
    for sessao in sessoes:
        if sessao.trilha_id is not None:
            sessoes_por_trilha[sessao.trilha_id] = sessoes_por_trilha.get(sessao.trilha_id, 0) + 1

    return {
        'total_sessoes': len(sessoes),
        'trilhas_distintas': len(sessoes_por_trilha),
        'total_avaliacoes': sum(1 for s in sessoes if s.avaliacao is not None),
        'dias_consecutivos': _dias_consecutivos(s.criado_em.date() for s in sessoes),
        'pontos_xp': aluno.pontos_xp,
        'tem_trilha_completa': any(
            total >= META_SESSOES_TRILHA for total in sessoes_por_trilha.values()
        ),
    }


# Cada criterio guardado na tabela conquistas vira uma regra aqui.
CRITERIOS = {
    'PRIMEIRA_PERGUNTA':   lambda c: c['total_sessoes'] >= 1,
    'SESSOES_10':          lambda c: c['total_sessoes'] >= 10,
    'TRILHAS_5':           lambda c: c['trilhas_distintas'] >= 5,
    'AVALIACOES_5':        lambda c: c['total_avaliacoes'] >= 5,
    'DIAS_CONSECUTIVOS_3': lambda c: c['dias_consecutivos'] >= 3,
    'XP_500':              lambda c: c['pontos_xp'] >= 500,
    'XP_1000':             lambda c: c['pontos_xp'] >= 1000,
    'TRILHA_COMPLETA':     lambda c: c['tem_trilha_completa'],
}


def avaliar_conquistas(aluno) -> list[dict]:
    """Desbloqueia as conquistas que o aluno passou a merecer.

    Repete ate estabilizar porque o bonus de XP de uma conquista pode
    desbloquear a proxima (o bonus do Maratonista pode levar o aluno aos
    500 XP e liberar o Dedicado de uma vez).
    """
    ja_tem = {
        vinculo.conquista_id
        for vinculo in AlunoConquista.query.filter_by(aluno_id=aluno.id).all()
    }

    desbloqueadas = []

    # Limite de voltas: uma por conquista, para nunca virar loop infinito.
    for _ in range(len(CRITERIOS) + 1):
        contexto = _contexto(aluno)
        novas = []

        for conquista in Conquista.query.all():
            if conquista.id in ja_tem:
                continue

            criterio = CRITERIOS.get(conquista.criterio)
            if criterio is None or not criterio(contexto):
                continue

            db.session.add(
                AlunoConquista(aluno_id=aluno.id, conquista_id=conquista.id)
            )
            ja_tem.add(conquista.id)

            if conquista.xp_bonus:
                aluno.adicionar_xp(conquista.xp_bonus)

            novas.append({
                'nome': conquista.nome,
                'descricao': conquista.descricao,
                'emoji': emoji_de(conquista.icone),
                'xp_bonus': conquista.xp_bonus,
            })

        if not novas:
            break

        desbloqueadas.extend(novas)
        db.session.flush()

    return desbloqueadas


# ══════════════════════════════════════════════════════════════════════════
# ALERTAS DE DIFICULDADE
# ══════════════════════════════════════════════════════════════════════════
def verificar_dificuldade(aluno, assunto: str) -> dict | None:
    """Abre (ou atualiza) um alerta quando o aluno insiste no mesmo assunto.

    A partir de LIMITE_ALERTA_DIFICULDADE perguntas sobre o mesmo tema, o
    responsavel passa a ver o aviso no painel. Se o alerta ja existe e esta
    aberto, so atualizamos a contagem — nao criamos um alerta duplicado.

    Devolve o alerta apenas quando ele e criado agora (para avisar na tela).
    """
    chave = normalizar(assunto)
    if not chave:
        return None

    repeticoes = sum(
        1 for sessao in Sessao.query.filter_by(aluno_id=aluno.id).all()
        if normalizar(sessao.assunto) == chave
    )

    if repeticoes < LIMITE_ALERTA_DIFICULDADE:
        return None

    aberto = next(
        (
            alerta
            for alerta in AlertaDificuldade.query.filter_by(
                aluno_id=aluno.id, resolvido=False
            ).all()
            if normalizar(alerta.assunto) == chave
        ),
        None,
    )

    if aberto is not None:
        aberto.total_perguntas = repeticoes
        return None

    alerta = AlertaDificuldade(
        aluno_id=aluno.id,
        assunto=assunto,
        total_perguntas=repeticoes,
        resolvido=False,
    )
    db.session.add(alerta)

    return {'assunto': assunto, 'total_perguntas': repeticoes}


# ══════════════════════════════════════════════════════════════════════════
# PONTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════
def estado_do_aluno(aluno) -> dict:
    """Resumo da gamificacao usado pela barra de XP e pelo cabecalho da tela."""
    return {
        'xp_total': aluno.pontos_xp,
        'nivel': aluno.nivel,
        'nivel_nome': aluno.nivel_nome,
        'progresso_nivel': aluno.progresso_nivel(),
        'xp_para_proximo': aluno.xp_para_proximo_nivel(),
    }


def processar_sessao(aluno, sessao) -> dict:
    """Aplica as regras da Semana 5 depois que uma pergunta e registrada.

    Espera que `sessao` ja tenha sido adicionada a sessao do SQLAlchemy e que
    um flush tenha ocorrido, para que ela entre nas contagens. Nao faz commit:
    quem chama decide a hora de gravar.
    """
    nivel_antes = aluno.nivel

    if sessao.xp_ganho:
        aluno.adicionar_xp(sessao.xp_ganho)

    conquistas = avaliar_conquistas(aluno)
    alerta = verificar_dificuldade(aluno, sessao.assunto)

    resultado = estado_do_aluno(aluno)
    resultado.update({
        'xp_ganho': sessao.xp_ganho,
        'subiu_de_nivel': aluno.nivel > nivel_antes,
        'conquistas': conquistas,
        'alerta': alerta,
    })
    return resultado
