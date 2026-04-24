import tkinter as tk
from tkinter import ttk, messagebox
import joblib
import numpy as np
import os
import threading
from PIL import Image, ImageTk

# ─────────────────────────────────────────────
#  THEME
# ─────────────────────────────────────────────
BG         = "#0b0e1a"
PANEL      = "#111827"
CARD       = "#1a2235"
BORDER     = "#1f2d45"
ACCENT     = "#1D9E75"
ACCENT2    = "#16856200"
TEXT       = "#e8eaf0"
MUTED      = "#6b7a99"
DANGER     = "#e24b4a"
WARNING    = "#ba7517"
SUCCESS    = "#1D9E75"
MONO       = ("Courier New", 10, "bold")
TITLE_FONT = ("Georgia", 22, "bold")
HEAD_FONT  = ("Georgia", 13, "bold")
BODY_FONT  = ("Helvetica", 10)
SMALL_FONT = ("Helvetica", 9)
TAG_FONT   = ("Courier New", 9, "bold")

# ─────────────────────────────────────────────
#  LOAD MODELS  (graceful fallback if missing)
# ─────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
FIG_DIR   = os.path.join(os.path.dirname(__file__), "notebooks", "figures")

def _load(name):
    path = os.path.join(MODEL_DIR, name)
    try:
        return joblib.load(path)
    except Exception:
        return None

credit_model  = _load("credit_risk_model.pkl")
churn_model   = _load("churn_model.pkl")
fraud_model   = _load("fraud_model.pkl")
spend_model   = _load("spend_model_weights.pkl")


# ─────────────────────────────────────────────
#  HELPER WIDGETS
# ─────────────────────────────────────────────
class AnimButton(tk.Canvas):
    """Sharp pixel-perfect button with hover + click animation."""
    def __init__(self, parent, text, command=None,
                 width=160, height=36,
                 bg=ACCENT, fg=BG,
                 font=("Helvetica", 10, "bold"),
                 radius=6, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=PANEL, highlightthickness=0)
        self._bg0   = bg
        self._bg1   = self._lighten(bg, 30)
        self._fg    = fg
        self._text  = text
        self._font  = font
        self._r     = radius
        self._w     = width
        self._h     = height
        self._cmd   = command
        try:
            self._draw(self._bg0)
        except:
            pass
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _lighten(self, hex_col, amt):
        hex_col = hex_col.lstrip("#")
        r,g,b = (int(hex_col[i:i+2],16) for i in (0,2,4))
        return "#{:02x}{:02x}{:02x}".format(
            min(255,r+amt), min(255,g+amt), min(255,b+amt))

    def _darken(self, hex_col, amt):
        hex_col = hex_col.lstrip("#")
        r,g,b = (int(hex_col[i:i+2],16) for i in (0,2,4))
        return "#{:02x}{:02x}{:02x}".format(
            max(0,r-amt), max(0,g-amt), max(0,b-amt))

    def _draw(self, color):
        self.delete("all")
        r,w,h = self._r, self._w, self._h
        self.create_polygon(
            r,0, w-r,0, w,r, w,h-r, w-r,h, r,h, 0,h-r, 0,r,
            smooth=True, fill=color, outline="")
        self.create_text(w//2, h//2, text=self._text,
                         fill=self._fg, font=self._font)

    def _on_enter(self, e):
        self._draw(self._bg1)
        self.config(cursor="hand2")

    def _on_leave(self, e):
        self._draw(self._bg0)
        self.config(cursor="")

    def _on_press(self, e):
        self._draw(self._darken(self._bg0, 20))

    def _on_release(self, e):
        self._draw(self._bg1)
        if self._cmd:
            self._cmd()


