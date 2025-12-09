import sys
import json
import os
import time
from datetime import datetime
from PyQt6.QtCore import QUrl, Qt, QSize, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QMessageBox, QTabWidget, QMenu, QDialog, QPlainTextEdit
)
from PyQt6.QtGui import QAction, QIcon, QFont, QActionGroup
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings

# --- Constants ---
DATA_FILE = "navi_data.json"
TWO_WEEKS_SECONDS = 1209600

# --- Helper Functions ---
def get_wholesome_history():
    return [
        {"url": "https://www.google.com/search?q=how+to+make+my+parents+proud", "time": time.time(), "title": "Self Improvement"},
        {"url": "https://www.google.com/search?q=local+animal+shelter+donations", "time": time.time() - 100, "title": "Charity"},
        {"url": "https://www.youtube.com/watch?v=cute_puppies", "time": time.time() - 200, "title": "Stress Relief"},
    ]

def is_seasonal(event):
    today = datetime.now()
    if event == "christmas": return today.month == 12 or (today.month == 1 and today.day <= 8)
    if event == "halloween": return today.month == 10
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
    base = engines.get(engine, engines["Google"])
    return base + query.replace(" ", "+")

# --- Styles ---
class ProStyles:
    @staticmethod
    def get(theme_name, pro_mode=False):
        # Base Colors
        colors = {
            "light": {"bg": "#f3f3f3", "fg": "#000", "tab": "#fff", "sel": "#fff", "bar": "#fff", "acc": "#1a73e8"},
            "dark": {"bg": "#202124", "fg": "#e8eaed", "tab": "#292a2d", "sel": "#35363a", "bar": "#35363a", "acc": "#8ab4f8"},
            "christmas": {"bg": "#0f2e1c", "fg": "#fff", "tab": "#1a472a", "sel": "#c41e3a", "bar": "#1a472a", "acc": "#d4af37"},
            "halloween": {"bg": "#121212", "fg": "#ffa500", "tab": "#1f1f1f", "sel": "#2d2d2d", "bar": "#1f1f1f", "acc": "#ff4500"},
            "cyberpunk": {"bg": "#0b0d17", "fg": "#00f3ff", "tab": "#121526", "sel": "#1c1f3a", "bar": "#121526", "acc": "#ff0099"},
            "sunset": {"bg": "#2d1b2e", "fg": "#ffcc00", "tab": "#442244", "sel": "#b3446c", "bar": "#442244", "acc": "#f6511d"},
            "matrix": {"bg": "#000000", "fg": "#00ff00", "tab": "#0a0a0a", "sel": "#111", "bar": "#0a0a0a", "acc": "#008f11"},
        }
        
        c = colors.get(theme_name, colors["light"])
        
        # Professional UI (Pro Mode) vs Basic UI
        radius = "8px" if pro_mode else "0px"
        padding = "8px 16px" if pro_mode else "5px"
        tab_margin = "4px" if pro_mode else "0px"
        
        return f"""
        QMainWindow {{ background-color: {c['bg']}; color: {c['fg']}; }}
        QWidget {{ color: {c['fg']}; }}
        
        /* Tabs */
        QTabWidget::pane {{ border: 0; background: {c['bg']}; }}
        QTabBar::tab {{
            background: {c['tab']}; color: {c['fg']}; padding: {padding};
            border-top-left-radius: {radius}; border-top-right-radius: {radius};
            margin-right: {tab_margin}; font-family: 'Segoe UI'; font-size: 13px;
        }}
        QTabBar::tab:selected {{ background: {c['sel']}; font-weight: bold; border-bottom: 2px solid {c['acc']}; }}
        
        /* Toolbar */
        QToolBar {{ background: {c['bar']}; border-bottom: 1px solid {c['tab']}; spacing: 8px; padding: 5px; }}
        
        /* Inputs */
        QLineEdit {{
            background: {c['bg']}; border: 1px solid {c['tab']}; border-radius: 20px;
            padding: 8px 15px; color: {c['fg']}; font-size: 14px;
        }}
        QLineEdit:focus {{ border: 1px solid {c['acc']}; }}
        
        /* Buttons */
        QPushButton {{
            background-color: transparent; border-radius: 6px; padding: 6px;
            color: {c['fg']}; font-weight: bold; font-size: 16px;
        }}
        QPushButton:hover {{ background-color: {c['tab']}; }}
        
        /* Menus */
        QMenu {{ background: {c['bar']}; color: {c['fg']}; border: 1px solid {c['tab']}; }}
        QMenu::item:selected {{ background: {c['acc']}; color: #fff; }}
        QPlainTextEdit {{ background: {c['bg']}; color: {c['fg']}; border: 1px solid {c['tab']}; }}
        """

