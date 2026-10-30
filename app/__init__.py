import logging
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response

from config import get_config

from .extensions import csrf, db, limiter, login_manager

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
}


def create_app(env_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(get_config(env_name))

    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    # Garante que a pasta instance/ exista. O SQLite será salvo nela.
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)

    _register_user_loader()
    _register_blueprints(app)
    _register_error_handlers(app)

    @app.after_request
    def set_security_headers(response: Response) -> Response:
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        if app.config.get('SESSION_COOKIE_SECURE'):
            response.headers.setdefault(
                'Strict-Transport-Security', 'max-age=31536000; includeSubDomains'
            )
        return response

    return app


def _register_user_loader() -> None:
    from .models import Aluno, Responsavel

    @login_manager.user_loader
    def load_user(user_id: str) -> Aluno | Responsavel | None:
        try:
            user_type, pk = user_id.split('-', 1)
            pk = int(pk)
        except (ValueError, AttributeError):
            return None

        if user_type == 'a':
            return db.session.get(Aluno, pk)
        if user_type == 'r':
            return db.session.get(Responsavel, pk)
        return None


def _register_blueprints(app: Flask) -> None:
    from .routes.auth import auth_bp
    from .routes.guardian import guardian_bp
    from .routes.student import student_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(guardian_bp)


def _register_error_handlers(app: Flask) -> None:
    """Erros viram JSON nas chamadas da API e página amigável no navegador."""

    def wants_json() -> bool:
        return request.is_json or request.accept_mimetypes.best == 'application/json'

    def render_error(status: int, message: str) -> tuple[Response | str, int]:
        if wants_json():
            return jsonify({'erro': message}), status
        return render_template('error.html', status=status, message=message), status

    @app.errorhandler(CSRFError)
    def handle_csrf(_: CSRFError) -> tuple[Response | str, int]:
        return render_error(400, 'Sua sessão expirou. Recarregue a página e tente de novo.')

    @app.errorhandler(429)
    def handle_rate_limit(_: HTTPException) -> tuple[Response | str, int]:
        return render_error(429, 'Muitas tentativas em pouco tempo. Aguarde um instante.')

    @app.errorhandler(HTTPException)
    def handle_http(error: HTTPException) -> tuple[Response | str, int]:
        messages = {
            403: 'Você não tem permissão para acessar esta página.',
            404: 'Página não encontrada.',
        }
        return render_error(error.code or 500, messages.get(error.code, error.description))
