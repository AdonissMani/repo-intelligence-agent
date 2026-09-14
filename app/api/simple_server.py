from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.db.registry import load_registry
from app.routing.router import RepositoryRouter


class RouteHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/route":
            self.send_error(404)
            return
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        repositories, relationships = load_registry()
        router = RepositoryRouter(repositories, relationships)
        results, stats = router.route(
            payload.get("question", ""),
            strategy=payload.get("strategy", "hybrid"),
            limit=int(payload.get("limit", 5)),
        )
        body = json.dumps(
            {
                "repositories": [result.__dict__ for result in results],
                "strategy": payload.get("strategy", "hybrid"),
                "stats": stats,
            }
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    HTTPServer(("127.0.0.1", 8000), RouteHandler).serve_forever()


if __name__ == "__main__":
    main()
