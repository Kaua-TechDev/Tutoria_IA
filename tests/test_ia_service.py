from unittest import mock

import httpx
import openai
import pytest

from app import ia_service

REQUEST = httpx.Request('POST', 'https://api.openai.com/v1/chat/completions')


def _status_error(cls: type[openai.APIStatusError], status: int) -> openai.APIStatusError:
    return cls('erro', response=httpx.Response(status, request=REQUEST), body=None)


def _fake_client(content: str | None = None, error: Exception | None = None) -> mock.MagicMock:
    client = mock.MagicMock()
    if error is not None:
        client.chat.completions.create.side_effect = error
    else:
        message = mock.MagicMock(content=content)
        client.chat.completions.create.return_value.choices = [mock.MagicMock(message=message)]
    return client


def test_keyword_guardrail_blocks_without_calling_api() -> None:
    client = _fake_client('{}')
    with mock.patch.object(ia_service, 'client', client):
        result = ia_service.answer_question('Mat', 'Quanto custa a mensalidade?', 'MEDIO')

    assert result['bloqueado'] is True
    client.chat.completions.create.assert_not_called()


def test_demo_mode_without_api_key() -> None:
    with mock.patch.object(ia_service, 'client', None):
        result = ia_service.answer_question('Banco de Dados', 'O que é chave estrangeira?', 'TECNICO')

    assert result['bloqueado'] is False
    assert 'modo de demonstração' in result['explicacao']
    assert result['assunto'] == 'Chave estrangeira'


@pytest.mark.parametrize(('error', 'expected'), [
    (openai.APITimeoutError(request=REQUEST), 'demorou demais'),
    (_status_error(openai.RateLimitError, 429), 'muitas perguntas'),
    (_status_error(openai.AuthenticationError, 401), 'Não consegui falar com a IA'),
    (openai.APIConnectionError(request=REQUEST), 'Não consegui falar com a IA'),
    (_status_error(openai.InternalServerError, 500), 'Não consegui falar com a IA'),
])
def test_api_failures_fall_back_to_local_answer(error: Exception, expected: str) -> None:
    with mock.patch.object(ia_service, 'client', _fake_client(error=error)):
        result = ia_service.answer_question('Mat', 'O que é fração?', 'MEDIO')

    assert expected in result['explicacao']
    assert result['bloqueado'] is False
    assert result['assunto']


def test_valid_json_answer() -> None:
    content = '{"bloqueado": false, "assunto": "Frações", "explicacao": "ok", "sugestao_pratica": "p"}'
    with mock.patch.object(ia_service, 'client', _fake_client(content)):
        result = ia_service.answer_question('Mat', 'O que é fração?', 'MEDIO')

    assert result == {'bloqueado': False, 'assunto': 'Frações', 'explicacao': 'ok', 'sugestao_pratica': 'p'}


@pytest.mark.parametrize('content', ['não é json', None, '[1, 2]'])
def test_invalid_answer_does_not_break(content: str | None) -> None:
    with mock.patch.object(ia_service, 'client', _fake_client(content)):
        result = ia_service.answer_question('Mat', 'O que é fração?', 'MEDIO')

    assert result['bloqueado'] is False
    assert result['assunto']
