from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import create_app, ia_service
from app.extensions import db
from app.models import Aluno, Conquista, Responsavel, Trilha

PASSWORD = 'senha-de-teste'


@pytest.fixture(autouse=True)
def offline_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nenhum teste chama a OpenAI de verdade, mesmo com chave no .env."""
    monkeypatch.setattr(ia_service, 'client', None)


@pytest.fixture
def app() -> Iterator[Flask]:
    app = create_app('testing')

    with app.app_context():
        db.create_all()

        ana = Aluno(nome='Ana Lima', matricula='1001', segmento='TECNICO')
        bia = Aluno(nome='Bia Costa', matricula='1002', segmento='MEDIO')
        maria = Responsavel(nome='Maria Lima', email='maria@example.com')
        other = Responsavel(nome='Outro Responsável', email='outro@example.com')
        for user in (ana, bia, maria, other):
            user.set_password(PASSWORD)

        maria.alunos.append(ana)
        other.alunos.append(bia)

        db.session.add_all([
            ana, bia, maria, other,
            Trilha(nome='Banco de Dados', disciplina='Banco de Dados', segmento='TECNICO'),
            Trilha(nome='Redação', disciplina='Redacao', segmento='MEDIO'),
            Conquista(nome='Primeira Pergunta', icone='alvo', xp_bonus=20, criterio='PRIMEIRA_PERGUNTA'),
        ])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


def login(client: FlaskClient, login_type: str, identifier: str, password: str = PASSWORD) -> TestResponse:
    return client.post('/auth/login', data={
        'tipo_login': login_type,
        'identificador': identifier,
        'senha': password,
    })


@pytest.fixture
def student_client(client: FlaskClient) -> FlaskClient:
    login(client, 'aluno', '1001')
    return client


@pytest.fixture
def guardian_client(client: FlaskClient) -> FlaskClient:
    login(client, 'responsavel', 'maria@example.com')
    return client
