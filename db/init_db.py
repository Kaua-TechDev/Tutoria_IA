"""Cria as tabelas e popula o banco com dados de demonstração.

Usa o banco configurado em DATABASE_URL (SQLite por padrão).

Execute na raiz do projeto:
    python db/init_db.py

Para apagar o banco e recriá-lo:
    python db/init_db.py --reset

As sessões de demonstração ficam espalhadas pelos últimos dias para o
dashboard ter uma curva de engajamento. As conquistas e os alertas não são
inseridos na mão: saem de app/gamificacao.py, as mesmas regras do app.
"""

from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

# Permite executar este arquivo diretamente a partir da pasta db/.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.gamificacao import check_difficulty, evaluate_achievements
from app.models import (
    Aluno,
    Conquista,
    Responsavel,
    Sessao,
    Trilha,
    utcnow,
)


def create_achievements() -> list[Conquista]:
    rows = [
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
        for n, d, i, xp, c in rows
    ]


def create_tracks() -> list[Trilha]:
    rows = [
        ('Lógica de Programação do Zero', 'Variáveis, condicionais, laços e funções.', 'Programacao', 'TECNICO'),
        ('Banco de Dados na Prática', 'Modelagem relacional, SQL, JOINs e normalização.', 'Banco de Dados', 'TECNICO'),
        ('Python para Iniciantes', 'Sintaxe básica, estruturas de rows e boas práticas.', 'Programacao', 'TECNICO'),
        ('Redação Nota 1000', 'Estrutura dissertativa, argumentação e proposta de intervenção.', 'Redacao', 'MEDIO'),
        ('Geometria e Álgebra', 'Funções, trigonometria e geometria.', 'Matematica', 'MEDIO'),
        ('Interpretação de Texto', 'Estratégias de leitura e compreensão crítica.', 'Portugues', 'FUNDAMENTAL_II'),
        ('Ciências da Natureza', 'Biologia, Física e Química integradas.', 'Ciencias', 'FUNDAMENTAL_II'),
        ('Matemática Básica', 'Números, operações e frações.', 'Matematica', 'FUNDAMENTAL_I'),
    ]
    return [
        Trilha(nome=n, descricao=d, disciplina=disc, segmento=seg)
        for n, d, disc, seg in rows
    ]


def make_student(name: str, enrollment: str, email: str, segment: str) -> Aluno:
    record = Aluno(
        nome=name,
        matricula=enrollment,
        email=email,
        segmento=segment,
        pontos_xp=0,
        nivel=1,
    )
    record.set_password('teste123')
    return record


def make_guardian(name: str, email: str, phone: str) -> Responsavel:
    record = Responsavel(nome=name, email=email, telefone=phone)
    record.set_password('teste123')
    return record


