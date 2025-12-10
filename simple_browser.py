import sys
import json
import os
import time
from datetime import datetime
from PyQt6.QtCore import QUrl, Qt, QSize, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QMessageBox, QTabWidget, QMenu, QDialog, QPlainTextEdit,
    QInputDialog
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings

# --- Constants ---
DATA_FILE = "navi_data.json"
TWO_WEEKS_SECONDS = 1209600

# --- Helper Functions ---
def get_wholesome_history():
    return [
        {"url": "https://www.google.com/search?q=how+to+be+happy", "time": time.time(), "title": "Happiness"},
        {"url": "https://www.google.com/search?q=charity+work+near+me", "time": time.time() - 100, "title": "Charity"},
        {"url": "https://www.youtube.com/watch?v=cute_kittens", "time": time.time() - 200, "title": "Kittens"},
    ]

def is_seasonal(event):
    m = datetime.now().month
    d = datetime.now().day
    if event == "christmas": return m == 12 or (m == 1 and d <= 8)
    if event == "halloween": return m == 10
    return False

def get_search_url(engine, query):
    engines = {
        "Google": "https://www.google.com/search?q=",
        "Bing": "https://www.bing.com/search?q=",
        "Yahoo": "https://search.yahoo.com/search?p=",
        "DuckDuckGo": "https://duckduckgo.com/?q=",
        "Ecosia": "https://www.ecosia.org/search?q=",
        "Yandex": "https://yandex.com/search/?text="
    }
    return engines.get(engine, engines["Google"]) + query.replace(" ", "+")

# --- UI Styling Logic ---
class BrowserStyles:
    @staticmethod
    def get(theme, engine_mode):
        # Colors
        c = {
            "light": {"bg": "#f8f9fa", "fg": "#212529", "tab": "#ffffff", "sel": "#e9ecef", "bar": "#ffffff", "acc": "#0d6efd", "border": "#dee2e6"},
            "dark": {"bg": "#212529", "fg": "#f8f9fa", "tab": "#2c3034", "sel": "#343a40", "bar": "#343a40", "acc": "#0d6efd", "border": "#495057"},
            "christmas": {"bg": "#0f2e1c", "fg": "#fff", "tab": "#1a472a", "sel": "#c41e3a", "bar": "#1a472a", "acc": "#d4af37", "border": "#5d8a6f"},
            "halloween": {"bg": "#121212", "fg": "#ffa500", "tab": "#1f1f1f", "sel": "#2d2d2d", "bar": "#1f1f1f", "acc": "#ff4500", "border": "#444"},
            "cyberpunk": {"bg": "#0b0d17", "fg": "#00f3ff", "tab": "#121526", "sel": "#1c1f3a", "bar": "#121526", "acc": "#ff0099", "border": "#00f3ff"},
            "sunset": {"bg": "#2d1b2e", "fg": "#ffcc00", "tab": "#442244", "sel": "#b3446c", "bar": "#442244", "acc": "#f6511d", "border": "#b3446c"},
            "matrix": {"bg": "#000000", "fg": "#00ff00", "tab": "#0a0a0a", "sel": "#111", "bar": "#0a0a0a", "acc": "#008f11", "border": "#003300"},
        }.get(theme, {})

        if not c: c = {"bg": "#f8f9fa", "fg": "#212529", "tab": "#fff", "sel": "#e9ecef", "bar": "#fff", "acc": "#0d6efd", "border": "#dee2e6"}

        # Engine Mode (Legacy vs Modern)
        radius = "12px" if engine_mode == "modern" else "0px"
        padding = "8px 20px" if engine_mode == "modern" else "4px 10px"
        margin = "4px" if engine_mode == "modern" else "0px"
        bar_border = "0px" if engine_mode == "modern" else f"1px solid {c['border']}"

        return f"""
        QMainWindow {{ background-color: {c['bg']}; color: {c['fg']}; }}
        QWidget {{ color: {c['fg']}; }}
        QTabWidget::pane {{ border: 0; background: {c['bg']}; }}
        QTabBar::tab {{
            background: {c['tab']}; color: {c['fg']}; padding: {padding};
            border-top-left-radius: {radius}; border-top-right-radius: {radius};
            margin-right: {margin}; font-family: 'Segoe UI'; font-size: 13px;
        }}
        QTabBar::tab:selected {{ background: {c['sel']}; font-weight: bold; border-bottom: 3px solid {c['acc']}; }}
        QToolBar {{ background: {c['bar']}; border-bottom: 1px solid {c['border']}; spacing: 8px; padding: 6px; }}
        QLineEdit {{
            background: {c['bg']}; border: 1px solid {c['border']}; border-radius: {radius};
            padding: 8px 15px; color: {c['fg']}; font-size: 14px;
        }}
        QLineEdit:focus {{ border: 1px solid {c['acc']}; }}
        QPushButton {{
            background-color: transparent; border-radius: 6px; padding: 6px;
            color: {c['fg']}; font-weight: bold; font-size: 16px; border: {bar_border};
        }}
        QPushButton:hover {{ background-color: {c['tab']}; }}
        QMenu {{ background: {c['bar']}; color: {c['fg']}; border: 1px solid {c['border']}; }}
        QMenu::item:selected {{ background: {c['acc']}; color: #fff; }}
        """

