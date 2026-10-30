from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from app import create_app
from app.extensions import db
from app.models import AlertaDificuldade, Aluno, Sessao

from .conftest import login


def _ask(client: FlaskClient, question: str = 'O que é chave estrangeira?', **extra: object) -> TestResponse:
    return client.post('/chat/perguntar', json={'disciplina': 'Banco de Dados', 'pergunta': question, **extra})


# ── Autenticação ──────────────────────────────────────────────────────────
def test_login_redirects_each_role_to_its_home(client: FlaskClient) -> None:
    assert login(client, 'aluno', '1001').location == '/'
    client.post('/auth/logout')
    assert login(client, 'responsavel', 'maria@example.com').location == '/painel'


def test_login_rejects_wrong_password_and_unknown_user(client: FlaskClient) -> None:
    assert login(client, 'aluno', '1001', 'errada').status_code == 401
    assert login(client, 'aluno', '9999').status_code == 401
    assert login(client, 'invalido', 'maria@example.com').status_code == 401


def test_logout_requires_post(student_client: FlaskClient) -> None:
    assert student_client.get('/auth/logout').status_code == 405
    assert student_client.post('/auth/logout').status_code == 302


def test_pages_require_login(client: FlaskClient) -> None:
    for url in ('/', '/painel', '/dashboard'):
        assert client.get(url).status_code == 302


def test_csrf_is_enforced_outside_tests() -> None:
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = True
    with app.app_context():
        db.create_all()
        response = app.test_client().post('/auth/login', data={'tipo_login': 'aluno'})
    assert response.status_code == 400


# ── Aluno ─────────────────────────────────────────────────────────────────
def test_ask_saves_session_and_grants_xp(app: Flask, student_client: FlaskClient) -> None:
    response = _ask(student_client, trilha_id=1)
    data = response.get_json()

    assert response.status_code == 200
    assert data['xp_ganho'] == 10
    assert [c['nome'] for c in data['conquistas']] == ['Primeira Pergunta']
    assert data['xp_total'] == 30  # 10 da pergunta + 20 de bônus

    with app.app_context():
        assert Sessao.query.count() == 1


def test_blocked_question_gives_no_xp(student_client: FlaskClient) -> None:
    data = _ask(student_client, 'Qual o valor da mensalidade?').get_json()

    assert data['bloqueado'] is True
    assert data['xp_ganho'] == 0
    assert data['conquistas'] == []


def test_ask_validates_input(student_client: FlaskClient) -> None:
    assert _ask(student_client, '').status_code == 400
    assert _ask(student_client, 'x' * 2001).status_code == 400
    assert _ask(student_client, trilha_id='abc').status_code == 400
    assert _ask(student_client, trilha_id=999).status_code == 404
    assert _ask(student_client, trilha_id=2).status_code == 403  # trilha de outro segmento


def test_repeated_topic_opens_one_alert(app: Flask, student_client: FlaskClient) -> None:
    alerts = [_ask(student_client).get_json()['alerta'] for _ in range(4)]

    assert alerts[:2] == [None, None]
    assert alerts[2] == {'assunto': 'Chave estrangeira', 'total_perguntas': 3}
    assert alerts[3] is None
    with app.app_context():
        assert AlertaDificuldade.query.one().total_perguntas == 4


def test_rate_only_own_sessions(app: Flask, student_client: FlaskClient) -> None:
    session_id = _ask(student_client).get_json()['sessao_id']

    assert student_client.post('/chat/avaliar', json={'sessao_id': session_id, 'nota': 6}).status_code == 400
    assert student_client.post('/chat/avaliar', json={'sessao_id': session_id, 'nota': 5}).status_code == 200

    with app.app_context():
        other = Sessao(aluno_id=2, disciplina='X', pergunta='?', xp_ganho=10)
        db.session.add(other)
        db.session.commit()
        other_id = other.id

    assert student_client.post('/chat/avaliar', json={'sessao_id': other_id, 'nota': 5}).status_code == 404


def test_student_cannot_open_guardian_pages(student_client: FlaskClient) -> None:
    assert student_client.get('/dashboard').status_code == 403
    assert student_client.get('/painel/aluno/1').status_code == 403


# ── Responsável ───────────────────────────────────────────────────────────
def test_guardian_cannot_ask(guardian_client: FlaskClient) -> None:
    assert _ask(guardian_client).status_code == 403


def test_guardian_sees_only_linked_students(app: Flask, guardian_client: FlaskClient) -> None:
    with app.app_context():
        bia = db.session.get(Aluno, 2)
        bia.add_xp(500)
        db.session.add(AlertaDificuldade(aluno_id=bia.id, assunto='Tema da Bia', total_perguntas=3))
        db.session.commit()

    assert guardian_client.get('/painel/aluno/1').status_code == 200
    assert guardian_client.get('/painel/aluno/2').status_code == 404

    for url in ('/painel', '/dashboard'):
        page = guardian_client.get(url).get_data(as_text=True)
        assert 'Ana' in page
        assert 'Bia' not in page


def test_security_headers(client: FlaskClient) -> None:
    headers = client.get('/auth/login').headers
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert headers['X-Frame-Options'] == 'DENY'
