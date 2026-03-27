#!/usr/bin/env python3
"""
Docker API Proxy - Restricts Docker API access for sandbox executor manager.

This proxy allows only specific Docker API operations needed for sandbox container management:
- Container creation, removal, inspection, and execution
- Image listing and pulling (for base sandbox images)
- Docker info queries

All other API calls are blocked to limit the attack surface.
"""

import http.client
import http.server
import json
import re
import socketserver
import sys
import os
from typing import Optional
from urllib.parse import urlparse

PROXY_PORT = 2376

ALLOWED_ENDPOINTS = [
    re.compile(r"^/v1\.\d+/containers/create$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/exec$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/start$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/exec$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/json$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/wait$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/logs$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/resize$"),
    re.compile(r"^/v1\.\d+/containers/[a-zA-Z0-9_-]+/archive\?.*$"),
    re.compile(r"^/v1\.\d+/containers/json\?.*$"),
    re.compile(r"^/v1\.\d+/images/json\?.*$"),
    re.compile(r"^/v1\.\d+/images/create\?.*$"),
    re.compile(r"^/v1\.\d+/info$"),
    re.compile(r"^/v1\.\d+/version$"),
    re.compile(r"^/v1\.\d+/_ping$"),
    re.compile(r"^/containers/create$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+/exec$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+/start$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+/json$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+/wait$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+/logs$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+/resize$"),
    re.compile(r"^/containers/[a-zA-Z0-9_-]+/archive\?.*$"),
    re.compile(r"^/containers/json\?.*$"),
    re.compile(r"^/images/json\?.*$"),
    re.compile(r"^/images/create\?.*$"),
    re.compile(r"^/info$"),
    re.compile(r"^/version$"),
    re.compile(r"^/_ping$"),
]

ALLOWED_METHODS = {"GET", "POST", "DELETE"}

DOCKER_SOCKET = "/var/run/docker.sock"


def is_allowed(path: str, method: str) -> tuple[bool, Optional[str]]:
    if method not in ALLOWED_METHODS:
        return False, f"Method {method} not allowed"
    for pattern in ALLOWED_ENDPOINTS:
        if pattern.match(path):
            return True, None
    return False, f"Endpoint {path} not allowed"


class DockerProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 300

    def log_message(self, format: str, *args) -> None:
        print(f"[PROXY] {self.client_address[0]} - {format % args}")

    def proxy_request(self) -> None:
        allowed, error_msg = is_allowed(self.path, self.method)
        if not allowed:
            self.log_message("BLOCKED: %s %s", self.method, self.path)
            self.send_response(403)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"error": "Forbidden", "message": error_msg}
            self.wfile.write(json.dumps(response).encode())
            return

        self.log_message("ALLOWED: %s %s", self.method, self.path)

        content_length = self.headers.get("Content-Length")
        body = None
        if content_length:
            body = self.rfile.read(int(content_length))

        docker_conn = http.client.HTTPConnection("localhost", path=DOCKER_SOCKET, timeout=self.timeout)
        try:
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length")}
            docker_conn.request(self.method, self.path, body=body, headers=headers)
            response = docker_conn.getresponse()
            response_body = response.read()

            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() != "transfer-encoding":
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response_body)
        except Exception as e:
            self.log_message("ERROR: %s", str(e))
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"error": "Bad Gateway", "message": str(e)}
            self.wfile.write(json.dumps(response).encode())
        finally:
            docker_conn.close()

    def do_GET(self) -> None:
        self.method = "GET"
        self.proxy_request()

    def do_POST(self) -> None:
        self.method = "POST"
        self.proxy_request()

    def do_DELETE(self) -> None:
        self.method = "DELETE"
        self.proxy_request()

    def do_PUT(self) -> None:
        self.method = "PUT"
        self.proxy_request()

    def do_HEAD(self) -> None:
        self.method = "HEAD"
        self.proxy_request()


class ThreadedTCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = PROXY_PORT

    server = ThreadedTCPServer(("0.0.0.0", port), DockerProxyHandler)
    print(f"[*] Docker API Proxy listening on 0.0.0.0:{port}")
    print(f"[*] Forwarding to Docker socket: {DOCKER_SOCKET}")
    print(f"[*] Restricted mode: Only sandbox-related operations allowed")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down proxy...")
        server.shutdown()


if __name__ == "__main__":
    main()
