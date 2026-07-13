"""Cria e popula o banco SQLite local do projeto Tutoria.

Execute na raiz do projeto:
    python db/inicializar_sqlite.py

Para apagar o banco e recriá-lo:
    python db/inicializar_sqlite.py --reset

As sessões de demonstração ficam espalhadas pelos últimos dias para o
dashboard ter uma curva de engajamento. As conquistas e os alertas não são
inseridos na mão: saem de app/gamificacao.py, as mesmas regras do app.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Permite executar este arquivo diretamente a partir da pasta db/.
RAIZ_PROJETO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from app import create_app
from app.extensions import db
from app.gamificacao import avaliar_conquistas, verificar_dificuldade
from app.models import (
    Aluno,
    Conquista,
    Responsavel,
    Sessao,
    Trilha,
)


def criar_conquistas() -> list[Conquista]:
    dados = [
        ('Primeira Pergunta', 'Você fez sua primeira pergunta. A jornada começou!', 'alvo', 20, 'PRIMEIRA_PERGUNTA'),
        ('Maratonista', 'Realizou 10 sessões de estudo.', 'corrida', 50, 'SESSOES_10'),
        ('Explorador', 'Estudou em 5 trilhas diferentes.', 'mapa', 40, 'TRILHAS_5'),
        ('Avaliador', 'Avaliou 5 respostas.', 'estrela', 15, 'AVALIACOES_5'),
        ('Persistente', 'Estudou em 3 dias consecutivos.', 'fogo', 30, 'DIAS_CONSECUTIVOS_3'),
        ('Dedicado', 'Acumulou 500 pontos de XP.', 'musculo', 60, 'XP_500'),
        ('Mestre do Conhecimento', 'Acumulou 1000 pontos de XP.', 'coroa', 100, 'XP_1000'),
        ('Trilheiro', 'Completou uma trilha de estudos.', 'medalha', 45, 'TRILHA_COMPLETA'),
    ]
    return [
        Conquista(nome=n, descricao=d, icone=i, xp_bonus=xp, criterio=c)
        for n, d, i, xp, c in dados
    ]


def criar_trilhas() -> list[Trilha]:
    dados = [
        ('Lógica de Programação do Zero', 'Variáveis, condicionais, laços e funções.', 'Programacao', 'TECNICO'),
        ('Banco de Dados na Prática', 'Modelagem relacional, SQL, JOINs e normalização.', 'Banco de Dados', 'TECNICO'),
        ('Python para Iniciantes', 'Sintaxe básica, estruturas de dados e boas práticas.', 'Programacao', 'TECNICO'),
        ('Redação Nota 1000', 'Estrutura dissertativa, argumentação e proposta de intervenção.', 'Redacao', 'MEDIO'),
        ('Geometria e Álgebra', 'Funções, trigonometria e geometria.', 'Matematica', 'MEDIO'),
        ('Interpretação de Texto', 'Estratégias de leitura e compreensão crítica.', 'Portugues', 'FUNDAMENTAL_II'),
        ('Ciências da Natureza', 'Biologia, Física e Química integradas.', 'Ciencias', 'FUNDAMENTAL_II'),
        ('Matemática Básica', 'Números, operações e frações.', 'Matematica', 'FUNDAMENTAL_I'),
    ]
    return [
        Trilha(nome=n, descricao=d, disciplina=disc, segmento=seg)
        for n, d, disc, seg in dados
    ]


def aluno(nome: str, matricula: str, email: str, segmento: str) -> Aluno:
    registro = Aluno(
        nome=nome,
        matricula=matricula,
        email=email,
        segmento=segmento,
        pontos_xp=0,
        nivel=1,
    )
    registro.set_senha('teste123')
    return registro


def responsavel(nome: str, email: str, telefone: str) -> Responsavel:
    registro = Responsavel(nome=nome, email=email, telefone=telefone)
    registro.set_senha('teste123')
    return registro


def popular_banco() -> None:
    if Aluno.query.first() is not None:
        print('O banco já possui dados. Nada foi alterado.')
        print('Use --reset para apagar e recriar o banco.')
        return

    conquistas = criar_conquistas()
    trilhas = criar_trilhas()

    ana = aluno('Ana Lima', '2026001', 'ana.lima@escola.edu.br', 'TECNICO')
    bruno = aluno('Bruno Souza', '2026002', 'bruno.souza@escola.edu.br', 'MEDIO')
    carla = aluno('Carla Mendes', '2026003', 'carla.mendes@escola.edu.br', 'FUNDAMENTAL_II')
    diego = aluno('Diego Alves', '2026004', 'diego.alves@escola.edu.br', 'TECNICO')

    maria = responsavel('Maria Lima', 'maria.lima@email.com', '(22) 99001-0001')
    joao = responsavel('João Souza', 'joao.souza@email.com', '(22) 99001-0002')

    maria.alunos.extend([ana, carla])
    joao.alunos.append(bruno)

    db.session.add_all(conquistas + trilhas + [ana, bruno, carla, diego, maria, joao])
    db.session.flush()

    agora = datetime.utcnow()

    # (aluno, trilha, disciplina, assunto, pergunta, nota, dias_atras)
    #
    # As três perguntas de Ana sobre "Chaves estrangeiras" são propositais:
    # elas disparam o alerta automático de dificuldade.
    roteiro = [
        (ana, trilhas[0], 'Programacao', 'Variáveis', 'O que é uma variável?', 5, 12),
        (ana, trilhas[0], 'Programacao', 'Laços de repetição', 'Como funciona o laço for?', 4, 11),
        (ana, trilhas[1], 'Banco de Dados', 'Chaves estrangeiras', 'O que é uma chave estrangeira?', 3, 9),
        (ana, trilhas[1], 'Banco de Dados', 'Chaves estrangeiras', 'Não entendi chave estrangeira, explica de novo?', 3, 8),
        (ana, trilhas[1], 'Banco de Dados', 'Chaves estrangeiras', 'Qual a diferença entre chave estrangeira e primária?', 4, 7),
        (ana, trilhas[1], 'Banco de Dados', 'JOIN em SQL', 'Como funciona o INNER JOIN?', 5, 5),
        (ana, trilhas[2], 'Programacao', 'Listas em Python', 'Como percorrer uma lista?', 5, 3),
        (ana, trilhas[2], 'Programacao', 'Funções em Python', 'Para que serve o return?', 4, 2),

        (bruno, trilhas[3], 'Redacao', 'Redação dissertativa', 'Como estruturar uma redação dissertativa?', 5, 10),
        (bruno, trilhas[3], 'Redacao', 'Proposta de intervenção', 'Como fazer a proposta de intervenção?', 4, 6),
        (bruno, trilhas[4], 'Matematica', 'Equação do 2º grau', 'Como resolver equação do segundo grau?', 5, 4),
        (bruno, trilhas[4], 'Matematica', 'Trigonometria', 'O que é seno e cosseno?', 3, 1),

        (carla, trilhas[5], 'Portugues', 'Interpretação de texto', 'Como achar a ideia principal de um texto?', 5, 6),
        (carla, trilhas[6], 'Ciencias', 'Fotossíntese', 'Como funciona a fotossíntese?', 5, 2),

        # Diego tem mais sessões de propósito: é ele quem completa uma trilha
        # e destrava as conquistas de volume.
        (diego, trilhas[0], 'Programacao', 'Condicionais', 'Quando usar if e else?', 5, 13),
        (diego, trilhas[0], 'Programacao', 'Laços de repetição', 'Qual a diferença entre for e while?', 5, 12),
        (diego, trilhas[0], 'Programacao', 'Funções', 'O que é um parâmetro de função?', 4, 11),
        (diego, trilhas[0], 'Programacao', 'Recursividade', 'O que é recursão?', 4, 10),
        (diego, trilhas[0], 'Programacao', 'Complexidade', 'O que é notação Big O?', 5, 9),
        (diego, trilhas[1], 'Banco de Dados', 'Normalização', 'O que é a terceira forma normal?', 5, 7),
        (diego, trilhas[1], 'Banco de Dados', 'Índices', 'Para que serve um índice no banco?', 4, 5),
        (diego, trilhas[2], 'Programacao', 'Dicionários em Python', 'Quando usar dicionário em vez de lista?', 5, 4),
        (diego, trilhas[2], 'Programacao', 'Tratamento de erros', 'Como usar try e except?', 5, 3),
        (diego, trilhas[2], 'Programacao', 'Módulos em Python', 'Como organizar o código em módulos?', 4, 1),
    ]

    for estudante, trilha, disciplina, assunto, pergunta, nota, dias_atras in roteiro:
        db.session.add(Sessao(
            aluno_id=estudante.id,
            trilha_id=trilha.id,
            disciplina=disciplina,
            assunto=assunto,
            pergunta=pergunta,
            resposta_ia=f'Explicação de demonstração sobre {assunto.lower()}.',
            sugestao_pratica=f'Pratique um exercício curto sobre {assunto.lower()}.',
            avaliacao=nota,
            xp_ganho=10,
            criado_em=agora - timedelta(days=dias_atras, hours=2),
        ))
        estudante.adicionar_xp(10)

    db.session.flush()

    for estudante in (ana, bruno, carla, diego):
        avaliar_conquistas(estudante)

        for assunto in {s.assunto for s in Sessao.query.filter_by(aluno_id=estudante.id).all()}:
            verificar_dificuldade(estudante, assunto)

    db.session.commit()

    print('Banco SQLite criado e populado com sucesso!')
    print('Arquivo: instance/tutoria.db')
    print('')
    print('Aluno:       matricula 2026001 | senha teste123')
    print('Responsavel: maria.lima@email.com | senha teste123')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Apaga o banco existente antes de recriá-lo.',
    )
    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        if args.reset:
            db.drop_all()
        db.create_all()
        popular_banco()


if __name__ == '__main__':
    main()