# --- Internal Pages (HTML/CSS) ---
class InternalPages:
    @staticmethod
    def css(theme, bg_url):
        # Glassmorphism Logic
        is_dark = theme != "light"
        glass_bg = "rgba(0, 0, 0, 0.6)" if is_dark else "rgba(255, 255, 255, 0.8)"
        text = "#f8f9fa" if is_dark else "#212529"
        border = "rgba(255,255,255,0.1)" if is_dark else "rgba(0,0,0,0.1)"
        
        # Background handling
        body_bg = f"background-color: {bg_url};" if bg_url.startswith("#") else f"background-image: url('{bg_url}'); background-size: cover; background-position: center;"
        if not bg_url: body_bg = f"background-color: {'#212529' if is_dark else '#f8f9fa'};"

        return f"""
        body {{ font-family: 'Segoe UI', sans-serif; {body_bg} color: {text}; margin: 0; min-height: 100vh; backdrop-filter: blur(5px); }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 40px 20px; }}
        .card {{ 
            background: {glass_bg}; backdrop-filter: blur(10px); 
            padding: 25px; border-radius: 16px; margin-bottom: 20px; 
            border: 1px solid {border}; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }}
        h1, h2, h3 {{ color: {text}; margin-top: 0; }}
        .btn {{ 
            padding: 10px 20px; background: #0d6efd; color: white; border: none; border-radius: 8px; 
            text-decoration: none; cursor: pointer; display: inline-block; font-weight: 500; transition: 0.2s;
        }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(13, 110, 253, 0.4); }}
        .btn-gold {{ background: #ffc107; color: #000; }}
        .btn-danger {{ background: #dc3545; }}
        input, select, textarea {{ 
            width: 100%; padding: 12px; border-radius: 8px; border: 1px solid {border}; 
            background: rgba(255,255,255,0.1); color: {text}; margin-top: 5px; box-sizing: border-box;
        }}
        input:focus {{ outline: 2px solid #0d6efd; background: rgba(255,255,255,0.2); }}
        
        /* New Tab Specific */
        .nt-center {{ display: flex; flex-direction: column; align-items: center; justify-content: center; height: 85vh; }}
        .search-box {{ 
            width: 100%; max-width: 650px; padding: 18px 30px; border-radius: 50px; 
            font-size: 18px; border: none; box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            background: {glass_bg}; color: {text}; outline: none; transition: 0.3s;
        }}
        .search-box:focus {{ transform: scale(1.02); box-shadow: 0 15px 40px rgba(0,0,0,0.3); }}
        .widget-row {{ display: flex; gap: 15px; margin-top: 30px; flex-wrap: wrap; justify-content: center; }}
        .mini-card {{ background: {glass_bg}; padding: 15px; border-radius: 12px; text-align: center; min-width: 100px; cursor: pointer; transition: 0.2s; }}
        .mini-card:hover {{ background: rgba(255,255,255,0.2); }}
        .clock {{ font-size: 4em; font-weight: 200; margin-bottom: 20px; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }}
        """

    @staticmethod
    def new_tab(data):
        s = data['settings']
        widgets = data['inventory']
        
        # Zen Mode Check
        if s.get('zen_mode', False):
            return f"""<html><head><title>New Tab</title><style>{InternalPages.css(s['theme'], s.get('bg_url', ''))}</style>
            <script>
            function search(e){{ if(e.key==='Enter') window.location='navi://search/'+encodeURIComponent(e.target.value); }}
            </script></head><body>
            <div style="position:absolute; top:20px; right:20px;">
                <a href="navi://toggle/zen" class="btn" style="background:transparent; border:1px solid white;">Exit Zen</a>
            </div>
            <div class="nt-center">
                <input class="search-box" placeholder="Search..." onkeypress="search(event)" autofocus>
            </div></body></html>"""

        # Normal Mode
        extras = ""
        if "widgets" in widgets:
            extras = """
            <div class="card" style="width: 300px;">
                <b>🧮 Calc</b> <input onchange="this.value=eval(this.value)" placeholder="2*2">
            </div>"""

        return f"""<html><head><title>New Tab</title><style>{InternalPages.css(s['theme'], s.get('bg_url', ''))}</style>
        <script>
            function search(e){{ if(e.key==='Enter') window.location='navi://search/'+encodeURIComponent(e.target.value); }}
            setInterval(() => document.getElementById('clock').innerText = new Date().toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}}), 1000);
            function saveNote(v) {{ window.location='navi://save_notes/'+encodeURIComponent(v); }}
        </script></head><body>
        <div style="position:absolute; top:20px; right:20px; display:flex; gap:10px;">
            <a href="navi://customize" class="btn" style="background:rgba(0,0,0,0.5)">🎨 Customize</a>
            <a href="navi://toggle/zen" class="btn" style="background:rgba(0,0,0,0.5)">🧘 Zen</a>
            <span class="btn btn-gold">🪙 {data['navits']}</span>
        </div>
        
        <div class="nt-center">
            <div id="clock" class="clock">00:00</div>
            <input class="search-box" placeholder="Search {s['engine']} or type a URL..." onkeypress="search(event)" autofocus>
            
            <div class="widget-row">
                <a href="navi://pw" class="mini-card" style="text-decoration:none; color:inherit">🌐<br>Sites</a>
                <a href="navi://cws" class="mini-card" style="text-decoration:none; color:inherit">🧩<br>Exts</a>
                <a href="navi://dlw" class="mini-card" style="text-decoration:none; color:inherit">⬇️<br>Saved</a>
                <a href="navi://history" class="mini-card" style="text-decoration:none; color:inherit">🕒<br>History</a>
                <a href="navi://settings" class="mini-card" style="text-decoration:none; color:inherit">⚙️<br>Settings</a>
            </div>

            <div style="display:flex; gap:20px; margin-top:30px; align-items:start;">
                <div class="card" style="width: 300px; text-align:left;">
                    <b>📝 Notes</b>
                    <textarea style="height:100px; background:transparent; border:none;" oninput="saveNote(this.value)">{s['home_notes']}</textarea>
                </div>
                {extras}
            </div>
        </div></body></html>"""