# --- Internal HTML Generator ---
class InternalPages:
    @staticmethod
    def css(theme):
        is_dark = theme != "light"
        bg = "#202124" if is_dark else "#f1f3f4"
        card = "#303134" if is_dark else "#ffffff"
        text = "#e8eaed" if is_dark else "#202124"
        border = "#5f6368" if is_dark else "#dadce0"
        
        return f"""
        body {{ font-family: 'Roboto', 'Segoe UI', sans-serif; background: {bg}; color: {text}; padding: 0; margin: 0; }}
        .container {{ max-width: 900px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #1a73e8; font-weight: 400; }}
        .card {{ background: {card}; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); border: 1px solid {border}; }}
        .btn {{ padding: 10px 20px; background: #1a73e8; color: white; border: none; border-radius: 20px; text-decoration: none; cursor: pointer; display: inline-block; transition: 0.2s; }}
        .btn:hover {{ background: #1557b0; transform: translateY(-1px); }}
        .btn-gold {{ background: #fbbc04; color: #202124; }}
        .btn-danger {{ background: #ea4335; }}
        .widget-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        input, select, textarea {{ 
            width: 100%; padding: 12px; border-radius: 8px; border: 1px solid {border}; 
            background: {bg}; color: {text}; margin-top: 10px; box-sizing: border-box;
        }}
        /* New Tab Specific */
        .new-tab-center {{ 
            display: flex; flex-direction: column; align-items: center; justify-content: center; 
            height: 80vh; text-align: center; 
        }}
        .search-wrapper {{ width: 100%; max-width: 600px; position: relative; }}
        .big-search {{ 
            width: 100%; padding: 15px 25px; border-radius: 30px; border: 1px solid {border}; 
            font-size: 18px; outline: none; box-shadow: 0 2px 5px rgba(0,0,0,0.1); 
        }}
        .big-search:focus {{ box-shadow: 0 2px 8px rgba(26,115,232,0.4); border-color: #1a73e8; }}
        .navit-badge {{ background: #fbbc04; color: #000; padding: 5px 12px; border-radius: 15px; font-weight: bold; font-size: 14px; position: absolute; top: 20px; right: 20px; }}
        """

    @staticmethod
    def new_tab(theme, navits, widgets_unlocked, notes):
        extra = ""
        if widgets_unlocked:
            extra = """<div class="card" style="margin-top:20px; width:100%; max-width:600px;">
                <h3>Widgets</h3>
                <p>🧮 <b>Calc:</b> <input placeholder="2+2" onchange="this.value=eval(this.value)"></p>
                <p>📅 <b>Date:</b> <script>document.write(new Date().toDateString())</script></p>
            </div>"""
            
        return f"""<html><head><title>New Tab</title><style>{InternalPages.css(theme)}</style>
        <script>
            function handleSearch(e) {{
                if (e.key === 'Enter') {{
                    window.location = 'navi://search/' + encodeURIComponent(e.target.value);
                }}
            }}
        </script>
        </head><body>
        <div class="navit-badge">🪙 {navits}</div>
        <div class="new-tab-center">
            <h1 style="font-size: 3em; margin-bottom: 30px;">Navi Browser</h1>
            <div class="search-wrapper">
                <input class="big-search" placeholder="Visit or search a website..." onkeypress="handleSearch(event)">
            </div>
            {extra}
            <div style="margin-top: 30px; display: flex; gap: 15px;">
                <a href="navi://pw" class="btn">My Sites</a>
                <a href="navi://cws" class="btn">Extensions</a>
                <a href="navi://settings" class="btn" style="background:#5f6368">Settings</a>
            </div>
        </div>
        </body></html>"""

# --- Custom Web Engine ---
class NaviWebPage(QWebEnginePage):
    def certificateError(self, error): return True
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() == "navi":
            view = self.view()
            if view and hasattr(view, 'parent_window'):
                view.parent_window.handle_internal_pages(url.toString(), view)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

