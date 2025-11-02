"""Simple HTTP servers for WordPress and Shopify integrations."""

from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event, Thread
from typing import Generator, Iterable, Optional, Type

from .integrations import (
    IntegrationError,
    IntegrationResponse,
    ShopifyAppProxyAdapter,
    WordPressWebhookAdapter,
)


class _AdapterHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP handler that forwards POST payloads to an integration adapter."""

    adapter: WordPressWebhookAdapter | ShopifyAppProxyAdapter

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        try:
            response = self.adapter.dispatch(body, headers=self.headers)
        except IntegrationError as exc:
            self._send_error_response(str(exc))
            return

        self._send_integration_response(response)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - from base class
        """Silence default logging to keep console output clean."""

    def _send_error_response(self, message: str) -> None:
        payload = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(400)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_integration_response(self, response: IntegrationResponse) -> None:
        payload = response.to_http()
        body = payload["body"].encode("utf-8")

        self.send_response(payload["status_code"])
        for header, value in payload["headers"].items():
            self.send_header(header, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _build_handler(adapter: WordPressWebhookAdapter | ShopifyAppProxyAdapter) -> Type[_AdapterHTTPRequestHandler]:
    """Bind an adapter instance to a handler subclass for HTTPServer."""

    adapter_instance = adapter

    class Handler(_AdapterHTTPRequestHandler):
        adapter = adapter_instance  # type: ignore[assignment]

    return Handler


def _serve(adapter: WordPressWebhookAdapter | ShopifyAppProxyAdapter, host: str, port: int) -> HTTPServer:
    """Create and start an HTTP server for the provided adapter."""

    server = HTTPServer((host, port), _build_handler(adapter))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


@contextmanager
def serve_wordpress(
    shared_secret: Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> Generator[HTTPServer, None, None]:
    """Context manager that serves the WordPress adapter until closed."""

    adapter = WordPressWebhookAdapter(shared_secret=shared_secret)
    server = _serve(adapter, host, port)
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


@contextmanager
def serve_shopify(
    shared_secret: Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8080,
) -> Generator[HTTPServer, None, None]:
    """Context manager that serves the Shopify adapter until closed."""

    adapter = ShopifyAppProxyAdapter(shared_secret=shared_secret)
    server = _serve(adapter, host, port)
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


def _parse_args(argv: Optional[Iterable[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve webhook adapters for integrations.")
    subparsers = parser.add_subparsers(dest="platform", required=True)

    def add_common_arguments(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--host", default="0.0.0.0", help="Hostname or IP address to bind.")
        subparser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080).")
        subparser.add_argument(
            "--shared-secret",
            dest="shared_secret",
            default=None,
            help="Optional shared secret for verifying incoming requests.",
        )

    add_common_arguments(subparsers.add_parser("wordpress", help="Serve the WordPress adapter."))
    add_common_arguments(subparsers.add_parser("shopify", help="Serve the Shopify adapter."))

    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> None:
    args = _parse_args(argv)
    stop_signal = Event()

    if args.platform == "wordpress":
        context = serve_wordpress(shared_secret=args.shared_secret, host=args.host, port=args.port)
        message = "WordPress"
    else:
        context = serve_shopify(shared_secret=args.shared_secret, host=args.host, port=args.port)
        message = "Shopify"

    print(f"Serving {message} adapter on http://{args.host}:{args.port}. Press Ctrl+C to stop.")

    with context:
        try:
            stop_signal.wait()
        except KeyboardInterrupt:  # pragma: no cover - interactive stop
            print("Stopping server...")


if __name__ == "__main__":  # pragma: no cover - exercised via CLI
    main()
