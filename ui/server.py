from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json


HOST = "127.0.0.1"
PORT = 8080

DEMO_STATE = {
    "mode": "demo",
    "project": "cloudpilot",
    "environment": "development",
    "provider": "gcp",
    "region": "asia-south1",
    "status": "Ready for plan",
    "resources": [
        {"name": "cloudpilot-vpc", "type": "Network", "provider": "GCP", "status": "Configured"},
        {"name": "cloudpilot-vm", "type": "Compute", "provider": "GCP", "status": "Preview only"},
        {"name": "cloudpilot-firewall", "type": "Security", "provider": "GCP", "status": "Configured"},
    ],
    "activity": [
        {"time": "Just now", "message": "Demo environment loaded"},
        {"time": "Today", "message": "Configuration validation passed"},
        {"time": "Today", "message": "No cloud account connected"},
    ],
}


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CloudPilot Demo</title>
<style>
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#e8eefc;background:#0b1220;--muted:#91a0ba;--card:#121d31;--line:#24334c;--blue:#5b8cff;--green:#32d583}
*{box-sizing:border-box}body{margin:0}.layout{display:flex;min-height:100vh}.side{width:240px;padding:26px 18px;border-right:1px solid var(--line);background:#0d1728}.brand{font-size:22px;font-weight:800;margin:0 12px 38px}.brand span{color:var(--blue)}nav a{display:block;color:var(--muted);padding:12px;border-radius:9px;text-decoration:none;margin:5px 0}nav a.active,nav a:hover{background:#1b2b4a;color:#fff}.main{max-width:1250px;width:100%;padding:34px 42px}.top{display:flex;justify-content:space-between;align-items:flex-start;gap:20px}.eyebrow{color:var(--blue);font-size:12px;font-weight:700;letter-spacing:1.6px;text-transform:uppercase}.title{font-size:32px;margin:8px 0}.muted{color:var(--muted)}.badge{background:#183c37;color:#6ee7b7;padding:8px 12px;border-radius:20px;font-size:13px;font-weight:700}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:30px 0}.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:20px}.metric{font-size:27px;font-weight:800;margin-top:8px}.label{font-size:13px;color:var(--muted)}.section{display:flex;justify-content:space-between;align-items:center;margin:26px 0 12px}.section h2{font-size:18px;margin:0}.controls{display:flex;gap:10px;flex-wrap:wrap}.select,button{background:#16243b;color:#e8eefc;border:1px solid var(--line);border-radius:8px;padding:10px 13px;font-size:14px}button{background:var(--blue);border:0;font-weight:700;cursor:pointer}button.secondary{background:#16243b;border:1px solid var(--line)}.table{width:100%;border-collapse:collapse}.table th,.table td{text-align:left;padding:15px 10px;border-bottom:1px solid var(--line);font-size:14px}.table th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.7px}.status{color:var(--green)}.columns{display:grid;grid-template-columns:1.4fr 1fr;gap:16px}.activity{list-style:none;padding:0;margin:0}.activity li{padding:14px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:20px}.notice{margin-top:22px;padding:14px 16px;border:1px solid #6b5224;background:#302614;color:#f5cf7a;border-radius:10px;font-size:14px}@media(max-width:850px){.side{display:none}.main{padding:25px 18px}.grid{grid-template-columns:repeat(2,1fr)}.columns{grid-template-columns:1fr}}@media(max-width:480px){.grid{grid-template-columns:1fr}.top{display:block}.badge{display:inline-block;margin-top:14px}}
</style>
</head>
<body><div class="layout"><aside class="side"><h1 class="brand">Cloud<span>Pilot</span></h1><nav><a class="active" href="#">Overview</a><a href="#resources">Resources</a><a href="#activity">Activity</a><a href="#settings">Configuration</a></nav></aside>
<main class="main"><div class="top"><div><div class="eyebrow">Local preview</div><h2 class="title">Infrastructure overview</h2><div class="muted">See how CloudPilot manages multi-cloud environments.</div></div><div class="badge">● Demo mode · No account connected</div></div>
<div class="grid"><div class="card"><div class="label">Provider</div><div class="metric" id="provider">GCP</div><div class="muted" id="region">asia-south1</div></div><div class="card"><div class="label">Environment</div><div class="metric">Development</div><div class="muted">cloudpilot</div></div><div class="card"><div class="label">Resources</div><div class="metric" id="resource-count">3</div><div class="muted">defined in config</div></div><div class="card"><div class="label">Deployment status</div><div class="metric status" id="state">Ready</div><div class="muted">Nothing provisioned</div></div></div>
<div class="section"><h2>Environment controls</h2><div class="controls"><select class="select" id="provider-select"><option value="gcp">Google Cloud</option><option value="aws">AWS</option><option value="azure">Microsoft Azure</option></select><button class="secondary" onclick="validate()">Validate config</button><button onclick="plan()">Preview plan</button></div></div>
<div class="columns"><section class="card" id="resources"><div class="section"><h2>Configured resources</h2><span class="muted">Mock data</span></div><table class="table"><thead><tr><th>Name</th><th>Type</th><th>Provider</th><th>Status</th></tr></thead><tbody id="resource-table"></tbody></table></section>
<section class="card" id="activity"><div class="section"><h2>Recent activity</h2></div><ul class="activity" id="activity-list"></ul></section></div>
<div class="notice" id="notice">Demo mode is safe: validation and plan actions are simulated locally. No credentials, account, or cloud resources are used.</div>
</main></div>
<script>
async function load(){const state=await fetch('/api/state').then(r=>r.json());document.getElementById('provider').textContent=state.provider.toUpperCase();document.getElementById('region').textContent=state.region;document.getElementById('resource-count').textContent=state.resources.length;document.getElementById('resource-table').innerHTML=state.resources.map(r=>`<tr><td>${r.name}</td><td>${r.type}</td><td>${r.provider}</td><td class="status">${r.status}</td></tr>`).join('');document.getElementById('activity-list').innerHTML=state.activity.map(a=>`<li><span>${a.message}</span><small class="muted">${a.time}</small></li>`).join('')}
async function action(path,message){const result=await fetch(path,{method:'POST'}).then(r=>r.json());document.getElementById('notice').textContent=result.message;document.getElementById('state').textContent=result.status;load()}
function validate(){action('/api/validate','Configuration validation completed locally.')}
function plan(){action('/api/plan','Plan preview generated locally. No cloud API was called.')}
load()
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            self.send_json(DEMO_STATE)
        else:
            self.send_html(PAGE)

    def do_POST(self):
        if self.path == "/api/validate":
            self.send_json({"status": "Valid", "message": "Configuration validation completed locally."})
        elif self.path == "/api/plan":
            self.send_json({"status": "Plan ready", "message": "Plan preview generated locally. No cloud API was called."})
        else:
            self.send_error(404)

    def send_html(self, content):
        payload = content.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, content):
        payload = json.dumps(content).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print(f"CloudPilot demo UI: http://{HOST}:{PORT}")
    print("Demo mode only. No cloud account or credentials are used.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