# --- Browser Tab ---
class BrowserTab(QWebEngineView):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.yt_timer = QTimer(self); self.yt_timer.timeout.connect(self.check_yt); self.yt_timer.start(60000)
        self.yt_min = 0; self.curr_yt = ""
        
        s = self.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        
        self.setPage(NaviWebPage(self))
        self.page().loadFinished.connect(self.on_load_finished)
        self.urlChanged.connect(self.on_url_change)

    def on_url_change(self, u):
        s = u.toString()
        if "youtube.com/watch" not in s: self.yt_min = 0; self.curr_yt = ""
        elif s != self.curr_yt: self.yt_min = 0; self.curr_yt = s

    def check_yt(self):
        if "youtube.com/watch" in self.url().toString():
            self.yt_min += 1
            if self.yt_min == 15:
                self.parent_window.add_navits(1, "YouTube Watch (15m)")
                self.yt_min = 0

    def on_load_finished(self, ok):
        if not ok: return
        for n, e in self.parent_window.data['extensions'].items():
            if e['active']: self.page().runJavaScript(e['code'])
        
        u = self.url().toString()
        h = self.url().host()
        
        # Search Rewards
        if "google.com" in h or "duckduckgo.com" in h: self.parent_window.search_reward(1)
        elif "ecosia.org" in h: self.parent_window.search_reward(2)

        if not u.startswith("local://") and not u.startswith("navi://"):
            self.parent_window.add_history(u, self.title())

    def createWindow(self, _type): return self.parent_window.add_new_tab()

# --- Editors ---
class CodeEditor(QWidget):
    def __init__(self, main, mode="site", key=None):
        super().__init__()
        self.main, self.mode, self.key = main, mode, key
        self.resize(800, 600); self.setWindowTitle("Editor")
        l = QVBoxLayout()
        self.name = QLineEdit(); self.name.setPlaceholderText("Name"); l.addWidget(QLabel("Name")); l.addWidget(self.name)
        if key: self.name.setText(key.replace(main.data['settings']['suffix'], "") if mode=="site" else key); self.name.setReadOnly(True)
        if mode=="site": 
            self.ti = QLineEdit(); self.ti.setPlaceholderText("Title"); l.addWidget(QLabel("Title")); l.addWidget(self.ti)
        self.code = QTextEdit(); l.addWidget(QLabel("Code")); l.addWidget(self.code)
        b = QPushButton("Save"); b.clicked.connect(self.save); l.addWidget(b); self.setLayout(l)
        if key:
            d = main.data['sites' if mode=="site" else 'extensions'].get(key)
            if d and mode=="site": self.ti.setText(d['title']); self.code.setText(d['html_content'])
            elif d: self.code.setText(d['code'])

    def save(self):
        n = self.name.text().strip()
        c = self.code.toPlainText()
        if not n: return
        if self.mode == "site":
            s = self.main.data['settings']['suffix']
            f = f"{n.lower()}{s}" if not n.endswith(s) else n.lower()
            self.main.data['sites'][f] = {'domain': f, 'title': self.ti.text(), 'html_content': c}
            self.main.add_new_tab(QUrl(f"local://{f}/"))
        else:
            self.main.data['extensions'][n] = {'code': c, 'active': True}
        self.main.save(); self.close()

class SourceViewer(QDialog):
    def __init__(self, txt, parent=None):
        super().__init__(parent); self.resize(800,600)
        t = QPlainTextEdit(txt); t.setReadOnly(True); l = QVBoxLayout(); l.addWidget(t); self.setLayout(l)

