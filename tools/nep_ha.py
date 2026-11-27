"""Nep-Home Assistant voor lokaal testen van de app (poort 8123).

Start de app met HA_API=http://127.0.0.1:8123/api SUPERVISOR_API=http://127.0.0.1:8123 SUPERVISOR_TOKEN=test.
GET /test/log toont de ontvangen service-aanroepen.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATES = {f"input_select.gbs_{i}_locatie": "Niet geplaatst"
          for i in ["t1", "t2", "t3", "t4", "a1", "a2", "a3", "a4", "a5"]}
STATES["input_select.gbs_t1_locatie"] = "Deur"
STATES["input_select.gbs_a2_locatie"] = "Deur"
LOG = []


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def antw(self, data):
        b = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path == "/api/states":
            return self.antw([{"entity_id": k, "state": v} for k, v in STATES.items()])
        if self.path == "/test/log":
            return self.antw({"log": LOG, "states": STATES})
        self.send_error(404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        data = json.loads(self.rfile.read(n) or b"{}")
        LOG.append([self.path, data])
        if self.path == "/api/services/input_select/select_option":
            STATES[data["entity_id"]] = data["option"]
        if self.path == "/core/check":
            return self.antw({"result": "ok"})
        self.antw([])


ThreadingHTTPServer(("127.0.0.1", 8123), H).serve_forever()
