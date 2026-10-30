"""Login e logout de alunos (matrícula) e responsáveis (e-mail)."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.wrappers import Response

from ..extensions import limiter
from ..models import Aluno, Responsavel, verify_dummy_password

LOGIN_TYPES = ('aluno', 'responsavel')

# Blueprint isolado com prefixo /auth -> as rotas ficam /auth/login e /auth/logout
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


def _home_for(user: Aluno | Responsavel) -> str:
    return url_for('guardian.panel') if user.is_guardian else url_for('student.index')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute; 50 per hour', methods=['POST'])
def login() -> str | Response:
    # Se já está logado, não faz sentido mostrar a tela de login de novo.
    if current_user.is_authenticated:
        return redirect(_home_for(current_user))

    if request.method == 'GET':
        return render_template('auth/login.html', tipo_ativo='aluno')

    login_type = request.form.get('tipo_login', '')
    if login_type not in LOGIN_TYPES:
        login_type = 'aluno'

    identifier = request.form.get('identificador', '').strip()
    password = request.form.get('senha', '')

    # Aluno loga com matrícula; responsável, com e-mail.
    if login_type == 'aluno':
        user = Aluno.query.filter_by(matricula=identifier).first()
    else:
        user = Responsavel.query.filter_by(email=identifier).first()

    if user is None:
        verify_dummy_password(password)

    if user is None or not user.check_password(password):
        flash('Credenciais inválidas. Confira o dado de login e a senha.', 'erro')
        return render_template('auth/login.html', tipo_ativo=login_type), 401

    login_user(user)
    return redirect(_home_for(user))


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout() -> Response:
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))