# --- Main Window ---
class NaviBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser Ultimate v5")
        self.resize(1300, 900)
        self.data = {
            'sites': {}, 'extensions': {}, 'history': [], 'downloads': [],
            'settings': {'theme': 'light', 'pyqt6_mode': False, 'engine': 'Google', 'suffix': '.pw-navi', 'wholesome': True},
            'navits': 0, 'inventory': [], 'last_active': time.time(), 'last_reward': 0
        }
        self.load()
        self.check_wholesome()
        self.setup_ui()
        self.apply_theme()
        self.add_new_tab(QUrl("local://navi/"))

    def setup_ui(self):
        tb = QToolBar(); tb.setMovable(False); self.addToolBar(tb)
        for t, f in [("←", self.back), ("→", self.fwd), ("⟳", self.reload), ("🏠", self.home)]:
            b = QPushButton(t); b.setFixedSize(35,35); b.clicked.connect(f); tb.addWidget(b)
        
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter address...")
        self.url_bar.returnPressed.connect(self.navigate)
        tb.addWidget(self.url_bar)
        
        for t, f, tip in [("⬇️", self.dl_page, "DL"), ("< >", self.view_src, "Src"), ("+", self.add_new_tab_safe, "New")]:
            b = QPushButton(t); b.setToolTip(tip); b.setFixedSize(35,35); b.clicked.connect(f); tb.addWidget(b)

        self.tabs = QTabWidget(); self.tabs.setDocumentMode(True); self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.setCentralWidget(self.tabs)

    def back(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().back()
    def fwd(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().forward()
    def reload(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().reload()
    def home(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().setUrl(QUrl("local://navi/"))
    def close_tab(self, i): 
        if self.tabs.count() > 1: self.tabs.removeTab(i)
    def add_new_tab_safe(self): self.add_new_tab()

    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None: qurl = QUrl("local://navi/")
        b = BrowserTab(self); b.setUrl(qurl)
        b.urlChanged.connect(lambda q, b=b: self.update_url_bar_for(q, b))
        b.titleChanged.connect(lambda t, b=b: self.update_title(t, b))
        i = self.tabs.addTab(b, label); self.tabs.setCurrentIndex(i)

    def navigate(self):
        txt = self.url_bar.text().strip()
        b = self.tabs.currentWidget()
        if not b: return
        
        if txt.lower().startswith("navi://"): self.handle_internal_pages(txt, b)
        elif txt.lower().endswith(self.data['settings']['suffix']):
            d = self.data['sites'].get(txt.lower())
            if d: b.setHtml(d['html_content'], QUrl(f"local://{txt}/"))
        else:
            u = QUrl(txt)
            if "." not in txt: u = QUrl(get_search_url(self.data['settings']['engine'], txt))
            elif "://" not in txt: u = QUrl("https://" + txt)
            b.setUrl(u)

    def update_url_bar_for(self, q, b):
        if b == self.tabs.currentWidget():
            u = q.toString()
            if u.startswith("local://navi/"): self.url_bar.setText(u.replace("local://navi/", "navi://").rstrip("/"))
            elif not u.startswith("local://"): self.url_bar.setText(u)
        if q.scheme() == "navi": self.handle_internal_pages(q.toString(), b)

    def update_url_bar(self, i):
        if i >= 0: self.update_url_bar_for(self.tabs.widget(i).url(), self.tabs.widget(i))
    
    def update_title(self, t, b):
        i = self.tabs.indexOf(b)
        if i != -1: self.tabs.setTabText(i, t[:15])

    def search_reward(self, amt):
        if time.time() - self.data.get('last_reward', 0) > 60:
            self.add_navits(amt)
            self.data['last_reward'] = time.time()

    def add_navits(self, amt, msg=""):
        self.data['navits'] += amt
        print(f"+{amt} Navits {msg}")
        self.save()

    def add_history(self, u, t):
        if self.data['history'] and self.data['history'][0]['url'] == u: return
        self.data['history'].insert(0, {'url': u, 'title': t, 'time': time.time()})
        self.data['history'] = self.data['history'][:1000]; self.save()

    def check_wholesome(self):
        if self.data['settings']['wholesome'] and time.time() - self.data['last_active'] > TWO_WEEKS_SECONDS:
            self.data['history'] = get_wholesome_history()
        self.data['last_active'] = time.time(); self.save()

    def handle_internal_pages(self, url, b):
        cmd = url.lower().replace("navi://", "").strip("/")
        st = self.data['settings']
        
        if cmd == "" or cmd == "home":
            b.setHtml(InternalPages.new_tab(st['theme'], self.data['navits'], "widgets" in self.data['inventory'], ""), QUrl("local://navi/"))
        elif cmd.startswith("search/"):
            q = QUrl.fromPercentEncoding(url.split("search/")[1].encode())
            b.setUrl(QUrl(get_search_url(st['engine'], q)))
        
        # --- Pages ---
        elif cmd == "settings":
            engines = ["Google", "Bing", "Yahoo", "DuckDuckGo", "Ecosia", "Yandex"]
            eng_opts = "".join([f"<option {'selected' if e==st['engine'] else ''}>{e}</option>" for e in engines])
            
            themes = ["light", "dark", "cyberpunk", "sunset", "matrix"]
            if "christmas" in self.data['inventory']: themes.append("christmas")
            if "halloween" in self.data['inventory']: themes.append("halloween")
            thm_opts = "".join([f"<a href='navi://set/theme/{t}' class='btn' style='margin:5px'>{t.capitalize()}</a>" for t in themes])
            
            pro_check = "checked" if st['pyqt6_mode'] else ""
            
            h = f"""<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class="container">
            <h1>Settings</h1>
            <div class="card">
                <h3>🔍 Search Engine</h3>
                <select onchange="window.location='navi://set/engine/'+this.value">{eng_opts}</select>
            </div>
            <div class="card">
                <h3>🎨 Themes</h3>
                {thm_opts}
            </div>
            <div class="card">
                <h3>⚡ Pro Features</h3>
                <label><input type="checkbox" {pro_check} onclick="window.location='navi://toggle/pyqt6'"> <b>PyQt6 Enhanced Mode</b> (Requires Purchase)</label>
            </div>
            <div class="card">
                <h3>👻 Privacy</h3>
                <label><input type="checkbox" {'checked' if st['wholesome'] else ''} onclick="window.location='navi://toggle/wholesome'"> Dead Man's Switch</label>
            </div>
            </div></body></html>"""
            b.setHtml(h, QUrl("local://navi/settings"))

        elif cmd == "navits/buy":
            inv = self.data['inventory']
            def item(id, name, cost, desc, seasonal=False):
                if seasonal and not is_seasonal(id): return ""
                if id in inv: return f"<div class='card'><h3>{name}</h3><p>Owned</p></div>"
                return f"<div class='card'><h3>{name}</h3><p>{desc}</p><a href='navi://buy/{id}' class='btn btn-gold'>Buy ({cost} N)</a></div>"
            
            items = item("christmas", "🎄 Christmas Theme", 150, "Seasonal Theme", True) + \
                    item("halloween", "🎃 Halloween Theme", 150, "Seasonal Theme", True) + \
                    item("pyqt6", "⚡ PyQt6 Enhanced", 25, "Professional UI Mode") + \
                    item("widgets", "🧩 Pro Widgets", 200, "Calc & Calendar") + \
                    item("cyberpunk", "🌆 Cyberpunk Theme", 100, "Neon Style") + \
                    item("sunset", "🌅 Sunset Theme", 100, "Relaxing Colors") + \
                    item("matrix", "💻 Matrix Theme", 125, "Hacker Style")

            b.setHtml(f"""<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class="container"><h1>🛒 Store</h1><p>Balance: {self.data['navits']} N</p><div class="widget-grid">{items}</div></div></body></html>""", QUrl("local://navi/store"))

        # --- Actions ---
        elif cmd.startswith("set/theme/"):
            st['theme'] = url.split("theme/")[1]; self.apply_theme(); self.save(); self.handle_internal_pages("navi://settings", b)
        elif cmd.startswith("set/engine/"):
            st['engine'] = url.split("engine/")[1]; self.save()
        elif cmd.startswith("toggle/pyqt6"):
            if "pyqt6" in self.data['inventory']:
                st['pyqt6_mode'] = not st['pyqt6_mode']; self.apply_theme(); self.save(); self.handle_internal_pages("navi://settings", b)
            else: QMessageBox.warning(self, "Locked", "Buy PyQt6 Enhanced in the Store first!")
        elif cmd.startswith("toggle/wholesome"):
            st['wholesome'] = not st['wholesome']; self.save()
        elif cmd.startswith("buy/"):
            itm = url.split("buy/")[1]
            costs = {"pyqt6": 25, "cyberpunk": 100, "sunset": 100, "matrix": 125, "christmas": 150, "halloween": 150, "widgets": 200}
            cost = costs.get(itm, 9999)
            if self.data['navits'] >= cost:
                self.data['navits'] -= cost; self.data['inventory'].append(itm); self.save()
                QMessageBox.information(self, "Bought", f"You bought {itm}!")
                self.handle_internal_pages("navi://navits/buy", b)
            else: QMessageBox.warning(self, "Poor", f"Need {cost} Navits.")
        
        # --- Other Pages (Standard) ---
        elif cmd == "cws":
            rows = "".join([f"<div class='card'><h3>{k}</h3><a href='navi://cws/edit/{k}' class='btn'>Edit</a> <a href='navi://cws/toggle/{k}' class='btn'>Toggle</a></div>" for k in self.data['extensions']])
            b.setHtml(f"""<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class="container"><h1>Extensions</h1><a href='navi://cws/new' class='btn'>+ New</a><br><br>{rows}</div></body></html>""", QUrl("local://navi/cws"))
        elif cmd == "pw":
            rows = "".join([f"<div class='card'><b>{v['title']}</b> ({d})<br><a href='{d}' class='btn'>Visit</a> <a href='navi://pw/edit/{d}' class='btn'>Edit</a> <a href='navi://pw/del/{d}' class='btn btn-danger'>Del</a></div>" for d, v in self.data['sites'].items()])
            b.setHtml(f"""<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class="container"><h1>Sites</h1><a href='navi://pw/new' class='btn'>+ New</a><br><br>{rows}</div></body></html>""", QUrl("local://navi/pw"))
        elif cmd == "history":
            rows = "".join([f"<div class='card'><a href='{h['url']}'>{h.get('title','Link')}</a><br><small>{h['url']}</small></div>" for h in self.data['history']])
            b.setHtml(f"""<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class="container"><h1>History</h1>{rows}</div></body></html>""", QUrl("local://navi/history"))
        elif cmd == "dlw":
            rows = "".join([f"<div class='card'><h3>{d['title']}</h3><a href='navi://dlw/view/{d['id']}' class='btn'>View</a></div>" for d in self.data['downloads']])
            b.setHtml(f"""<html><head><style>{InternalPages.css(st['theme'])}</style></head><body><div class="container"><h1>Downloads</h1>{rows}</div></body></html>""", QUrl("local://navi/dlw"))

        # --- Editor Actions ---
        elif cmd == "pw/new": CodeEditor(self, "site").show()
        elif cmd.startswith("pw/edit/"): CodeEditor(self, "site", QUrl.fromPercentEncoding(url.split("edit/")[1].encode())).show()
        elif cmd.startswith("pw/del/"): 
            d = QUrl.fromPercentEncoding(url.split("del/")[1].encode())
            if d in self.data['sites']: del self.data['sites'][d]; self.save(); self.handle_internal_pages("navi://pw", b)
        elif cmd == "cws/new": CodeEditor(self, "ext").show()
        elif cmd.startswith("cws/edit/"): CodeEditor(self, "ext", QUrl.fromPercentEncoding(url.split("edit/")[1].encode())).show()
        elif cmd.startswith("cws/toggle/"): 
            n = QUrl.fromPercentEncoding(url.split("toggle/")[1].encode())
            if n in self.data['extensions']: 
                self.data['extensions'][n]['active'] = not self.data['extensions'][n]['active']
                self.save(); self.handle_internal_pages("navi://cws", b)
        elif cmd.startswith("dlw/view/"):
            did = url.split("view/")[1]
            pg = next((d for d in self.data['downloads'] if d['id'] == did), None)
            if pg: b.setHtml(pg['html'], QUrl("local://offline"))

    def dl_page(self):
        if self.tabs.currentWidget(): self.tabs.currentWidget().page().toHtml(lambda h: self.save_dl(self.tabs.currentWidget().title(), h))
    def save_dl(self, t, h):
        self.data['downloads'].append({'title': t, 'html': h, 'id': str(int(time.time()))}); self.save(); QMessageBox.information(self, "Saved", "Offline copy saved.")
    def view_src(self):
        if self.tabs.currentWidget(): self.tabs.currentWidget().page().toHtml(lambda h: SourceViewer(h, self).exec())

    def save(self):
        try:
            with open(DATA_FILE, 'w') as f: json.dump(self.data, f)
        except: pass
    
    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f: 
                    d = json.load(f)
                    self.data.update(d)
                    # Migrations
                    if 'pyqt6_mode' not in self.data['settings']: self.data['settings']['pyqt6_mode'] = False
                    if 'engine' not in self.data['settings']: self.data['settings']['engine'] = "Google"
                    if 'suffix' not in self.data['settings']: self.data['settings']['suffix'] = ".pw-navi"
                    if 'wholesome' not in self.data['settings']: self.data['settings']['wholesome'] = True
            except: pass

    def apply_theme(self):
        s = self.data['settings']
        self.setStyleSheet(ProStyles.get(s['theme'], s['pyqt6_mode']))
        if self.tabs.currentWidget(): self.tabs.currentWidget().reload()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Navi Browser")
    window = NaviBrowser()
    window.show()
    sys.exit(app.exec())