class MetricCard(tk.Frame):
    """Animated metric card with progress bar."""
    def __init__(self, parent, label, **kw):
        super().__init__(parent, bg=CARD,
                         highlightbackground=BORDER,
                         highlightthickness=1, **kw)
        self._label = label
        self._pct   = 0

        tk.Label(self, text=label.upper(), font=("Helvetica", 8, "bold"),
                 fg=MUTED, bg=CARD).pack(anchor="w", padx=14, pady=(12,0))

        self._val_lbl = tk.Label(self, text="—",
                                  font=("Courier New", 26, "bold"),
                                  fg=TEXT, bg=CARD)
        self._val_lbl.pack(anchor="w", padx=14)

        # bar track
        bar_bg = tk.Frame(self, bg=BORDER, height=4)
        bar_bg.pack(fill="x", padx=14, pady=(4,0))
        bar_bg.pack_propagate(False)
        self._bar = tk.Frame(bar_bg, bg=ACCENT, height=4)
        self._bar.place(x=0, y=0, relheight=1, width=0)
        self._bar_w = 0

        self._tag_lbl = tk.Label(self, text="", font=TAG_FONT,
                                  fg=ACCENT, bg=CARD)
        self._tag_lbl.pack(anchor="w", padx=14, pady=(6,12))

        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, e):
        self._bar_w = e.width - 28
        self._set_bar(self._pct)

    def _set_bar(self, pct):
        w = int(self._bar_w * pct / 100)
        self._bar.place(x=0, y=0, relheight=1, width=max(0,w))

    def update(self, value_pct, tag, color):
        self._pct = value_pct
        self._val_lbl.config(text=f"{value_pct:.0f}%", fg=color)
        self._tag_lbl.config(text=tag, fg=color)
        self._bar.config(bg=color)
        self._animate_bar(0, value_pct)

    def _animate_bar(self, current, target):
        if current >= target:
            return
        nxt = min(current + 2, target)
        self._set_bar(nxt)
        self.after(12, lambda: self._animate_bar(nxt, target))


