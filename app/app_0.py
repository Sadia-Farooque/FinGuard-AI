import tkinter as tk
from tkinter import ttk, messagebox
import joblib
import numpy as np
import os
import threading
import math
import time
from PIL import Image, ImageTk

# ─────────────────────────────────────────────
#  MONGODB CONNECTION
# ─────────────────────────────────────────────
try:
    import pymongo
    _mongo_client = pymongo.MongoClient(
        "add your connection tring ",
        serverSelectionTimeoutMS=2000
    )
    # ping to confirm connection
    _mongo_client.admin.command("ping")
    _mongo_db         = _mongo_client["finguard"]
    _mongo_collection = _mongo_db["customers"]
    MONGO_CONNECTED   = True
    print("[MongoDB] Connected successfully")
except Exception as _e:
    _mongo_client     = None
    _mongo_db         = None
    _mongo_collection = None
    MONGO_CONNECTED   = False
    print(f"[MongoDB] Not connected: {_e}")

# ─────────────────────────────────────────────
#  THEME  — mirrors the CSS vars in Desktop.py
# ─────────────────────────────────────────────
BG      = "#0b0e1a"
PANEL   = "#111827"
CARD    = "#1a2235"
BORDER  = "#1e2a3a"   # rgba(255,255,255,0.10)
BORDER2 = "#2a3d55"   # rgba(255,255,255,0.20) hover
TEXT    = "#ffffff"
MUTED   = "#8b9bb4"
ACCENT  = "#1D9E75"
DANGER  = "#ef4444"
WARNING = "#f59e0b"
SUCCESS = "#1D9E75"

FONT_SANS  = ("Segoe UI",  10)
FONT_MONO  = ("Consolas",  11, "bold")
FONT_LOGO  = ("Georgia",   20, "bold")
FONT_NUM   = ("Consolas",  38, "bold")
FONT_HEAD  = ("Segoe UI",   8, "bold")
FONT_SMALL = ("Segoe UI",   8)
FONT_TAG   = ("Consolas",   9, "bold")
FONT_BTN   = ("Segoe UI",  10, "bold")

# ─────────────────────────────────────────────
#  MODEL LOADING
# ─────────────────────────────────────────────
ROOT_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(ROOT_DIR, "models")
FIG_DIR   = os.path.join(ROOT_DIR, "notebooks", "figures")

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


