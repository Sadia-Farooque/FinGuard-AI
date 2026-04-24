import os
import joblib
import numpy as np
import pymongo
import webview
import threading
import time
from flask import Flask, render_template_string, request, jsonify

# ─────────────────────────────────────────────
#  1. EMBEDDED UI (HTML, CSS, JS)
# ─────────────────────────────────────────────

CSS_CONTENT = """
:root {
    --bg-dark: #0b0e1a;
    --panel-bg: rgba(17, 24, 39, 0.65);
    --card-bg: rgba(26, 34, 53, 0.7);
    --border: rgba(255, 255, 255, 0.1);
    --border-hover: rgba(255, 255, 255, 0.2);
    --text-main: #ffffff;
    --text-muted: #8b9bb4;
    --accent: #1D9E75;
    --accent-glow: rgba(29, 158, 117, 0.4);
    --success: #1D9E75;
    --warning: #f59e0b;
    --danger: #ef4444;
    --font-sans: 'Outfit', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font-sans); background-color: var(--bg-dark); color: var(--text-main); min-height: 100vh; overflow: hidden; }
#particles-js { position: absolute; width: 100%; height: 100%; z-index: -2; top: 0; left: 0; }
.glow-sphere { position: absolute; border-radius: 50%; filter: blur(80px); z-index: -1; opacity: 0.5; animation: float 10s infinite ease-in-out alternate; }
.sphere-1 { width: 400px; height: 400px; background: radial-gradient(circle, rgba(29,158,117,0.3) 0%, rgba(11,14,26,0) 70%); top: -100px; left: -100px; }
.sphere-2 { width: 500px; height: 500px; background: radial-gradient(circle, rgba(59,130,246,0.2) 0%, rgba(11,14,26,0) 70%); bottom: -150px; right: -100px; animation-delay: -5s; }
@keyframes float { 0% { transform: translate(0, 0); } 100% { transform: translate(30px, 50px); } }
.glass-panel { background: var(--panel-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3); }
.app-container { max-width: 1400px; margin: 0 auto; padding: 20px; height: 100vh; display: flex; flex-direction: column; gap: 20px; }
.topbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; height: 70px; }
.logo-text { font-size: 24px; font-weight: 800; letter-spacing: 1px; }
.logo-text .accent { color: var(--accent); }
.status-indicator { display: flex; align-items: center; gap: 10px; font-size: 14px; color: var(--text-muted); }
.pulse-dot { width: 10px; height: 10px; background-color: var(--accent); border-radius: 50%; box-shadow: 0 0 10px var(--accent-glow); animation: pulse 2s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(29, 158, 117, 0.7); } 70% { box-shadow: 0 0 0 10px rgba(29, 158, 117, 0); } 100% { box-shadow: 0 0 0 0 rgba(29, 158, 117, 0); } }
.dashboard-layout { display: flex; gap: 24px; flex: 1; min-height: 0; }
.sidebar { width: 320px; display: flex; flex-direction: column; overflow: hidden; }
.sidebar-header { padding: 20px 24px; border-bottom: 1px solid var(--border); }
.sidebar-header h3 { font-size: 12px; font-weight: 700; color: var(--text-muted); letter-spacing: 1px; }
.input-grid { padding: 24px; overflow-y: auto; display: flex; flex-wrap: wrap; gap: 16px; }
.input-grid::-webkit-scrollbar { width: 6px; }
.input-grid::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
.input-group { width: calc(50% - 8px); display: flex; flex-direction: column; gap: 6px; }
.input-group.full-width { width: 100%; }
.input-group label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.input-group input, .input-group select { background: rgba(0, 0, 0, 0.2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; color: var(--text-main); font-family: var(--font-mono); font-size: 14px; outline: none; }
.input-group input:focus { border-color: var(--accent); }
.action-buttons { margin-top: 10px; display: flex; flex-direction: column; gap: 10px; }
.btn-primary { width: 100%; background: var(--accent); color: #fff; border: none; padding: 14px; border-radius: 8px; font-weight: 700; cursor: pointer; transition: 0.3s; box-shadow: 0 4px 15px rgba(29, 158, 117, 0.3); }
.btn-primary:hover { transform: translateY(-2px); background: #148560; }
.btn-secondary { width: 100%; background: var(--card-bg); color: var(--text-muted); border: 1px solid var(--border); padding: 12px; border-radius: 8px; font-size: 12px; cursor: pointer; transition: 0.3s; }
.btn-secondary:hover { color: #fff; background: rgba(255,255,255,0.05); }
.results-area { flex: 1; display: flex; flex-direction: column; gap: 24px; overflow-y: auto; }
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.metric-card { background: var(--card-bg); padding: 24px; display: flex; flex-direction: column; gap: 16px; border: 1px solid var(--border); border-radius: 16px; }
.card-header { font-size: 11px; font-weight: 700; color: var(--text-muted); letter-spacing: 1px; }
.card-value { font-family: var(--font-mono); font-size: 42px; font-weight: 700; color: var(--text-muted); }
.progress-track { width: 100%; height: 6px; background: rgba(0,0,0,0.3); border-radius: 3px; overflow: hidden; }
.progress-bar { height: 100%; width: 0%; transition: width 1.5s ease; border-radius: 3px; }
.explain-panel { flex: 1; display: flex; flex-direction: column; }
.panel-header { padding: 20px 24px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 10px; color: var(--text-muted); }
.explain-content { padding: 24px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.reason-item { display: flex; align-items: flex-start; gap: 16px; background: rgba(0,0,0,0.2); padding: 16px; border-radius: 8px; border: 1px solid var(--border); }
.reason-icon { width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: #fff; flex-shrink: 0; }
.text-success { color: var(--success) !important; } .bg-success { background: var(--success) !important; }
.text-warning { color: var(--warning) !important; } .bg-warning { background: var(--warning) !important; }
.text-danger { color: var(--danger) !important; } .bg-danger { background: var(--danger) !important; }
"""

