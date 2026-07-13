from pathlib import Path
import os

from flask import Flask
from dotenv import load_dotenv

from .extensions import db, login_manager


def create_app():
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    # Garante que a pasta instance/ exista. O SQLite será salvo nela.
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    sqlite_path = Path(app.instance_path) / 'tutoria.db'

    app.config['SECRET_KEY'] = (
        os.getenv('SECRET_KEY', '').strip() or 'dev-secret-change-me'
    )

    # Sem DATABASE_URL, o projeto usa SQLite e roda sem MySQL instalado.
    # Um `DATABASE_URL=` vazio no .env devolve string vazia, e não o default
    # do getenv — por isso o `or`.
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.getenv('DATABASE_URL', '').strip()
        or f"sqlite:///{sqlite_path.as_posix()}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    from .models import Aluno, Responsavel

    @login_manager.user_loader
    def load_user(user_id):
        try:
            tipo, pk = user_id.split('-', 1)
            pk = int(pk)
        except (ValueError, AttributeError):
            return None

        if tipo == 'a':
            return db.session.get(Aluno, pk)
        if tipo == 'r':
            return db.session.get(Responsavel, pk)
        return None

    from .routes.auth import auth_bp
    from .routes.chat import chat_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)

    return app