# ─────────────────────────────────────────────
#  PARTICLE CANVAS  (animated background dots)
# ─────────────────────────────────────────────
class ParticleCanvas(tk.Canvas):
    """Lightweight particle system matching particles.js feel."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, highlightthickness=0, **kw)
        self._particles = []
        self._running   = True
        self.bind("<Configure>", self._on_resize)
        self.after(500, self._init_particles)

    def _on_resize(self, e):
        self._w = e.width
        self._h = e.height

    def _init_particles(self):
        # guard: if widget is already destroyed, stop
        try:
            self.winfo_exists()
        except Exception:
            return
        w = self.winfo_width()
        h = self.winfo_height()
        self._w = w if w > 1 else 1200
        self._h = h if h > 1 else 800
        import random
        self._particles = []
        for _ in range(55):
            x  = random.uniform(0, self._w)
            y  = random.uniform(0, self._h)
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
        w, h = self._w, self._h
        pts  = self._particles
        for p in pts:
            p[0] += p[2]
            p[1] += p[3]
            if p[0] < 0: p[0] = w
            if p[0] > w: p[0] = 0
            if p[1] < 0: p[1] = h
            if p[1] > h: p[1] = 0
        # draw links
        for i, a in enumerate(pts):
            for b in pts[i+1:]:
                dist = math.hypot(a[0]-b[0], a[1]-b[1])
                if dist < 140:
                    alpha = int(12 * (1 - dist/140))
                    col   = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
                    self.create_line(a[0], a[1], b[0], b[1],
                                     fill=col, tags="particle")
        # draw dots
        for p in pts:
            x, y, r = p[0], p[1], p[4]
            self.create_oval(x-r, y-r, x+r, y+r,
                             fill="#1a1a2a", outline="#1a2535",
                             tags="particle")
        self.after(30, self._tick)

    def stop(self):
        self._running = False


# ─────────────────────────────────────────────
#  GLOW SPHERE  (CSS .glow-sphere equivalent)
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
            alpha = int(40 * (1 - ratio))
            ci    = self._blend(color_inner, BG, ratio)
            self.create_oval(r0-r, r0-r, r0+r, r0+r,
                             fill=ci, outline="")

    def _blend(self, hex1, hex2, t):
        h1 = hex1.lstrip("#")
        h2 = hex2.lstrip("#")
        r = int(int(h1[0:2],16)*(1-t) + int(h2[0:2],16)*t)
        g = int(int(h1[2:4],16)*(1-t) + int(h2[2:4],16)*t)
        b = int(int(h1[4:6],16)*(1-t) + int(h2[4:6],16)*t)
        return f"#{r:02x}{g:02x}{b:02x}"


# ─────────────────────────────────────────────
#  GLASS PANEL  (backdrop blur equivalent)
# ─────────────────────────────────────────────
class GlassFrame(tk.Frame):
    """Semi-transparent dark panel with border — glass-panel equivalent."""
    def __init__(self, parent, radius=14, **kw):
        kw.setdefault("bg", "#111827")
        kw.setdefault("highlightbackground", "#253045")
        kw.setdefault("highlightthickness", 1)
        super().__init__(parent, **kw)


# ─────────────────────────────────────────────
#  ANIMATED BUTTON  (btn-primary / btn-secondary)
# ─────────────────────────────────────────────
class GlowButton(tk.Frame):
    """Stable hover-animated button using Frame+Label — no Canvas conflicts."""
    def __init__(self, parent, text, command=None,
                 primary=True, btn_width=240, btn_height=40, **kw):
        bg_parent = parent.cget("bg") if hasattr(parent, "cget") else PANEL
        super().__init__(parent, bg=bg_parent)
        self._cmd     = command
        self._primary = primary
        self._normal  = ACCENT       if primary else CARD
        self._hover   = "#17a874"   if primary else "#1f2d45"
        self._press   = "#148560"   if primary else "#151e2e"
        self._fg_col  = BG           if primary else MUTED
        self._fg_hov  = BG           if primary else "#aabbcc"
        fnt = FONT_BTN if primary else ("Segoe UI", 9, "bold")
        self._btn = tk.Button(
            self, text=text, command=command,
            bg=self._normal, fg=self._fg_col,
            font=fnt,
            relief="flat", bd=0,
            cursor="hand2",
            activebackground=self._press,
            activeforeground=BG if primary else "#ffffff",
            padx=12, pady=0
        )
        self._btn.pack(fill="both", expand=True, ipady=8 if primary else 6)
        self._btn.bind("<Enter>",           self._enter)
        self._btn.bind("<Leave>",           self._leave)
        self._btn.bind("<Button-1>",        self._press_ev)
        self._btn.bind("<ButtonRelease-1>", self._release_ev)

    def _enter(self, e):
        self._btn.config(bg=self._hover, fg=self._fg_hov)

    def _leave(self, e):
        self._btn.config(bg=self._normal, fg=self._fg_col)

    def _press_ev(self, e):
        self._btn.config(bg=self._press)

    def _release_ev(self, e):
        self._btn.config(bg=self._hover)
        if self._cmd:
            self._cmd()


# ─────────────────────────────────────────────
#  METRIC CARD  (matches .metric-card in CSS)
# ─────────────────────────────────────────────
class MetricCard(tk.Frame):
    def __init__(self, parent, title, **kw):
        super().__init__(parent,
                         bg=CARD,
                         highlightbackground="#1e2a3a",
                         highlightthickness=1, **kw)
        self._pct   = 0
        self._bar_w = 0
        self._anim_id = None

        tk.Label(self, text=title.upper(),
                 font=FONT_HEAD, fg=MUTED, bg=CARD
                 ).pack(anchor="w", padx=20, pady=(18, 0))

        self._val = tk.Label(self, text="0%",
                             font=FONT_NUM, fg=MUTED, bg=CARD)
        self._val.pack(anchor="w", padx=20, pady=(2, 0))

        # progress track
        track = tk.Frame(self, bg="#0a0d16", height=6)
        track.pack(fill="x", padx=20, pady=(6, 0))
        track.pack_propagate(False)
        self._bar = tk.Frame(track, bg=SUCCESS, height=6)
        self._bar.place(x=0, y=0, relheight=1, width=0)
        self._track = track

        self._tag = tk.Label(self, text="READY",
                             font=FONT_TAG, fg=MUTED, bg=CARD)
        self._tag.pack(anchor="w", padx=20, pady=(8, 18))

        self.bind("<Configure>", self._resize)

    def _resize(self, e):
        self._bar_w = max(0, e.width - 40)
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

    def _anim(self, cur, target):
        if cur >= target:
            return
        nxt = min(cur + 2, target)
        self._set_bar_px(nxt)
        self.after(14, lambda: self._anim(nxt, target))


# ─────────────────────────────────────────────
#  SHAP BAR PANEL
# ─────────────────────────────────────────────
class SHAPPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent,
                         bg=CARD,
                         highlightbackground="#1e2a3a",
                         highlightthickness=1, **kw)
        tk.Label(self, text="SHAP — FEATURE IMPACT",
                 font=FONT_HEAD, fg=MUTED, bg=CARD
                 ).pack(anchor="w", padx=20, pady=(18, 10))
        self._body = tk.Frame(self, bg=CARD)
        self._body.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def render(self, rows):
        for w in self._body.winfo_children():
            w.destroy()
        for label, pct, color in rows:
            row = tk.Frame(self._body, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=("Segoe UI", 9),
                     fg=TEXT, bg=CARD, width=20, anchor="w"
                     ).pack(side="left")
            track = tk.Frame(row, bg="#141e2e", height=8)
            track.pack(side="left", fill="x", expand=True, padx=(6, 8))
            bar = tk.Frame(track, bg=color, height=8)
            bar.place(x=0, y=0, relheight=1, relwidth=max(0, min(1, pct/100)))
            tk.Label(row, text=f"{pct:.0f}",
                     font=("Consolas", 8), fg=MUTED, bg=CARD, width=3
                     ).pack(side="left")


# ─────────────────────────────────────────────
#  EXPLAINABILITY PANEL
# ─────────────────────────────────────────────
class ExplainPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent,
                         bg=CARD,
                         highlightbackground="#1e2a3a",
                         highlightthickness=1, **kw)
        tk.Label(self, text="AI EXPLAINABILITY",
                 font=FONT_HEAD, fg=MUTED, bg=CARD
                 ).pack(anchor="w", padx=20, pady=(18, 10))
        self._body = tk.Frame(self, bg=CARD)
        self._body.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        self._placeholder()

    def _placeholder(self):
        tk.Label(self._body,
                 text="Run analysis to see AI-generated explanations.",
                 font=("Segoe UI", 9), fg=MUTED, bg=CARD, justify="left"
                 ).pack(anchor="w", pady=16)

    def render(self, reasons):
        for w in self._body.winfo_children():
            w.destroy()
        for icon, color, text in reasons:
            row = tk.Frame(self._body,
                           bg="#0d1220",
                           highlightbackground="#1e2a3a",
                           highlightthickness=1)
            row.pack(fill="x", pady=4, ipady=2)
            # icon badge
            badge = tk.Frame(row, bg=color, width=26, height=26)
            badge.pack(side="left", padx=(10, 10), pady=8)
            badge.pack_propagate(False)
            tk.Label(badge, text=icon, font=("Segoe UI", 10, "bold"),
                     fg=BG, bg=color).place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(row, text=text, font=("Segoe UI", 9),
                     fg=TEXT, bg="#0d1220",
                     wraplength=260, justify="left"
                     ).pack(side="left", fill="x", expand=True, pady=6)


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
        r     = 5
        cx    = 7
        glow  = int(abs(math.sin(self._phase)) * 60)
        gcol  = f"#{glow:02x}{glow+158:02x}{glow+117:02x}"
        # outer glow ring
        gr = r + int(abs(math.sin(self._phase)) * 4)
        self.create_oval(cx-gr, 7-gr, cx+gr, 7+gr,
                         fill=gcol, outline="")
        self.create_oval(cx-r, 7-r, cx+r, 7+r,
                         fill=ACCENT, outline="")
        self._phase += 0.08
        self.after(50, self._tick)


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class FinGuardApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("FinGuard AI — Intelligent Financial Risk Engine")
        root.geometry("1200x800")
        root.minsize(1050, 700)
        root.configure(bg=BG)
        root.resizable(True, True)

        self._build()

    # ── BUILD ────────────────────────────────
    def _build(self):
        # particle background layer
        self._particles = ParticleCanvas(self.root)
        self._particles.place(x=0, y=0, relwidth=1, relheight=1)

        # glow spheres
        s1 = GlowSphere(self.root, "#1D9E75", size=380)
        s1.place(x=-80, y=-80)
        s2 = GlowSphere(self.root, "#3b82f6", size=460)
        s2.place(relx=1.0, rely=1.0, anchor="se", x=80, y=80)

        # foreground container
        self._fg = tk.Frame(self.root, bg=BG)
        self._fg.place(x=0, y=0, relwidth=1, relheight=1)

        self._build_topbar()
        self._build_dashboard()

    # ── TOP BAR ──────────────────────────────
    def _build_topbar(self):
        bar = GlassFrame(self._fg, height=66)
        bar.pack(fill="x", padx=18, pady=(16, 0))
        bar.pack_propagate(False)

        # Logo
        logo = tk.Frame(bar, bg=PANEL)
        logo.pack(side="left", padx=24)
        tk.Label(logo, text="Fin",    font=FONT_LOGO, fg=TEXT,   bg=PANEL).pack(side="left")
        tk.Label(logo, text="Guard",  font=FONT_LOGO, fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Label(logo, text=" AI",    font=FONT_LOGO, fg=TEXT,   bg=PANEL).pack(side="left")

        # Right — status
        right = tk.Frame(bar, bg=PANEL)
        right.pack(side="right", padx=24)
        PulseDot(right).pack(side="left", padx=(0, 6))
        tk.Label(right, text="Local AI Engine Active",
                 font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(side="left")

    # ── DASHBOARD LAYOUT ─────────────────────
    def _build_dashboard(self):
        layout = tk.Frame(self._fg, bg=BG)
        layout.pack(fill="both", expand=True, padx=18, pady=14)

        self._build_sidebar(layout)
        self._build_main(layout)

    # ── SIDEBAR ──────────────────────────────
    def _build_sidebar(self, parent):
        side = GlassFrame(parent, width=310)
        side.pack(side="left", fill="y", padx=(0, 18))
        side.pack_propagate(False)

        # ── BUTTONS at bottom — pack first so they are always visible ──
        btn_area = tk.Frame(side, bg=PANEL)
        btn_area.pack(side="bottom", fill="x", padx=16, pady=12)

        tk.Button(btn_area, text="⬡   LOAD FROM DATABASE",
                  command=self._open_db_selector,
                  bg=CARD, fg=ACCENT,
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0,
                  activebackground="#1f2d45",
                  activeforeground=ACCENT,
                  cursor="hand2"
                  ).pack(fill="x", ipady=7, pady=(0, 8))

        tk.Button(btn_area, text="▶   ANALYZE RISK",
                  command=self._run_analysis,
                  bg=ACCENT, fg=BG,
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0,
                  activebackground="#148560",
                  activeforeground=BG,
                  cursor="hand2"
                  ).pack(fill="x", ipady=10)

        # ── header ──
        tk.Label(side, text="CUSTOMER PROFILE",
                 font=FONT_HEAD, fg=MUTED, bg=PANEL
                 ).pack(anchor="w", padx=20, pady=(18, 10))

        tk.Frame(side, bg="#1e2a3a", height=1).pack(fill="x")

        # ── plain frame — no scroll ──
        inner = tk.Frame(side, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        # ── fields ──
        self._entries = {}

        grid = tk.Frame(inner, bg=PANEL)
        grid.pack(fill="x")

        pairs = [
            ("Age",           "34"   ),
            ("Income",        "5200" ),
            ("Debt Ratio",    "0.74" ),
            ("Loan Amount",   "18500"),
            ("Credit Score",  "620"  ),
            ("Tenure (yrs)",  "2"    ),
            ("Num Products",  "1"    ),
            ("Balance",       "45000"),
        ]
        for i, (label, default) in enumerate(pairs):
            r, c = divmod(i, 2)
            cell = tk.Frame(grid, bg=PANEL)
            cell.grid(row=r, column=c, padx=(0, 8 if c==0 else 0),
                      pady=4, sticky="ew")
            grid.columnconfigure(c, weight=1)
            tk.Label(cell, text=label, font=("Segoe UI", 8),
                     fg=MUTED, bg=PANEL).pack(anchor="w")
            var = tk.StringVar(value=default)
            ent = tk.Entry(cell, textvariable=var,
                           font=("Consolas", 10),
                           fg=ACCENT, bg="#0d1220",
                           insertbackground=ACCENT,
                           relief="flat",
                           highlightbackground="#253045",
                           highlightcolor=ACCENT,
                           highlightthickness=1)
            ent.pack(fill="x", ipady=4)
            self._entries[label] = var
            ent.bind("<FocusIn>",  lambda e, w=ent: w.config(highlightbackground=ACCENT))
            ent.bind("<FocusOut>", lambda e, w=ent: w.config(highlightbackground="#253045"))

        # ── dropdowns ──
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("FG.TCombobox",
                         fieldbackground="#0d1220",
                         background="#0d1220",
                         foreground=ACCENT,
                         bordercolor="#253045",
                         arrowcolor=ACCENT,
                         selectbackground="#0d1220",
                         selectforeground=ACCENT,
                         padding=4)

        for label, values, attr in [
            ("Gender",        ["Male", "Female"],             "_gender"),
            ("Geography",     ["France", "Germany", "Spain"], "_geo"),
            ("Active Member", ["Yes", "No"],                  "_active"),
        ]:
            tk.Label(inner, text=label, font=("Segoe UI", 8),
                     fg=MUTED, bg=PANEL).pack(anchor="w", pady=(6, 0))
            cb = ttk.Combobox(inner, values=values,
                              state="readonly", style="FG.TCombobox")
            cb.set(values[0])
            cb.pack(fill="x", pady=(2, 0))
            setattr(self, attr, cb)

    def _db_placeholder(self):
        pass  # replaced by _open_db_selector

    def _open_db_selector(self):
        if not MONGO_CONNECTED:
            messagebox.showerror(
                "Database Not Connected",
                "Could not connect to MongoDB on localhost:27017.\n\nMake sure MongoDB is running.")
            return
        try:
            records = list(_mongo_collection.find({}, {"_id": 0}))
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to load records:\n{e}")
            return
        if not records:
            messagebox.showinfo("Empty", "No customers found. Run create_db.py first.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Select Customer from Database")
        popup.geometry("420x480")
        popup.configure(bg=PANEL)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text="SELECT CUSTOMER",
                 font=FONT_HEAD, fg=MUTED, bg=PANEL
                 ).pack(anchor="w", padx=20, pady=(18, 6))
        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x")

        list_frame = tk.Frame(popup, bg=PANEL)
        list_frame.pack(fill="both", expand=True, padx=16, pady=12)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        listbox = tk.Listbox(list_frame,
                             bg=CARD, fg=TEXT,
                             font=("Consolas", 10),
                             selectbackground=ACCENT,
                             selectforeground=BG,
                             activestyle="none",
                             highlightthickness=0,
                             relief="flat",
                             yscrollcommand=scrollbar.set)
        listbox.pack(fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        for rec in records:
            cid  = rec.get("customer_id", "-")
            name = rec.get("name", "Unknown")
            age  = rec.get("age", "?")
            listbox.insert(tk.END, f"  {cid}   {name}   (Age {age})")

        preview = tk.Label(popup,
                           text="Select a customer to preview",
                           font=("Segoe UI", 8), fg=MUTED,
                           bg=PANEL, wraplength=380, justify="left")
        preview.pack(padx=20, pady=(0, 8))

        def _on_select(e):
            idx = listbox.curselection()
            if not idx:
                return
            r = records[idx[0]]
            preview.config(
                text=f"ID: {r.get('customer_id')}  |  Income: {r.get('income')}  |  "
                     f"Debt: {r.get('debt_ratio')}  |  Score: {r.get('credit_score')}  |  "
                     f"Geo: {r.get('geography')}",
                fg=ACCENT)

        listbox.bind("<<ListboxSelect>>", _on_select)

        def _load_selected():
            idx = listbox.curselection()
            if not idx:
                messagebox.showwarning("No Selection", "Please select a customer first.")
                return
            rec = records[idx[0]]
            popup.destroy()
            self._fill_from_db(rec)

        tk.Button(popup, text="▶   LOAD & ANALYZE",
                  command=_load_selected,
                  bg=ACCENT, fg=BG,
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0,
                  activebackground="#148560",
                  cursor="hand2"
                  ).pack(fill="x", padx=16, ipady=10, pady=(0, 16))

    def _fill_from_db(self, rec):
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
        self._gender.set(rec.get("gender",        "Male"))
        self._geo.set(   rec.get("geography",     "France"))
        self._active.set(rec.get("active_member", "Yes"))
        self._run_analysis()

    # ── MAIN RESULTS AREA ────────────────────
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="right", fill="both", expand=True)

        # 4 metric cards
        cards_row = tk.Frame(main, bg=BG)
        cards_row.pack(fill="x", pady=(0, 14))

        self._cards = {}
        for label, key in [
            ("Credit Risk",      "credit"),
            ("Fraud",            "fraud"),
            ("Churn",            "churn"),
            ("Spend Forecast",   "spend"),
        ]:
            c = MetricCard(cards_row, label)
            c.pack(side="left", fill="both", expand=True, padx=(0, 12))
            self._cards[key] = c
        list(cards_row.winfo_children())[-1].pack_configure(padx=0)

        # lower row: SHAP + Explainability
        lower = tk.Frame(main, bg=BG)
        lower.pack(fill="both", expand=True)

        self._shap = SHAPPanel(lower)
        self._shap.pack(side="left", fill="both", expand=True, padx=(0, 14))

        right = tk.Frame(lower, bg=BG, width=310)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        self._explain = ExplainPanel(right)
        self._explain.pack(fill="both", expand=True, pady=(0, 10))

        # model badges
        badges = tk.Frame(right, bg=BG)
        badges.pack(fill="x")
        for name, col in [("XGBoost", ACCENT), ("GBM", "#3b82f6"), ("LR", MUTED)]:
            b = tk.Frame(badges, bg=col)
            b.pack(side="left", padx=(0, 6), pady=2)
            tk.Label(b, text=f"  {name}  ", font=FONT_TAG,
                     fg=BG if col != MUTED else BG, bg=col).pack()
        tk.Label(badges, text="Active models",
                 font=("Segoe UI", 8), fg=MUTED, bg=BG).pack(side="left", padx=6)

    # ── ANALYSIS ─────────────────────────────
    def _run_analysis(self):
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

        # Credit Risk
        try:
            if credit_model:
                f = np.array([[debt, income/12000, loan/50000, score/850,
                               age/80, tenure/30, bal/100000, prods, gender, active]])
                res["credit"] = float(credit_model.predict_proba(f)[0][1]) * 100
            else:
                raise ValueError
        except:
            res["credit"] = min(99, max(1, debt*60 + (loan/max(income,1))*20))

        # Fraud
        try:
            if fraud_model:
                f = np.array([[loan, income, age, score, bal, tenure, prods, active]])
                res["fraud"] = float(fraud_model.predict_proba(f)[0][1]) * 100
            else:
                raise ValueError
        except:
            res["fraud"] = min(99, max(1, (loan/max(income,1))*15 + (1-active)*10))

        # Churn
        try:
            if churn_model:
                f = np.array([[score, age, tenure, bal, prods,
                               1, active, income, gender, geo_de, geo_sp]])
                res["churn"] = float(churn_model.predict_proba(f)[0][1]) * 100
            else:
                raise ValueError
        except:
            res["churn"] = min(99, max(1, (1-active)*40 + (1/max(prods,1))*30))

        # Spend
        try:
            if spend_model:
                f   = np.array([[income, age, bal, tenure, prods, score]])
                raw = float(spend_model.predict(f)[0])
                res["spend"] = min(99, max(1, (raw / max(income*0.6, 1)) * 50))
            else:
                raise ValueError
        except:
            res["spend"] = min(99, max(1, (income * 0.35) / 500))

        for k in res:
            res[k] = min(99, max(1, res[k]))

        self.root.after(0, lambda: self._update_ui(
            res, age, income, debt, loan, score, tenure, prods, bal, active))

    # ── UPDATE UI ────────────────────────────
    def _color(self, p):
        return SUCCESS if p < 35 else (WARNING if p < 65 else DANGER)

    def _tag(self, p):
        return "LOW RISK" if p < 35 else ("MEDIUM RISK" if p < 65 else "HIGH RISK")

    def _update_ui(self, res, age, income, debt, loan,
                   score, tenure, prods, bal, active):
        # metric cards
        for key, val in res.items():
            self._cards[key].update(val, self._tag(val), self._color(val))

        # SHAP bars
        shap_rows = [
            ("Debt Ratio",     min(100, debt*100),          DANGER  if debt > 0.5 else SUCCESS),
            ("Monthly Income", min(100, 100-income/200),    SUCCESS if income > 4000 else DANGER),
            ("Loan Amount",    min(100, loan/500),           DANGER  if loan > 15000 else SUCCESS),
            ("Credit Score",   min(100, 100-score/10),      SUCCESS if score > 700 else DANGER),
            ("Age",            min(100, age/80*100),         WARNING),
            ("Active Member",  100 if active else 30,        SUCCESS if active else DANGER),
            ("Num Products",   min(100, prods*25),           SUCCESS if prods > 1 else WARNING),
            ("Balance",        min(100, bal/2000),           SUCCESS if bal > 10000 else WARNING),
        ]
        self._shap.render(shap_rows)

        # Explainability reasons
        reasons = []
        if debt > 0.6:
            reasons.append(("!", DANGER,
                f"Debt ratio {debt:.2f} exceeds the safe threshold of 0.43 "
                f"— elevated default risk."))
        if res["churn"] > 60:
            reasons.append(("!", DANGER,
                f"Churn probability {res['churn']:.0f}% — "
                f"low product engagement detected."))
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

        self._explain.render(reasons)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    FinGuardApp(root)
    root.mainloop()