JS_CONTENT = """
document.addEventListener('DOMContentLoaded', () => {
    particlesJS("particles-js", {
        particles: {
            number: { value: 60, density: { enable: true, value_area: 800 } },
            color: { value: "#ffffff" },
            shape: { type: "circle" },
            opacity: { value: 0.1 },
            size: { value: 3, random: true },
            line_linked: { enable: true, distance: 150, color: "#ffffff", opacity: 0.05, width: 1 },
            move: { enable: true, speed: 1 }
        },
        interactivity: { detect_on: "canvas", events: { onhover: { enable: true, mode: "grab" }, resize: true } }
    });

    const form = document.getElementById('analysis-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            "Age": document.getElementById('Age').value,
            "Monthly Income": document.getElementById('Income').value,
            "Debt Ratio": document.getElementById('Debt').value,
            "Loan Amount": document.getElementById('Loan').value,
            "Credit Score": document.getElementById('Score').value,
            "Tenure": document.getElementById('Tenure').value,
            "Num Products": document.getElementById('Products').value,
            "Balance": document.getElementById('Balance').value,
            "Gender": document.getElementById('Gender').value,
            "Geography": document.getElementById('Geography').value,
            "Active Member": document.getElementById('Active').value
        };

        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        updateDashboard(await res.json());
    });

    document.getElementById('load-db-btn').addEventListener('click', async () => {
        const id = prompt("Enter Customer ID (e.g., CUST001):");
        if (!id) return;
        const res = await fetch('/api/load_customer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ "customer_id": id })
        });
        if (res.ok) {
            const c = await res.json();
            document.getElementById('Age').value = c.Age;
            document.getElementById('Income').value = c["Monthly Income"];
            document.getElementById('Debt').value = c["Debt Ratio"];
            document.getElementById('Loan').value = c["Loan Amount"];
            document.getElementById('Score').value = c["Credit Score"];
            document.getElementById('Tenure').value = c.Tenure;
            document.getElementById('Products').value = c["Num Products"];
            document.getElementById('Balance').value = c.Balance;
            document.getElementById('Gender').value = c.Gender;
            document.getElementById('Geography').value = c.Geography;
            document.getElementById('Active').value = c["Active Member"];
            form.dispatchEvent(new Event('submit'));
        } else { alert("Not found"); }
    });
});

function updateDashboard(data) {
    const { scores, explanations } = data;
    ['credit', 'fraud', 'churn', 'spend'].forEach(k => updateCard(k, scores[k]));
    const box = document.getElementById('explain-box');
    box.innerHTML = '';
    explanations.forEach(item => {
        const div = document.createElement('div');
        div.className = 'reason-item';
        div.innerHTML = `<div class="reason-icon bg-${item.color}">${item.icon}</div><div class="reason-text">${item.text}</div>`;
        box.appendChild(div);
    });
}

function updateCard(type, val) {
    const card = document.getElementById(`card-${type}`);
    const num = card.querySelector('.number');
    const bar = card.querySelector('.progress-bar');
    const tag = card.querySelector('.card-tag');
    let cls = 'success', txt = 'LOW RISK';
    if (val >= 65) { cls = 'danger'; txt = 'HIGH RISK'; }
    else if (val >= 35) { cls = 'warning'; txt = 'MEDIUM RISK'; }
    card.querySelector('.card-value').className = `card-value text-${cls}`;
    bar.className = `progress-bar bg-${cls}`;
    tag.className = `card-tag text-${cls}`;
    tag.innerText = txt;
    bar.style.width = `${val}%`;
    num.innerText = Math.round(val);
}
"""

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html>
<head>
    <title>FinGuard AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
    <style>{CSS_CONTENT}</style>
