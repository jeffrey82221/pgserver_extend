"""Basic usage of the pgsql-http extension, against a local HTTP server (no internet needed)."""
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"hello from pgserver"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def test_http_get(tmp_postgres, require_extension):
    require_extension("http")
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        out = tmp_postgres.psql(f"""
            CREATE EXTENSION http;
            SELECT status, content FROM http_get('http://127.0.0.1:{server.server_port}/');
        """)
    finally:
        server.shutdown()
        server.server_close()
    assert "CREATE EXTENSION" in out
    assert "200" in out
    assert "hello from pgserver" in out
