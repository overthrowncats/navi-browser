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

# --- UI Styling ---
class BrowserStyles:
    @staticmethod
    def get(theme, engine_mode):
        c = {
            "light": {"bg": "#f8f9fa", "fg": "#212529", "tab": "#ffffff", "sel": "#e9ecef", "bar": "#ffffff", "acc": "#0d6efd", "border": "#dee2e6"},
            "dark": {"bg": "#212529", "fg": "#f8f9fa", "tab": "#2c3034", "sel": "#343a40", "bar": "#343a40", "acc": "#0d6efd", "border": "#495057"},
            "christmas": {"bg": "#0f2e1c", "fg": "#fff", "tab": "#1a472a", "sel": "#c41e3a", "bar": "#1a472a", "acc": "#d4af37", "border": "#5d8a6f"},
            "halloween": {"bg": "#121212", "fg": "#ffa500", "tab": "#1f1f1f", "sel": "#2d2d2d", "bar": "#1f1f1f", "acc": "#ff4500", "border": "#444"},
            "cyberpunk": {"bg": "#0b0d17", "fg": "#00f3ff", "tab": "#121526", "sel": "#1c1f3a", "bar": "#121526", "acc": "#ff0099", "border": "#00f3ff"},
            "sunset": {"bg": "#2d1b2e", "fg": "#ffcc00", "tab": "#442244", "sel": "#b3446c", "bar": "#442244", "acc": "#f6511d", "border": "#b3446c"},
            "matrix": {"bg": "#000000", "fg": "#00ff00", "tab": "#0a0a0a", "sel": "#111", "bar": "#0a0a0a", "acc": "#008f11", "border": "#003300"},
        }.get(theme, {})
        if not c: c = {"bg": "#222222", "fg": "#f8f9fa", "tab": "#2c3034", "sel": "#343a40", "bar": "#343a40", "acc": "#0d6efd", "border": "#495057"}

        radius = "12px" if engine_mode == "modern" else "0px"
        padding = "8px 20px" if engine_mode == "modern" else "4px 10px"
        margin = "4px" if engine_mode == "modern" else "0px"
        bar_border = "0px" if engine_mode == "modern" else f"1px solid {c['border']}"
        font = "'Poppins', sans-serif" if engine_mode == "modern" else "'Segoe UI', sans-serif"

        return f"""
        QMainWindow {{ background-color: {c['bg']}; color: {c['fg']}; }}
        QWidget {{ color: {c['fg']}; font-family: {font}; }}
        QTabWidget::pane {{ border: 0; background: {c['bg']}; }}
        QTabBar::tab {{ background: {c['tab']}; color: {c['fg']}; padding: {padding}; border-top-left-radius: {radius}; border-top-right-radius: {radius}; margin-right: {margin}; font-size: 13px; }}
        QTabBar::tab:selected {{ background: {c['sel']}; font-weight: bold; border-bottom: 3px solid {c['acc']}; }}
        QToolBar {{ background: {c['bar']}; border-bottom: 1px solid {c['border']}; spacing: 8px; padding: 6px; }}
        QLineEdit {{ background: {c['bg']}; border: 1px solid {c['border']}; border-radius: {radius}; padding: 8px 15px; color: {c['fg']}; font-size: 14px; }}
        QLineEdit:focus {{ border: 1px solid {c['acc']}; }}
        QPushButton {{ background-color: transparent; border-radius: 6px; padding: 6px; color: {c['fg']}; font-weight: bold; font-size: 16px; border: {bar_border}; }}
        QPushButton:hover {{ background-color: {c['tab']}; }}
        QMenu {{ background: {c['bar']}; color: {c['fg']}; border: 1px solid {c['border']}; }}
        QMenu::item:selected {{ background: {c['acc']}; color: #fff; }}
        """

