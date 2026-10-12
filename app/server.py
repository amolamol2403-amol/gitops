"""Dependency-free demo HTTP app for Kubernetes GitOps."""
import html
import json
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/healthz":
            body, content_type = b'{"status":"ok"}', "application/json"
        elif path in ("/", "/api/info"):
            message_file = Path(os.environ.get("MESSAGE_FILE", "/config/message"))
            message = message_file.read_text().strip() if message_file.exists() else "Hello from GitOps!"
            info = {"message": message, "version": os.environ.get("APP_VERSION", "1.0.0"), "pod": socket.gethostname()}
            if path == "/api/info":
                body, content_type = json.dumps(info).encode(), "application/json"
            else:
                fields = "".join(f"<dt>{html.escape(k.title())}</dt><dd>{html.escape(v)}</dd>" for k, v in info.items())
                body = ("<!doctype html><html lang='en'><meta charset='utf-8'>"
                        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                        "<title>GitOps Demo</title><style>"
                        "body{font:18px system-ui;background:#102039;color:#edf5ff;margin:0;padding:8vw}"
                        "main{max-width:700px;margin:auto}h1{font-size:48px}"
                        "dt{color:#74dec6;margin-top:24px}dd{margin:8px 0;overflow-wrap:anywhere}"
                        "</style><main><p>KUBERNETES + ARGO CD</p><h1>GitOps Demo</h1>"
                        f"<dl>{fields}</dl><p>Commit a new message to Git to see it here.</p></main></html>").encode()
                content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler).serve_forever()