</head>
<body>
    <div id="particles-js"></div>
    <div class="glow-sphere sphere-1"></div>
    <div class="glow-sphere sphere-2"></div>
    <div class="app-container">
        <nav class="topbar glass-panel">
            <div class="logo"><span class="logo-text">Fin<span class="accent">Guard</span> AI</span></div>
            <div class="status-indicator"><div class="pulse-dot"></div><span>Local AI Engine Active</span></div>
        </nav>
        <div class="dashboard-layout">
            <aside class="sidebar glass-panel">
                <div class="sidebar-header"><h3>CUSTOMER PROFILE</h3></div>
                <form id="analysis-form" class="input-grid">
                    <div class="input-group"><label>Age</label><input type="number" id="Age" value="34"></div>
                    <div class="input-group"><label>Income</label><input type="number" id="Income" value="5200"></div>
                    <div class="input-group"><label>Debt Ratio</label><input type="number" id="Debt" value="0.74"></div>
                    <div class="input-group"><label>Loan</label><input type="number" id="Loan" value="18500"></div>
                    <div class="input-group"><label>Score</label><input type="number" id="Score" value="620"></div>
                    <div class="input-group"><label>Tenure</label><input type="number" id="Tenure" value="2"></div>
                    <div class="input-group"><label>Products</label><input type="number" id="Products" value="1"></div>
                    <div class="input-group"><label>Balance</label><input type="number" id="Balance" value="45000"></div>
                    <div class="input-group full-width"><label>Gender</label><select id="Gender"><option>Male</option><option>Female</option></select></div>
                    <div class="input-group full-width"><label>Geography</label><select id="Geography"><option>France</option><option>Germany</option><option>Spain</option></select></div>
                    <div class="input-group full-width"><label>Active</label><select id="Active"><option>Yes</option><option>No</option></select></div>
                    <div class="action-buttons full-width">
                        <button type="submit" class="btn-primary">▶ ANALYZE RISK</button>
                        <button type="button" class="btn-secondary" id="load-db-btn">⬡ LOAD FROM DB</button>
                    </div>
                </form>
            </aside>
            <main class="results-area">
                <div class="metrics-grid">
                    <div class="metric-card" id="card-credit"><div class="card-header">CREDIT RISK</div><div class="card-value"><span class="number">0</span>%</div><div class="progress-track"><div class="progress-bar"></div></div><div class="card-tag">READY</div></div>
                    <div class="metric-card" id="card-fraud"><div class="card-header">FRAUD</div><div class="card-value"><span class="number">0</span>%</div><div class="progress-track"><div class="progress-bar"></div></div><div class="card-tag">READY</div></div>
                    <div class="metric-card" id="card-churn"><div class="card-header">CHURN</div><div class="card-value"><span class="number">0</span>%</div><div class="progress-track"><div class="progress-bar"></div></div><div class="card-tag">READY</div></div>
                    <div class="metric-card" id="card-spend"><div class="card-header">SPEND</div><div class="card-value"><span class="number">0</span>%</div><div class="progress-track"><div class="progress-bar"></div></div><div class="card-tag">READY</div></div>
                </div>
                <div class="explain-panel glass-panel">
                    <div class="panel-header"><h3>AI EXPLAINABILITY</h3></div>
                    <div class="explain-content" id="explain-box"><div style="color:var(--text-muted)">Run analysis...</div></div>
                </div>
            </main>
        </div>
    </div>
    <script>{JS_CONTENT}</script>
</body>
</html>
"""

# ─────────────────────────────────────────────
#  2. BACKEND LOGIC (Flask)
# ─────────────────────────────────────────────

app = Flask(__name__)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(ROOT_DIR, "models")

def _load(name):
    path = os.path.join(MODEL_DIR, name)
    try:
        m = joblib.load(path)
        # Fix for XGBoost version mismatch
        if hasattr(m, 'get_params'):
            try: m.use_label_encoder = False
            except: pass
        return m
    except: return None

credit_model = _load("credit_risk_model.pkl")
churn_model  = _load("churn_model.pkl")
fraud_model  = _load("fraud_model.pkl")
spend_model  = _load("spend_model_weights.pkl")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    try:
        age, inc, debt, loan = int(data['Age']), float(data['Monthly Income']), float(data['Debt Ratio']), float(data['Loan Amount'])
        score, ten, prd, bal = float(data['Credit Score']), int(data['Tenure']), int(data['Num Products']), float(data['Balance'])
        act = 1 if data['Active Member'] == "Yes" else 0
        gen = 1 if data['Gender'] == "Male" else 0
        de = 1 if data['Geography'] == "Germany" else 0
        sp = 1 if data['Geography'] == "Spain" else 0
    except: return jsonify({"error": "Invalid data"}), 400

    res = {}
    if credit_model:
        f = np.array([[debt, inc/12000, loan/50000, score/850, age/80, ten/30, bal/100000, prd]])
        res["credit"] = credit_model.predict_proba(f)[0][1] * 100
    else: res["credit"] = min(99, max(1, debt*60 + (loan/inc)*20))

    if fraud_model:
        f = np.array([[loan, inc, age, score, bal, ten, prd, act]])
        res["fraud"] = fraud_model.predict_proba(f)[0][1] * 100
    else: res["fraud"] = min(99, max(1, (loan/inc)*15 + (1-act)*10))

    if churn_model:
        f = np.array([[score, age, ten, bal, prd, 1, act, inc, gen, de, sp]])
        res["churn"] = churn_model.predict_proba(f)[0][1] * 100
    else: res["churn"] = min(99, max(1, (1-act)*40 + (1/max(prd,1))*30))

    if spend_model:
        f = np.array([[inc, age, bal, ten, prd, score]])
        raw = float(spend_model.predict(f)[0])
        res["spend"] = min(99, max(1, (raw/(inc*0.6))*50))
    else: res["spend"] = min(99, max(1, (inc*0.35)/500))

    for k in res: res[k] = min(99, max(1, res[k]))
    
    reasons = []
    if debt > 0.6: reasons.append({"icon": "!", "color": "danger", "text": "High Debt Ratio detected."})
    if score > 700: reasons.append({"icon": "+", "color": "success", "text": "Excellent Credit Score."})
    if act: reasons.append({"icon": "+", "color": "success", "text": "Active account usage."})
    if not reasons: reasons.append({"icon": "+", "color": "success", "text": "Stable profile."})

    return jsonify({"scores": res, "explanations": reasons})

@app.route('/api/load_customer', methods=['POST'])
def load_customer():
    cust_id = request.json.get("customer_id")
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        c = client.finguard.customers.find_one({"customer_id": cust_id}, {"_id": 0})
        return jsonify(c) if c else (jsonify({"error": "Not found"}), 404)
    except: return jsonify({"error": "DB Error"}), 500

# ─────────────────────────────────────────────
#  3. DESKTOP LAUNCHER
# ─────────────────────────────────────────────

def run_server():
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_server, daemon=True).start()
    time.sleep(1.5)
    webview.create_window('FinGuard AI Desktop', 'http://127.0.0.1:5000', width=1200, height=800, background_color='#0b0e1a')
    webview.start()
