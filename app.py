from __future__ import annotations

import html
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "10000"))
PVIT_TOKEN = os.environ.get("MYPVIT_SECRET_RECEIVER_TOKEN", "pvit-btp-b9a1c7a2759644a7b005")

LAST_SECRET = ""
LAST_PAYLOAD = ""
LAST_TIME = ""


def page(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} - BTP Smart Tools</title>
<style>
body{{margin:0;background:#06101f;color:#eaf2ff;font-family:Segoe UI,Arial,sans-serif}}
header{{background:#020817;border-bottom:1px solid #164e63;padding:18px 28px;font-weight:900}}
.logo{{color:#22d3ee;font-size:30px;margin-right:10px}}
main{{max-width:1100px;margin:auto;padding:28px}}
.hero,.card{{background:linear-gradient(135deg,#0b1220,#0f1d33);border:1px solid #1e3a5f;border-radius:16px;padding:26px;margin-bottom:18px;box-shadow:0 18px 48px rgba(0,0,0,.28)}}
h1{{font-size:48px;margin:0 0 10px}}h2{{margin-top:0}}
p{{color:#bfd0e5;line-height:1.55}}a,.btn{{display:inline-block;background:#22d3ee;color:#06101f;text-decoration:none;font-weight:900;border-radius:10px;padding:12px 16px;margin:6px 6px 6px 0}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}
.ok{{color:#4ade80;font-weight:900}}.warn{{color:#fbbf24;font-weight:900}}
code{{background:#020817;color:#a7f3d0;padding:3px 6px;border-radius:6px}}
@media(max-width:800px){{.grid{{grid-template-columns:1fr}}h1{{font-size:34px}}}}
</style>
</head>
<body>
<header><span class="logo">BTP</span> Smart Tools</header>
<main>{body}</main>
</body>
</html>""".encode("utf-8")


class App(BaseHTTPRequestHandler):
    def send_html(self, title: str, body: str, status: int = 200) -> None:
        data = page(title, body)
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, data: dict, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json({"ok": True, "service": "BTP Smart Tools secours"})
            return
        if parsed.path in ("/pvit/secret-status", "/pvit/status"):
            self.send_html(
                "Statut PVit",
                f"""
                <div class="hero"><h1>Statut PVit</h1>
                <p>Secret reçu : <span class="{'ok' if LAST_SECRET else 'warn'}">{'Oui' if LAST_SECRET else 'Non reçu'}</span></p>
                <p>Dernière réception : {html.escape(LAST_TIME or 'Aucune')}</p>
                <p>Token attendu : <code>{html.escape(PVIT_TOKEN)}</code></p>
                <p>URL à mettre dans PVit :<br><code>https://www.btpsmarttools.com/pvit/secret-receiver?token={html.escape(PVIT_TOKEN)}</code></p>
                <p>Dernier payload : <code>{html.escape(LAST_PAYLOAD[:500])}</code></p></div>
                <p><a class="btn" href="/">Retour accueil</a></p>
                """,
            )
            return
        if parsed.path in ("/pvit/secret-receiver", "/pvit/secret-receiver-open"):
            qs = parse_qs(parsed.query)
            token = (qs.get("token") or [""])[0]
            ok = parsed.path.endswith("-open") or token == PVIT_TOKEN
            self.send_json({"received": True, "token_ok": ok, "method": "GET"})
            return
        if parsed.path == "/generator":
            self.send_html(
                "Générateur",
                """
                <div class="hero"><h1>Générateur de cartouches</h1>
                <p class="warn">Mode secours actif.</p>
                <p>Le site est volontairement allégé pour remettre BTP Smart Tools en ligne. Le grand générateur sera réintégré après stabilisation du déploiement.</p>
                <p><a class="btn" href="/">Retour</a></p></div>
                """,
            )
            return
        self.send_html(
            "Accueil",
            """
            <div class="hero">
              <h1>BTP Smart Tools</h1>
              <p>Plateforme BTP pour cartouches professionnelles, paiements PVit et futurs outils intelligents.</p>
              <p class="ok">Site en ligne - mode secours stable.</p>
              <a class="btn" href="/health">Tester serveur</a>
              <a class="btn" href="/pvit/secret-status">Statut PVit</a>
              <a class="btn" href="/generator">Générateur</a>
            </div>
            <div class="grid">
              <div class="card"><h2>Cartouches</h2><p>Le module complet sera remis après validation du démarrage Render.</p></div>
              <div class="card"><h2>PVit</h2><p>Les endpoints de réception de clé restent présents pour les tests.</p></div>
              <div class="card"><h2>Support</h2><p>Contact : admin@btpsmarttools.com</p></div>
            </div>
            """,
        )

    def do_POST(self) -> None:
        global LAST_PAYLOAD, LAST_SECRET, LAST_TIME
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        if parsed.path in ("/pvit/secret-receiver", "/pvit/secret-receiver-open"):
            qs = parse_qs(parsed.query)
            token = (qs.get("token") or [""])[0]
            ok = parsed.path.endswith("-open") or token == PVIT_TOKEN
            LAST_PAYLOAD = raw
            LAST_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                data = json.loads(raw)
            except Exception:
                data = parse_qs(raw)
            if isinstance(data, dict):
                for key in ("X-Secret", "x_secret", "secret", "secret_key", "key"):
                    value = data.get(key)
                    if isinstance(value, list):
                        value = value[0] if value else ""
                    if value:
                        LAST_SECRET = str(value)
                        break
            self.send_json({"received": True, "token_ok": ok, "secret_detected": bool(LAST_SECRET)})
            return
        self.send_json({"ok": False, "error": "route inconnue"}, 404)


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), App)
    print(f"BTP Smart Tools secours lancé sur {HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    run()