# --- Internal Pages Generator ---
class InternalPages:
    @staticmethod
    def css(theme):
        is_dark = theme != "light"
        bg = "#2b3035" if is_dark else "#f8f9fa"
        card_bg = "#343a40" if is_dark else "#ffffff"
        text = "#f8f9fa" if is_dark else "#212529"
        border = "#495057" if is_dark else "#dee2e6"
        return f"""
        body {{ font-family: 'Poppins', sans-serif; background: {bg}; color: {text}; padding: 40px; margin: 0; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #0d6efd; }}
        .card {{ background: {card_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px; border: 1px solid {border}; }}
        .btn {{ padding: 8px 16px; background: #0d6efd; color: white; border: none; border-radius: 6px; text-decoration: none; cursor: pointer; display: inline-block; margin-right: 5px; }}
        .btn:hover {{ background: #0b5ed7; }}
        .btn-danger {{ background: #dc3545; }}
        .btn-gold {{ background: #ffc107; color: #000; }}
        .widget-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        input, select {{ padding: 10px; border-radius: 6px; border: 1px solid {border}; background: {bg}; color: {text}; width: 100%; box-sizing: border-box; }}
        """

    @staticmethod
    def new_tab(data):
        s = data['settings']
        navits = data['navits']
        
        # User requested background
        if s.get('bg_url') and not s['bg_url'].startswith('#'):
            bg_style = f"background-image: url('{s['bg_url']}');"
        else:
            bg_style = f"background-color: {s.get('bg_url', '#222222')};"

        navit_display = f'<span class="btn btn-gold" style="position: absolute; top: 20px; right: 20px;">🪙 {navits}</span>'

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>New Tab</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
        
        body {{ {bg_style} background-size: cover; background-position: center; color: #FFFFFF; font-family: "Poppins", serif; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; flex-direction: column; transition: background-image 0.5s ease; }}
        
        .container {{ text-align: center; position: relative; max-width: 900px; width: 95%; display: flex; flex-direction: column; align-items: center; }}
        
        h1 {{ font-size: 3em; margin-bottom: 20px; color: rgba(255, 255, 255, 0.9); text-shadow: 0 0 10px rgba(0, 0, 0, 0.7); }}
        
        .search-box {{ padding: 12px; font-size: 1.3em; font-family: "Poppins", serif; width: 500px; max-width: 80vw; border-radius: 15px; border: none; background-color: rgba(51, 51, 51, 0.7); color: #FFFFFF; margin-bottom: 20px; backdrop-filter: blur(5px); transition: box-shadow 0.3s ease; }}
        .search-box:focus {{ outline: none; box-shadow: 0 0 20px #000000d7; }}
        
        .settings, .sidebar-toggle, .sidebar {{ z-index: 1000; }}
        
        .settings {{ position: fixed; top: 20px; left: 60px; display: flex; gap: 10px; align-items: center; }}
        .settings input {{ padding: 8px; background-color: rgba(51, 51, 51, 0.8); color: #FFFFFF; border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 8px; }}
        .settings button {{ padding: 8px 12px; border: none; border-radius: 8px; background-color: #0d6efd; color: white; cursor: pointer; font-family: "Poppins", serif; }}
        
        .sidebar-toggle {{ position: fixed; left: 10px; top: 10px; cursor: pointer; padding: 10px; background-color: #333333b0; border-radius: 50%; backdrop-filter: blur(5px); }}
        
        .sidebar {{ position: fixed; left: -300px; top: 0; width: 300px; height: 100vh; background-color: #33333381; transition: left 0.5s ease; padding: 20px; box-sizing: border-box; overflow-y: auto; backdrop-filter: blur(10px); }}
        .sidebar.open {{ left: 0; }}
        
        .background-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 20px; }}
        .background-option {{ width: 100%; height: 100px; background-size: cover; background-position: center; border-radius: 5px; cursor: pointer; transition: 0.3s; border: 3px solid transparent; }}
        .background-option:hover {{ transform: scale(1.02); box-shadow: 0 0 15px rgba(255,255,255,0.4); }}
        
        .material-icons {{ color: white; font-size: 24px; }}
        
        /* Widget Grid */
        .widget-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; width: 100%; max-width: 600px; margin-top: 20px; }}
        .mini-card {{ background: rgba(51,51,51,0.7); backdrop-filter: blur(5px); padding: 15px; border-radius: 12px; text-align: center; color: white; text-decoration: none; transition: 0.2s; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 80px; }}
        .mini-card:hover {{ background: rgba(0,0,0,0.5); transform: translateY(-3px); }}
        
        .btn-gold {{ background: #ffc107; color: #000; padding: 8px 15px; border-radius: 20px; text-decoration: none; font-weight: bold; }}
    </style>
    <script>
        const backgrounds = [
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR5hNaF09ykqTB3f7Vh0bjIdZwnjP8zgLK3ltDyjk91Fw&s=10',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRX-_RMHWqoAs6PkpHB9N0Lbar1hOTmJLDaK1ExfZiVJA&s=10',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ7aaASVlsLNoAIyXAlkAy3CInHuYaejCIRrYcwo8ZWSQ&s=10',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTyigMXGvP60gWjZ8W5W4sMfcYTe303m5u3pViEeVjjuw&s=10',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTHb8KtmhdnOBZey7jZ_SJxIN0xheUbuuy28QjCB4kXfQ&s=10',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTAakSD_9_vTzNUvHm0_FACBw_Bk3-oJoA1ySd2pPOOfw&s=10',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQHcTxQ_JwawDivZOCGADoK2E7biH6YwoZ4vlhn7cSTTw&s=10',
            'https://plus.unsplash.com/premium_photo-1733306435632-9860ace48cb9?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8b3V0ZXIlMjBoZWJyaWRlc3xlbnwwfHwwfHx8MA%3D%3D'
        ];
        
        function handleSearch(e) {{
            if (e.key === 'Enter') window.location.href = 'app://navigate?url=' + encodeURIComponent(e.target.value);
        }}
        function setBg(url) {{ window.location.href = 'navi://set/bg/' + encodeURIComponent(url); }}
        function toggleSidebar() {{ document.querySelector('.sidebar').classList.toggle('open'); }}
        
        document.addEventListener('DOMContentLoaded', () => {{
            const grid = document.querySelector('.background-grid');
            backgrounds.forEach(bg => {{
                const div = document.createElement('div'); div.className = 'background-option';
                div.style.backgroundImage = `url('${{bg}}')`;
                div.onclick = () => setBg(bg);
                grid.appendChild(div);
            }});
            document.querySelector('.search-box').focus();
        }});
    </script>
</head>
<body>
    {navit_display}
    <div class="sidebar-toggle" onclick="toggleSidebar()"><span class="material-icons">wallpaper</span></div>
    <div class="sidebar">
        <h2 style="color: white; text-align: center;">Backgrounds</h2>
        <div class="background-grid"></div>
    </div>
    <div class="settings">
        <input type="text" id="bgUrl" placeholder="Background URL">
        <button onclick="setBg(document.getElementById('bgUrl').value)">Set</button>
    </div>
    <div class="container">
        <h1>New Tab</h1>
        <input type="text" class="search-box" placeholder="Search or enter URL" onkeypress="handleSearch(event)">
        
        <!-- Restored Feature Grid -->
        <div class="widget-grid">
            <a href="navi://pw" class="mini-card"><span class="material-icons">language</span><br>Sites</a>
            <a href="navi://cws" class="mini-card"><span class="material-icons">extension</span><br>Exts</a>
            <a href="navi://history" class="mini-card"><span class="material-icons">history</span><br>History</a>
            <a href="navi://dlw" class="mini-card"><span class="material-icons">download</span><br>Saved</a>
            <a href="navi://store" class="mini-card"><span class="material-icons">store</span><br>Store</a>
            <a href="navi://settings" class="mini-card"><span class="material-icons">settings</span><br>Settings</a>
        </div>
    </div>
    <small class="credit">Original HTML by cursorhex on github</small>

<style>
.credit {
  font-size: 0.6rem;
  opacity: 0.6;
}
</style>
</body>
</html>
"""

# --- Editors ---
class CodeEditor(QWidget):
    def __init__(self, main, mode="site", key=None):
        super().__init__()
        self.main, self.mode, self.key = main, mode, key
        self.resize(900, 700); self.setWindowTitle("Navi Editor")
        l = QVBoxLayout()
        self.name = QLineEdit(); self.name.setPlaceholderText("Name"); l.addWidget(QLabel("Name")); l.addWidget(self.name)
        if key: 
            clean_key = key.replace(main.data['settings']['suffix'], "") if mode=="site" else key
            self.name.setText(clean_key); self.name.setReadOnly(True)
        
        if mode=="site": 
            self.ti = QLineEdit(); self.ti.setPlaceholderText("Title"); l.addWidget(QLabel("Title")); l.addWidget(self.ti)
        
        self.code = QTextEdit(); self.code.setPlaceholderText("HTML Code" if mode=="site" else "JavaScript Code"); l.addWidget(QLabel("Code")); l.addWidget(self.code)
        
        btn = QPushButton("Save"); btn.setStyleSheet("background:#198754;color:white;padding:10px;"); btn.clicked.connect(self.save); l.addWidget(btn)
        self.setLayout(l)
        
        if key:
            d = main.data['sites' if mode=="site" else 'extensions'].get(key)
            if d:
                self.code.setText(d['html_content'] if mode=="site" else d['code'])
                if mode=="site": self.ti.setText(d['title'])

    def save(self):
        n = self.name.text().strip()
        c = self.code.toPlainText()
        if not n: return
        
        if self.mode == "site":
            s = self.main.data['settings']['suffix']
            f = f"{n.lower()}{s}" if not n.endswith(s) else n.lower()
            self.main.data['sites'][f] = {'domain': f, 'title': self.ti.text(), 'html_content': c}
            self.main.add_tab(QUrl(f"local://{f}/"))
        else:
            self.main.data['extensions'][n] = {'code': c, 'active': True}
        
        self.main.save_data(); self.close()

class SourceViewer(QDialog):
    def __init__(self, t, p=None):
        super().__init__(p); self.resize(800,600); e=QPlainTextEdit(t); e.setReadOnly(True); l=QVBoxLayout(); l.addWidget(e); self.setLayout(l)

# --- Browser Tab ---
class BrowserTab(QWebEngineView):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.yt_t = QTimer(self); self.yt_t.timeout.connect(self.chk_yt); self.yt_t.start(60000)
        self.yt_m = 0
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        self.setPage(NaviWebPage(self)) 
        self.page().loadFinished.connect(self.loaded)

    def chk_yt(self):
        if "youtube.com/watch" in self.url().toString():
            self.yt_m += 1
            if self.yt_m == 15: self.main.add_navits(1, "YouTube"); self.yt_m = 0

    def loaded(self, ok):
        if not ok: return
        for e in self.main.data['extensions'].values():
            if e['active']: self.page().runJavaScript(e['code'])
        
        u = self.url().toString()
        if "google.com" in u or "duckduckgo" in u: self.main.sch_rwd(1)
        elif "ecosia" in u: self.main.sch_rwd(2)
        
        if not u.startswith("local://") and not u.startswith("navi://") and not u.startswith("app://"):
            self.main.add_hist(u, self.title())

    def createWindow(self, _type): return self.main.add_tab()

# --- Custom Web Page with View Fix ---
class NaviWebPage(QWebEnginePage):
    def __init__(self, view):
        super().__init__(view)
        self.view_ref = view # Explicitly store view reference to prevent AttributeError

    def certificateError(self, error): return True
    
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() in ["navi", "app"]:
            if self.view_ref and hasattr(self.view_ref, 'main'):
                self.view_ref.main.handle_cmd(url.toString(), self.view_ref)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

# --- Main Window ---
class NaviBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser Ultimate v7")
        self.resize(1300, 900)
        # Default Data Structure
        self.data = {
            'sites': {}, 'extensions': {}, 'history': [], 'downloads': [],
            'settings': {'theme': 'dark', 'engine': 'Google', 'suffix': '.pw-navi', 'wholesome': True, 'mode': 'modern', 'bg_url': ''},
            'navits': 0, 'inventory': [], 'last_active': time.time(), 'last_reward': 0
        }
        self.load_data()
        self.check_dead()
        self.setup_ui()
        self.apply_theme()
        self.add_tab(QUrl("local://navi/"))

    def setup_ui(self):
        tb = QToolBar(); tb.setMovable(False); self.addToolBar(tb)
        for t, f in [("←", self.back), ("→", self.fwd), ("⟳", self.reload), ("🏠", self.home)]:
            b = QPushButton(t); b.setFixedSize(38,38); b.clicked.connect(f); tb.addWidget(b)
        
        self.url = QLineEdit(); self.url.setPlaceholderText("Search..."); self.url.returnPressed.connect(self.nav)
        tb.addWidget(self.url)
        
        for t, f in [("⬇️", self.dl_pg), ("< >", self.src), ("+", self.add_tab_safe)]:
            b = QPushButton(t); b.setFixedSize(38,38); b.clicked.connect(f); tb.addWidget(b)

        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True); self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(lambda i: self.tabs.removeTab(i) if self.tabs.count()>1 else None)
        self.tabs.currentChanged.connect(self.upd_url)
        self.setCentralWidget(self.tabs)

    def add_tab_safe(self): self.add_tab()
    def add_tab(self, u=None, l="New Tab"):
        if not u: u = QUrl("local://navi/")
        b = BrowserTab(self); b.setUrl(u)
        b.urlChanged.connect(lambda q, b=b: self.upd_url_for(q, b))
        b.titleChanged.connect(lambda t, b=b: self.upd_ti(t, b))
        i = self.tabs.addTab(b, l); self.tabs.setCurrentIndex(i); return b

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
            if u.startswith("local://navi/") or u.startswith("app://"): self.url.setText("New Tab")
            elif not u.startswith("local://"): self.url.setText(u)
        if q.scheme() in ["navi", "app"]: self.handle_cmd(q.toString(), b)

    def upd_url(self, i): 
        if i>=0: self.upd_url_for(self.tabs.widget(i).url(), self.tabs.widget(i))
    def upd_ti(self, t, b): 
        i = self.tabs.indexOf(b); 
        if i!=-1: self.tabs.setTabText(i, t[:15])

    def back(self): self.tabs.currentWidget().back() if self.tabs.currentWidget() else None
    def fwd(self): self.tabs.currentWidget().forward() if self.tabs.currentWidget() else None
    def reload(self): self.tabs.currentWidget().reload() if self.tabs.currentWidget() else None
    def home(self): self.tabs.currentWidget().setUrl(QUrl("local://navi/"))

    def sch_rwd(self, n):
        if time.time()-self.data['last_reward']>60: self.add_navits(n); self.data['last_reward']=time.time()
    def add_navits(self, n, m=""): self.data['navits']+=n; self.save_data(); print(f"+{n} {m}")
    def add_hist(self, u, t):
        if not self.data['history'] or self.data['history'][0]['url']!=u:
            self.data['history'].insert(0, {'url':u, 'title':t, 'time':time.time()}); self.save_data()
    def check_dead(self):
        if self.data['settings']['wholesome'] and time.time()-self.data['last_active']>TWO_WEEKS_SECONDS:
            self.data['history'] = get_wholesome_history()
        self.data['last_active'] = time.time(); self.save_data()

    def handle_cmd(self, u, b):
        cmd = u.lower().replace("navi://", "").replace("app://", "").strip("/")
        st = self.data['settings']
        
        if cmd=="" or cmd=="home" or cmd=="newtab" or cmd.startswith("newtab"): 
            b.setHtml(InternalPages.new_tab(self.data), QUrl("local://navi/"))
        elif cmd.startswith("navigate"):
            q = QUrl(u).queryItems(); tgt=""
            for k,v in q: 
                if k=="url": tgt=v
            if tgt: b.setUrl(QUrl(tgt))
        
        # --- Pages ---
        elif cmd=="settings":
            engines = "".join([f"<option {'selected' if e==st['engine'] else ''}>{e}</option>" for e in ["Google","Bing","Yahoo","DuckDuckGo","Ecosia","Yandex"]])
            themes = "".join([f"<a href='navi://set/theme/{t}' class='btn' style='margin:5px'>{t.title()}</a>" for t in ["light","dark","cyberpunk","sunset","matrix"] if t in ["light","dark"] or t in self.data['inventory']])
            m_l = "checked" if st.get('mode')=="legacy" else ""; m_m = "checked" if st.get('mode')=="modern" else ""
            
            h = f"""<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class="container"><div class="card"><h1>Settings</h1>
            <h3>🎨 Visuals</h3>
            <p><b>Engine Mode:</b> <label><input type="radio" name="m" {m_m} onclick="window.location='navi://set/mode/modern'"> Modern</label> <label><input type="radio" name="m" {m_l} onclick="window.location='navi://set/mode/legacy'"> Legacy</label></p>
            <p>{themes}</p>
            <h3>🔍 Search</h3><select onchange="window.location='navi://set/engine/'+this.value">{engines}</select>
            <h3>🔗 Suffix</h3><input value="{st['suffix']}" onchange="window.location='navi://set/suffix/'+this.value">
            </div></div></body></html>"""
            b.setHtml(h, QUrl("local://navi/settings"))

        elif cmd=="store":
            inv = self.data['inventory']
            def itm(i,n,c): return f"<div class='card'><h3>{n}</h3><a href='navi://buy/{i}' class='btn btn-gold'>Buy ({c})</a></div>" if i not in inv else ""
            items = itm("cyberpunk","Cyberpunk",100) + itm("sunset","Sunset",100) + itm("matrix","Matrix",125) + itm("christmas","Christmas",150) + itm("halloween","Halloween",150)
            b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class='container'><h1>🛒 Store ({self.data['navits']} N)</h1><div class='widget-grid'>{items}</div></div></body></html>", QUrl("local://navi/store"))

        # Actions
        elif cmd.startswith("set/theme/"): st['theme'] = u.split("theme/")[1]; self.apply_theme(); self.save_data(); self.handle_cmd("navi://settings", b)
        elif cmd.startswith("set/engine/"): st['engine'] = u.split("engine/")[1]; self.save_data()
        elif cmd.startswith("set/mode/"): st['mode'] = u.split("mode/")[1]; self.apply_theme(); self.save_data(); self.handle_cmd("navi://settings", b)
        elif cmd.startswith("set/suffix/"): st['suffix'] = u.split("suffix/")[1]; self.save_data()
        elif cmd.startswith("set/bg/"): st['bg_url'] = QUrl.fromPercentEncoding(u.split("bg/")[1].encode()); self.save_data(); self.handle_cmd("navi://home", b)
        elif cmd.startswith("buy/"):
            i = u.split("buy/")[1]; c = {"cyberpunk":100,"sunset":100,"matrix":125,"christmas":150,"halloween":150}.get(i,999)
            if self.data['navits']>=c: self.data['navits']-=c; self.data['inventory'].append(i); self.save_data(); self.handle_cmd("navi://store",b)
            else: QMessageBox.warning(self,"Poor","Need more Navits!")

        # Lists & Tools
        elif cmd=="pw": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class='container'><h1>Sites</h1><a href='navi://pw/new' class='btn'>+ New</a><br><br><div class='widget-grid'>{''.join([f'<div class=card><b>{v["title"]}</b><br>{k}<br><a href="{k}" class=btn>Go</a> <a href="navi://pw/edit/{k}" class=btn>Edit</a> <a href="navi://pw/del/{k}" class="btn btn-danger">Del</a></div>' for k,v in self.data['sites'].items()])}</div></div></body></html>", QUrl("local://pw"))
        elif cmd=="cws": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class='container'><h1>Extensions</h1><a href='navi://cws/new' class='btn'>+ New</a><br><br><div class='widget-grid'>{''.join([f'<div class=card><h3>{k}</h3><a href=navi://cws/toggle/{k} class=btn>Toggle ({self.data["extensions"][k]["active"]})</a></div>' for k in self.data['extensions']])}</div></div></body></html>", QUrl("local://cws"))
        elif cmd=="history": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class='container'><h1>History</h1>{''.join([f'<div class=card><a href={h["url"]}>{h["title"]}</a></div>' for h in self.data["history"]])}</div></body></html>", QUrl("local://hist"))
        elif cmd=="dlw": b.setHtml(f"<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class='container'><h1>Downloads</h1>{''.join([f'<div class=card><h3>{d["title"]}</h3><a href=navi://dlw/view/{d["id"]} class=btn>View</a></div>' for d in self.data["downloads"]])}</div></body></html>", QUrl("local://dlw"))
        
        # Editors
        elif cmd=="pw/new": CodeEditor(self, "site").show()
        elif cmd.startswith("pw/edit/"): CodeEditor(self, "site", QUrl.fromPercentEncoding(u.split("edit/")[1].encode())).show()
        elif cmd.startswith("pw/del/"): d = QUrl.fromPercentEncoding(u.split("del/")[1].encode()); del self.data['sites'][d]; self.save_data(); self.handle_cmd("navi://pw", b)
        elif cmd=="cws/new": CodeEditor(self, "ext").show()
        elif cmd.startswith("cws/toggle/"): n=u.split("toggle/")[1]; self.data['extensions'][n]['active'] = not self.data['extensions'][n]['active']; self.save_data(); self.handle_cmd("navi://cws",b)
        elif cmd.startswith("dlw/view/"): 
            did=u.split("view/")[1]; p=next((x for x in self.data['downloads'] if x['id']==did),None)
            if p: b.setHtml(p['html'], QUrl("local://offline"))

    def dl_pg(self): self.tabs.currentWidget().page().toHtml(lambda h: self.save_dl(self.tabs.currentWidget().title(), h))
    def save_dl(self, t, h): self.data['downloads'].append({'title':t,'html':h,'id':str(int(time.time()))}); self.save_data()
    def src(self): self.tabs.currentWidget().page().toHtml(lambda h: SourceViewer(h, self).exec())
    def save_data(self):
        try: 
            with open(DATA_FILE, 'w') as f: json.dump(self.data, f)
        except: pass
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f: 
                    d = json.load(f)
                    # Safe Merge
                    if 'settings' in d: self.data['settings'].update(d['settings'])
                    for k in d: 
                        if k!='settings' and k in self.data: self.data[k]=d[k]
                    # Ensure defaults
                    defaults = {'theme': 'dark', 'engine': 'Google', 'suffix': '.pw-navi', 'wholesome': True, 'mode': 'modern', 'bg_url': ''}
                    for k,v in defaults.items(): 
                        if k not in self.data['settings']: self.data['settings'][k]=v
            except: pass
    def apply_theme(self):
        self.setStyleSheet(BrowserStyles.get(self.data['settings']['theme'], self.data['settings'].get('mode', 'modern')))
        if self.tabs.currentWidget(): self.tabs.currentWidget().reload()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Navi Browser")
    window = NaviBrowser()
    window.show()
    sys.exit(app.exec())


