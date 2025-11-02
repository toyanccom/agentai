import http.client
import json

import pytest

from src.servers import serve_shopify, serve_wordpress


@pytest.mark.parametrize("context_manager", [serve_wordpress, serve_shopify])
def test_server_success(context_manager):
    with context_manager(host="127.0.0.1", port=0) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        payload = {
            "intent": "order_status",
            "language": "en",
            "context": {"order_id": "A1234", "status": "on the way", "eta": "May 18"},
        }
        connection.request(
            "POST",
            "/",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read())
        connection.close()

    assert response.status == 200
    assert body["intent"] == "order_status"
    assert body["language"] == "en"
    assert "A1234" in body["reply"]


def test_server_validation_error_returns_400():
    with serve_wordpress(host="127.0.0.1", port=0) as server:
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request(
            "POST",
            "/",
            body=json.dumps({"language": "en"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        body = json.loads(response.read())
        connection.close()

    assert response.status == 400
    assert "intent" in body["error"].lower()
