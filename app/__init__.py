from flask import Flask
from dotenv import load_dotenv
import os

from .extensions import db, login_manager


def create_app():
    load_dotenv()

    app = Flask(__name__)

    # ── Configurações ────────────────────────────────────────
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST', 'localhost')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ── Extensões ────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)

    # ── User Loader ──────────────────────────────────────────
    from .models import Aluno, Responsavel

    @login_manager.user_loader
    def load_user(user_id):
        # ID prefixado: "a-1" = Aluno id 1 | "r-1" = Responsavel id 1
        tipo, pk = user_id.split('-', 1)
        if tipo == 'a':
            return Aluno.query.get(int(pk))
        if tipo == 'r':
            return Responsavel.query.get(int(pk))
        return None

    # ── Blueprints (serão registrados nas semanas seguintes) ─
    # from .routes.auth import auth_bp
    # app.register_blueprint(auth_bp)

    return app