# --- Custom Web Engine ---
class NaviWebPage(QWebEnginePage):
    def certificateError(self, error): return True
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() == "navi":
            view = self.view()
            if view and hasattr(view, 'main'):
                view.main.handle_cmd(url.toString(), view)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

# --- Browser Tab ---
class BrowserTab(QWebEngineView):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.yt_timer = QTimer(self); self.yt_timer.timeout.connect(self.check_yt); self.yt_timer.start(60000)
        self.yt_m = 0; self.last_yt = ""
        
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        
        self.setPage(NaviWebPage(self))
        self.page().loadFinished.connect(self.loaded)
        self.urlChanged.connect(self.url_chg)

    def url_chg(self, u):
        s = u.toString()
        if "youtube.com/watch" not in s: self.yt_m = 0
        elif s != self.last_yt: self.yt_m = 0; self.last_yt = s

    def check_yt(self):
        if "youtube.com/watch" in self.url().toString():
            self.yt_m += 1
            if self.yt_m == 15: self.main.add_navits(1, "YouTube"); self.yt_m = 0

    def loaded(self, ok):
        if not ok: return
        for e in self.main.data['extensions'].values():
            if e['active']: self.page().runJavaScript(e['code'])
        
        u = self.url().toString()
        if "google.com" in u or "duckduckgo" in u: self.main.search_reward(1)
        elif "ecosia" in u: self.main.search_reward(2)
        
        if not u.startswith("local://") and not u.startswith("navi://"):
            self.main.add_hist(u, self.title())

    def createWindow(self, _type): return self.main.add_tab()

