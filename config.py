"""
Configuração do Flask separada por ambiente.

O ambiente é escolhido pela variável APP_ENV ('development', 'production' ou
'testing'); sem ela, vale development.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SQLITE_PATH = BASE_DIR / 'instance' / 'tutoria.db'


def _env(name: str, default: str = '') -> str:
    """Lê uma variável de ambiente tratando `VAR=` vazio no .env como ausente."""
    return os.getenv(name, '').strip() or default


class Config:
    """Valores comuns a todos os ambientes."""

    SECRET_KEY = _env('SECRET_KEY', 'dev-secret-change-me')

    # Sem DATABASE_URL, o projeto usa SQLite e roda sem MySQL instalado.
    SQLALCHEMY_DATABASE_URI = _env(
        'DATABASE_URL', f'sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Corpo máximo aceito por requisição: barra payloads gigantes antes de
    # chegarem às rotas.
    MAX_CONTENT_LENGTH = 64 * 1024

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'

    # Limite de requisições (login e chat). Em memória serve para um único
    # processo; com vários workers, aponte para um Redis (redis://...).
    RATELIMIT_STORAGE_URI = _env('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_HEADERS_ENABLED = True

    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Ambiente local: debug ligado."""

    DEBUG = True


class TestingConfig(Config):
    """Testes automatizados: banco em memória, sem CSRF nem rate limit."""

    TESTING = True
    SECRET_KEY = 'test-secret'  # noqa: S105 - só existe nos testes
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Produção: exige SECRET_KEY de verdade e cookies só por HTTPS."""

    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @classmethod
    def validate(cls) -> None:
        """Impede subir em produção com a chave de sessão padrão."""
        if not _env('SECRET_KEY'):
            raise RuntimeError('Defina SECRET_KEY no ambiente de produção.')


CONFIG_BY_ENV: dict[str, type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}


def get_config(env_name: str | None = None) -> type[Config]:
    """Retorna a classe de configuração do ambiente (APP_ENV por padrão)."""
    name = (env_name or _env('APP_ENV', 'development')).lower()
    config_class = CONFIG_BY_ENV.get(name, DevelopmentConfig)

    if config_class is ProductionConfig:
        ProductionConfig.validate()

    return config_class
