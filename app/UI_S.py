# FinGuard AI — Complete Application

import tkinter as tk
from tkinter import ttk, messagebox
import joblib
import numpy as np
import os
import threading
import math
import time
import random
import datetime

# ─────────────────────────────────────────────
#  SOUND ENGINE
#  Uses winsound on Windows (built-in, zero install)
# ─────────────────────────────────────────────
try:
    import winsound
    def _beep(freq: int, dur: int):
        """Play a short beep on a background thread so UI never blocks."""
        threading.Thread(
            target=winsound.Beep, args=(freq, dur), daemon=True
        ).start()
    def sound_click():   _beep(1200, 40)    # short high tick
    def sound_confirm(): _beep(1400, 50); threading.Timer(0.08, lambda: _beep(1600, 60)).start()
    def sound_analyze(): _beep(1100, 40); threading.Timer(0.06, lambda: _beep(1300, 100)).start()
    def sound_error():   _beep(700, 150)    # softer warning tone
    def sound_success(): _beep(1400, 50); threading.Timer(0.08, lambda: _beep(1800, 80)).start()
    SOUND_ON = True
except ImportError:

    def sound_click():   pass
    def sound_confirm(): pass
    def sound_analyze(): pass
    def sound_error():   pass
    def sound_success(): pass
    SOUND_ON = False

# ─────────────────────────────────────────────
#  ADMIN CREDENTIALS
#  Only these two users can log in.
# ─────────────────────────────────────────────
ADMINS = {
    "sadia baloch":   "sadia123",
    "abdul qudoos":   "qudoos123",
}

# ── NEW: Persistent Decision Tracking ─────
# Key: customer_id, Value: "Approved" or "Rejected"
ADMIN_DECISIONS = {}


# ─────────────────────────────────────────────
#  100 DUMMY CUSTOMERS
#  Generated once at module level so both the
#  login page and the dashboard share the same list.
# ─────────────────────────────────────────────
FIRST_NAMES = [
    "Ali","Sara","Omar","Fatima","Hassan","Aisha","Bilal","Zara","Tariq","Nadia",
    "Imran","Hina","Kashif","Rida","Usman","Maryam","Asad","Sana","Faisal","Layla",
    "Danish","Anum","Kamran","Sobia","Waqas","Amna","Junaid","Ayesha","Shahid","Rabia",
    "Rizwan","Mehwish","Adnan","Farah","Zahid","Kiran","Naveed","Huma","Naeem","Sidra",
    "Salman","Iqra","Hamid","Nimra","Babar","Zainab","Ahsan","Noor","Irfan","Shazia",
]
LAST_NAMES = [
    "Khan","Ahmed","Ali","Sheikh","Malik","Butt","Chaudhry","Siddiqui","Hussain","Raja",
]
GEOS    = ["France", "Germany", "Spain"]
JOBS    = ["Engineer","Doctor","Teacher","Businessman","Analyst","Manager","Designer",
           "Accountant","Nurse","Lawyer","Student","Retired","Sales Rep","Officer"]

def _gen_customers(n=100):
    """Build n synthetic customer records covering a wide range of risk profiles."""
    random.seed(42)           # reproducible every run
    records = []
    for i in range(1, n + 1):
        age         = random.randint(20, 70)
        income      = random.randint(1500, 15000)
        debt_ratio  = round(random.uniform(0.10, 0.95), 2)
        loan_amount = random.randint(1000, 80000)
        credit_score= random.randint(300, 850)
        tenure      = random.randint(0, 20)
        num_products= random.randint(1, 4)
        balance     = random.randint(0, 200000)
        gender      = random.choice(["Male", "Female"])
        geography   = random.choice(GEOS)
        active      = random.choice(["Yes", "No"])
        occupation  = random.choice(JOBS)
        name        = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

        records.append({
            "customer_id":  f"CUS{i:04d}",
            "name":         name,
            "age":          age,
            "income":       income,
            "debt_ratio":   debt_ratio,
            "loan_amount":  loan_amount,
            "credit_score": credit_score,
            "tenure":       tenure,
            "num_products": num_products,
            "balance":      balance,
            "gender":       gender,
            "geography":    geography,
            "active_member":active,
            "occupation":   occupation,
        })
    return records

DUMMY_CUSTOMERS = _gen_customers(100)   # shared in-memory list

# ─────────────────────────────────────────────
#  MONGODB CONNECTION  (optional — falls back to DUMMY_CUSTOMERS)
# ─────────────────────────────────────────────
try:
    import pymongo
    _mongo_client = pymongo.MongoClient(
        "mongodb://localhost:27017/",
        # serverSelectionTimeoutMS=2000
    )
    _mongo_client.admin.command("ping")
    _mongo_db         = _mongo_client["finguard"]
    _mongo_collection = _mongo_db["customers"]

    # Seed the collection with dummy data if it is empty
    if _mongo_collection.count_documents({}) == 0:
        _mongo_collection.insert_many(DUMMY_CUSTOMERS)
        print("[MongoDB] Seeded 100 dummy customers")

    MONGO_CONNECTED = True
    print("[MongoDB] Connected successfully")
except Exception as _e:
    _mongo_client     = None
    _mongo_db         = None
    _mongo_collection = None
    MONGO_CONNECTED   = False
    print(f"[MongoDB] Not connected — using in-memory dummy data: {_e}")

# ─────────────────────────────────────────────
#  THEME  
# ─────────────────────────────────────────────
BG      = "#0b0e1a"
PANEL   = "#111827"
CARD    = "#1a2235"
BORDER  = "#1e2a3a"
BORDER2 = "#2a3d55"
TEXT    = "#ffffff"
MUTED   = "#8b9bb4"
ACCENT  = "#1D9E75"
DANGER  = "#ef4444"
WARNING = "#f59e0b"
SUCCESS = "#1D9E75"
INFO    = "#3b82f6"

FONT_SANS  = ("Segoe UI",  10)
FONT_MONO  = ("Consolas",  11, "bold")
FONT_LOGO  = ("Georgia",   20, "bold")
FONT_NUM   = ("Consolas",  38, "bold")
FONT_HEAD  = ("Segoe UI",   8, "bold")
FONT_SMALL = ("Segoe UI",   8)
FONT_TAG   = ("Consolas",   9, "bold")
FONT_BTN   = ("Segoe UI",  10, "bold")

# ─────────────────────────────────────────────
#  MODEL LOADING  (identical to original)
# ─────────────────────────────────────────────
ROOT_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(ROOT_DIR, "models")

def _load(name):
    path = os.path.join(MODEL_DIR, name)
    try:
        m = joblib.load(path)
        if hasattr(m, "get_params"):
            try: m.use_label_encoder = False
            except: pass
        return m
    except Exception:
        return None

credit_model = _load("credit_risk_model.pkl")
churn_model  = _load("churn_model.pkl")
fraud_model  = _load("fraud_model.pkl")
spend_model  = _load("spend_model_weights.pkl")


