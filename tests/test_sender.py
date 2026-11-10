import pytest
import requests

import sender

TOKEN = "123456:SECRET-TOKEN"


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload


@pytest.fixture(autouse=True)
def fake_token(monkeypatch):
    monkeypatch.setattr(sender.config, "BOT_TOKEN", TOKEN)


def test_send_message_success(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return FakeResponse(200, {"ok": True, "result": {}})

    monkeypatch.setattr(sender.requests, "post", fake_post)

    sender.send_message("42", "привет")

    assert len(calls) == 1
    url, body, _ = calls[0]
    assert url.endswith("/sendMessage")
    assert body == {"chat_id": "42", "text": "привет"}


def test_send_message_ok_false_raises_without_token(monkeypatch):
    monkeypatch.setattr(
        sender.requests,
        "post",
        lambda url, json, timeout: FakeResponse(
            400, {"ok": False, "description": "Bad Request: chat not found"}
        ),
    )

    with pytest.raises(sender.TelegramSendError) as exc_info:
        sender.send_message("42", "привет")

    message = str(exc_info.value)
    assert "400" in message
    assert "chat not found" in message
    assert TOKEN not in message


def test_send_message_ok_false_with_status_200_raises(monkeypatch):
    monkeypatch.setattr(
        sender.requests,
        "post",
        lambda url, json, timeout: FakeResponse(200, {"ok": False, "description": "strange"}),
    )

    with pytest.raises(sender.TelegramSendError):
        sender.send_message("42", "привет")


def test_send_message_network_error_hides_token(monkeypatch):
    def fake_post(url, json, timeout):
        raise requests.ConnectionError(f"Max retries exceeded with url: {url}")

    monkeypatch.setattr(sender.requests, "post", fake_post)

    with pytest.raises(sender.TelegramSendError) as exc_info:
        sender.send_message("42", "привет")

    assert TOKEN not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__
