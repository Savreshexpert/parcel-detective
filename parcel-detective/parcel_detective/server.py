"""Private hackathon server. Keep on loopback/SSM; not a public production API."""

import argparse
import json
import mimetypes
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from . import __version__
from .agent import investigate
from .evaluate import evaluate
from .records import ROOT, get_case, list_cases

LOCK = threading.Lock()
JOBS = {}
MODE = os.getenv("PARCEL_MODE", "demo")


class Handler(BaseHTTPRequestHandler):
    def send(self, data, status=200, mime="application/json"):
        if not isinstance(data, bytes):
            data = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
        )
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            return self.send(
                {
                    "status": "server_ready",
                    "mode": MODE,
                    "version": __version__,
                    "cloud_verified": False,
                    "note": "Readiness does not verify model access; run preflight.",
                }
            )
        if path == "/api/cases":
            return self.send({"mode": MODE, "cases": list_cases()})
        if path.startswith("/api/cases/"):
            try:
                return self.send(get_case(path.rsplit("/", 1)[-1]))
            except ValueError as e:
                return self.send({"error": str(e)}, 404)
        if path == "/api/evaluation":
            return self.send(JOBS.get("current", {"status": "idle"}))
        allowed = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}
        if path in allowed:
            file = ROOT / "web" / allowed[path]
            return self.send(
                file.read_bytes(),
                mime=mimetypes.guess_type(str(file))[0] or "text/plain",
            )
        self.send({"error": "Not found"}, 404)

    def do_POST(self):
        # Same-origin JSON only: avoids cross-site requests to this private server.
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != self.headers.get("Host"):
            return self.send({"error": "Origin is not allowed."}, 403)
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.send({"error": "Send application/json."}, 415)
        path = urlsplit(self.path).path
        if path not in ("/api/investigate", "/api/evaluate"):
            return self.send({"error": "Not found"}, 404)
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 100_000:
                return self.send(
                    {"error": "Request must be between 1 and 100,000 bytes."}, 413
                )
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Send a JSON object.")
        except (ValueError, UnicodeDecodeError) as e:
            return self.send({"error": str(e)}, 400)
        if not LOCK.acquire(blocking=False):
            return self.send(
                {"error": "An investigation or evaluation is running. Please wait."},
                429,
            )
        if path == "/api/evaluate":
            JOBS["current"] = {"status": "running", "mode": MODE}

            def work():
                try:
                    JOBS["current"] = {"status": "complete", "result": evaluate(MODE)}
                except Exception as exc:
                    JOBS["current"] = {"status": "error", "error": str(exc)}
                finally:
                    LOCK.release()

            threading.Thread(target=work, daemon=True).start()
            return self.send({"status": "running"}, 202)
        try:
            return self.send(
                investigate(data.get("case_id"), data.get("overrides"), mode=MODE)
            )
        except ValueError as exc:
            return self.send({"error": str(exc), "mode": MODE}, 400)
        except Exception as exc:
            # No automatic demo fallback: live failures must stay visible.
            print(f"Investigation failed: {type(exc).__name__}: {exc}", flush=True)
            return self.send(
                {
                    "error": "Live provider failed. Check Decider health, the AWS role and Bedrock model access. See server logs.",
                    "mode": MODE,
                },
                502,
            )
        finally:
            LOCK.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--strictPort", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if MODE not in ("demo", "aws"):
        parser.error("PARCEL_MODE must be demo or aws")
    try:
        server = ThreadingHTTPServer((args.host, args.port), Handler)
    except OSError as exc:
        parser.error(
            f"Cannot open {args.host}:{args.port}. Stop the other server or choose --port 8081. {exc}"
        )
    print(f"Parcel Detective: http://{args.host}:{args.port} · {MODE} mode", flush=True)
    print("Keep this terminal open. Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nParcel Detective stopped.", flush=True)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
