from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "10000"))

APP_NAME = "BTP Smart Tools"
DOMAIN = os.environ.get("BTP_PUBLIC_URL", "https://btpsmarttools.com").rstrip("/")
ADMIN_MAIL = os.environ.get("BTP_ADMIN_MAIL", "admin@btpsmarttools.com")

PVIT_MODE = os.environ.get("MYPVIT_MODE", "TEST")
PVIT_BASE_URL = os.environ.get("MYPVIT_BASE_URL", "https://api.mypvit.pro")
PVIT_MERCHANT_SLUG = os.environ.get("MYPVIT_MERCHANT_SLUG", "MR_1778797178")
PVIT_SECRET_RECEIVER_TOKEN = os.environ.get(
    "MYPVIT_SECRET_RECEIVER_TOKEN",
    "pvit-btp-b9a1c7a2759644a7b005",
)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
SECRET_LOG = DATA / "pvit_secret_receiver.log"
SECRET_STORE = DATA / "pvit_secret_store.json"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_store() -> dict:
    if SECRET_STORE.exists():
        try:
            return json.loads(SECRET_STORE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_store(data: dict) -> None:
    SECRET_STORE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def append_log(line: str) -> None:
    with SECRET_LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{now()}] {line}\n")


def mask_secret(secret: str) -> str:
    if not secret:
        return "Non recu"
    if len(secret) <= 8:
        return "recu"
    return f"{secret[:4]}...{secret[-4:]}"


def extract_secret(payload: dict, raw: str) -> str:
    keys = [
        "X-Secret",
        "x-secret",
        "x_secret",
        "secret",
        "secret_key",
        "secretKey",
        "api_secret",
        "key",
    ]
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            value = value[0] if value else ""
        if value:
            return str(value).strip()

    match = re.search(
        r"(?i)(?:x[-_]?secret|secret(?:_key)?|secretKey|api_secret|key)\s*[:=]\s*['\"]?([A-Za-z0-9._~:/+=-]{8,})",
        raw,
    )
    return match.group(1).strip() if match else ""


