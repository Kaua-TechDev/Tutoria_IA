import pytest

from app.models import Aluno


@pytest.mark.parametrize(('xp', 'level', 'name', 'progress', 'missing'), [
    (0, 1, 'Iniciante', 0, 100),
    (150, 2, 'Aprendiz', 25, 150),
    (999, 4, 'Avancado', 100, 1),
    (1500, 5, 'Mestre', 100, 0),
])
def test_level_rules(xp: int, level: int, name: str, progress: int, missing: int) -> None:
    student = Aluno(pontos_xp=0, nivel=1)
    student.add_xp(xp)

    assert student.nivel == level
    assert student.level_name == name
    assert student.level_progress() == progress
    assert student.xp_to_next_level() == missing


def test_password_hash_roundtrip() -> None:
    student = Aluno()
    student.set_password('segredo')

    assert student.senha_hash != 'segredo'
    assert student.check_password('segredo')
    assert not student.check_password('errada')


def test_malformed_hash_does_not_raise() -> None:
    assert not Aluno(senha_hash='$2b$12$PLACEHOLDER').check_password('x')