def seed_database() -> None:
    if Aluno.query.first() is not None:
        print('O banco já possui dados. Nada foi alterado.')
        print('Use --reset para apagar e recriar o banco.')
        return

    achievements = create_achievements()
    tracks = create_tracks()

    ana = make_student('Ana Lima', '2026001', 'ana.lima@escola.edu.br', 'TECNICO')
    bruno = make_student('Bruno Souza', '2026002', 'bruno.souza@escola.edu.br', 'MEDIO')
    carla = make_student('Carla Mendes', '2026003', 'carla.mendes@escola.edu.br', 'FUNDAMENTAL_II')
    diego = make_student('Diego Alves', '2026004', 'diego.alves@escola.edu.br', 'TECNICO')

    maria = make_guardian('Maria Lima', 'maria.lima@email.com', '(22) 99001-0001')
    joao = make_guardian('João Souza', 'joao.souza@email.com', '(22) 99001-0002')

    maria.alunos.extend([ana, carla])
    joao.alunos.append(bruno)

    db.session.add_all(achievements + tracks + [ana, bruno, carla, diego, maria, joao])
    db.session.flush()

    now = utcnow()

    # (student, track, subject, topic, question, score, days_ago)
    #
    # As três perguntas de Ana sobre "Chaves estrangeiras" são propositais:
    # elas disparam o alerta automático de dificuldade.
    script = [
        (ana, tracks[0], 'Programacao', 'Variáveis', 'O que é uma variável?', 5, 12),
        (ana, tracks[0], 'Programacao', 'Laços de repetição', 'Como funciona o laço for?', 4, 11),
        (ana, tracks[1], 'Banco de Dados', 'Chaves estrangeiras', 'O que é uma chave estrangeira?', 3, 9),
        (ana, tracks[1], 'Banco de Dados', 'Chaves estrangeiras', 'Não entendi chave estrangeira, explica de novo?', 3, 8),
        (ana, tracks[1], 'Banco de Dados', 'Chaves estrangeiras', 'Qual a diferença entre chave estrangeira e primária?', 4, 7),
        (ana, tracks[1], 'Banco de Dados', 'JOIN em SQL', 'Como funciona o INNER JOIN?', 5, 5),
        (ana, tracks[2], 'Programacao', 'Listas em Python', 'Como percorrer uma lista?', 5, 3),
        (ana, tracks[2], 'Programacao', 'Funções em Python', 'Para que serve o return?', 4, 2),

        (bruno, tracks[3], 'Redacao', 'Redação dissertativa', 'Como estruturar uma redação dissertativa?', 5, 10),
        (bruno, tracks[3], 'Redacao', 'Proposta de intervenção', 'Como fazer a proposta de intervenção?', 4, 6),
        (bruno, tracks[4], 'Matematica', 'Equação do 2º grau', 'Como resolver equação do segundo grau?', 5, 4),
        (bruno, tracks[4], 'Matematica', 'Trigonometria', 'O que é seno e cosseno?', 3, 1),

        (carla, tracks[5], 'Portugues', 'Interpretação de texto', 'Como achar a ideia principal de um texto?', 5, 6),
        (carla, tracks[6], 'Ciencias', 'Fotossíntese', 'Como funciona a fotossíntese?', 5, 2),

        # Diego tem mais sessões de propósito: é ele quem completa uma trilha
        # e destrava as conquistas de volume.
        (diego, tracks[0], 'Programacao', 'Condicionais', 'Quando usar if e else?', 5, 13),
        (diego, tracks[0], 'Programacao', 'Laços de repetição', 'Qual a diferença entre for e while?', 5, 12),
        (diego, tracks[0], 'Programacao', 'Funções', 'O que é um parâmetro de função?', 4, 11),
        (diego, tracks[0], 'Programacao', 'Recursividade', 'O que é recursão?', 4, 10),
        (diego, tracks[0], 'Programacao', 'Complexidade', 'O que é notação Big O?', 5, 9),
        (diego, tracks[1], 'Banco de Dados', 'Normalização', 'O que é a terceira forma normal?', 5, 7),
        (diego, tracks[1], 'Banco de Dados', 'Índices', 'Para que serve um índice no banco?', 4, 5),
        (diego, tracks[2], 'Programacao', 'Dicionários em Python', 'Quando usar dicionário em vez de lista?', 5, 4),
        (diego, tracks[2], 'Programacao', 'Tratamento de erros', 'Como usar try e except?', 5, 3),
        (diego, tracks[2], 'Programacao', 'Módulos em Python', 'Como organizar o código em módulos?', 4, 1),
    ]

    for student, track, subject, topic, question, score, days_ago in script:
        db.session.add(Sessao(
            aluno_id=student.id,
            trilha_id=track.id,
            disciplina=subject,
            assunto=topic,
            pergunta=question,
            resposta_ia=f'Explicação de demonstração sobre {topic.lower()}.',
            sugestao_pratica=f'Pratique um exercício curto sobre {topic.lower()}.',
            avaliacao=score,
            xp_ganho=10,
            criado_em=now - timedelta(days=days_ago, hours=2),
        ))
        student.add_xp(10)

    db.session.flush()

    for student in (ana, bruno, carla, diego):
        evaluate_achievements(student)

        for topic in {s.assunto for s in Sessao.query.filter_by(aluno_id=student.id).all()}:
            check_difficulty(student, topic)

    db.session.commit()

    print('Banco criado e populado com sucesso!')
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
        seed_database()


if __name__ == '__main__':
    main()