def page(title: str, body: str) -> bytes:
    html_doc = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - {APP_NAME}</title>
  <style>
    :root {{
      --bg:#050b14; --panel:#0b1220; --line:#203044;
      --text:#eaf2ff; --muted:#94a3b8; --cyan:#22d3ee; --blue:#2f8cff;
      --green:#10b981; --red:#ef4444;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; font-family:Segoe UI, Arial, sans-serif; color:var(--text);
      background:
        radial-gradient(circle at 10% 0%, rgba(47,140,255,.22), transparent 30%),
        radial-gradient(circle at 90% 10%, rgba(124,58,237,.18), transparent 28%),
        linear-gradient(135deg,#050b14,#07111f 55%,#0a1020);
      min-height:100vh;
    }}
    header {{
      padding:18px 24px; border-bottom:1px solid rgba(34,211,238,.18);
      background:rgba(5,11,20,.86); position:sticky; top:0;
    }}
    .brand {{ font-weight:900; font-size:26px; color:var(--cyan); }}
    .brand span {{ color:white; font-size:14px; margin-left:8px; }}
    main {{ max-width:1120px; margin:auto; padding:28px; }}
    .hero {{
      border:1px solid rgba(34,211,238,.22); border-radius:20px;
      padding:38px; background:linear-gradient(135deg,rgba(15,23,42,.95),rgba(8,15,28,.96));
      box-shadow:0 28px 80px rgba(0,0,0,.35);
    }}
    h1 {{ font-size:54px; margin:0 0 8px; }}
    h2 {{ margin-top:0; }}
    p {{ color:var(--muted); line-height:1.55; }}
    .grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-top:18px; }}
    .card {{
      background:rgba(15,23,42,.88); border:1px solid rgba(148,163,184,.20);
      border-radius:14px; padding:20px;
    }}
    .pill {{
      display:inline-block; padding:7px 11px; border-radius:999px;
      background:rgba(34,211,238,.12); border:1px solid rgba(34,211,238,.28);
      color:#8deeff; font-weight:800; font-size:12px;
    }}
    .btn {{
      display:inline-flex; align-items:center; justify-content:center;
      min-height:42px; padding:11px 16px; border-radius:9px;
      color:white; text-decoration:none; font-weight:900;
      background:linear-gradient(135deg,var(--blue),var(--cyan));
      margin:6px 8px 6px 0;
    }}
    .ok {{ color:var(--green); font-weight:900; }}
    .bad {{ color:var(--red); font-weight:900; }}
    pre {{
      white-space:pre-wrap; overflow:auto; background:#020617; color:#dbeafe;
      border-radius:12px; padding:16px; border:1px solid rgba(148,163,184,.18);
    }}
    code {{ color:#8deeff; }}
    @media(max-width:850px) {{ .grid {{ grid-template-columns:1fr; }} h1 {{ font-size:38px; }} }}
  </style>
</head>
<body>
  <header><div class="brand">BTP <span>Smart Tools</span></div></header>
  <main>{body}</main>
</body>
</html>"""
    return html_doc.encode("utf-8")


class App(BaseHTTPRequestHandler):
    server_version = "BTP-Smart-Tools/1.0"

    def send_bytes(self, status: int, content: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_page(self, title: str, body: str, status: int = 200) -> None:
        self.send_bytes(status, page(title, body))

    def read_body(self) -> str:
        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length).decode("utf-8", errors="replace") if length else ""

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/":
            return self.home()
        if path == "/health":
            return self.json_response({"ok": True, "service": APP_NAME, "time": now()})
        if path in ("/pvit/secret-receiver", "/pvit/secret-receiver-open"):
            return self.pvit_secret_receiver()
        if path == "/pvit/secret-status":
            return self.pvit_secret_status()
        if path == "/payment/success":
            return self.payment_result(True)
        if path == "/payment/failed":
            return self.payment_result(False)
        return self.send_page("Page introuvable", "<div class='card'><h2>Page introuvable</h2></div>", 404)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path in ("/pvit/secret-receiver", "/pvit/secret-receiver-open"):
            return self.pvit_secret_receiver()
        if path == "/payment/callback":
            return self.payment_callback()
        return self.send_page("Action introuvable", "<div class='card'><h2>Action introuvable</h2></div>", 404)

    def json_response(self, data: dict, status: int = 200) -> None:
        self.send_bytes(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def home(self) -> None:
        receiver_url = f"{DOMAIN}/pvit/secret-receiver?token={PVIT_SECRET_RECEIVER_TOKEN}"
        open_url = f"{DOMAIN}/pvit/secret-receiver-open"
        body = f"""
        <section class="hero">
          <span class="pill">Service actif : cartouches professionnelles</span>
          <h1>BTP Smart Tools</h1>
          <h2>Plateforme cartouches, paiements PVit et futurs outils BTP intelligents.</h2>
          <p>Le serveur Render fonctionne. Cette première version met en ligne le socle du site et les endpoints PVit nécessaires aux tests.</p>
          <a class="btn" href="/pvit/secret-status">Voir statut Secret PVit</a>
          <a class="btn" href="/health">Tester le serveur</a>
        </section>
        <div class="grid">
          <div class="card"><span class="pill">Paiement TEST</span><h2>PVit</h2><p>Mode : <b>{html.escape(PVIT_MODE)}</b><br>Marchand : <b>{html.escape(PVIT_MERCHANT_SLUG)}</b></p></div>
          <div class="card"><span class="pill">URL Secret</span><h2>Avec token</h2><p><code>{html.escape(receiver_url)}</code></p></div>
          <div class="card"><span class="pill">Alternative TEST</span><h2>Sans token</h2><p><code>{html.escape(open_url)}</code></p></div>
        </div>
        """
        self.send_page("Accueil", body)

    def pvit_secret_receiver(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        token = (params.get("token") or [""])[0]
        token_ok = token == PVIT_SECRET_RECEIVER_TOKEN
        if PVIT_MODE.upper() == "TEST" and (parsed.path.endswith("-open") or not token):
            token_ok = True

        raw = self.read_body()
        append_log(
            f"{self.command} {self.path} token_ok={token_ok} "
            f"length={len(raw.encode('utf-8'))} ip={self.client_address[0]} body={raw[:1000]}"
        )

        if not token_ok:
            return self.json_response({"ok": False, "error": "invalid token"}, 403)

        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            payload = {k: v[0] if v else "" for k, v in urllib.parse.parse_qs(raw).items()}

        secret = extract_secret(payload, raw)
        store = load_store()
        store.update(
            {
                "last_at": now(),
                "last_method": self.command,
                "last_path": self.path,
                "last_headers": dict(self.headers),
                "last_payload": raw,
                "last_error": "" if secret else "Requete recue, mais aucune Secret Key detectee.",
            }
        )
        if secret:
            store["secret"] = secret
            store["secret_masked"] = mask_secret(secret)
        save_store(store)
        return self.json_response({"ok": True, "secret_received": bool(secret)})

    def pvit_secret_status(self) -> None:
        store = load_store()
        log_tail = ""
        if SECRET_LOG.exists():
            log_tail = "".join(SECRET_LOG.read_text(encoding="utf-8", errors="replace").splitlines(True)[-40:])
        receiver_url = f"{DOMAIN}/pvit/secret-receiver?token={PVIT_SECRET_RECEIVER_TOKEN}"
        open_url = f"{DOMAIN}/pvit/secret-receiver-open"
        body = f"""
        <div class="card">
          <h1>Statut Secret Key PVit</h1>
          <p><b>Secret recu :</b> <span class="{'ok' if store.get('secret') else 'bad'}">{html.escape(store.get('secret_masked', 'Non recu'))}</span></p>
          <p><b>Derniere reception :</b> {html.escape(store.get('last_at', 'Aucune'))}</p>
          <p><b>Derniere erreur :</b> {html.escape(store.get('last_error', 'Aucune'))}</p>
          <p><b>URL a mettre dans PVit :</b><br><code>{html.escape(receiver_url)}</code></p>
          <p><b>URL alternative TEST :</b><br><code>{html.escape(open_url)}</code></p>
        </div>
        <div class="card"><h2>Dernier payload</h2><pre>{html.escape(store.get('last_payload', 'Aucun payload recu.'))}</pre></div>
        <div class="card"><h2>Journal receiver</h2><pre>{html.escape(log_tail or 'Aucun log.')}</pre></div>
        """
        self.send_page("Secret PVit", body)

    def payment_callback(self) -> None:
        raw = self.read_body()
        append_log(f"PAYMENT_CALLBACK {self.command} {self.path} ip={self.client_address[0]} body={raw[:1000]}")
        return self.json_response({"ok": True, "callback_received": True})

    def payment_result(self, success: bool) -> None:
        if success:
            body = "<div class='card'><h1>Paiement réussi</h1><p>Le paiement a été validé ou est en cours de confirmation.</p></div>"
        else:
            body = "<div class='card'><h1>Paiement échoué</h1><p>Le paiement n'a pas été validé. Vous pouvez refaire un essai.</p></div>"
        self.send_page("Paiement", body)


def main() -> None:
    DATA.mkdir(exist_ok=True)
    server = ThreadingHTTPServer((HOST, PORT), App)
    print(f"{APP_NAME} lance sur http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