# --- Main Window ---
class NaviBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser Ultimate v6")
        self.resize(1300, 900)
        self.data = {
            'sites': {}, 'extensions': {}, 'history': [], 'downloads': [],
            'settings': {'theme': 'light', 'engine': 'Google', 'suffix': '.pw-navi', 'wholesome': True, 'mode': 'modern', 'bg_url': '', 'home_notes': ''},
            'navits': 0, 'inventory': [], 'last_active': time.time(), 'last_reward': 0
        }
        self.load_data()
        self.check_dead_mans()
        self.setup_ui()
        self.apply_theme()
        self.add_tab(QUrl("local://navi/"))

    def setup_ui(self):
        tb = QToolBar(); tb.setMovable(False); self.addToolBar(tb)
        for t, f in [("←", self.back), ("→", self.fwd), ("⟳", self.reload), ("🏠", self.home)]:
            b = QPushButton(t); b.setFixedSize(38,38); b.clicked.connect(f); tb.addWidget(b)
        
        self.url = QLineEdit()
        self.url.setPlaceholderText("Search or enter URL..."); self.url.returnPressed.connect(self.nav)
        tb.addWidget(self.url)
        
        for t, f in [("⬇️", self.dl_page), ("< >", self.src), ("+", self.add_tab_safe)]:
            b = QPushButton(t); b.setFixedSize(38,38); b.clicked.connect(f); tb.addWidget(b)

        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True); self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda i: self.tabs.removeTab(i) if self.tabs.count()>1 else None)
        self.tabs.currentChanged.connect(self.upd_url)
        self.setCentralWidget(self.tabs)

    # --- Logic ---
    def add_tab_safe(self): self.add_tab()
    def add_tab(self, url=None, label="New Tab"):
        if not url: url = QUrl("local://navi/")
        b = BrowserTab(self); b.setUrl(url)
        b.urlChanged.connect(lambda q, b=b: self.upd_url_for(q, b))
        b.titleChanged.connect(lambda t, b=b: self.upd_title(t, b))
        i = self.tabs.addTab(b, label); self.tabs.setCurrentIndex(i); return b

    def nav(self):
        t = self.url.text().strip(); b = self.tabs.currentWidget()
        if not b: return
        if t.lower().startswith("navi://"): self.handle_cmd(t, b)
        elif t.endswith(self.data['settings']['suffix']):
            d = self.data['sites'].get(t.lower())
            if d: b.setHtml(d['html_content'], QUrl(f"local://{t}/"))
        else:
            u = QUrl(t) if "." in t else QUrl(get_search_url(self.data['settings']['engine'], t))
            if "://" not in t and "." in t: u = QUrl("https://"+t)
            b.setUrl(u)

    def upd_url_for(self, q, b):
        if b == self.tabs.currentWidget():
            u = q.toString()
            if u.startswith("local://navi/"): self.url.setText(u.replace("local://navi/", "navi://").strip("/"))
            elif not u.startswith("local://"): self.url.setText(u)
        if q.scheme() == "navi": self.handle_cmd(q.toString(), b)

    def upd_url(self, i): 
        if i>=0: self.upd_url_for(self.tabs.widget(i).url(), self.tabs.widget(i))
    def upd_title(self, t, b): 
        i = self.tabs.indexOf(b); 
        if i!=-1: self.tabs.setTabText(i, t[:15])

    def back(self): self.tabs.currentWidget().back() if self.tabs.currentWidget() else None
    def fwd(self): self.tabs.currentWidget().forward() if self.tabs.currentWidget() else None
    def reload(self): self.tabs.currentWidget().reload() if self.tabs.currentWidget() else None
    def home(self): self.tabs.currentWidget().setUrl(QUrl("local://navi/"))

    def search_reward(self, n):
        if time.time() - self.data['last_reward'] > 60: self.add_navits(n); self.data['last_reward'] = time.time()
    def add_navits(self, n, msg=""): self.data['navits']+=n; self.save_data(); print(f"+{n} {msg}")
    def add_hist(self, u, t):
        if not self.data['history'] or self.data['history'][0]['url']!=u:
            self.data['history'].insert(0, {'url':u, 'title':t, 'time':time.time()}); self.save_data()

    def check_dead_mans(self):
        if self.data['settings']['wholesome'] and time.time()-self.data['last_active']>TWO_WEEKS_SECONDS:
            self.data['history'] = get_wholesome_history()
        self.data['last_active'] = time.time(); self.save_data()

    # --- Internal Page Handler ---
    def handle_cmd(self, u, b):
        cmd = u.lower().replace("navi://", "").strip("/")
        st = self.data['settings']
        
        if cmd=="" or cmd=="home": b.setHtml(InternalPages.new_tab(self.data), QUrl("local://navi/"))
        elif cmd.startswith("search/"): b.setUrl(QUrl(get_search_url(st['engine'], QUrl.fromPercentEncoding(u.split("search/")[1].encode()))))
        
        elif cmd=="settings":
            engines = "".join([f"<option {'selected' if e==st['engine'] else ''}>{e}</option>" for e in ["Google","Bing","Yahoo","DuckDuckGo","Ecosia","Yandex"]])
            themes = "".join([f"<a href='navi://set/theme/{t}' class='btn' style='margin:5px'>{t.title()}</a>" for t in ["light","dark","cyberpunk","sunset","matrix"] if t in ["light","dark"] or t in self.data['inventory']])
            m_l = "checked" if st['mode']=="legacy" else ""; m_m = "checked" if st['mode']=="modern" else ""
            
            h = f"""<html><head><style>{InternalPages.css(st['theme'], st.get('bg_url',''))}</style></head><body><div class="container"><div class="card"><h1>Settings</h1>
            <h3>🎨 Visuals</h3>
            <p><b>Engine Mode:</b> <label><input type="radio" name="m" {m_m} onclick="window.location='navi://set/mode/modern'"> Modern (PyQt6)</label> <label><input type="radio" name="m" {m_l} onclick="window.location='navi://set/mode/legacy'"> Legacy (PyQt5 Style)</label></p>
            <p>{themes}</p>
            <h3>🔍 Search</h3><select onchange="window.location='navi://set/engine/'+this.value">{engines}</select>
            </div></div></body></html>"""
            b.setHtml(h, QUrl("local://navi/settings"))

        elif cmd=="customize":
            bg = st.get('bg_url','')
            h = f"""<html><head><style>{InternalPages.css(st['theme'], bg)}</style></head><body><div class="container"><div class="card"><h1>🎨 Customize New Tab</h1>
            <p>Enter a Hex Color (e.g., #000000) or an Image URL.</p>
            <input id="bg" value="{bg}" placeholder="https://image.jpg OR #123456">
            <br><button class="btn" onclick="window.location='navi://set/bg/'+encodeURIComponent(document.getElementById('bg').value)">Save Background</button>
            <button class="btn btn-danger" onclick="window.location='navi://set/bg/'">Reset</button>
            </div></div></body></html>"""
            b.setHtml(h, QUrl("local://navi/customize"))

        # Actions
        elif cmd.startswith("save_notes/"): st['home_notes'] = QUrl.fromPercentEncoding(u.split("notes/")[1].encode()); self.save_data()
        elif cmd.startswith("set/theme/"): st['theme'] = u.split("theme/")[1]; self.apply_theme(); self.save_data(); self.handle_cmd("navi://settings", b)
        elif cmd.startswith("set/engine/"): st['engine'] = u.split("engine/")[1]; self.save_data()
        elif cmd.startswith("set/mode/"): st['mode'] = u.split("mode/")[1]; self.apply_theme(); self.save_data(); self.handle_cmd("navi://settings", b)
        elif cmd.startswith("set/bg/"): 
            p = u.split("bg/"); val = QUrl.fromPercentEncoding(p[1].encode()) if len(p)>1 else ""
            st['bg_url'] = val; self.save_data(); self.handle_cmd("navi://home", b)
        elif cmd=="toggle/zen": st['zen_mode'] = not st.get('zen_mode', False); self.save_data(); self.handle_cmd("navi://home", b)

        # Stores/Navits
        elif cmd=="navits": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'],st.get('bg_url',''))}</style></head><body><div class='container'><div class='card'><h1>🏆 Navits: {self.data['navits']}</h1><a href='navi://store' class='btn btn-gold'>Store</a></div></div></body></html>", QUrl("local://navi/navits"))
        elif cmd=="store":
            inv = self.data['inventory']
            def itm(i,n,c,d): return f"<div class='card'><h3>{n}</h3><p>{d}</p><a href='navi://buy/{i}' class='btn btn-gold'>Buy ({c})</a></div>" if i not in inv else ""
            items = itm("widgets","Pro Widgets",200,"Calc & Calendar") + itm("cyberpunk","Cyberpunk",100,"Neon Theme") + itm("sunset","Sunset",100,"Chill Theme") + itm("matrix","Matrix",125,"Hacker Theme")
            b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'],st.get('bg_url',''))}</style></head><body><div class='container'><h1>🛒 Store</h1><p>Balance: {self.data['navits']}</p><div class='widget-grid'>{items}</div></div></body></html>", QUrl("local://navi/store"))
        elif cmd.startswith("buy/"):
            i = u.split("buy/")[1]; c = {"widgets":200,"cyberpunk":100,"sunset":100,"matrix":125}.get(i,999)
            if self.data['navits']>=c: self.data['navits']-=c; self.data['inventory'].append(i); self.save_data(); self.handle_cmd("navi://store",b)
            else: QMessageBox.warning(self,"Poor","Not enough Navits!")

        # Editors & Tools (Simplified routing)
        elif cmd=="pw": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'],st.get('bg_url',''))}</style></head><body><div class='container'><h1>Sites</h1><a href='navi://pw/new' class='btn'>+ New</a><br><br>{''.join([f'<div class=card><b>{v["title"]}</b> ({k}) <a href="{k}" class=btn>Go</a></div>' for k,v in self.data['sites'].items()])}</div></body></html>", QUrl("local://pw"))
        elif cmd=="pw/new": self.open_editor("site")
        elif cmd=="cws": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'],st.get('bg_url',''))}</style></head><body><div class='container'><h1>Extensions</h1><a href='navi://cws/new' class='btn'>+ New</a><br><br>{''.join([f'<div class=card><h3>{k}</h3><a href=navi://cws/toggle/{k} class=btn>Toggle</a></div>' for k in self.data['extensions']])}</div></body></html>", QUrl("local://cws"))
        elif cmd=="cws/new": self.open_editor("ext")
        elif cmd.startswith("cws/toggle/"): 
            n=u.split("toggle/")[1]; self.data['extensions'][n]['active'] = not self.data['extensions'][n]['active']; self.save_data(); self.handle_cmd("navi://cws",b)
        elif cmd=="history": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'],st.get('bg_url',''))}</style></head><body><div class='container'><h1>History</h1>{''.join([f'<div class=card><a href={h["url"]}>{h["title"]}</a></div>' for h in self.data["history"]])}</div></body></html>", QUrl("local://hist"))
        elif cmd=="dlw": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'],st.get('bg_url',''))}</style></head><body><div class='container'><h1>Downloads</h1>{''.join([f'<div class=card><h3>{d["title"]}</h3><a href=navi://dlw/view/{d["id"]} class=btn>View</a></div>' for d in self.data["downloads"]])}</div></body></html>", QUrl("local://dlw"))
        elif cmd.startswith("dlw/view/"): 
            did=u.split("view/")[1]; p=next((x for x in self.data['downloads'] if x['id']==did),None)
            if p: b.setHtml(p['html'], QUrl("local://offline"))

    def dl_page(self): self.tabs.currentWidget().page().toHtml(lambda h: self.save_dl(self.tabs.currentWidget().title(), h))
    def save_dl(self, t, h): self.data['downloads'].append({'title':t,'html':h,'id':str(int(time.time()))}); self.save_data()
    def src(self): self.tabs.currentWidget().page().toHtml(lambda h: SourceViewer(h, self).exec())
    
    def open_editor(self, m, k=None):
        d = QDialog(self); d.setWindowTitle("Editor"); d.resize(600,500); l=QVBoxLayout()
        nm = QLineEdit(); nm.setPlaceholderText("Name"); l.addWidget(nm)
        cd = QTextEdit(); cd.setPlaceholderText("Code/HTML"); l.addWidget(cd)
        def sv():
            if m=="site": self.data['sites'][nm.text()+self.data['settings']['suffix']]={'title':nm.text(),'html_content':cd.toPlainText(),'domain':nm.text()}
            else: self.data['extensions'][nm.text()]={'code':cd.toPlainText(),'active':True}
            self.save_data(); d.close()
        btn=QPushButton("Save"); btn.clicked.connect(sv); l.addWidget(btn); d.setLayout(l); d.exec()

    def save_data(self):
        try: 
            with open(DATA_FILE, 'w') as f: json.dump(self.data, f)
        except: pass
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f: 
                    d = json.load(f)
                    self.data.update(d)
                    # Migrations
                    s = self.data['settings']
                    if 'theme' not in s: s['theme']='light'
                    if 'mode' not in s: s['mode']='modern'
                    if 'bg_url' not in s: s['bg_url']=''
            except: pass

    def apply_theme(self):
        self.setStyleSheet(BrowserStyles.get(self.data['settings']['theme'], self.data['settings']['mode']))
        if self.tabs.currentWidget(): self.tabs.currentWidget().reload()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Navi Browser")
    window = NaviBrowser()
    window.show()
    sys.exit(app.exec())

