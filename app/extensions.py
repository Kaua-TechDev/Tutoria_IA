from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()

csrf = CSRFProtect()

# Os limites ficam em cada rota; o storage vem de RATELIMIT_STORAGE_URI.
limiter = Limiter(key_func=get_remote_address)

login_manager = LoginManager()
login_manager.login_view    = 'auth.login'
login_manager.login_message = 'Faça login para acessar esta página.'
