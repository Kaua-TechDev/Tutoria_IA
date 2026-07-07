from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from ..models import Aluno, Responsavel

# Blueprint isolado com prefixo /auth -> as rotas ficam /auth/login e /auth/logout
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se já está logado, não faz sentido mostrar a tela de login de novo.
    if current_user.is_authenticated:
        return redirect(url_for('chat.index'))

    if request.method == 'POST':
        tipo = request.form.get('tipo_login')          # 'aluno' ou 'responsavel'
        identificador = request.form.get('identificador', '').strip()
        senha = request.form.get('senha', '')

        usuario = None

        if tipo == 'aluno':
            # Aluno loga com matrícula
            usuario = Aluno.query.filter_by(matricula=identificador).first()
        elif tipo == 'responsavel':
            # Responsável loga com e-mail
            usuario = Responsavel.query.filter_by(email=identificador).first()

        if usuario is None or not usuario.check_senha(senha):
            flash('Credenciais inválidas. Confira o dado de login e a senha.', 'erro')
            return render_template('auth/login.html', tipo_ativo=tipo or 'aluno')

        login_user(usuario)

        # Aluno vai para o chat. Responsável vai para o painel dele (Semana 4).
        if tipo == 'aluno':
            return redirect(url_for('chat.index'))
        return redirect(url_for('chat.painel_responsavel'))

    return render_template('auth/login.html', tipo_ativo='aluno')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))