class SHAPPanel(tk.Frame):
    def __init__(self, parent, title, **kw):
        super().__init__(parent, bg=CARD,
                         highlightbackground=BORDER,
                         highlightthickness=1, **kw)
        tk.Label(self, text=title.upper(),
                 font=("Helvetica", 8, "bold"),
                 fg=MUTED, bg=CARD).pack(anchor="w", padx=14, pady=(12,8))
        self._inner = tk.Frame(self, bg=CARD)
        self._inner.pack(fill="both", expand=True, padx=14, pady=(0,12))
        self._img_lbl = None

    def show_image(self, path):
        for w in self._inner.winfo_children():
            w.destroy()
        try:
            img = Image.open(path)
            img = img.resize((340, 220), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(self._inner, image=photo, bg=CARD)
            lbl.image = photo
            lbl.pack()
        except Exception:
            tk.Label(self._inner, text="Figure not found",
                     font=SMALL_FONT, fg=MUTED, bg=CARD).pack()

    def show_bars(self, rows):
        """rows = [(label, pct, color), ...]"""
        for w in self._inner.winfo_children():
            w.destroy()
        for label, pct, color in rows:
            row = tk.Frame(self._inner, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, font=("Helvetica", 9),
                     fg=TEXT, bg=CARD, width=22, anchor="w").pack(side="left")
            track = tk.Frame(row, bg=BORDER, height=8)
            track.pack(side="left", fill="x", expand=True, padx=(4,6))
            bar = tk.Frame(track, bg=color, height=8)
            bar.place(x=0, y=0, relheight=1, relwidth=pct/100)
            tk.Label(row, text=f"{pct:.0f}",
                     font=("Courier New", 8), fg=MUTED, bg=CARD,
                     width=4).pack(side="left")


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class FinGuardApp:
    def __init__(self, root):
        self.root = root
        root.title("FinGuard AI — Intelligent Financial Risk Engine")
        root.geometry("1180x780")
        root.minsize(1000, 680)
        root.configure(bg=BG)
        root.resizable(True, True)

        self._build_topbar()
        self._build_body()

    # ── TOP BAR ──────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=PANEL,
                       highlightbackground=BORDER, highlightthickness=1,
                       height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo
        logo = tk.Frame(bar, bg=PANEL)
        logo.pack(side="left", padx=20)
        tk.Label(logo, text="Fin", font=("Georgia", 17, "bold"),
                 fg=TEXT, bg=PANEL).pack(side="left")
        tk.Label(logo, text="Guard", font=("Georgia", 17, "bold"),
                 fg=ACCENT, bg=PANEL).pack(side="left")
        tk.Label(logo, text=" AI", font=("Georgia", 17, "bold"),
                 fg=TEXT, bg=PANEL).pack(side="left")

        # Status dot
        status = tk.Frame(bar, bg=PANEL)
        status.pack(side="right", padx=20)
        self._dot = tk.Label(status, text="●", font=("Helvetica", 11),
                              fg=ACCENT, bg=PANEL)
        self._dot.pack(side="left")
        tk.Label(status, text=" Models active",
                 font=SMALL_FONT, fg=MUTED, bg=PANEL).pack(side="left")
        self._pulse_dot()

        # Nav tabs
        nav = tk.Frame(bar, bg=PANEL)
        nav.pack(side="left", padx=30)
        for t in ["Dashboard", "History", "Settings"]:
            lbl = tk.Label(nav, text=t, font=("Helvetica", 10),
                           fg=ACCENT if t == "Dashboard" else MUTED,
                           bg=PANEL, cursor="hand2")
            lbl.pack(side="left", padx=12)

    def _pulse_dot(self):
        cur = self._dot.cget("fg")
        self._dot.config(fg=ACCENT if cur == MUTED else MUTED)
        self.root.after(900, self._pulse_dot)

    # ── BODY ─────────────────────────────────
    def _build_body(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=14)

        self._build_sidebar(body)
        self._build_main(body)

    # ── SIDEBAR ──────────────────────────────
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=PANEL, width=270,
                        highlightbackground=BORDER, highlightthickness=1)
        side.pack(side="left", fill="y", padx=(0,14))
        side.pack_propagate(False)

        tk.Label(side, text="CUSTOMER PROFILE",
                 font=("Helvetica", 8, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w", padx=16, pady=(16,10))

        # ── input fields ──
        self._entries = {}
        fields = [
            ("Age",            "34",     "slider",  18, 90),
            ("Monthly Income", "5200",   "entry",   None, None),
            ("Debt Ratio",     "0.74",   "entry",   None, None),
            ("Loan Amount",    "18500",  "entry",   None, None),
            ("Credit Score",   "620",    "entry",   None, None),
            ("Tenure (yrs)",   "2",      "slider",  0, 30),
            ("Num Products",   "1",      "slider",  1, 4),
            ("Balance",        "45000",  "entry",   None, None),
        ]

        scroll_frame = tk.Frame(side, bg=PANEL)
        scroll_frame.pack(fill="both", expand=True, padx=12)

        for label, default, kind, mn, mx in fields:
            grp = tk.Frame(scroll_frame, bg=PANEL)
            grp.pack(fill="x", pady=4)
            tk.Label(grp, text=label, font=("Helvetica", 9),
                     fg=MUTED, bg=PANEL).pack(anchor="w")

            if kind == "slider":
                var = tk.IntVar(value=int(default))
                row = tk.Frame(grp, bg=PANEL)
                row.pack(fill="x")
                sl = tk.Scale(row, from_=mn, to=mx, orient="horizontal",
                              variable=var, bg=PANEL, fg=TEXT,
                              troughcolor=BORDER, activebackground=ACCENT,
                              highlightthickness=0, bd=0,
                              showvalue=False, sliderlength=16)
                sl.pack(side="left", fill="x", expand=True)
                val_lbl = tk.Label(row, textvariable=var,
                                   font=MONO, fg=ACCENT, bg=PANEL, width=3)
                val_lbl.pack(side="right")
                self._entries[label] = var
            else:
                var = tk.StringVar(value=default)
                ent = tk.Entry(grp, textvariable=var,
                               font=MONO, fg=ACCENT, bg=CARD,
                               insertbackground=ACCENT,
                               relief="flat", bd=0,
                               highlightbackground=BORDER,
                               highlightthickness=1)
                ent.pack(fill="x", ipady=5, padx=1)
                self._entries[label] = var

        # dropdowns
        tk.Label(scroll_frame, text="Gender",
                 font=("Helvetica", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(8,0))
        self._gender = ttk.Combobox(scroll_frame, values=["Male", "Female"],
                                     state="readonly", font=BODY_FONT)
        self._gender.set("Male")
        self._gender.pack(fill="x", pady=(2,0))

        tk.Label(scroll_frame, text="Geography",
                 font=("Helvetica", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(8,0))
        self._geo = ttk.Combobox(scroll_frame,
                                  values=["France", "Germany", "Spain"],
                                  state="readonly", font=BODY_FONT)
        self._geo.set("France")
        self._geo.pack(fill="x", pady=(2,0))

        tk.Label(scroll_frame, text="Active Member",
                 font=("Helvetica", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(8,0))
        self._active = ttk.Combobox(scroll_frame, values=["Yes", "No"],
                                     state="readonly", font=BODY_FONT)
        self._active.set("Yes")
        self._active.pack(fill="x", pady=(2,4))

        # style comboboxes
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                         fieldbackground=CARD,
                         background=CARD,
                         foreground=ACCENT,
                         bordercolor=BORDER,
                         arrowcolor=ACCENT,
                         selectbackground=CARD,
                         selectforeground=ACCENT)

        # ── buttons ──
        btn_frame = tk.Frame(side, bg=PANEL)
        btn_frame.pack(fill="x", padx=12, pady=12)

        btn1 = tk.Button(btn_frame, text="▶  ANALYZE RISK",
                         command=self._run_analysis,
                         bg=ACCENT, fg=BG,
                         font=("Helvetica", 10, "bold"),
                         relief="flat", bd=0, padx=10, pady=6)
        btn1.pack(pady=(0,8), fill="x")

        # DB button — placeholder for future development
        btn2 = tk.Button(btn_frame, text="⬡  LOAD FROM DATABASE",
                         command=self._db_placeholder,
                         bg=CARD, fg=MUTED,
                         font=("Helvetica", 9, "bold"),
                         relief="flat", bd=0, padx=10, pady=6)
        btn2.pack(fill="x")

        tk.Label(side, text="Database integration — coming soon",
                 font=("Helvetica", 7), fg=BORDER, bg=PANEL).pack(pady=(0,8))

    def _db_placeholder(self):
        messagebox.showinfo(
            "Coming Soon",
            "Database integration is planned for the next development phase.\n\n"
            "Will support: PostgreSQL, MySQL, and CSV batch imports.")

    # ── MAIN PANEL ───────────────────────────
    def _build_main(self, parent):
        main = tk.Frame(parent, bg=BG)
        main.pack(side="right", fill="both", expand=True)

        # ── 4 metric cards ──
        cards_row = tk.Frame(main, bg=BG)
        cards_row.pack(fill="x", pady=(0,12))

        self._cards = {}
        specs = [
            ("Credit Risk",       "credit"),
            ("Fraud Probability",  "fraud"),
            ("Churn Risk",         "churn"),
            ("Spend Forecast",     "spend"),
        ]
        for label, key in specs:
            c = MetricCard(cards_row, label)
            c.pack(side="left", fill="both", expand=True, padx=(0,10))
            self._cards[key] = c
        # remove last padx
        list(cards_row.winfo_children())[-1].pack_configure(padx=0)

        # ── bottom two panels ──
        bottom = tk.Frame(main, bg=BG)
        bottom.pack(fill="both", expand=True)

        # SHAP panel
        self._shap_panel = SHAPPanel(bottom, "SHAP — feature impact")
        self._shap_panel.pack(side="left", fill="both",
                               expand=True, padx=(0,12))

        # Explainability panel
        right_col = tk.Frame(bottom, bg=BG)
        right_col.pack(side="right", fill="both", expand=True)

        self._explain_panel = tk.Frame(right_col, bg=CARD,
                                        highlightbackground=BORDER,
                                        highlightthickness=1)
        self._explain_panel.pack(fill="both", expand=True, pady=(0,10))

        tk.Label(self._explain_panel,
                 text="AI EXPLAINABILITY",
                 font=("Helvetica", 8, "bold"),
                 fg=MUTED, bg=CARD).pack(anchor="w", padx=14, pady=(12,6))

        self._explain_inner = tk.Frame(self._explain_panel, bg=CARD)
        self._explain_inner.pack(fill="both", expand=True, padx=14, pady=(0,12))

        self._placeholder_explain()

        # model badge row
        badge_row = tk.Frame(right_col, bg=BG)
        badge_row.pack(fill="x")
        for name, color in [("XGBoost", ACCENT), ("GBM", "#378ADD"), ("LR", MUTED)]:
            b = tk.Frame(badge_row, bg=color, height=22)
            b.pack(side="left", padx=(0,6), pady=2)
            tk.Label(b, text=f" {name} ", font=TAG_FONT,
                     fg=BG, bg=color).pack()

        tk.Label(badge_row, text="Active models",
                 font=SMALL_FONT, fg=MUTED, bg=BG).pack(side="left", padx=6)

    def _placeholder_explain(self):
        for w in self._explain_inner.winfo_children():
            w.destroy()
        tk.Label(self._explain_inner,
                 text="Run analysis to see\nAI-generated explanations.",
                 font=BODY_FONT, fg=MUTED, bg=CARD,
                 justify="left").pack(anchor="w", pady=20)

    # ── ANALYSIS ─────────────────────────────
    def _run_analysis(self):
        threading.Thread(target=self._analyze, daemon=True).start()

    def _analyze(self):
        try:
            age    = int(self._entries["Age"].get())
            income = float(self._entries["Monthly Income"].get())
            debt   = float(self._entries["Debt Ratio"].get())
            loan   = float(self._entries["Loan Amount"].get())
            score  = float(self._entries["Credit Score"].get())
            tenure = int(self._entries["Tenure (yrs)"].get())
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

        results = {}

        # ── Credit Risk ──
        if credit_model:
            feats = np.array([[debt, income/12000, loan/50000, score/850,
                               age/80, tenure/30, bal/100000, prods]])
            p = credit_model.predict_proba(feats)[0][1] * 100
        else:
            p = min(99, max(1, debt*60 + (loan/income)*20))
        results["credit"] = p

        # ── Fraud ──
        if fraud_model:
            feats = np.array([[loan, income, age, score, bal,
                               tenure, prods, active]])
            p = fraud_model.predict_proba(feats)[0][1] * 100
        else:
            p = min(99, max(1, (loan/income)*15 + (1-active)*10))
        results["fraud"] = p

        # ── Churn ──
        if churn_model:
            feats = np.array([[score, age, tenure, bal, prods,
                               1, active, income, gender, geo_de, geo_sp]])
            p = churn_model.predict_proba(feats)[0][1] * 100
        else:
            p = min(99, max(1, (1-active)*40 + (1/max(prods,1))*30 + (age/80)*20))
        results["churn"] = p

        # ── Spend forecast (regression → normalise to 0-100) ──
        if spend_model:
            feats = np.array([[income, age, bal, tenure, prods, score]])
            raw = float(spend_model.predict(feats)[0])
            p   = min(99, max(1, (raw / (income * 0.6)) * 50))
        else:
            p = min(99, max(1, (income * 0.35) / 500))
        results["spend"] = p

        self.root.after(0, lambda: self._update_ui(results, age, income,
                                                    debt, loan, score,
                                                    tenure, prods, bal,
                                                    active))

    def _color(self, pct):
        if pct < 35:   return SUCCESS
        if pct < 65:   return WARNING
        return DANGER

    def _tag(self, pct):
        if pct < 35:   return "LOW RISK"
        if pct < 65:   return "MEDIUM RISK"
        return "HIGH RISK"

    def _update_ui(self, results, age, income, debt,
                   loan, score, tenure, prods, bal, active):
        for key, val in results.items():
            c = self._color(val)
            self._cards[key].update(val, self._tag(val), c)

        # SHAP bars (feature importance approximation)
        cr = results["credit"]
        shap_rows = [
            ("Debt ratio",      min(100, debt*100),            DANGER  if debt > 0.5 else SUCCESS),
            ("Monthly income",  min(100, 100 - income/150),    SUCCESS if income > 4000 else DANGER),
            ("Loan amount",     min(100, loan/500),             DANGER  if loan > 15000 else SUCCESS),
            ("Credit score",    min(100, 100 - score/10),      SUCCESS if score > 700 else DANGER),
            ("Age",             min(100, age/80*100),           WARNING),
            ("Active member",   100 if active else 30,          SUCCESS if active else DANGER),
            ("Num products",    min(100, prods*25),             SUCCESS if prods > 1 else WARNING),
            ("Balance",         min(100, bal/2000),             SUCCESS if bal > 10000 else WARNING),
        ]
        self._shap_panel.show_bars(shap_rows)

        # Explainability reasons
        for w in self._explain_inner.winfo_children():
            w.destroy()

        reasons = []
        if debt > 0.6:
            reasons.append(("!", DANGER,
                f"Debt ratio {debt:.2f} exceeds safe threshold of 0.43 — elevated default risk."))
        if results["churn"] > 60:
            reasons.append(("!", DANGER,
                f"Churn probability {results['churn']:.0f}% — low product engagement detected."))
        if active:
            reasons.append(("+", SUCCESS,
                "Active member status reduces fraud and churn likelihood significantly."))
        if score > 700:
            reasons.append(("+", SUCCESS,
                f"Credit score {score:.0f} is above 700 — strong repayment history signal."))
        if income < 3000:
            reasons.append(("!", WARNING,
                f"Monthly income ${income:,.0f} may limit repayment capacity on this loan."))
        if prods == 1:
            reasons.append(("!", WARNING,
                "Single product usage — customers with 1 product have higher churn rates."))
        if not reasons:
            reasons.append(("+", SUCCESS,
                "Profile shows no major risk indicators across all four models."))

        for icon, color, text in reasons:
            row = tk.Frame(self._explain_inner, bg=CARD)
            row.pack(fill="x", pady=4)
            dot = tk.Label(row, text=icon,
                           font=("Helvetica", 10, "bold"),
                           fg=BG, bg=color,
                           width=2, height=1)
            dot.pack(side="left", padx=(0,8))
            tk.Label(row, text=text, font=("Helvetica", 9),
                     fg=TEXT, bg=CARD,
                     wraplength=280, justify="left",
                     anchor="w").pack(side="left", fill="x", expand=True)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app  = FinGuardApp(root)
    root.mainloop()