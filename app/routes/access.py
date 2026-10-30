"""Controle de acesso por papel (aluno ou responsável)."""

from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from flask import abort
from flask_login import current_user, login_required

from ..models import Aluno, Responsavel

P = ParamSpec('P')
R = TypeVar('R')


def role_required(role: type[Aluno] | type[Responsavel]) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Exige login e que o usuário logado seja do papel informado (senão 403)."""

    def decorator(view: Callable[P, R]) -> Callable[P, R]:
        @wraps(view)
        @login_required
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not isinstance(current_user._get_current_object(), role):
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator
