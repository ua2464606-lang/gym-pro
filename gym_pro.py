import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import cv2
import face_recognition
import numpy as np
from PIL import Image, ImageTk, ImageDraw
import os, sys, datetime, csv, threading, time, io, base64, random

# ─── PYINSTALLER COMPAT ───────────────────────────────────────
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

DB_PATH = resource_path("gymPro.db")

# ─── DATABASE ─────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS members (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT,
        plan TEXT DEFAULT 'monthly', fee REAL DEFAULT 0,
        join_date TEXT, due_day INTEGER DEFAULT 1,
        shift TEXT DEFAULT 'any', photo BLOB,
        face_encoding TEXT, active INTEGER DEFAULT 1
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id TEXT, member_name TEXT, date TEXT, time TEXT, method TEXT,
        UNIQUE(member_id, date)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS fees (
        member_id TEXT, month TEXT, status TEXT DEFAULT 'unpaid',
        paid_date TEXT, PRIMARY KEY(member_id, month)
    )""")
    conn.commit(); conn.close()

def get_conn(): return sqlite3.connect(DB_PATH)

# ═══════════════════════════════════════════════════════════════
#   THEME  —  MUSCLE FACTORY  (Black + Neon Green)
# ═══════════════════════════════════════════════════════════════
BG        = "#050508"
BG2       = "#0a0a0f"
SURFACE   = "#0d0d12"
CARD      = "#0f0f16"
CARD2     = "#141420"
BORDER    = "#1a1a28"
BORDER2   = "#252538"

NEON      = "#39ff14"
NEON_DIM  = "#071200"
NEON2     = "#00e676"
AMBER     = "#ffab00"
AMBER_DIM = "#1f1500"
RED       = "#ff1744"
RED_DIM   = "#1f0008"
GOLD      = "#ffd740"

TEXT      = "#e8eaf6"
TEXT2     = "#6c6c8a"
TEXT3     = "#363652"

FT        = ("Segoe UI",     11)
FT_SM     = ("Segoe UI",      9)
FT_MONO   = ("Consolas",     10)
FT_MONO_B = ("Consolas",     10, "bold")

# ─── HELPERS ──────────────────────────────────────────────────
def today_str():     return datetime.date.today().isoformat()
def now_time():      return datetime.datetime.now().strftime("%H:%M:%S")
def this_month():    return datetime.date.today().strftime("%Y-%m")
def yesterday_str(): return (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

def format_date(s):
    try:    return datetime.date.fromisoformat(s).strftime("%d %b %Y")
    except: return s

def gen_member_id():
    return "MF" + str(random.randint(100000, 999999))

def encode_face_from_image(img_bytes):
    try:
        nparr = np.frombuffer(img_bytes, np.uint8)
        img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb   = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        locs  = face_recognition.face_locations(rgb, model="hog")
        if not locs: return None
        enc = face_recognition.face_encodings(rgb, locs)[0]
        return base64.b64encode(enc.tobytes()).decode()
    except Exception as e:
        print("Face encode error:", e); return None

def decode_face_encoding(b64_str):
    return np.frombuffer(base64.b64decode(b64_str.encode()), dtype=np.float64)

def photo_to_tk(blob, size=(52, 52)):
    try:
        img  = Image.open(io.BytesIO(blob)).convert("RGBA").resize(size, Image.LANCZOS)
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size[0]-1, size[1]-1], fill=255)
        img.putalpha(mask)
        return ImageTk.PhotoImage(img)
    except: return None

def _lighten(h, a=25):
    r,g,b=int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(min(255,r+a),min(255,g+a),min(255,b+a))

def _darken(h, a=30):
    r,g,b=int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(max(0,r-a),max(0,g-a),max(0,b-a))

def _tint(hex_color, alpha=0.12, bg="#050508"):
    fc=[int(hex_color[i:i+2],16) for i in (1,3,5)]
    bc=[int(bg[i:i+2],16)        for i in (1,3,5)]
    bl=[int(fc[i]*alpha + bc[i]*(1-alpha)) for i in range(3)]
    return "#{:02x}{:02x}{:02x}".format(*bl)

# ═══════════════════════════════════════════════════════════════
#   WIDGETS
# ═══════════════════════════════════════════════════════════════
def NeonBtn(parent, text, command, color=NEON, fg=BG, **kw):
    wrap = tk.Frame(parent, bg=_tint(color, 0.35), padx=1, pady=1)
    b = tk.Button(wrap, text=text, command=command, bg=color, fg=fg,
                  relief="flat", bd=0, font=("Consolas", 10, "bold"),
                  cursor="hand2", padx=20, pady=10, **kw)
    b.pack(fill="both", expand=True)
    b.bind("<Enter>", lambda e: (b.config(bg=_lighten(color,35)), wrap.config(bg=_lighten(color,12))))
    b.bind("<Leave>", lambda e: (b.config(bg=color), wrap.config(bg=_tint(color,0.35))))
    return wrap

def SmallBtn(parent, text, command, color=NEON, fg=BG, **kw):
    b = tk.Button(parent, text=text, command=command, bg=color, fg=fg,
                  relief="flat", bd=0, font=("Consolas", 9, "bold"),
                  cursor="hand2", padx=14, pady=7, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=_lighten(color,30)))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

def GhostBtn(parent, text, command, **kw):
    b = tk.Button(parent, text=text, command=command, bg=BORDER, fg=TEXT2,
                  relief="flat", bd=0, font=("Consolas", 9, "bold"),
                  cursor="hand2", padx=14, pady=7, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=BORDER2, fg=TEXT))
    b.bind("<Leave>", lambda e: b.config(bg=BORDER, fg=TEXT2))
    return b

def DarkEntry(parent, textvariable=None, width=25, **kw):
    return tk.Entry(parent, textvariable=textvariable, width=width,
                    bg=CARD2, fg=TEXT, insertbackground=NEON,
                    relief="flat", bd=0, font=FT,
                    highlightthickness=1, highlightbackground=BORDER2,
                    highlightcolor=NEON, **kw)

def DarkCombo(parent, values, textvariable=None, width=22, **kw):
    s = ttk.Style()
    s.theme_use("default")
    s.configure("MF.TCombobox",
                fieldbackground=CARD2, background=BORDER2,
                foreground=TEXT, selectbackground=NEON_DIM,
                selectforeground=NEON, arrowcolor=NEON,
                bordercolor=BORDER2, lightcolor=BORDER2, darkcolor=BORDER2)
    s.map("MF.TCombobox", fieldbackground=[("readonly", CARD2)],
          foreground=[("readonly", TEXT)])
    return ttk.Combobox(parent, values=values, textvariable=textvariable,
                        width=width, style="MF.TCombobox", font=FT, state="readonly", **kw)

def HSep(parent, color=BORDER, **kw):
    return tk.Frame(parent, bg=color, height=1, **kw)

def Badge(parent, text, color=NEON):
    return tk.Label(parent, text=f"  {text}  ",
                    bg=_tint(color,0.18), fg=color,
                    font=("Consolas", 8, "bold"), relief="flat", padx=2, pady=3)

def SectionHeader(parent, title, icon="", accent=NEON, sub_var=None):
    f = tk.Frame(parent, bg=CARD)
    tk.Frame(f, bg=accent, height=2).pack(fill="x")
    row = tk.Frame(f, bg=CARD)
    row.pack(fill="x", padx=18, pady=(14,10))
    if icon:
        tk.Label(row, text=icon, font=("Segoe UI Emoji",14),
                 fg=accent, bg=CARD).pack(side="left", padx=(0,8))
    tk.Label(row, text=title, font=("Consolas",10,"bold"),
             fg=accent, bg=CARD).pack(side="left")
    if sub_var:
        tk.Label(row, textvariable=sub_var, font=("Consolas",8),
                 fg=TEXT2, bg=CARD).pack(side="right")
    return f

# ═══════════════════════════════════════════════════════════════
#   STAT CARD
# ═══════════════════════════════════════════════════════════════
class StatCard(tk.Frame):
    def __init__(self, parent, title, value_var, icon, accent=NEON, sub_var=None, **kw):
        super().__init__(parent, bg=CARD, **kw)
        tk.Frame(self, bg=accent, width=3).pack(side="left", fill="y")
        inner = tk.Frame(self, bg=CARD)
        inner.pack(fill="both", expand=True)
        tk.Frame(inner, bg=_tint(accent, 0.07), height=1).pack(fill="x")
        body = tk.Frame(inner, bg=CARD)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        top = tk.Frame(body, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text=icon, font=("Segoe UI Emoji",16),
                 fg=accent, bg=CARD).pack(side="left")
        tk.Label(top, text=title, font=("Consolas",8,"bold"),
                 fg=TEXT2, bg=CARD).pack(side="left", padx=10, pady=(3,0))
        tk.Label(body, textvariable=value_var,
                 font=("Consolas",36,"bold"), fg=accent, bg=CARD, anchor="w").pack(
                 fill="x", pady=(8,0))
        if sub_var:
            tk.Label(body, textvariable=sub_var, font=("Consolas",8),
                     fg=TEXT2, bg=CARD, anchor="w").pack(fill="x")

# ═══════════════════════════════════════════════════════════════
#   PRO TABLE
# ═══════════════════════════════════════════════════════════════
class ProTable(tk.Frame):
    def __init__(self, parent, columns, col_widths=None, row_height=44, accent=NEON, **kw):
        super().__init__(parent, bg=CARD, **kw)
        self.columns    = columns
        self.col_widths = col_widths or [150]*len(columns)
        self._rh        = row_height
        self._accent    = accent
        self._init_style()
        self._build()

    def _init_style(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("MFT.Treeview",
            background=CARD, foreground=TEXT, rowheight=self._rh,
            fieldbackground=CARD, borderwidth=0, font=FT, relief="flat")
        s.configure("MFT.Treeview.Heading",
            background=BG2, foreground=self._accent,
            font=("Consolas",9,"bold"), relief="flat", borderwidth=0)
        s.map("MFT.Treeview",
            background=[("selected", _tint(self._accent, 0.14))],
            foreground=[("selected",  self._accent)])
        s.configure("MFV.Vertical.TScrollbar",
            background=BORDER, troughcolor=BG, arrowcolor=TEXT3,
            bordercolor=BG, lightcolor=BORDER, darkcolor=BORDER,
            gripcount=0, relief="flat", width=5)
        s.map("MFV.Vertical.TScrollbar", background=[("active", BORDER2)])

    def _build(self):
        tk.Frame(self, bg=BORDER2, height=1).pack(fill="x")
        self.tree = ttk.Treeview(self, columns=self.columns,
                                  show="headings", style="MFT.Treeview", selectmode="browse")
        for col, w in zip(self.columns, self.col_widths):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=w, anchor="w", minwidth=40)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview,
                            style="MFV.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.tag_configure("odd",  background=CARD)
        self.tree.tag_configure("even", background=BG2)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def insert(self, values, tags=()):
        n   = len(self.tree.get_children())
        row = "even" if n % 2 == 0 else "odd"
        self.tree.insert("", "end", values=values, tags=(row,)+tuple(tags))

    def tag_config(self, tag, **kw):
        self.tree.tag_configure(tag, **kw)

# ═══════════════════════════════════════════════════════════════
#   TOAST
# ═══════════════════════════════════════════════════════════════
class Toast(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG, height=0)
        self._job = None; self._bar = None

    def show(self, msg, color=NEON):
        if self._bar:
            try: self._bar.destroy()
            except: pass
        self._bar = tk.Frame(self, bg=_darken(color, 55))
        self._bar.pack(fill="x")
        tk.Frame(self._bar, bg=color, width=4).pack(side="left", fill="y")
        tk.Label(self._bar, text=f"   {msg}   ", font=("Consolas",10),
                 fg=TEXT, bg=_darken(color,55), pady=11).pack(side="left")
        self.pack(fill="x", side="bottom")
        if self._job: self.after_cancel(self._job)
        self._job = self.after(3500, self._hide)

    def _hide(self):
        try:
            if self._bar: self._bar.destroy()
            self.pack_forget()
        except: pass

# ═══════════════════════════════════════════════════════════════
#   NAV BUTTON
# ═══════════════════════════════════════════════════════════════
class NavBtn(tk.Frame):
    def __init__(self, parent, icon, label, command, **kw):
        super().__init__(parent, bg=SURFACE, **kw)
        self._active = False
        self._stripe = tk.Frame(self, bg=SURFACE, width=3)
        self._stripe.pack(side="left", fill="y")
        self._inner  = tk.Frame(self, bg=SURFACE)
        self._inner.pack(side="left", fill="both", expand=True)
        self._ico = tk.Label(self._inner, text=icon, font=("Segoe UI Emoji",13),
                              fg=TEXT3, bg=SURFACE)
        self._ico.pack(side="left", padx=(16,10), pady=15)
        self._lbl = tk.Label(self._inner, text=label,
                              font=("Consolas",10,"bold"), fg=TEXT3, bg=SURFACE)
        self._lbl.pack(side="left")
        for w in (self, self._inner, self._ico, self._lbl, self._stripe):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>",    self._on)
            w.bind("<Leave>",    self._off)
        self.config(cursor="hand2")

    def _set_bg(self, col):
        for w in (self, self._inner, self._ico, self._lbl): w.config(bg=col)

    def _on(self, e=None):
        if not self._active: self._set_bg(_tint(NEON, 0.06))

    def _off(self, e=None):
        if not self._active: self._set_bg(SURFACE)

    def set_active(self, active):
        self._active = active
        if active:
            self._stripe.config(bg=NEON)
            self._set_bg(_tint(NEON, 0.10))
            self._ico.config(fg=NEON)
            self._lbl.config(fg=TEXT)
        else:
            self._stripe.config(bg=SURFACE)
            self._set_bg(SURFACE)
            self._ico.config(fg=TEXT3)
            self._lbl.config(fg=TEXT3)

# ═══════════════════════════════════════════════════════════════
#   MAIN APP
# ═══════════════════════════════════════════════════════════════
class MusclefactoryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MUSCLE FACTORY  —  Attendance & Management System")
        self.geometry("1440x860")
        self.minsize(1200,720)
        self.config(bg=BG)
        try:
            icon_path = resource_path("icon.ico")
            if os.path.exists(icon_path): self.iconbitmap(icon_path)
        except: pass
        try:    self.state("zoomed")
        except: self.attributes("-zoomed", True)

        init_db()
        self.current_page    = None
        self.camera_thread   = None
        self.cam_running     = False
        self.cap             = None
        self._scanning       = False
        self.detected_member = None
        self.photo_blob      = None
        self.editing_id      = None
        self._face_cache     = {}
        self._cam_frame      = None

        self._build_ui()
        self._load_face_cache()
        self._update_clock()
        self.show_page("dashboard")

    # ──────────────────── SKELETON ────────────────────────────
    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=SURFACE, width=242)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Frame(self.sidebar, bg=NEON, height=2).pack(fill="x")

        # Logo
        logo_bg = _tint(NEON, 0.07)
        logo_wrap = tk.Frame(self.sidebar, bg=logo_bg)
        logo_wrap.pack(fill="x")
        logo_inner = tk.Frame(logo_wrap, bg=logo_bg)
        logo_inner.pack(fill="x", padx=18, pady=18)

        icon_sq = tk.Frame(logo_inner, bg=NEON, width=44, height=44)
        icon_sq.pack(side="left"); icon_sq.pack_propagate(False)
        tk.Label(icon_sq, text="M", font=("Consolas",20,"bold"),
                 fg=BG, bg=NEON).place(relx=0.5,rely=0.5,anchor="center")

        name_f = tk.Frame(logo_inner, bg=logo_bg)
        name_f.pack(side="left", padx=(12,0))
        tk.Label(name_f, text="MUSCLE", font=("Consolas",14,"bold"),
                 fg=NEON, bg=logo_bg).pack(anchor="w")
        tk.Label(name_f, text="FACTORY", font=("Consolas",14,"bold"),
                 fg=TEXT, bg=logo_bg).pack(anchor="w")
        tk.Label(name_f, text="MANAGEMENT SYSTEM",
                 font=("Consolas",6,"bold"), fg=TEXT3, bg=logo_bg).pack(anchor="w",pady=(2,0))

        HSep(self.sidebar, BORDER).pack(fill="x")

        tk.Label(self.sidebar, text="MAIN MENU",
                 font=("Consolas",7,"bold"), fg=TEXT3, bg=SURFACE,
                 anchor="w").pack(fill="x", padx=18, pady=(16,6))

        self.nav_btns = {}
        for key, icon, lbl in [
            ("dashboard",  "📊", "Dashboard"),
            ("attendance", "📷", "Attendance"),
            ("members",    "👥", "Members"),
            ("fees",       "💰", "Fees"),
            ("reports",    "📋", "Reports"),
        ]:
            btn = NavBtn(self.sidebar, icon, lbl, command=lambda k=key: self.show_page(k))
            btn.pack(fill="x")
            self.nav_btns[key] = btn

        HSep(self.sidebar, BORDER).pack(fill="x", pady=(12,0))

        clock_f = tk.Frame(self.sidebar, bg=SURFACE)
        clock_f.pack(side="bottom", fill="x", padx=18, pady=18)
        HSep(self.sidebar, BORDER).pack(side="bottom", fill="x")

        self.clock_time = tk.StringVar()
        self.clock_date = tk.StringVar()
        tk.Label(clock_f, textvariable=self.clock_time,
                 font=("Consolas",24,"bold"), fg=NEON, bg=SURFACE).pack(anchor="w")
        tk.Label(clock_f, textvariable=self.clock_date,
                 font=("Consolas",8), fg=TEXT2, bg=SURFACE).pack(anchor="w")

        # Main
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        # Topbar
        topbar = tk.Frame(self.main, bg=SURFACE, height=62)
        topbar.pack(fill="x"); topbar.pack_propagate(False)
        HSep(topbar, BORDER).pack(side="bottom", fill="x")

        self.page_title_var = tk.StringVar(value="DASHBOARD")
        tk.Label(topbar, textvariable=self.page_title_var,
                 font=("Consolas",15,"bold"), fg=TEXT,
                 bg=SURFACE).pack(side="left", padx=26, pady=18)
        tk.Label(topbar, text="/", font=("Consolas",16), fg=TEXT3,
                 bg=SURFACE).pack(side="left")
        self.breadcrumb = tk.StringVar(value="Overview")
        tk.Label(topbar, textvariable=self.breadcrumb,
                 font=("Consolas",9), fg=TEXT2, bg=SURFACE).pack(side="left", padx=10)

        topright = tk.Frame(topbar, bg=SURFACE)
        topright.pack(side="right", padx=22, pady=12)
        NeonBtn(topright, "＋  NEW MEMBER", self.open_add_member, NEON, BG).pack(side="right")

        self.toast = Toast(self.main)

        self.content = tk.Frame(self.main, bg=BG)
        self.content.pack(fill="both", expand=True)

        self.pages = {}
        self._build_dashboard()
        self._build_attendance()
        self._build_members()
        self._build_fees()
        self._build_reports()

    def _update_clock(self):
        now = datetime.datetime.now()
        self.clock_time.set(now.strftime("%H:%M:%S"))
        self.clock_date.set(now.strftime("%A, %d %B %Y"))
        self.after(1000, self._update_clock)

    def show_page(self, name):
        if self.current_page:
            self.pages[self.current_page].pack_forget()
        for k, b in self.nav_btns.items():
            b.set_active(k == name)
        titles = {
            "dashboard":  ("DASHBOARD",  "Overview & Live Stats"),
            "attendance": ("ATTENDANCE", "Face Recognition & Manual Entry"),
            "members":    ("MEMBERS",    "Member Management"),
            "fees":       ("FEES",       "Payment Tracking"),
            "reports":    ("REPORTS",    "Attendance Reports & CSV Export"),
        }
        t, bc = titles.get(name, (name.upper(), ""))
        self.page_title_var.set(t); self.breadcrumb.set(bc)
        self.pages[name].pack(fill="both", expand=True)
        self.current_page = name
        refresh = {
            "dashboard":  self.refresh_dashboard,
            "attendance": self.refresh_att_manual,
            "members":    self.refresh_members,
            "fees":       self.refresh_fees,
            "reports":    self.refresh_reports,
        }
        if name in refresh: refresh[name]()
        if name != "attendance": self.stop_camera()
        else: self.after(300, self.start_camera)

    # ══════════════════════════════════════════
    #              DASHBOARD
    # ══════════════════════════════════════════
    def _build_dashboard(self):
        f = tk.Frame(self.content, bg=BG)
        self.pages["dashboard"] = f

        cards_f = tk.Frame(f, bg=BG)
        cards_f.pack(fill="x", padx=24, pady=(24,16))
        cards_f.columnconfigure((0,1,2,3), weight=1)

        self.stat_vars = {}
        self.stat_sub  = {}
        for i,(key,title,icon,color,sub_key) in enumerate([
            ("total_members","TOTAL MEMBERS","👥",NEON,  "s0"),
            ("today_present","PRESENT TODAY","✅",NEON2, "s1"),
            ("fees_paid",    "FEES PAID",   "💰",AMBER,  "s2"),
            ("fees_unpaid",  "DUES PENDING","⚠️", RED,    "s3"),
        ]):
            v  = tk.StringVar(value="0")
            sv = tk.StringVar(value="")
            self.stat_vars[key] = v
            self.stat_sub[sub_key] = sv
            StatCard(cards_f, title, v, icon, color, sv).grid(
                row=0, column=i, padx=6, sticky="nsew", ipady=6)

        HSep(f, BORDER).pack(fill="x", padx=24, pady=(0,18))

        # Three columns: today / yesterday / dues
        cols = tk.Frame(f, bg=BG)
        cols.pack(fill="both", expand=True, padx=24, pady=(0,24))
        cols.columnconfigure(0, weight=5)
        cols.columnconfigure(1, weight=4)
        cols.columnconfigure(2, weight=3)
        cols.rowconfigure(0, weight=1)

        # Today
        left = tk.Frame(cols, bg=CARD)
        left.grid(row=0, column=0, padx=(0,10), sticky="nsew")
        self._today_count_var = tk.StringVar(value="")
        SectionHeader(left, "TODAY'S ATTENDANCE", "📋", NEON, self._today_count_var).pack(fill="x")
        self.dash_log_table = ProTable(left,
            ["#","Name","Member ID","Check-in","Method"],
            [36,200,120,90,130], row_height=44, accent=NEON)
        self.dash_log_table.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Yesterday
        mid = tk.Frame(cols, bg=CARD)
        mid.grid(row=0, column=1, padx=(0,10), sticky="nsew")
        self._yest_count_var = tk.StringVar(value="")
        SectionHeader(mid, "YESTERDAY", "📅", AMBER, self._yest_count_var).pack(fill="x")
        self.dash_yest_table = ProTable(mid,
            ["#","Name","Check-in"],
            [36,210,90], row_height=44, accent=AMBER)
        self.dash_yest_table.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Dues
        right = tk.Frame(cols, bg=CARD)
        right.grid(row=0, column=2, sticky="nsew")
        SectionHeader(right, "DUES THIS MONTH", "⚠️", RED).pack(fill="x")
        self.fees_due_table = ProTable(right,
            ["Name","Amount"],
            [170,110], row_height=44, accent=RED)
        self.fees_due_table.pack(fill="both", expand=True, padx=10, pady=(0,10))

    def refresh_dashboard(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM members WHERE active=1")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM attendance WHERE date=?", (today_str(),))
        present = c.fetchone()[0]
        month = this_month()
        c.execute("SELECT COUNT(*) FROM fees WHERE month=? AND status='paid'", (month,))
        paid = c.fetchone()[0]
        unpaid = total - paid

        self.stat_vars["total_members"].set(str(total))
        self.stat_vars["today_present"].set(str(present))
        self.stat_vars["fees_paid"].set(str(paid))
        self.stat_vars["fees_unpaid"].set(str(unpaid))
        self.stat_sub["s0"].set("Active members")
        self.stat_sub["s1"].set(f"Out of {total} members")
        self.stat_sub["s2"].set(f"Cleared for {month}")
        self.stat_sub["s3"].set("Pending payment")

        # Today log
        self.dash_log_table.clear()
        c.execute("""SELECT member_name,member_id,time,method
                     FROM attendance WHERE date=? ORDER BY time DESC""", (today_str(),))
        rows = c.fetchall()
        self._today_count_var.set(f"{len(rows)} present")
        for i,(mn,mid,t,meth) in enumerate(rows,1):
            self.dash_log_table.insert([i,mn,mid,t,meth])

        # Yesterday log
        self.dash_yest_table.clear()
        c.execute("""SELECT member_name,time FROM attendance
                     WHERE date=? ORDER BY time DESC""", (yesterday_str(),))
        yrows = c.fetchall()
        self._yest_count_var.set(f"{len(yrows)} present")
        for i,(mn,t) in enumerate(yrows,1):
            self.dash_yest_table.insert([i,mn,t])
        if not yrows:
            self.dash_yest_table.insert(["—","No records",""])

        # Dues
        self.fees_due_table.clear()
        c.execute("""SELECT m.name,m.fee FROM members m
                     WHERE m.active=1 AND m.id NOT IN
                       (SELECT member_id FROM fees WHERE month=? AND status='paid')
                     ORDER BY m.name""", (month,))
        for mn,fee in c.fetchall():
            self.fees_due_table.insert([mn, f"PKR {fee:,.0f}"])
        self.fees_due_table.tag_config("odd",  foreground=RED)
        self.fees_due_table.tag_config("even", foreground=RED)
        conn.close()

    # ══════════════════════════════════════════
    #             ATTENDANCE
    # ══════════════════════════════════════════
    def _build_attendance(self):
        f = tk.Frame(self.content, bg=BG)
        self.pages["attendance"] = f

        tab_bar = tk.Frame(f, bg=SURFACE)
        tab_bar.pack(fill="x")
        HSep(tab_bar, BORDER).pack(side="bottom", fill="x")

        self.att_tab_btns = {}
        for key, lbl in [("face","📷  FACE RECOGNITION"),("manual","✎  MANUAL ENTRY")]:
            b = tk.Button(tab_bar, text=lbl, font=("Consolas",10,"bold"),
                          relief="flat", bd=0, padx=30, pady=15, cursor="hand2",
                          command=lambda k=key: self.switch_att_tab(k))
            b.pack(side="left")
            self.att_tab_btns[key] = b

        self.att_content = tk.Frame(f, bg=BG)
        self.att_content.pack(fill="both", expand=True)

        # Face tab
        self.att_face = tk.Frame(self.att_content, bg=BG)
        outer = tk.Frame(self.att_face, bg=BG)
        outer.pack(fill="both", expand=True, padx=22, pady=22)
        outer.columnconfigure(0,weight=3); outer.columnconfigure(1,weight=2)
        outer.rowconfigure(0,weight=1)

        cam_card = tk.Frame(outer, bg=CARD)
        cam_card.grid(row=0, column=0, padx=(0,12), sticky="nsew")
        SectionHeader(cam_card,"LIVE CAMERA FEED","📷",NEON).pack(fill="x")

        cam_sr = tk.Frame(cam_card, bg=CARD)
        cam_sr.pack(fill="x", padx=16, pady=(0,8))
        self.cam_status_dot = tk.Label(cam_sr,text="●",font=("Segoe UI",10),fg=RED,bg=CARD)
        self.cam_status_dot.pack(side="left")
        self.cam_status_lbl = tk.Label(cam_sr,text=" OFFLINE",font=("Consolas",9,"bold"),fg=RED,bg=CARD)
        self.cam_status_lbl.pack(side="left")

        cam_wrap = tk.Frame(cam_card, bg=BORDER2, padx=2, pady=2)
        cam_wrap.pack(padx=16, pady=(0,8))
        self.cam_canvas = tk.Canvas(cam_wrap, width=540, height=400,
                                     bg="#030308", highlightthickness=0)
        self.cam_canvas.pack()
        self.cam_canvas.create_text(270,200,text="[ CAMERA OFFLINE ]",
                                     fill=TEXT3,font=("Consolas",11),tags="init_txt")

        cam_foot = tk.Frame(cam_card, bg=CARD)
        cam_foot.pack(fill="x", padx=16, pady=(0,16))
        self.cam_label_var = tk.StringVar(value="Camera offline")
        tk.Label(cam_foot,textvariable=self.cam_label_var,
                 font=("Consolas",9),fg=TEXT2,bg=CARD).pack(side="left")
        SmallBtn(cam_foot,"◼  STOP",self.stop_camera,RED,TEXT).pack(side="right")

        det = tk.Frame(outer, bg=CARD)
        det.grid(row=0, column=1, sticky="nsew")
        SectionHeader(det,"SCAN RESULT","🎯",NEON2).pack(fill="x")

        photo_ring = tk.Frame(det, bg=_tint(NEON,0.25), width=100, height=100)
        photo_ring.pack(pady=(20,0)); photo_ring.pack_propagate(False)
        self.det_photo_lbl = tk.Label(photo_ring,text="?",
                                       font=("Consolas",36),fg=BORDER2,bg=CARD2,
                                       width=100,height=100)
        self.det_photo_lbl.place(relx=0.5,rely=0.5,anchor="center",width=96,height=96)

        self.det_name_var   = tk.StringVar(value="— — —")
        self.det_info_var   = tk.StringVar(value="Awaiting scan...")
        self.det_status_var = tk.StringVar(value="")
        self.det_conf_var   = tk.StringVar(value="")

        tk.Label(det,textvariable=self.det_name_var,
                 font=("Consolas",18,"bold"),fg=TEXT,bg=CARD).pack(pady=(12,0))
        tk.Label(det,textvariable=self.det_info_var,
                 font=("Consolas",9),fg=TEXT2,bg=CARD).pack(pady=2)
        tk.Label(det,textvariable=self.det_conf_var,
                 font=("Consolas",9,"bold"),fg=AMBER,bg=CARD).pack(pady=2)
        tk.Label(det,textvariable=self.det_status_var,
                 font=("Consolas",9),fg=GOLD,bg=CARD,wraplength=290).pack(pady=2)

        HSep(det,BORDER).pack(fill="x",padx=18,pady=10)
        btn_wrap = tk.Frame(det,bg=CARD); btn_wrap.pack(padx=18,fill="x")
        self.confirm_btn_wrap = NeonBtn(btn_wrap,"✓  MARK ATTENDANCE",
                                         self.confirm_attendance,NEON,BG)
        self.confirm_btn_wrap.pack(fill="x")
        self._confirm_inner = self.confirm_btn_wrap.winfo_children()[0]
        self._confirm_inner.config(state="disabled",bg=BORDER,fg=TEXT3)

        HSep(det,BORDER).pack(fill="x",padx=18,pady=(14,8))
        tk.Label(det,text="TODAY'S LOG",font=("Consolas",9,"bold"),fg=TEXT3,bg=CARD).pack(anchor="w",padx=18)
        self.att_log_table = ProTable(det,["Name","ID","Time","Method"],
            [140,90,75,110],row_height=38,accent=NEON)
        self.att_log_table.pack(fill="both",expand=True,padx=10,pady=(4,12))

        # Manual tab
        self.att_manual = tk.Frame(self.att_content, bg=BG)
        mcols = tk.Frame(self.att_manual, bg=BG)
        mcols.pack(fill="both",expand=True,padx=22,pady=22)
        mcols.columnconfigure(0,weight=3); mcols.columnconfigure(1,weight=2)
        mcols.rowconfigure(0,weight=1)

        left_m = tk.Frame(mcols,bg=CARD)
        left_m.grid(row=0,column=0,padx=(0,12),sticky="nsew")
        SectionHeader(left_m,"MANUAL ATTENDANCE","✎",AMBER).pack(fill="x")

        search_row = tk.Frame(left_m,bg=CARD)
        search_row.pack(fill="x",padx=14,pady=(0,10))
        tk.Label(search_row,text="🔍",font=("Segoe UI Emoji",12),fg=TEXT3,bg=CARD).pack(side="left",padx=(0,6))
        self.manual_search = tk.StringVar()
        self.manual_search.trace("w",lambda *_: self.refresh_att_manual())
        DarkEntry(search_row,self.manual_search,width=32).pack(side="left",fill="x",expand=True)

        self.manual_table = ProTable(left_m,["●","Name","Member ID","Status","Action"],
            [32,200,130,140,110],row_height=46,accent=AMBER)
        self.manual_table.pack(fill="both",expand=True,padx=10,pady=(0,12))
        self.manual_table.tree.bind("<ButtonRelease-1>",self._manual_click)

        right_m = tk.Frame(mcols,bg=CARD)
        right_m.grid(row=0,column=1,sticky="nsew")
        SectionHeader(right_m,"TODAY'S LOG","📋",AMBER).pack(fill="x")
        self.manual_log_table = ProTable(right_m,["#","Name","ID","Time"],
            [36,170,110,90],row_height=44,accent=AMBER)
        self.manual_log_table.pack(fill="both",expand=True,padx=10,pady=(0,12))

        self.switch_att_tab("face")

    def switch_att_tab(self, tab):
        col = NEON if tab=="face" else AMBER
        for k,b in self.att_tab_btns.items():
            is_a = (k==tab)
            b.config(fg=col if is_a else TEXT2,
                     bg=_tint(col,0.08) if is_a else SURFACE)
        self.att_face.pack_forget(); self.att_manual.pack_forget()
        if tab=="face":
            self.att_face.pack(fill="both",expand=True)
            self.after(200,self.start_camera)
        else:
            self.stop_camera()
            self.att_manual.pack(fill="both",expand=True)
            self.refresh_att_manual()

    def start_camera(self):
        if self.cam_running: return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Camera Error","Cannot open camera!\nCheck if another app is using it.")
            return
        self.cam_running = True
        self.cam_label_var.set("Camera LIVE  ●")
        self.cam_status_dot.config(fg=NEON)
        self.cam_status_lbl.config(text=" LIVE",fg=NEON)
        try: self.cam_canvas.delete("init_txt")
        except: pass
        self.camera_thread = threading.Thread(target=self._cam_loop,daemon=True)
        self.camera_thread.start()
        self.toast.show("Camera started",NEON)

    def _cam_loop(self):
        last_scan_time=0; scan_interval=2.5
        while self.cam_running:
            if self.cap and self.cap.isOpened():
                ret,frame = self.cap.read()
                if ret:
                    frame   = cv2.flip(frame,1)
                    display = frame.copy()
                    now     = time.time()
                    if not self._scanning and (now-last_scan_time)>=scan_interval:
                        last_scan_time=now; self._scanning=True
                        threading.Thread(target=self._auto_recognize,
                                         args=(frame.copy(),),daemon=True).start()
                    h,w = display.shape[:2]
                    if self._scanning:
                        cv2.rectangle(display,(4,4),(w-4,h-4),(57,255,20),2)
                        cl=22
                        for x,y in [(4,4),(w-5,4),(4,h-5),(w-5,h-5)]:
                            dx=1 if x<10 else -1; dy=1 if y<10 else -1
                            cv2.line(display,(x,y),(x+dx*cl,y),(57,255,20),3)
                            cv2.line(display,(x,y),(x,y+dy*cl),(57,255,20),3)
                        cv2.putText(display,"SCANNING...",(w//2-62,h-14),
                                    cv2.FONT_HERSHEY_SIMPLEX,0.55,(57,255,20),1)
                    img   = Image.fromarray(cv2.cvtColor(display,cv2.COLOR_BGR2RGB)).resize((540,400),Image.LANCZOS)
                    self._cam_frame = frame.copy()
                    photo = ImageTk.PhotoImage(img)
                    try:
                        self.cam_canvas.create_image(0,0,anchor="nw",image=photo)
                        self.cam_canvas._photo=photo
                    except: pass
            time.sleep(0.03)

    def _auto_recognize(self, frame):
        try:
            small = cv2.resize(frame,(0,0),fx=0.5,fy=0.5)
            rgb   = cv2.cvtColor(small,cv2.COLOR_BGR2RGB)
            locs  = face_recognition.face_locations(rgb,model="hog")
            if not locs: self._scanning=False; return
            encs  = face_recognition.face_encodings(rgb,locs)
            if not encs: self._scanning=False; return
            captured_enc=encs[0]; best_member_id=None; best_dist=0.55
            if not self._face_cache: self._scanning=False; return
            for mid,enc in self._face_cache.items():
                dist=face_recognition.face_distance([enc],captured_enc)[0]
                if dist<best_dist: best_dist=dist; best_member_id=mid
            if best_member_id:
                conn=get_conn(); c=conn.cursor()
                c.execute("SELECT id,name,phone,shift,photo,fee FROM members WHERE id=?",(best_member_id,))
                row=c.fetchone()
                c.execute("SELECT status FROM fees WHERE member_id=? AND month=?",
                          (best_member_id,this_month()))
                fs=c.fetchone(); conn.close()
                if row:
                    self.detected_member={
                        "id":row[0],"name":row[1],"phone":row[2],
                        "shift":row[3],"photo":row[4],"fee":row[5],
                        "fees_status":fs[0] if fs else "unpaid",
                        "confidence":round((1-best_dist)*100,1)
                    }
                    conn2=get_conn(); c2=conn2.cursor()
                    c2.execute("SELECT id FROM attendance WHERE member_id=? AND date=?",
                               (best_member_id,today_str()))
                    already=c2.fetchone(); conn2.close()
                    if not already:
                        self.after(0,lambda m=best_member_id,n=row[1]:
                                   self._mark_attendance(m,n,"Face Recognition"))
                    else:
                        self.after(0,lambda n=row[1]:
                                   self.toast.show(f"✔ {n} already marked today",GOLD))
                    self.after(0,self._show_detected)
        except Exception as e:
            self.after(0,lambda: self.toast.show(f"Scan error: {e}",RED))
        finally:
            self._scanning=False

    def stop_camera(self):
        self.cam_running=False
        if self.cap: self.cap.release(); self.cap=None
        self.cam_label_var.set("Camera offline")
        try:
            self.cam_status_dot.config(fg=RED)
            self.cam_status_lbl.config(text=" OFFLINE",fg=RED)
        except: pass
        self._cam_frame=None

    def _do_recognition(self, frame):
        try:
            small=cv2.resize(frame,(0,0),fx=0.5,fy=0.5)
            rgb=cv2.cvtColor(small,cv2.COLOR_BGR2RGB)
            locs=face_recognition.face_locations(rgb,model="hog")
            if not locs:
                self.after(0,lambda:self.toast.show("No face detected!",RED)); return
            encs=face_recognition.face_encodings(rgb,locs)
            if not encs:
                self.after(0,lambda:self.toast.show("Could not encode face!",RED)); return
            captured_enc=encs[0]; best_member_id=None; best_dist=0.55
            if not self._face_cache:
                self.after(0,lambda:self.toast.show("No members with photos!",AMBER)); return
            for mid,enc in self._face_cache.items():
                dist=face_recognition.face_distance([enc],captured_enc)[0]
                if dist<best_dist: best_dist=dist; best_member_id=mid
            if best_member_id:
                conn=get_conn(); c=conn.cursor()
                c.execute("SELECT id,name,phone,shift,photo,fee FROM members WHERE id=?",(best_member_id,))
                row=c.fetchone()
                c.execute("SELECT status FROM fees WHERE member_id=? AND month=?",
                          (best_member_id,this_month()))
                fs=c.fetchone(); conn.close()
                if row:
                    self.detected_member={
                        "id":row[0],"name":row[1],"phone":row[2],
                        "shift":row[3],"photo":row[4],"fee":row[5],
                        "fees_status":fs[0] if fs else "unpaid",
                        "confidence":round((1-best_dist)*100,1)
                    }
                    self.after(0,self._show_detected)
            else:
                self.after(0,lambda:self.toast.show("Face not recognized!",RED))
        except Exception as e:
            self.after(0,lambda:self.toast.show(f"Error: {e}",RED))

    def _show_detected(self):
        m=self.detected_member
        if not m: return
        if m["photo"]:
            tk_img=photo_to_tk(m["photo"],(92,92))
            if tk_img:
                self.det_photo_lbl.config(image=tk_img,text="",bg=CARD)
                self.det_photo_lbl._img=tk_img
        else:
            self.det_photo_lbl.config(image="",text="?",font=("Consolas",36),fg=BORDER2)
        self.det_name_var.set(m["name"])
        self.det_info_var.set(f"ID: {m['id']}   Shift: {m['shift'] or 'Any'}")
        self.det_conf_var.set(f"Match confidence: {m['confidence']}%")
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT time FROM attendance WHERE member_id=? AND date=?",
                  (m["id"],today_str()))
        already=c.fetchone(); conn.close()
        fees_txt="✔ Fees PAID" if m["fees_status"]=="paid" else "✖ Fees UNPAID"
        status_txt=fees_txt
        if already:
            status_txt+=f"   |   ✔ Marked @ {already[0]}"
            self._confirm_inner.config(state="disabled",bg=BORDER,fg=TEXT3,
                                        text="✔  ALREADY MARKED")
        else:
            self._confirm_inner.config(state="normal",bg=NEON,fg=BG,
                                        text="✓  MARK ATTENDANCE")
        self.det_status_var.set(status_txt)
        self.toast.show(f"Recognized: {m['name']} ({m['confidence']}% match)",NEON)

    def confirm_attendance(self):
        if not self.detected_member: return
        self._mark_attendance(self.detected_member["id"],
                              self.detected_member["name"],"Face Recognition")

    def _mark_attendance(self, mid, mname, method):
        conn=get_conn(); c=conn.cursor()
        try:
            c.execute("INSERT OR IGNORE INTO attendance(member_id,member_name,date,time,method) VALUES(?,?,?,?,?)",
                      (mid,mname,today_str(),now_time(),method))
            if c.rowcount==0:
                self.toast.show("Already marked present today!",AMBER)
            else:
                conn.commit()
                self.toast.show(f"✓ Attendance marked: {mname}",NEON)
                self._confirm_inner.config(state="disabled",bg=BORDER,fg=TEXT3,
                                            text="✔  ALREADY MARKED")
                self.refresh_att_log()
                self.refresh_att_manual()
                self.refresh_dashboard()
        except Exception as e:
            self.toast.show(f"Error: {e}",RED)
        finally:
            conn.close()

    def refresh_att_log(self):
        self.att_log_table.clear()
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT member_name,member_id,time,method FROM attendance WHERE date=? ORDER BY time DESC",
                  (today_str(),))
        for row in c.fetchall(): self.att_log_table.insert(list(row))
        conn.close()

    def refresh_att_manual(self):
        self.manual_table.clear(); self.manual_log_table.clear()
        search=self.manual_search.get().lower() if hasattr(self,"manual_search") else ""
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT id,name,phone,photo FROM members WHERE active=1 ORDER BY name")
        members=c.fetchall()
        c.execute("SELECT member_id,time FROM attendance WHERE date=?",(today_str(),))
        att_today={r[0]:r[1] for r in c.fetchall()}
        conn.close()
        for mid,mname,phone,photo in members:
            if search and search not in mname.lower() and search not in mid.lower(): continue
            status="✔  PRESENT" if mid in att_today else "—  ABSENT"
            tag="present" if mid in att_today else "absent"
            self.manual_table.insert(["●",mname,mid,status,
                                       "Remove" if mid in att_today else "Mark"],
                                      tags=(tag,mid))
        self.manual_table.tag_config("present",foreground=NEON)
        self.manual_table.tag_config("absent",foreground=TEXT3)
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT member_name,member_id,time,method FROM attendance WHERE date=? ORDER BY time DESC",
                  (today_str(),))
        for i,row in enumerate(c.fetchall(),1): self.manual_log_table.insert([i]+list(row))
        conn.close()

    def _manual_click(self, event):
        sel=self.manual_table.tree.selection()
        if not sel: return
        item=self.manual_table.tree.item(sel[0]); vals=item["values"]
        if not vals or len(vals)<3: return
        mname=vals[1]; mid=vals[2]; action=vals[4] if len(vals)>4 else ""
        if "Remove" in str(action):
            conn=get_conn()
            conn.execute("DELETE FROM attendance WHERE member_id=? AND date=?",(mid,today_str()))
            conn.commit(); conn.close()
            self.toast.show(f"Attendance removed: {mname}",AMBER)
        else:
            self._mark_attendance(mid,mname,"Manual")
        self.refresh_att_manual(); self.refresh_dashboard()

    # ══════════════════════════════════════════
    #               MEMBERS
    # ══════════════════════════════════════════
    def _build_members(self):
        f=tk.Frame(self.content,bg=BG); self.pages["members"]=f

        toolbar=tk.Frame(f,bg=SURFACE); toolbar.pack(fill="x")
        HSep(toolbar,BORDER).pack(side="bottom",fill="x")
        tb=tk.Frame(toolbar,bg=SURFACE); tb.pack(fill="x",padx=22,pady=14)

        sw=tk.Frame(tb,bg=BORDER2,padx=1,pady=1); sw.pack(side="left")
        si=tk.Frame(sw,bg=CARD2); si.pack()
        tk.Label(si,text="🔍",font=("Segoe UI Emoji",11),fg=TEXT3,bg=CARD2).pack(side="left",padx=8)
        self.mem_search=tk.StringVar()
        self.mem_search.trace("w",lambda *_: self.refresh_members())
        DarkEntry(si,self.mem_search,width=26).pack(side="left",pady=7,padx=(0,8))

        tk.Label(tb,text="FILTER:",font=("Consolas",8,"bold"),
                 fg=TEXT2,bg=SURFACE).pack(side="left",padx=(16,8))
        self.mem_filter=tk.StringVar(value="All")
        DarkCombo(tb,["All","Paid","Unpaid"],self.mem_filter,width=12).pack(side="left")
        self.mem_filter.trace("w",lambda *_: self.refresh_members())

        NeonBtn(tb,"＋  ADD MEMBER",self.open_add_member,NEON,BG).pack(side="right")
        self.mem_count_var=tk.StringVar(value="")
        tk.Label(tb,textvariable=self.mem_count_var,
                 font=("Consolas",9),fg=TEXT2,bg=SURFACE).pack(side="right",padx=16)

        self.mem_table=ProTable(f,
            ["Photo","Name","Member ID","Phone","Plan","Fee/mo","Shift","Status","Actions"],
            [52,170,120,130,100,120,90,95,140],row_height=50,accent=NEON)
        self.mem_table.pack(fill="both",expand=True,padx=18,pady=18)
        self.mem_table.tree.bind("<ButtonRelease-1>",self._member_action_click)

    def refresh_members(self):
        self.mem_table.clear()
        search=self.mem_search.get().lower() if hasattr(self,"mem_search") else ""
        filt=self.mem_filter.get() if hasattr(self,"mem_filter") else "All"
        month=this_month()
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT id,name,phone,plan,fee,shift FROM members WHERE active=1 ORDER BY name")
        rows=c.fetchall(); conn.close()
        count=0
        for mid,mname,phone,plan,fee,shift in rows:
            if search and search not in mname.lower() and search not in mid.lower(): continue
            fs=self._get_fees_status(mid,month)
            if filt=="Paid"   and fs!="paid": continue
            if filt=="Unpaid" and fs=="paid": continue
            fees_lbl="✔  PAID" if fs=="paid" else "✖  DUE"
            tag="paid" if fs=="paid" else "due"
            self.mem_table.insert(
                ["◈",mname,mid,phone or "—",plan or "monthly",
                 f"PKR {fee:,.0f}",shift or "any",fees_lbl,"✏  Edit   🗑  Del"],
                tags=(tag,mid))
            count+=1
        self.mem_table.tag_config("paid",foreground=NEON)
        self.mem_table.tag_config("due",foreground=RED)
        if hasattr(self,"mem_count_var"): self.mem_count_var.set(f"{count} members")

    def _member_action_click(self, event):
        sel=self.mem_table.tree.selection()
        if not sel: return
        item=self.mem_table.tree.item(sel[0]); vals=item["values"]
        if not vals or len(vals)<3: return
        mid=vals[2]
        col=self.mem_table.tree.identify_column(event.x)
        if col=="#9":
            x=event.x-sum(self.mem_table.col_widths[:8])
            if x<70: self.open_add_member(mid)
            else:
                if messagebox.askyesno("Confirm Delete",f"Delete member:\n{vals[1]}\n\nThis cannot be undone."):
                    self._delete_member(mid)

    def _delete_member(self, mid):
        conn=get_conn()
        conn.execute("UPDATE members SET active=0 WHERE id=?",(mid,))
        conn.commit(); conn.close()
        self._face_cache.pop(mid,None)
        self.refresh_members()
        self.toast.show("Member deleted",AMBER)

    # ══════════════════════════════════════════
    #          ADD / EDIT MEMBER
    # ══════════════════════════════════════════
    def open_add_member(self, edit_id=None):
        self.editing_id=edit_id; self.photo_blob=None
        win=tk.Toplevel(self)
        win.title("Add Member" if not edit_id else "Edit Member")
        win.geometry("600x780"); win.config(bg=BG); win.grab_set(); win.resizable(False,False)

        hdr=tk.Frame(win,bg=SURFACE); hdr.pack(fill="x")
        tk.Frame(hdr,bg=NEON,height=2).pack(fill="x")
        hdr_in=tk.Frame(hdr,bg=SURFACE); hdr_in.pack(fill="x",padx=24,pady=18)
        tk.Label(hdr_in,text="ADD NEW MEMBER" if not edit_id else "EDIT MEMBER",
                 font=("Consolas",14,"bold"),fg=TEXT,bg=SURFACE).pack(side="left")
        if not edit_id: Badge(hdr_in,"NEW",NEON).pack(side="left",padx=12)

        body=tk.Frame(win,bg=BG); body.pack(fill="both",expand=True,padx=26,pady=16)

        def flbl(txt):
            tk.Label(body,text=txt,font=("Consolas",8,"bold"),
                     fg=TEXT2,bg=BG,anchor="w").pack(fill="x",pady=(12,3))

        ps=tk.Frame(body,bg=BG); ps.pack(fill="x",pady=(0,10))
        pw=tk.Frame(ps,bg=BORDER2,width=104,height=104); pw.pack(side="left"); pw.pack_propagate(False)
        self._photo_lbl=tk.Label(pw,text="📷\nCLICK\nTO ADD",bg=CARD2,fg=TEXT3,
                                  cursor="hand2",font=("Consolas",8),justify="center")
        self._photo_lbl.place(relx=0.5,rely=0.5,anchor="center")
        self._photo_lbl.bind("<Button-1>",lambda e:self._pick_photo(win))
        pw.bind("<Button-1>",lambda e:self._pick_photo(win))

        pi=tk.Frame(ps,bg=BG); pi.pack(side="left",padx=16)
        tk.Label(pi,text="Profile Photo",font=("Consolas",10,"bold"),fg=TEXT,bg=BG).pack(anchor="w")
        tk.Label(pi,text="Required for face recognition\nJPG · PNG · BMP · WEBP",
                 font=("Consolas",8),fg=TEXT2,bg=BG,justify="left").pack(anchor="w",pady=4)
        SmallBtn(pi,"Choose File",lambda:self._pick_photo(win),NEON,BG).pack(anchor="w")

        HSep(body,BORDER).pack(fill="x",pady=(14,4))

        flbl("FULL NAME  *")
        v_name=tk.StringVar(); DarkEntry(body,v_name).pack(fill="x")

        flbl("PHONE NUMBER")
        v_phone=tk.StringVar(); DarkEntry(body,v_phone).pack(fill="x")

        r1=tk.Frame(body,bg=BG); r1.pack(fill="x"); r1.columnconfigure((0,1),weight=1)
        l1=tk.Frame(r1,bg=BG); l1.grid(row=0,column=0,padx=(0,8),sticky="ew")
        r1r=tk.Frame(r1,bg=BG); r1r.grid(row=0,column=1,sticky="ew")

        tk.Label(l1,text="MEMBERSHIP PLAN",font=("Consolas",8,"bold"),fg=TEXT2,bg=BG,anchor="w").pack(fill="x",pady=(12,3))
        v_plan=tk.StringVar(value="monthly")
        DarkCombo(l1,["monthly","quarterly","biannual","annual"],v_plan,width=20).pack(fill="x")

        tk.Label(r1r,text="MONTHLY FEE (PKR)",font=("Consolas",8,"bold"),fg=TEXT2,bg=BG,anchor="w").pack(fill="x",pady=(12,3))
        v_fee=tk.StringVar(); DarkEntry(r1r,v_fee).pack(fill="x")

        r2=tk.Frame(body,bg=BG); r2.pack(fill="x"); r2.columnconfigure((0,1),weight=1)
        l2=tk.Frame(r2,bg=BG); l2.grid(row=0,column=0,padx=(0,8),sticky="ew")
        r2r=tk.Frame(r2,bg=BG); r2r.grid(row=0,column=1,sticky="ew")

        tk.Label(l2,text="JOIN DATE",font=("Consolas",8,"bold"),fg=TEXT2,bg=BG,anchor="w").pack(fill="x",pady=(12,3))
        v_jdate=tk.StringVar(value=today_str()); DarkEntry(l2,v_jdate).pack(fill="x")

        tk.Label(r2r,text="FEE DUE DAY (1-31)",font=("Consolas",8,"bold"),fg=TEXT2,bg=BG,anchor="w").pack(fill="x",pady=(12,3))
        v_due=tk.StringVar(value="1"); DarkEntry(r2r,v_due).pack(fill="x")

        flbl("SHIFT / TIMING")
        v_shift=tk.StringVar(value="any")
        DarkCombo(body,["morning","afternoon","evening","any"],v_shift).pack(fill="x")

        if edit_id:
            conn=get_conn(); c=conn.cursor()
            c.execute("SELECT name,phone,plan,fee,join_date,due_day,shift,photo FROM members WHERE id=?",(edit_id,))
            m=c.fetchone(); conn.close()
            if m:
                v_name.set(m[0]); v_phone.set(m[1] or "")
                v_plan.set(m[2] or "monthly"); v_fee.set(str(m[3] or ""))
                v_jdate.set(m[4] or today_str()); v_due.set(str(m[5] or 1))
                v_shift.set(m[6] or "any")
                if m[7]: self.photo_blob=m[7]; self._show_photo_preview(m[7])

        HSep(body,BORDER).pack(fill="x",pady=16)
        btn_row=tk.Frame(body,bg=BG); btn_row.pack(fill="x")

        def save():
            name=v_name.get().strip()
            if not name: messagebox.showerror("Error","Name is required!",parent=win); return
            try: fee=float(v_fee.get() or 0)
            except: fee=0
            try: due=int(v_due.get() or 1)
            except: due=1
            face_enc=None
            if self.photo_blob:
                face_enc=encode_face_from_image(self.photo_blob)
                if face_enc is None and not edit_id:
                    if not messagebox.askyesno("Warning",
                        "No face detected in photo!\nSave anyway?",parent=win): return
            conn=get_conn(); c=conn.cursor()
            if edit_id:
                c.execute("""UPDATE members SET name=?,phone=?,plan=?,fee=?,
                             join_date=?,due_day=?,shift=?,
                             photo=COALESCE(?,photo),face_encoding=COALESCE(?,face_encoding)
                             WHERE id=?""",
                          (name,v_phone.get(),v_plan.get(),fee,
                           v_jdate.get(),due,v_shift.get(),self.photo_blob,face_enc,edit_id))
                mid=edit_id; self.toast.show("Member updated!",NEON)
            else:
                mid=gen_member_id()
                c.execute("""INSERT INTO members(id,name,phone,plan,fee,join_date,
                             due_day,shift,photo,face_encoding,active) VALUES(?,?,?,?,?,?,?,?,?,?,1)""",
                          (mid,name,v_phone.get(),v_plan.get(),fee,
                           v_jdate.get(),due,v_shift.get(),self.photo_blob,face_enc))
                self.toast.show(f"Member added! ID: {mid}",NEON)
            conn.commit(); conn.close()
            if face_enc: self._face_cache[mid]=decode_face_encoding(face_enc)
            win.destroy(); self.refresh_members(); self.refresh_dashboard()

        NeonBtn(btn_row,"💾  SAVE MEMBER",save,NEON,BG).pack(side="left",expand=True,fill="x",padx=(0,8))
        GhostBtn(btn_row,"Cancel",win.destroy).pack(side="left",expand=True,fill="x")

    def _pick_photo(self, parent):
        path=filedialog.askopenfilename(parent=parent,title="Select Profile Photo",
            filetypes=[("Images","*.jpg *.jpeg *.png *.bmp *.webp")])
        if not path: return
        with open(path,"rb") as fh: self.photo_blob=fh.read()
        self._show_photo_preview(self.photo_blob)

    def _show_photo_preview(self, blob):
        try:
            img=Image.open(io.BytesIO(blob)).convert("RGB").resize((100,100),Image.LANCZOS)
            ph=ImageTk.PhotoImage(img)
            self._photo_lbl.config(image=ph,text="",bg=BG,width=100,height=100)
            self._photo_lbl._img=ph
        except: pass

    # ══════════════════════════════════════════
    #                 FEES
    # ══════════════════════════════════════════
    def _build_fees(self):
        f=tk.Frame(self.content,bg=BG); self.pages["fees"]=f

        stats_f=tk.Frame(f,bg=BG); stats_f.pack(fill="x",padx=24,pady=(24,16))
        stats_f.columnconfigure((0,1,2),weight=1)
        self.fee_stat_vars={}
        for i,(key,title,icon,color) in enumerate([
            ("collected","TOTAL COLLECTED","💰",NEON),
            ("pending",  "PENDING DUES",   "⚠️", RED),
            ("rate",     "MEMBERS PAID",   "✅", AMBER),
        ]):
            v=tk.StringVar(value="—"); self.fee_stat_vars[key]=v
            StatCard(stats_f,title,v,icon,color).grid(row=0,column=i,padx=6,sticky="nsew",ipady=6)

        HSep(f,BORDER).pack(fill="x",padx=24,pady=(0,16))

        ctrl=tk.Frame(f,bg=BG); ctrl.pack(fill="x",padx=24,pady=(0,12))
        tk.Label(ctrl,text="MONTH:",font=("Consolas",9,"bold"),fg=TEXT2,bg=BG).pack(side="left")
        months=[]
        for i in range(6):
            d=datetime.date.today().replace(day=1)
            for _ in range(i): d=(d-datetime.timedelta(days=1)).replace(day=1)
            months.append(d.strftime("%Y-%m"))
        self.fees_month=tk.StringVar(value=months[0])
        DarkCombo(ctrl,months,self.fees_month,width=14).pack(side="left",padx=10)
        self.fees_month.trace("w",lambda *_: self.refresh_fees())

        self.fees_table=ProTable(f,
            ["Name","Member ID","Plan","Fee / mo","Due Date","Status","Action"],
            [180,120,100,120,130,110,130],row_height=46,accent=NEON)
        self.fees_table.pack(fill="both",expand=True,padx=18,pady=(0,18))
        self.fees_table.tree.bind("<ButtonRelease-1>",self._fees_action_click)

    def refresh_fees(self):
        self.fees_table.clear()
        month=self.fees_month.get() if hasattr(self,"fees_month") else this_month()
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT id,name,plan,fee,due_day FROM members WHERE active=1 ORDER BY name")
        members=c.fetchall()
        total_collected=total_pending=paid_count=0
        for mid,mname,plan,fee,due_day in members:
            fs=self._get_fees_status(mid,month)
            due_date=f"{month}-{str(due_day or 1).zfill(2)}"
            status_lbl="✔  PAID" if fs=="paid" else "✖  UNPAID"
            action_lbl="Mark Unpaid" if fs=="paid" else "Mark Paid"
            tag="paid" if fs=="paid" else "due"
            if fs=="paid": paid_count+=1; total_collected+=fee or 0
            else: total_pending+=fee or 0
            self.fees_table.insert(
                [mname,mid,plan or "monthly",f"PKR {fee:,.0f}",
                 format_date(due_date),status_lbl,action_lbl],tags=(tag,mid))
        conn.close()
        self.fees_table.tag_config("paid",foreground=NEON)
        self.fees_table.tag_config("due",foreground=RED)
        n=len(members)
        self.fee_stat_vars["collected"].set(f"PKR {total_collected:,.0f}")
        self.fee_stat_vars["pending"].set(f"PKR {total_pending:,.0f}")
        self.fee_stat_vars["rate"].set(f"{paid_count}/{n}")

    def _fees_action_click(self, event):
        sel=self.fees_table.tree.selection()
        if not sel: return
        vals=self.fees_table.tree.item(sel[0])["values"]
        if not vals or len(vals)<7: return
        mid=vals[1]; action=vals[6]
        month=self.fees_month.get() if hasattr(self,"fees_month") else this_month()
        new_status="unpaid" if "Unpaid" in str(action) else "paid"
        conn=get_conn()
        conn.execute("INSERT OR REPLACE INTO fees(member_id,month,status,paid_date) VALUES(?,?,?,?)",
                     (mid,month,new_status,today_str() if new_status=="paid" else None))
        conn.commit(); conn.close()
        self.toast.show(f"Fees marked {new_status.upper()}",
                        NEON if new_status=="paid" else AMBER)
        self.refresh_fees(); self.refresh_dashboard()

    # ══════════════════════════════════════════
    #               REPORTS
    # ══════════════════════════════════════════
    def _build_reports(self):
        f=tk.Frame(self.content,bg=BG); self.pages["reports"]=f

        toolbar=tk.Frame(f,bg=SURFACE); toolbar.pack(fill="x")
        HSep(toolbar,BORDER).pack(side="bottom",fill="x")
        tb=tk.Frame(toolbar,bg=SURFACE); tb.pack(fill="x",padx=22,pady=14)

        tk.Label(tb,text="DATE:",font=("Consolas",9,"bold"),fg=TEXT2,bg=SURFACE).pack(side="left")
        self.report_date=tk.StringVar(value=today_str())
        DarkEntry(tb,self.report_date,width=14).pack(side="left",padx=10)
        SmallBtn(tb,"🔍  LOAD",self.refresh_reports,NEON,BG).pack(side="left",padx=4)
        tk.Frame(tb,bg=BORDER2,width=1,height=30).pack(side="left",padx=14)
        SmallBtn(tb,"↓  EXPORT CSV",self.export_csv,AMBER,BG).pack(side="left")

        self.report_count_var=tk.StringVar(value="")
        tk.Label(tb,textvariable=self.report_count_var,
                 font=("Consolas",9),fg=TEXT2,bg=SURFACE).pack(side="right")

        self.report_table=ProTable(f,
            ["#","Name","Member ID","Check-in Time","Method","Date"],
            [42,220,130,120,170,130],row_height=46,accent=NEON)
        self.report_table.pack(fill="both",expand=True,padx=18,pady=18)

    def refresh_reports(self):
        self.report_table.clear()
        date=self.report_date.get() if hasattr(self,"report_date") else today_str()
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT member_name,member_id,time,method,date FROM attendance WHERE date=? ORDER BY time",(date,))
        rows=c.fetchall()
        for i,row in enumerate(rows,1): self.report_table.insert([i]+list(row))
        conn.close()
        if hasattr(self,"report_count_var"):
            self.report_count_var.set(f"{len(rows)} records for {format_date(date)}")

    def export_csv(self):
        date=self.report_date.get() if hasattr(self,"report_date") else today_str()
        path=filedialog.asksaveasfilename(
            defaultextension=".csv",filetypes=[("CSV","*.csv")],
            initialfile=f"attendance_{date}.csv")
        if not path: return
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT member_name,member_id,time,method,date FROM attendance WHERE date=? ORDER BY time",(date,))
        rows=c.fetchall(); conn.close()
        with open(path,"w",newline="",encoding="utf-8") as fh:
            w=csv.writer(fh); w.writerow(["Name","ID","Time","Method","Date"]); w.writerows(rows)
        self.toast.show(f"CSV exported: {os.path.basename(path)}",NEON)

    # ══════════════════════════════════════════
    #               UTILITIES
    # ══════════════════════════════════════════
    def _get_fees_status(self, mid, month):
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT status FROM fees WHERE member_id=? AND month=?",(mid,month))
        row=c.fetchone(); conn.close()
        return row[0] if row else "unpaid"

    def _load_face_cache(self):
        self._face_cache={}
        conn=get_conn(); c=conn.cursor()
        c.execute("SELECT id,face_encoding FROM members WHERE active=1 AND face_encoding IS NOT NULL")
        for mid,enc_str in c.fetchall():
            try: self._face_cache[mid]=decode_face_encoding(enc_str)
            except: pass
        conn.close()

    def on_close(self):
        self.stop_camera(); self.destroy()

# ─── ENTRY ────────────────────────────────────────────────────
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    app = MusclefactoryApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()