# ═══════════════════════════════════════════════════════════════
#  LOGIN PAGE
#  Shown first. Switches to dashboard only if credentials match.
# ═══════════════════════════════════════════════════════════════
class LoginPage(tk.Frame):
    """
    Full-screen login frame.

    Flow:
      1. User types Name + Password and clicks SIGN IN.
      2. _attempt_login() checks ADMINS dict (case-insensitive name).
      3. On success  → calls on_success(username) callback.
      4. On failure  → shows red error label; clears password field.
    """

    def __init__(self, parent, on_success):
        super().__init__(parent, bg=BG)
        self._on_success = on_success   # callback(username: str)
        self._build()

    # ── build the login UI ────────────────────
    def _build(self):
        # ── animated particle background ──
        self._particles_canvas = ParticleCanvas(self)
        self._particles_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # ── subtle glow spheres ──
        GlowSphere(self, "#1D9E75", size=380).place(x=-80, y=-80)
        GlowSphere(self, "#3b82f6", size=460).place(relx=1.0, rely=1.0,
                                                     anchor="se", x=80, y=80)

        # ── centre card ──
        card = tk.Frame(self,
                        bg=PANEL,
                        highlightbackground="#253045",
                        highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center", width=400, height=480)

        # ── logo ──
        logo_row = tk.Frame(card, bg=PANEL)
        logo_row.pack(pady=(40, 4))
        tk.Label(logo_row, text="Fin",   font=FONT_LOGO, fg=TEXT,   bg=PANEL).pack(side="left")
        tk.Label(logo_row, text="Guard", font=FONT_LOGO, fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Label(logo_row, text=" AI",   font=FONT_LOGO, fg=TEXT,   bg=PANEL).pack(side="left")

        # ── welcome text ──
        tk.Label(card,
                 text="Welcome, Admin",
                 font=("Segoe UI", 13, "bold"),
                 fg=TEXT, bg=PANEL).pack(pady=(6, 2))

        tk.Label(card,
                 text="Sign in to access the FinGuard Risk Engine",
                 font=("Segoe UI", 9),
                 fg=MUTED, bg=PANEL).pack(pady=(0, 28))

        # ── divider ──
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=30)

        inner = tk.Frame(card, bg=PANEL)
        inner.pack(fill="x", padx=30, pady=20)

        # ── Name field ──
        tk.Label(inner, text="ADMIN NAME",
                 font=FONT_HEAD, fg=MUTED, bg=PANEL).pack(anchor="w")
        self._name_var = tk.StringVar()
        name_entry = tk.Entry(inner,
                              textvariable=self._name_var,
                              font=("Consolas", 11),
                              fg=ACCENT, bg="#0d1220",
                              insertbackground=ACCENT,
                              relief="flat",
                              highlightbackground="#253045",
                              highlightcolor=ACCENT,
                              highlightthickness=1)
        name_entry.pack(fill="x", ipady=7, pady=(3, 14))
        name_entry.bind("<FocusIn>",  lambda e: name_entry.config(highlightbackground=ACCENT))
        name_entry.bind("<FocusOut>", lambda e: name_entry.config(highlightbackground="#253045"))

        # ── Password field ──
        tk.Label(inner, text="PASSWORD",
                 font=FONT_HEAD, fg=MUTED, bg=PANEL).pack(anchor="w")
        self._pass_var = tk.StringVar()
        self._pass_entry = tk.Entry(inner,
                                    textvariable=self._pass_var,
                                    show="●",                     # mask characters
                                    font=("Consolas", 11),
                                    fg=ACCENT, bg="#0d1220",
                                    insertbackground=ACCENT,
                                    relief="flat",
                                    highlightbackground="#253045",
                                    highlightcolor=ACCENT,
                                    highlightthickness=1)
        self._pass_entry.pack(fill="x", ipady=7, pady=(3, 6))
        self._pass_entry.bind("<FocusIn>",  lambda e: self._pass_entry.config(highlightbackground=ACCENT))
        self._pass_entry.bind("<FocusOut>", lambda e: self._pass_entry.config(highlightbackground="#253045"))
        # pressing Enter in password field triggers login
        self._pass_entry.bind("<Return>", lambda e: self._attempt_login())

        # ── error label (hidden until a failed attempt) ──
        self._err_label = tk.Label(inner, text="",
                                   font=("Segoe UI", 8, "bold"),
                                   fg=DANGER, bg=PANEL)
        self._err_label.pack(anchor="w", pady=(2, 0))

        # ── sign-in button ──
        tk.Button(inner,
                  text="▶   SIGN IN",
                  command=self._attempt_login,
                  bg=ACCENT, fg=BG,
                  font=FONT_BTN,
                  relief="flat", bd=0,
                  activebackground="#148560",
                  activeforeground=BG,
                  cursor="hand2"
                  ).pack(fill="x", ipady=10, pady=(14, 0))

        # ── hint at bottom ──
        tk.Label(card,
                 text="Authorised personnel only",
                 font=("Segoe UI", 8),
                 fg="#2a3d55", bg=PANEL).pack(side="bottom", pady=16)

    # ── credential check ─────────────────────
    def _attempt_login(self):
        """
        Compare entered name (lowercase) and password against ADMINS dict.
        Success → hide login, show dashboard.
        Failure → show error message, clear password.
        """
        sound_click()   # click sound on every attempt
        name     = self._name_var.get().strip().lower()
        password = self._pass_var.get().strip()

        if name in ADMINS and ADMINS[name] == password:
            # ── SUCCESS ──
            sound_success()
            self._err_label.config(text="")
            self._on_success(self._name_var.get().strip())   # pass display name
        else:
            # ── FAILURE ──
            sound_error()
            if name not in ADMINS:
                msg = f"'{self._name_var.get().strip()}' is not a registered admin. Login failed."
            else:
                msg = "Incorrect password. Please try again."
            self._err_label.config(text=msg)
            self._pass_var.set("")          # clear password field only
            self._pass_entry.focus_set()


# ═══════════════════════════════════════════════════════════════
#  HISTORY PANEL
#  Tracks every customer loaded/analysed during the current session.
# ═══════════════════════════════════════════════════════════════
class HistoryPanel(tk.Frame):
    """
    A scrollable list of every customer record that was analysed.
    Each entry shows: time, customer ID, name, and the four risk scores.

    Usage:
        panel.add_entry(rec, scores)
            rec    — the customer dict from the DB
            scores — dict {"credit":x,"fraud":x,"churn":x,"spend":x}
    """

    def __init__(self, parent, **kw):
        super().__init__(parent,
                         bg=CARD,
                         highlightbackground=BORDER,
                         highlightthickness=1, **kw)
        self._entries = []   # list of (timestamp, rec, scores)

        # ── header ──
        header = tk.Frame(self, bg=CARD)
        header.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(header, text="SESSION HISTORY",
                 font=FONT_HEAD, fg=MUTED, bg=CARD).pack(side="left")
        # clear button
        tk.Button(header, text="CLEAR",
                  command=lambda: [sound_click(), self._clear()],
                  bg=CARD, fg=MUTED,
                  font=("Segoe UI", 7, "bold"),
                  relief="flat", bd=0,
                  activebackground="#0d1220",
                  cursor="hand2"
                  ).pack(side="right")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── scrollable body ──
        container = tk.Frame(self, bg=CARD)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=CARD,
                                 highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._body = tk.Frame(self._canvas, bg=CARD)
        self._win  = self._canvas.create_window(
            (0, 0), window=self._body, anchor="nw")

        self._body.bind("<Configure>", self._on_configure)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # mousewheel scroll — only active when mouse is inside panel
        self._canvas.bind("<Enter>", lambda e: self._canvas.bind_all("<MouseWheel>", self._on_wheel))
        self._canvas.bind("<Leave>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

        self._placeholder()

    # ── scroll helpers ────────────────────────
    def _on_configure(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        # stretch inner frame to fill canvas width so rows fill horizontally
        self._canvas.itemconfig(self._win, width=e.width)

    def _on_wheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    # ── placeholder when empty ────────────────
    def _placeholder(self):
        self._ph = tk.Label(self._body,
                            text="No analyses yet this session.",
                            font=("Segoe UI", 9), fg=MUTED, bg=CARD)
        self._ph.pack(pady=20, padx=16, anchor="w")

    # ── add a new history row ─────────────────
    def add_entry(self, rec, scores):
        """
        Called after every successful analysis.
        Adds one compact row to the top of the history list.
        """
        # remove placeholder on first real entry
        if hasattr(self, "_ph") and self._ph.winfo_exists():
            self._ph.destroy()

        ts = datetime.datetime.now().strftime("%H:%M:%S")

        row = tk.Frame(self._body,
                       bg="#0d1220",
                       highlightbackground=BORDER,
                       highlightthickness=1)
        row.pack(fill="x", padx=8, pady=3, ipady=4)

        # ── left: time + name ──
        left = tk.Frame(row, bg="#0d1220")
        left.pack(side="left", padx=10)
        tk.Label(left, text=ts,
                 font=("Consolas", 8), fg=MUTED, bg="#0d1220").pack(anchor="w")
        tk.Label(left,
                 text=f"{rec.get('customer_id','?')}  {rec.get('name','Unknown')}",
                 font=("Segoe UI", 9, "bold"), fg=TEXT, bg="#0d1220").pack(anchor="w")
        tk.Label(left,
                 text=f"Age {rec.get('age','?')}  |  {rec.get('geography','?')}",
                 font=("Segoe UI", 8), fg=MUTED, bg="#0d1220").pack(anchor="w")

        # ── right: four mini badges ──
        right = tk.Frame(row, bg="#0d1220")
        right.pack(side="right", padx=10)
        for label, key in [("CR","credit"),("FR","fraud"),("CH","churn"),("SP","spend")]:
            val   = scores.get(key, 0)
            color = SUCCESS if val < 35 else (WARNING if val < 65 else DANGER)
            badge = tk.Frame(right, bg=color)
            badge.pack(side="left", padx=2)
            tk.Label(badge,
                     text=f"{label} {val:.0f}%",
                     font=("Consolas", 7, "bold"),
                     fg=BG, bg=color).pack(padx=4, pady=2)

        # keep internal record for potential future export
        self._entries.append({"time": ts, "customer": rec, "scores": scores})

        # scroll to top so newest entry is visible
        self._canvas.after(50, lambda: self._canvas.yview_moveto(0))

    # ── clear all history ─────────────────────
    def _clear(self):
        for w in self._body.winfo_children():
            w.destroy()
        self._entries = []
        self._placeholder()


# ─────────────────────────────────────────────
#  PARTICLE CANVAS  
# ─────────────────────────────────────────────
class ParticleCanvas(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self._particles = []
        self._running   = True
        self.bind("<Configure>", self._on_resize)
        self.after(500, self._init_particles)

    def _on_resize(self, e):
        self.canvas_w = e.width
        self.canvas_h = e.height

    def _init_particles(self):
        try:
            self.winfo_exists()
        except Exception:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        self.canvas_w = w if w > 1 else 1200
        self.canvas_h = h if h > 1 else 800
        self._particles = []
        for _ in range(55):
            x  = random.uniform(0, self.canvas_w)
            y  = random.uniform(0, self.canvas_h)
            vx = random.uniform(-0.4, 0.4)
            vy = random.uniform(-0.4, 0.4)
            r  = random.uniform(1, 2.5)
            self._particles.append([x, y, vx, vy, r])
        self._tick()

    def _tick(self):
        if not self._running:
            return
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        self.delete("particle")
        w, h = self.canvas_w, self.canvas_h
        pts  = self._particles
        for p in pts:
            p[0] += p[2];  p[1] += p[3]
            if p[0] < 0: p[0] = w
            if p[0] > w: p[0] = 0
            if p[1] < 0: p[1] = h
            if p[1] > h: p[1] = 0
        for i, a in enumerate(pts):
            for b in pts[i+1:]:
                dist = math.hypot(a[0]-b[0], a[1]-b[1])
                if dist < 140:
                    alpha = int(12 * (1 - dist/140))
                    col   = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
                    self.create_line(a[0], a[1], b[0], b[1],
                                     fill=col, tags="particle")
        for p in pts:
            x, y, r = p[0], p[1], p[4]
            self.create_oval(x-r, y-r, x+r, y+r,
                             fill="#1a1a2a", outline="#1a2535",
                             tags="particle")
        self.after(30, self._tick)

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────
#  GLOW SPHERE  
# ─────────────────────────────────────────────
class GlowSphere(tk.Canvas):
    def __init__(self, parent, color_inner, size=340, **kw):
        super().__init__(parent, width=size, height=size,
                         bg=BG, highlightthickness=0, **kw)
        steps = 18
        r0    = size // 2
        for i in range(steps, 0, -1):
            ratio = i / steps
            r     = int(r0 * ratio)
            ci    = self._blend(color_inner, BG, ratio)
            self.create_oval(r0-r, r0-r, r0+r, r0+r, fill=ci, outline="")

    def _blend(self, hex1, hex2, t):
        h1 = hex1.lstrip("#"); h2 = hex2.lstrip("#")
        r = int(int(h1[0:2],16)*(1-t) + int(h2[0:2],16)*t)
        g = int(int(h1[2:4],16)*(1-t) + int(h2[2:4],16)*t)
        b = int(int(h1[4:6],16)*(1-t) + int(h2[4:6],16)*t)
        return f"#{r:02x}{g:02x}{b:02x}"


# ─────────────────────────────────────────────
#  GLASS FRAME  
# ─────────────────────────────────────────────
class GlassFrame(tk.Frame):
    def __init__(self, parent, radius=14, **kw):
        kw.setdefault("bg", "#111827")
        kw.setdefault("highlightbackground", "#253045")
        kw.setdefault("highlightthickness", 1)
        super().__init__(parent, **kw)


# ─────────────────────────────────────────────
#  GLOW BUTTON 
# ─────────────────────────────────────────────
class GlowButton(tk.Frame):
    def __init__(self, parent, text, command=None,
                 primary=True, btn_width=240, btn_height=40, **kw):
        bg_parent = parent.cget("bg") if hasattr(parent, "cget") else PANEL
        super().__init__(parent, bg=bg_parent)
        self._cmd     = command
        self._primary = primary
        self._normal  = ACCENT     if primary else CARD
        self._hover   = "#17a874"  if primary else "#1f2d45"
        self._press   = "#148560"  if primary else "#151e2e"
        self._fg_col  = BG         if primary else MUTED
        self._fg_hov  = BG         if primary else "#aabbcc"
        fnt = FONT_BTN if primary else ("Segoe UI", 9, "bold")
        self._btn = tk.Button(
            self, text=text, command=command,
            bg=self._normal, fg=self._fg_col,
            font=fnt, relief="flat", bd=0, cursor="hand2",
            activebackground=self._press,
            activeforeground=BG if primary else "#ffffff",
            padx=12, pady=0)
        self._btn.pack(fill="both", expand=True, ipady=8 if primary else 6)
        self._btn.bind("<Enter>",           self._enter)
        self._btn.bind("<Leave>",           self._leave)
        self._btn.bind("<Button-1>",        self._press_ev)
        self._btn.bind("<ButtonRelease-1>", self._release_ev)

    def _enter(self, e):    self._btn.config(bg=self._hover,  fg=self._fg_hov)
    def _leave(self, e):    self._btn.config(bg=self._normal, fg=self._fg_col)
    def _press_ev(self, e): self._btn.config(bg=self._press)
    def _release_ev(self, e):
        self._btn.config(bg=self._hover)
        if self._cmd: self._cmd()


# ─────────────────────────────────────────────
#  METRIC CARD
# ─────────────────────────────────────────────
class MetricCard(tk.Frame):
    def __init__(self, parent, title, **kw):
        super().__init__(parent, bg=CARD,
                         highlightbackground="#1e2a3a",
                         highlightthickness=1, **kw)
        self._pct = 0; self._bar_w = 0
        tk.Label(self, text=title.upper(),
                 font=FONT_HEAD, fg=MUTED, bg=CARD).pack(anchor="w", padx=20, pady=(18,0))
        self._val = tk.Label(self, text="0%", font=FONT_NUM, fg=MUTED, bg=CARD)
        self._val.pack(anchor="w", padx=20, pady=(2,0))
        track = tk.Frame(self, bg="#0a0d16", height=6)
        track.pack(fill="x", padx=20, pady=(6,0))
        track.pack_propagate(False)
        self._bar = tk.Frame(track, bg=SUCCESS, height=6)
        self._bar.place(x=0, y=0, relheight=1, width=0)
        self._track = track
        self._tag = tk.Label(self, text="READY", font=FONT_TAG, fg=MUTED, bg=CARD)
        self._tag.pack(anchor="w", padx=20, pady=(8,18))
        self.bind("<Configure>", self._resize)

    def _resize(self, e):
        self._bar_w = max(0, e.width-40)
        self._set_bar_px(self._pct)

    def _set_bar_px(self, pct):
        px = int(self._bar_w * pct / 100)
        self._bar.place(x=0, y=0, relheight=1, width=max(0, px))

    def update(self, pct, tag, color):
        self._pct = pct
        self._val.config(text=f"{pct:.0f}%", fg=color)
        self._tag.config(text=tag,           fg=color)
        self._bar.config(bg=color)
        self._anim(0, pct)
        # ── subtle border flash: briefly highlight card border on update ──
        self._flash_border(color, steps=6)

    def _flash_border(self, color, steps):
        """Briefly brightens the card border to the result colour then fades."""
        if steps <= 0:
            self.config(highlightbackground="#1e2a3a")
            return
        self.config(highlightbackground=color)
        self.after(60, lambda: self._flash_border("#1e2a3a" if steps == 1 else color, steps - 1))

    def _anim(self, cur, target):
        if cur >= target: return
        nxt = min(cur+2, target)
        self._set_bar_px(nxt)
        self.after(14, lambda: self._anim(nxt, target))


# ─────────────────────────────────────────────
#  SHAP PANEL
# ─────────────────────────────────────────────
class SHAPPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CARD,
                         highlightbackground="#1e2a3a",
                         highlightthickness=1, **kw)
        tk.Label(self, text="SHAP — FEATURE IMPACT",
                 font=FONT_HEAD, fg=MUTED, bg=CARD).pack(anchor="w", padx=20, pady=(18,10))
        self._body = tk.Frame(self, bg=CARD)
        self._body.pack(fill="both", expand=True, padx=20, pady=(0,16))

    def render(self, rows):
        for w in self._body.winfo_children(): w.destroy()
        for label, pct, color in rows:
            row = tk.Frame(self._body, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=("Segoe UI",9),
                     fg=TEXT, bg=CARD, width=20, anchor="w").pack(side="left")
            track = tk.Frame(row, bg="#141e2e", height=8)
            track.pack(side="left", fill="x", expand=True, padx=(6,8))
            bar = tk.Frame(track, bg=color, height=8)
            bar.place(x=0, y=0, relheight=1, relwidth=max(0, min(1, pct/100)))
            tk.Label(row, text=f"{pct:.0f}",
                     font=("Consolas",8), fg=MUTED, bg=CARD, width=3).pack(side="left")


# ─────────────────────────────────────────────
#  EXPLAIN PANEL  
# ─────────────────────────────────────────────
class ExplainPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CARD,
                         highlightbackground="#1e2a3a",
                         highlightthickness=1, **kw)

        # ── header row ──
        tk.Label(self, text="AI EXPLAINABILITY",
                 font=FONT_HEAD, fg=MUTED, bg=CARD).pack(anchor="w", padx=20, pady=(14,6))
        tk.Frame(self, bg="#1e2a3a", height=1).pack(fill="x")

        # ── scrollable container ──
        container = tk.Frame(self, bg=CARD)
        container.pack(fill="both", expand=True, padx=0, pady=0)

        self._canvas = tk.Canvas(container, bg=CARD, highlightthickness=0)
        scrollbar    = tk.Scrollbar(container, orient="vertical",
                                    command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        # only show scrollbar when needed — pack it last so it can be hidden
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # inner frame that holds the actual reason rows
        self._body = tk.Frame(self._canvas, bg=CARD)
        self._win  = self._canvas.create_window((0, 0), window=self._body, anchor="nw")

        self._body.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # mouse-wheel scroll anywhere inside the panel
        self._canvas.bind("<Enter>", self._bind_scroll)
        self._canvas.bind("<Leave>", self._unbind_scroll)

        self._placeholder()

    def _on_frame_configure(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        # make inner frame match canvas width so rows fill horizontally
        self._canvas.itemconfig(self._win, width=e.width)

    def _bind_scroll(self, e):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_scroll(self, e):
        self._canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _placeholder(self):
        tk.Label(self._body,
                 text="Run analysis to see\nAI-generated explanations.",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD,
                 justify="left").pack(anchor="w", pady=16, padx=16)

    def render(self, reasons, suggestion=None):
        # clear previous content
        for w in self._body.winfo_children():
            w.destroy()

        if suggestion:
            # ── final suggestion row ──
            box = tk.Frame(self._body, bg="#1a2235",
                           highlightbackground=suggestion["color"], highlightthickness=1)
            box.pack(fill="x", pady=(8, 12), padx=8)
            tk.Label(box, text=f"AI SUGGESTION:  {suggestion['text']}",
                     font=("Segoe UI", 10, "bold"),
                     fg=suggestion["color"], bg="#1a2235").pack(pady=12)

        for icon, color, text in reasons:
            row = tk.Frame(self._body, bg="#0d1220",
                           highlightbackground="#1e2a3a", highlightthickness=1)
            row.pack(fill="x", pady=3, padx=8)

            # coloured icon badge
            badge = tk.Frame(row, bg=color, width=26, height=26)
            badge.pack(side="left", padx=(10, 8), pady=8)
            badge.pack_propagate(False)
            tk.Label(badge, text=icon, font=("Segoe UI", 10, "bold"),
                     fg=BG, bg=color).place(relx=0.5, rely=0.5, anchor="center")

            # reason text — wraplength set dynamically to panel width minus badges
            tk.Label(row, text=text, font=("Segoe UI", 9),
                     fg=TEXT, bg="#0d1220",
                     wraplength=240, justify="left",
                     anchor="w").pack(side="left", fill="x", expand=True,
                                      pady=6, padx=(0, 8))

        # scroll back to top after re-render
        self._canvas.after(30, lambda: self._canvas.yview_moveto(0))


# ─────────────────────────────────────────────
#  PULSE DOT  
# ─────────────────────────────────────────────
class PulseDot(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, width=14, height=14,
                         bg=PANEL, highlightthickness=0)
        self._phase = 0
        self._tick()

    def _tick(self):
        self.delete("all")
        r = 5; cx = 7
        glow = int(abs(math.sin(self._phase)) * 60)
        gcol = f"#{glow:02x}{glow+158:02x}{glow+117:02x}"
        gr   = r + int(abs(math.sin(self._phase)) * 4)
        self.create_oval(cx-gr, 7-gr, cx+gr, 7+gr, fill=gcol, outline="")
        self.create_oval(cx-r,  7-r,  cx+r,  7+r,  fill=ACCENT, outline="")
        self._phase += 0.08
        self.after(50, self._tick)


# ─────────────────────────────────────────────
#  DECISION LOG PANEL
#  Tracks Admin approvals/rejections.
# ─────────────────────────────────────────────
class DecisionPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=CARD,
                         highlightbackground=BORDER,
                         highlightthickness=1, **kw)
        
        header = tk.Frame(self, bg=CARD)
        header.pack(fill="x", padx=16, pady=(14, 6))
        tk.Label(header, text="DECISION LOG",
                 font=FONT_HEAD, fg=MUTED, bg=CARD).pack(side="left")
        
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        container = tk.Frame(self, bg=CARD)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=CARD, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._body = tk.Frame(self._canvas, bg=CARD)
        self._win  = self._canvas.create_window((0, 0), window=self._body, anchor="nw")

        self._body.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._win, width=e.width))

        self._placeholder()

    def _placeholder(self):
        self._ph = tk.Label(self._body, text="No decisions logged yet.",
                            font=("Segoe UI", 9), fg=MUTED, bg=CARD)
        self._ph.pack(pady=20, padx=16, anchor="w")

    def add_decision(self, rec, decision, color):
        if hasattr(self, "_ph") and self._ph.winfo_exists():
            self._ph.destroy()

        ts = datetime.datetime.now().strftime("%H:%M:%S")
        row = tk.Frame(self._body, bg="#0d1220", highlightbackground=color, highlightthickness=1)
        row.pack(fill="x", padx=8, pady=3, ipady=4)

        left = tk.Frame(row, bg="#0d1220")
        left.pack(side="left", padx=10)
        tk.Label(left, text=f"{ts}  |  {rec.get('customer_id','?')}", 
                 font=("Consolas", 8), fg=MUTED, bg="#0d1220").pack(anchor="w")
        tk.Label(left, text=rec.get('name','Unknown'),
                 font=("Segoe UI", 9, "bold"), fg=TEXT, bg="#0d1220").pack(anchor="w")

        right = tk.Frame(row, bg=color)
        right.pack(side="right", padx=10, pady=5)
        tk.Label(right, text=decision.upper(), font=("Segoe UI", 8, "bold"),
                 fg=BG, bg=color, padx=8).pack()
        
        self._canvas.after(50, lambda: self._canvas.yview_moveto(0))


# ═══════════════════════════════════════════════════════════════
#  MAIN DASHBOARD  
# ═══════════════════════════════════════════════════════════════
class FinGuardApp:
    """
    Original dashboard, extended with:
      • admin_name  — displayed in the top-bar
      • HistoryPanel — injected below ExplainPanel
      • _last_rec   — stores the last-loaded customer for history logging
      • _update_ui  — calls history.add_entry() after every analysis
    """

    def __init__(self, root: tk.Tk, admin_name: str = "Admin", on_logout=None):
        self.root        = root
        self._admin_name = admin_name
        self._on_logout  = on_logout    # ← NEW: callback for sign out
        self._last_rec   = {}
        root.title("FinGuard AI — Intelligent Financial Risk Engine")
        root.geometry("1200x800")
        root.minsize(1050, 700)
        root.configure(bg=BG)
        root.resizable(True, True)
        self._build()

    # ── BUILD ────────────────────────────────
    def _build(self):
        # particle canvas sits at the very back — same class as the login page
        self._particles = ParticleCanvas(self.root)
        self._particles.place(x=0, y=0, relwidth=1, relheight=1)

        # glow spheres sit above particles
        GlowSphere(self.root, "#1D9E75", size=380).place(x=-80, y=-80)
        GlowSphere(self.root, "#3b82f6", size=460).place(
            relx=1.0, rely=1.0, anchor="se", x=80, y=80)

        # foreground frame — bg=BG matches the canvas bg so panels look
        # like they're floating on top of the particle layer
        self._fg = tk.Frame(self.root, bg=BG)
        self._fg.place(x=0, y=0, relwidth=1, relheight=1)

        # IMPORTANT: lower the fg frame so particles render above glow spheres
        # but below the panel widgets — order: particles → spheres → fg widgets
        self._fg.lift()

        self._build_topbar()
        self._build_dashboard()

    # ── TOP BAR  (shows logged-in admin name) ─
    def _build_topbar(self):
        bar = GlassFrame(self._fg, height=66)
        bar.pack(fill="x", padx=18, pady=(16,0))
        bar.pack_propagate(False)

        logo = tk.Frame(bar, bg=PANEL)
        logo.pack(side="left", padx=24)
        tk.Label(logo, text="Fin",   font=FONT_LOGO, fg=TEXT,   bg=PANEL).pack(side="left")
        tk.Label(logo, text="Guard", font=FONT_LOGO, fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Label(logo, text=" AI",   font=FONT_LOGO, fg=TEXT,   bg=PANEL).pack(side="left")

        right = tk.Frame(bar, bg=PANEL)
        right.pack(side="right", padx=24)

        # ── live clock — ticks every second, sits far right ──
        self._clock_lbl = tk.Label(right,
                                   text="",
                                   font=("Consolas", 9), fg="#2a4a3a", bg=PANEL)
        self._clock_lbl.pack(side="right", padx=(16, 0))
        self._tick_clock()

        # ── SIGN OUT button ──
        tk.Button(right,
                  text="[ SIGN OUT ]",
                  command=self._logout,
                  bg=PANEL, fg=DANGER,
                  font=("Segoe UI", 8, "bold"),
                  relief="flat", bd=0,
                  activebackground=PANEL,
                  activeforeground="#ff8888",
                  cursor="hand2").pack(side="right", padx=(12, 0))

        # ── NEW: show admin name next to pulse dot ──
        tk.Label(right,
                 text=f"Signed in as  {self._admin_name}",
                 font=("Segoe UI", 8), fg=MUTED, bg=PANEL).pack(side="right", padx=(10,0))
        PulseDot(right).pack(side="left", padx=(0,6))
        tk.Label(right, text="Local AI Engine Active",
                 font=("Segoe UI",9), fg=MUTED, bg=PANEL).pack(side="left")

    # ── live clock helper ─────────────────────
    def _tick_clock(self):
        """Updates the topbar clock label every second."""
        now = datetime.datetime.now().strftime("%Y-%m-%d   %H:%M:%S")
        try:
            self._clock_lbl.config(text=now)
            self.root.after(1000, self._tick_clock)
        except Exception:
            pass   # widget destroyed — stop ticking

    def _logout(self):
        """Clean up and return to login screen."""
        if messagebox.askyesno("Sign Out", "Are you sure you want to sign out?"):
            sound_click()
            self._particles.stop()
            for w in self.root.winfo_children():
                w.destroy()
            if self._on_logout:
                self._on_logout()

    # ── DASHBOARD LAYOUT ─────────────────────
    def _build_dashboard(self):
        # bg matches root bg — panels are opaque cards, gaps are transparent
        # so the particle animation behind shows through the spacing
        layout = tk.Frame(self._fg, bg=BG)
        layout.pack(fill="both", expand=True, padx=18, pady=14)
        self._build_sidebar(layout)
        self._build_main(layout)

    # ── SIDEBAR  (uses DUMMY_CUSTOMERS for DB load) ──
    def _build_sidebar(self, parent):
        side = GlassFrame(parent, width=310)
        side.pack(side="left", fill="y", padx=(0,18))
        side.pack_propagate(False)

        btn_area = tk.Frame(side, bg=PANEL)
        btn_area.pack(side="bottom", fill="x", padx=16, pady=12)

        tk.Button(btn_area, text="⬡   LOAD FROM DATABASE",
                  command=lambda: [sound_click(), self._open_db_selector()],
                  bg=CARD, fg=ACCENT,
                  font=("Segoe UI",9,"bold"),
                  relief="flat", bd=0,
                  activebackground="#1f2d45",
                  activeforeground=ACCENT,
                  cursor="hand2").pack(fill="x", ipady=7, pady=(0,8))

        tk.Button(btn_area, text="ANALYZE RISK",
                  command=lambda: [sound_analyze(), self._run_analysis()],
                  bg=ACCENT, fg=BG,
                  font=("Segoe UI",10,"bold"),
                  relief="flat", bd=0,
                  activebackground="#148560",
                  activeforeground=BG,
                  cursor="hand2").pack(fill="x", ipady=10, pady=(0,12))

        dec_row = tk.Frame(btn_area, bg=PANEL)
        dec_row.pack(fill="x")

        tk.Button(dec_row, text="APPROVE",
                  command=lambda: self._finalize_decision("Approved", SUCCESS),
                  bg="#0d1220", fg=SUCCESS,
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=1, highlightbackground=SUCCESS,
                  highlightthickness=1, cursor="hand2").pack(side="left", fill="x", expand=True, padx=(0,4), ipady=6)

        tk.Button(dec_row, text="REJECT",
                  command=lambda: self._finalize_decision("Rejected", DANGER),
                  bg="#0d1220", fg=DANGER,
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=1, highlightbackground=DANGER,
                  highlightthickness=1, cursor="hand2").pack(side="right", fill="x", expand=True, padx=(4,0), ipady=6)

        tk.Label(side, text="CUSTOMER PROFILE",
                 font=FONT_HEAD, fg=MUTED, bg=PANEL).pack(anchor="w", padx=20, pady=(18,10))
        tk.Frame(side, bg="#1e2a3a", height=1).pack(fill="x")

        inner = tk.Frame(side, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=16, pady=(10,0))

        self._entries = {}
        grid = tk.Frame(inner, bg=PANEL)
        grid.pack(fill="x")

        pairs = [
            ("Age","34"), ("Income","5200"), ("Debt Ratio","0.74"),
            ("Loan Amount","18500"), ("Credit Score","620"),
            ("Tenure (yrs)","2"), ("Num Products","1"), ("Balance","45000"),
        ]
        for i, (label, default) in enumerate(pairs):
            r, c = divmod(i, 2)
            cell = tk.Frame(grid, bg=PANEL)
            cell.grid(row=r, column=c, padx=(0,8 if c==0 else 0), pady=4, sticky="ew")
            grid.columnconfigure(c, weight=1)
            tk.Label(cell, text=label, font=("Segoe UI",8), fg=MUTED, bg=PANEL).pack(anchor="w")
            var = tk.StringVar(value=default)
            ent = tk.Entry(cell, textvariable=var,
                           font=("Consolas",10), fg=ACCENT, bg="#0d1220",
                           insertbackground=ACCENT, relief="flat",
                           highlightbackground="#253045", highlightcolor=ACCENT,
                           highlightthickness=1)
            ent.pack(fill="x", ipady=4)
            self._entries[label] = var
            ent.bind("<FocusIn>",  lambda e, w=ent: w.config(highlightbackground=ACCENT))
            ent.bind("<FocusOut>", lambda e, w=ent: w.config(highlightbackground="#253045"))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("FG.TCombobox",
                         fieldbackground="#0d1220", background="#0d1220",
                         foreground=ACCENT, bordercolor="#253045",
                         arrowcolor=ACCENT, selectbackground="#0d1220",
                         selectforeground=ACCENT, padding=4)

        for label, values, attr in [
            ("Gender",        ["Male","Female"],             "_gender"),
            ("Geography",     ["France","Germany","Spain"],  "_geo"),
            ("Active Member", ["Yes","No"],                  "_active"),
        ]:
            tk.Label(inner, text=label, font=("Segoe UI",8),
                     fg=MUTED, bg=PANEL).pack(anchor="w", pady=(6,0))
            cb = ttk.Combobox(inner, values=values, state="readonly", style="FG.TCombobox")
            cb.set(values[0])
            cb.pack(fill="x", pady=(2,0))
            setattr(self, attr, cb)

    # ── DB SELECTOR  (now uses 100 dummy customers) ──
    def _open_db_selector(self):
        """
        Opens a popup listing all 100 customers.
        Pulls from MongoDB if connected, otherwise uses in-memory DUMMY_CUSTOMERS.
        Admins can search by name or ID to filter the list quickly.
        """
        # decide data source
        # We start with our 100 core dummy customers.
        records = list(DUMMY_CUSTOMERS)

        if MONGO_CONNECTED:
            try:
                db_records = list(_mongo_collection.find({}, {"_id": 0}))
                # Combine both lists so we have the dummy ones PLUS the DB ones
                # Use a dict to avoid duplicate IDs if some dummy ones were actually saved to DB
                combined = {r["customer_id"]: r for r in records}
                for r in db_records:
                    if "customer_id" in r:
                        combined[r["customer_id"]] = r
                records = list(combined.values())
            except Exception:
                pass

        if not records:
            messagebox.showinfo("Empty", "No customers found.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Select Customer from Database")
        popup.geometry("520x560")
        popup.configure(bg=PANEL)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="SELECT CUSTOMER by name or ID",
                 font=FONT_HEAD, fg=MUTED, bg=PANEL).pack(anchor="w", padx=20, pady=(18,6))

        # ── search box ──
        search_var = tk.StringVar()
        search_entry = tk.Entry(popup, textvariable=search_var,
                                font=("Consolas",10), fg=ACCENT, bg="#0d1220",
                                insertbackground=ACCENT, relief="flat",
                                highlightbackground="#253045", highlightcolor=ACCENT,
                                highlightthickness=1)
        search_entry.pack(fill="x", padx=20, ipady=5, pady=(0,8))
        tk.Label(popup, text="Type to filter by name or ID",
                 font=("Segoe UI",7), fg=MUTED, bg=PANEL).pack(anchor="w", padx=20)

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x", pady=(6,0))

        list_frame = tk.Frame(popup, bg=PANEL)
        list_frame.pack(fill="both", expand=True, padx=16, pady=8)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame, bg=CARD, fg=TEXT,
                             font=("Consolas",9),
                             selectbackground=ACCENT, selectforeground=BG,
                             activestyle="none", highlightthickness=0,
                             relief="flat", yscrollcommand=scrollbar.set)
        listbox.pack(fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        # keep a filtered list so listbox index → record is always correct
        filtered = list(records)

        def _refresh_list(*_):
            """Re-populate listbox whenever the search text changes."""
            q = search_var.get().strip().lower()
            filtered.clear()
            for rec in records:
                haystack = (str(rec.get("customer_id","")) +
                            rec.get("name","")).lower()
                if q in haystack:
                    filtered.append(rec)
            listbox.delete(0, tk.END)
            for i, rec in enumerate(filtered):
                cid  = rec.get("customer_id","-")
                name = rec.get("name","Unknown")
                age  = rec.get("age","?")
                geo  = rec.get("geography","?")
                
                # Check for existing decision
                status = ADMIN_DECISIONS.get(cid)
                indicator = "  ● " if status else "    "  # Circle for decided ones
                
                listbox.insert(tk.END,
                    f"{indicator}{cid}   {name:<22}  Age {age}   {geo}")
                
                # Color the circle if a decision was made
                if status == "Approved":
                    listbox.itemconfig(tk.END, fg=SUCCESS)
                elif status == "Rejected":
                    listbox.itemconfig(tk.END, fg=DANGER)

        _refresh_list()                         # populate immediately
        search_var.trace_add("write", _refresh_list)  # live filter

        preview = tk.Label(popup, text="Select a customer to preview",
                           font=("Segoe UI",8), fg=MUTED, bg=PANEL,
                           wraplength=480, justify="left")
        preview.pack(padx=20, pady=(0,6))

        def _on_select(e):
            idx = listbox.curselection()
            if not idx: return
            r = filtered[idx[0]]
            preview.config(
                text=(f"ID: {r.get('customer_id')}  |  Name: {r.get('name')}  |  "
                      f"Age: {r.get('age')}  |  Income: ${r.get('income'):,}  |  "
                      f"Debt: {r.get('debt_ratio')}  |  Score: {r.get('credit_score')}  |  "
                      f"Geo: {r.get('geography')}  |  Active: {r.get('active_member')}"),
                fg=ACCENT)

        listbox.bind("<<ListboxSelect>>", _on_select)

        def _load_selected():
            idx = listbox.curselection()
            if not idx:
                messagebox.showwarning("No Selection", "Please select a customer first.")
                return
            rec = filtered[idx[0]]
            popup.destroy()
            self._fill_from_db(rec)

        tk.Button(popup, text=" LOAD & ANALYZE",
                  command=lambda: [sound_confirm(), _load_selected()],
                  bg=ACCENT, fg=BG,
                  font=("Segoe UI",10,"bold"),
                  relief="flat", bd=0,
                  activebackground="#148560",
                  cursor="hand2").pack(fill="x", padx=16, ipady=10, pady=(0,16))

    def _finalize_decision(self, status, color):
        """Logs the final Admin decision for the current customer."""
        if not self._last_rec:
            messagebox.showwarning("No Selection", "Please load and analyze a customer first.")
            return
        
        cid = self._last_rec.get("customer_id")
        if not cid:
            messagebox.showwarning("Invalid Record", "This manual entry has no ID and cannot be logged.")
            return

        sound_confirm()
        # Save to persistent tracking
        ADMIN_DECISIONS[cid] = status
        # Save to UI log
        self._decision_log.add_decision(self._last_rec, status, color)
        messagebox.showinfo("Decision Saved", f"Customer {self._last_rec.get('name')} has been {status}.")

    def _fill_from_db(self, rec):
        """Fill sidebar fields from a DB record then auto-run analysis."""
        # ── NEW: remember this record for history logging ──
        self._last_rec = rec

        mapping = {
            "Age":          str(rec.get("age",          "")),
            "Income":       str(rec.get("income",       "")),
            "Debt Ratio":   str(rec.get("debt_ratio",   "")),
            "Loan Amount":  str(rec.get("loan_amount",  "")),
            "Credit Score": str(rec.get("credit_score", "")),
            "Tenure (yrs)": str(rec.get("tenure",       "")),
            "Num Products": str(rec.get("num_products", "")),
            "Balance":      str(rec.get("balance",      "")),
        }
        for field, val in mapping.items():
            if field in self._entries:
                self._entries[field].set(val)
        self._gender.set(rec.get("gender",         "Male"))
        self._geo.set(   rec.get("geography",      "France"))
        self._active.set(rec.get("active_member",  "Yes"))
        self._run_analysis()

    # ── MAIN RESULTS AREA  (history panel added) ──
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="right", fill="both", expand=True)

        # 4 metric cards
        cards_row = tk.Frame(main, bg=BG)
        cards_row.pack(fill="x", pady=(0,14))
        self._cards = {}
        for label, key in [
            ("Credit Risk","credit"), ("Fraud","fraud"),
            ("Churn","churn"),        ("Spend Forecast","spend"),
        ]:
            c = MetricCard(cards_row, label)
            c.pack(side="left", fill="both", expand=True, padx=(0,12))
            self._cards[key] = c
        list(cards_row.winfo_children())[-1].pack_configure(padx=0)

        # lower row: SHAP | Explain + History stacked
        lower = tk.Frame(main, bg=BG)
        lower.pack(fill="both", expand=True)

        self._shap = SHAPPanel(lower)
        self._shap.pack(side="left", fill="both", expand=True, padx=(0,14))

        right = tk.Frame(lower, bg=BG, width=420)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        # Explainability takes top ~40%
        self._explain = ExplainPanel(right)
        self._explain.pack(fill="both", expand=True, pady=(0,8))

        # History and Decision panels share the bottom ~60%
        lower_right = tk.Frame(right, bg=BG)
        lower_right.pack(fill="both", expand=True)

        self._history = HistoryPanel(lower_right)
        self._history.pack(side="left", fill="both", expand=True, padx=(0,4))

        self._decision_log = DecisionPanel(lower_right)
        self._decision_log.pack(side="right", fill="both", expand=True, padx=(4,0))

        # model badges
        badges = tk.Frame(right, bg=BG)
        badges.pack(fill="x", pady=(6,0))
        for name, col in [("XGBoost",ACCENT),("GBM","#3b82f6"),("LR",MUTED)]:
            b = tk.Frame(badges, bg=col)
            b.pack(side="left", padx=(0,6), pady=2)
            tk.Label(b, text=f"  {name}  ", font=FONT_TAG,
                     fg=BG, bg=col).pack()
        tk.Label(badges, text="Active models",
                 font=("Segoe UI",8), fg=MUTED, bg=BG).pack(side="left", padx=6)

    # ── ANALYSIS  (with CREATE functionality) ──────────
    def _run_analysis(self):
        """
        If a customer was loaded from DB, run analysis directly.
        Otherwise, prompt for customer name to create a new record.
        """
        # Check if a customer was loaded from the database
        if self._last_rec and self._last_rec.get("customer_id", "").startswith("CUS"):
            # Customer loaded from DB - just run analysis
            print(f"[ANALYSIS] Running analysis for DB customer: {self._last_rec.get('name')}")
            threading.Thread(target=self._analyze, daemon=True).start()
        else:
            # No customer loaded - prompt for name to create new record
            print("[ANALYSIS] No DB customer loaded. Prompting for name to create new record.")
            self._show_create_customer_dialog()

    def _show_create_customer_dialog(self):
        """Show dialog to get customer name for CREATE operation."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Customer Record")
        dialog.geometry("400x180")
        dialog.configure(bg=PANEL)
        dialog.resizable(False, False)
        dialog.grab_set()
        
        # Center the dialog on the screen
        dialog.transient(self.root)
        dialog.geometry("+%d+%d" % (
            self.root.winfo_x() + self.root.winfo_width()//2 - 200,
            self.root.winfo_y() + self.root.winfo_height()//2 - 90
        ))
        
        # Header
        header = tk.Frame(dialog, bg=PANEL)
        header.pack(fill="x", padx=16, pady=(16,8))
        tk.Label(header, text="📋 Create New Customer Record",
                 font=("Segoe UI", 12, "bold"), fg=TEXT, bg=PANEL).pack(anchor="w")
        tk.Label(header, text="Enter customer name to save this analysis:",
                 font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(4,0))
        
        # Input frame
        input_frame = tk.Frame(dialog, bg=PANEL)
        input_frame.pack(fill="x", padx=16, pady=(8,16))
        
        tk.Label(input_frame, text="Customer Name:",
                 font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(0,4))
        
        name_var = tk.StringVar()
        name_entry = tk.Entry(input_frame, textvariable=name_var,
                              font=("Consolas", 11), fg=ACCENT, bg="#0d1220",
                              insertbackground=ACCENT, relief="flat",
                              highlightbackground="#253045", highlightcolor=ACCENT,
                              highlightthickness=1)
        name_entry.pack(fill="x", ipady=6)
        name_entry.focus()
        
        # Button frame
        button_frame = tk.Frame(dialog, bg=PANEL)
        button_frame.pack(fill="x", padx=16, pady=(0,16))
        
        def on_add():
            customer_name = name_var.get().strip()
            if not customer_name:
                messagebox.showwarning("Empty Name", "Please enter a customer name.")
                return
            sound_confirm()
            dialog.destroy()
            # Now insert the record and run analysis
            self._create_and_analyze(customer_name)
        
        def on_cancel():
            sound_click()
            dialog.destroy()
        
        # Bind Enter key to add
        name_entry.bind("<Return>", lambda e: on_add())
        
        # Buttons
        tk.Button(button_frame, text="ADD & ANALYZE",
                  command=on_add,
                  bg=ACCENT, fg=BG, font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0, activebackground="#148560",
                  activeforeground=BG, cursor="hand2").pack(side="right", padx=(4,0), ipady=6)
        
        tk.Button(button_frame, text="CANCEL",
                  command=on_cancel,
                  bg="#2a3d55", fg=TEXT, font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0, activebackground="#3a4d65",
                  activeforeground=TEXT, cursor="hand2").pack(side="right", padx=(0,4), ipady=6)

    def _create_and_analyze(self, customer_name):
        """Insert new customer record into database, then run analysis."""
        try:
            # Validate inputs
            age = float(self._entries["Age"].get())
            income = float(self._entries["Income"].get())
            debt = float(self._entries["Debt Ratio"].get())
            loan = float(self._entries["Loan Amount"].get())
            score = float(self._entries["Credit Score"].get())
            tenure = float(self._entries["Tenure (yrs)"].get())
            prods = int(self._entries["Num Products"].get())
            bal = float(self._entries["Balance"].get())
            gender = self._gender.get()
            geo = self._geo.get()
            active = self._active.get()
        except ValueError as ve:
            messagebox.showerror("Input Error",
                "Please check all input fields contain valid numbers.")
            print(f"[CREATE] Validation error: {ve}")
            return
        
        # Generate a unique customer ID
        # Format: CUST followed by timestamp-based ID
        customer_id = f"CUST{int(time.time() * 1000) % 1000000:06d}"
        
        # Create record dict matching MongoDB schema
        new_record = {
            "customer_id": customer_id,
            "name": customer_name,
            "age": int(age),
            "income": income,
            "debt_ratio": debt,
            "loan_amount": loan,
            "credit_score": score,
            "tenure": int(tenure),
            "num_products": prods,
            "balance": bal,
            "gender": gender,
            "geography": geo,
            "active_member": active,
            "occupation": "Not Specified",
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        print(f"[CREATE] Preparing record: {new_record}")
        print(f"[CREATE] MONGO_CONNECTED: {MONGO_CONNECTED}")
        print(f"[CREATE] _mongo_collection: {_mongo_collection}")
        
        # Try to insert into MongoDB
        insert_success = False
        try:
            if MONGO_CONNECTED and _mongo_collection is not None:
                result = _mongo_collection.insert_one(new_record)
                print(f"[CREATE] Insert successful. ObjectId: {result.inserted_id}")
                messagebox.showinfo("✓ Record Created", 
                    f"Customer '{customer_name}'\nID: {customer_id}\n\n"
                    f"Saved to database ✓\n"
                    f"Now analyzing...")
                sound_success()
                insert_success = True
            else:
                print(f"[CREATE] MongoDB not available. MONGO_CONNECTED={MONGO_CONNECTED}, collection={_mongo_collection}")
                messagebox.showinfo("⚠ Analyzing Only",
                    f"Customer: {customer_name}\n\n"
                    f"Database connection unavailable.\n"
                    f"Proceeding with analysis only.")
                sound_error()
        except Exception as db_error:
            print(f"[CREATE] Insert error: {type(db_error).__name__}: {str(db_error)}")
            messagebox.showerror("Database Error",
                f"Insert failed: {str(db_error)}\n\n"
                f"Proceeding with analysis only.")
            sound_error()
        
        # Store record for history regardless of insert success
        self._last_rec = new_record
        print(f"[CREATE] Starting analysis for: {customer_name}")
        threading.Thread(target=self._analyze, daemon=True).start()

    def _analyze(self):
        try:
            age    = float(self._entries["Age"].get())
            income = float(self._entries["Income"].get())
            debt   = float(self._entries["Debt Ratio"].get())
            loan   = float(self._entries["Loan Amount"].get())
            score  = float(self._entries["Credit Score"].get())
            tenure = float(self._entries["Tenure (yrs)"].get())
            prods  = int(self._entries["Num Products"].get())
            bal    = float(self._entries["Balance"].get())
            gender = 1 if self._gender.get() == "Male" else 0
            geo_de = 1 if self._geo.get() == "Germany" else 0
            geo_sp = 1 if self._geo.get() == "Spain" else 0
            active = 1 if self._active.get() == "Yes" else 0
        except ValueError:
            messagebox.showerror("Input Error",
                "Please check all input fields contain valid numbers.")
            return

        res = {}

        try:
            if credit_model:
                f = np.array([[debt, income/12000, loan/50000, score/850,
                               age/80, tenure/30, bal/100000, prods, gender, active]])
                res["credit"] = float(credit_model.predict_proba(f)[0][1]) * 100
            else: raise ValueError
        except:
            res["credit"] = min(99, max(1, debt*60 + (loan/max(income,1))*20))

        try:
            if fraud_model:
                f = np.array([[loan, income, age, score, bal, tenure, prods, active]])
                res["fraud"] = float(fraud_model.predict_proba(f)[0][1]) * 100
            else: raise ValueError
        except:
            res["fraud"] = min(99, max(1, (loan/max(income,1))*15 + (1-active)*10))

        try:
            if churn_model:
                f = np.array([[score, age, tenure, bal, prods,
                               1, active, income, gender, geo_de, geo_sp]])
                res["churn"] = float(churn_model.predict_proba(f)[0][1]) * 100
            else: raise ValueError
        except:
            res["churn"] = min(99, max(1, (1-active)*40 + (1/max(prods,1))*30))

        try:
            if spend_model:
                f   = np.array([[income, age, bal, tenure, prods, score]])
                raw = float(spend_model.predict(f)[0])
                res["spend"] = min(99, max(1, (raw / max(income*0.6, 1)) * 50))
            else: raise ValueError
        except:
            res["spend"] = min(99, max(1, (income * 0.35) / 500))

        for k in res:
            res[k] = min(99, max(1, res[k]))

        self.root.after(0, lambda: self._update_ui(
            res, age, income, debt, loan, score, tenure, prods, bal, active))

    # ── UPDATE UI  (history logging added) ───
    def _color(self, p): return SUCCESS if p < 35 else (WARNING if p < 65 else DANGER)
    def _tag(self, p):   return "LOW RISK" if p < 35 else ("MEDIUM RISK" if p < 65 else "HIGH RISK")

    def _update_ui(self, res, age, income, debt, loan,
                   score, tenure, prods, bal, active):
        # metric cards
        for key, val in res.items():
            self._cards[key].update(val, self._tag(val), self._color(val))

        # SHAP bars
        shap_rows = [
            ("Debt Ratio",     min(100,debt*100),         DANGER  if debt>0.5  else SUCCESS),
            ("Monthly Income", min(100,100-income/200),   SUCCESS if income>4000 else DANGER),
            ("Loan Amount",    min(100,loan/500),          DANGER  if loan>15000 else SUCCESS),
            ("Credit Score",   min(100,100-score/10),     SUCCESS if score>700  else DANGER),
            ("Age",            min(100,age/80*100),        WARNING),
            ("Active Member",  100 if active else 30,      SUCCESS if active     else DANGER),
            ("Num Products",   min(100,prods*25),          SUCCESS if prods>1    else WARNING),
            ("Balance",        min(100,bal/2000),          SUCCESS if bal>10000  else WARNING),
        ]
        self._shap.render(shap_rows)

        # Explainability
        reasons = []
        if debt > 0.6:
            reasons.append(("!", DANGER,
                f"Debt ratio {debt:.2f} exceeds the safe threshold of 0.43 — elevated default risk."))
        if res["churn"] > 60:
            reasons.append(("!", DANGER,
                f"Churn probability {res['churn']:.0f}% — low product engagement detected."))
        if active:
            reasons.append(("+", SUCCESS,
                "Active member status reduces fraud and churn likelihood significantly."))
        if score > 700:
            reasons.append(("+", SUCCESS,
                f"Credit score {score:.0f} is above 700 — strong repayment history."))
        if income < 3000:
            reasons.append(("!", WARNING,
                f"Monthly income ${income:,.0f} may limit repayment capacity."))
        if prods == 1:
            reasons.append(("!", WARNING,
                "Single-product customer — higher churn probability detected."))
        if not reasons:
            reasons.append(("+", SUCCESS,
                "Profile shows no major risk indicators across all four models."))
        
        # ── final suggestion based on average risk ──
        avg_risk = (res["credit"] + res["fraud"] + res["churn"]) / 3
        if avg_risk < 30:
            suggest = {"text": "APPROVE (Strong Profile)", "color": SUCCESS}
        elif avg_risk < 60:
            suggest = {"text": "REVIEW (Moderate Risk)", "color": WARNING}
        else:
            suggest = {"text": "REJECT (High Default Risk)", "color": DANGER}

        self._explain.render(reasons, suggestion=suggest)

        # ── NEW: log to history panel ──
        # Build a minimal record from current field values if no DB record was loaded
        rec_for_history = self._last_rec if self._last_rec else {
            "customer_id": "MANUAL",
            "name":        "Manual Entry",
            "age":         int(age),
            "geography":   self._geo.get(),
        }
        self._history.add_entry(rec_for_history, res)
        # reset so next manual analysis doesn't reuse old DB record label
        if not self._last_rec.get("customer_id","").startswith("CUS"):
            self._last_rec = {}


# ═══════════════════════════════════════════════════════════════
#  APPLICATION CONTROLLER
#  Manages the two-stage flow: Login → Dashboard
# ═══════════════════════════════════════════════════════════════
class AppController:
    """
    Owns the root window.
    Shows LoginPage first; on successful login destroys it and
    shows FinGuardApp in its place.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FinGuard AI")
        self.root.geometry("1200x800")
        self.root.minsize(1050, 700)
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self._show_login()

    def _show_login(self):
        """Instantiate and display the login page."""
        self._login_frame = LoginPage(self.root, on_success=self._on_login_success)
        self._login_frame.place(x=0, y=0, relwidth=1, relheight=1)

    def _on_login_success(self, username: str):
        """
        Called by LoginPage when credentials are verified.
        Removes the login frame and launches the dashboard.
        """
        self._login_frame.destroy()
        # Build the dashboard, passing the admin's display name
        FinGuardApp(self.root, admin_name=username, on_logout=self._show_login)

    def run(self):
        self.root.mainloop()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    AppController().run()