import sys
import json
import os
import time
from datetime import datetime
from PyQt5.QtCore import QUrl, Qt, QSize, QDateTime, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QMessageBox, QTabWidget, QMenu, QDialog, QPlainTextEdit,
    QHBoxLayout, QComboBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings

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
    if event == "christmas":
        # Dec 1 to Jan 8
        if today.month == 12 or (today.month == 1 and today.day <= 8):
            return True
    elif event == "halloween":
        # October
        if today.month == 10:
            return True
    return False

# --- Styles ---
class ModernStyles:
    @staticmethod
    def get(theme_name):
        # Default Colors
        bg, fg, input_bg, border, btn_hover, accent = "#f8f9fa", "#212529", "#ffffff", "#dee2e6", "#e9ecef", "#0d6efd"

        if theme_name == "dark":
            bg, fg, input_bg, border, btn_hover, accent = "#212529", "#f8f9fa", "#343a40", "#495057", "#495057", "#0d6efd"
        elif theme_name == "christmas":
            bg, fg, input_bg, border, btn_hover, accent = "#1a472a", "#f0f0f0", "#2d5a3f", "#5d8a6f", "#c41e3a", "#d42426" # Green/Red
        elif theme_name == "halloween":
            bg, fg, input_bg, border, btn_hover, accent = "#1a1a1a", "#ff9a00", "#2d2d2d", "#444", "#333", "#ff7518" # Black/Orange

        return f"""
        QMainWindow {{ background-color: {bg}; color: {fg}; }}
        QWidget {{ color: {fg}; }}
        QTabWidget::pane {{ border: 0; background: {bg}; }}
        QTabBar::tab {{
            background: {input_bg}; color: {fg}; padding: 8px 20px;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{ background: {bg}; border-bottom: 2px solid {accent}; font-weight: bold; }}
        QToolBar {{ background: {bg}; border-bottom: 1px solid {border}; spacing: 5px; }}
        QLineEdit {{
            background: {input_bg}; border: 1px solid {border}; border-radius: 15px;
            padding: 6px 15px; color: {fg}; selection-background-color: {accent};
        }}
        QPushButton {{
            background-color: transparent; border-radius: 5px; padding: 5px;
            color: {fg}; font-weight: bold; font-size: 14px;
        }}
        QPushButton:hover {{ background-color: {btn_hover}; }}
        QMenu {{ background: {input_bg}; color: {fg}; border: 1px solid {border}; }}
        QMenu::item:selected {{ background: {accent}; color: white; }}
        QPlainTextEdit {{ background: {input_bg}; color: {fg}; border: 1px solid {border}; }}
        """

# --- Custom Web Engine ---
class NaviWebPage(QWebEnginePage):
    def certificateError(self, error): return True # Ignore SSL errors

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() == "navi":
            view = self.view()
            if view and hasattr(view, 'parent_window'):
                view.parent_window.handle_internal_pages(url.toString(), view)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

# --- Internal Pages Generator ---
class InternalPages:
    @staticmethod
    def css(theme):
        # Map theme to basic colors for HTML
        is_dark = theme in ["dark", "christmas", "halloween"]
        bg = "#2b3035" if is_dark else "#f8f9fa"
        card_bg = "#343a40" if is_dark else "#ffffff"
        text = "#f8f9fa" if is_dark else "#212529"
        border = "#495057" if is_dark else "#dee2e6"
        
        return f"""
        body {{ font-family: 'Segoe UI', sans-serif; background: {bg}; color: {text}; padding: 40px; margin: 0; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #0d6efd; font-weight: 300; }}
        .card {{ background: {card_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid {border}; }}
        .btn {{ padding: 10px 20px; background: #0d6efd; color: white; border: none; border-radius: 6px; text-decoration: none; cursor: pointer; display: inline-block; }}
        .btn:hover {{ background: #0b5ed7; }}
        .btn-danger {{ background: #dc3545; }}
        .btn-success {{ background: #198754; }}
        .btn-gold {{ background: #ffc107; color: black; }}
        input, select, textarea {{ 
            padding: 12px; width: 100%; margin: 10px 0; border-radius: 6px; 
            border: 1px solid {border}; background: {bg}; color: {text}; box-sizing: border-box; 
        }}
        .widget-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .clock {{ font-size: 3em; font-weight: bold; text-align: center; margin: 20px 0; }}
        .navit-badge {{ background: #ffc107; color: black; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em; vertical-align: middle; }}
        """

    @staticmethod
    def home(theme, notes, navits, widgets_unlocked):
        extra_widgets = ""
        if widgets_unlocked:
            extra_widgets = """
            <div class="card">
                <h3>🧮 Calculator</h3>
                <input id="calc" placeholder="2 + 2" onchange="try{this.value = eval(this.value)}catch(e){this.value='Error'}">
            </div>
            <div class="card">
                <h3>📅 Calendar</h3>
                <p>Today is: <script>document.write(new Date().toDateString())</script></p>
            </div>
            """
        
        return f"""<html><head><style>{InternalPages.css(theme)}</style>
        <script>
            setInterval(() => document.getElementById('clock').innerText = new Date().toLocaleTimeString(), 1000);
            function saveNotes(val) {{ window.location = 'navi://save_notes/' + encodeURIComponent(val); }}
        </script>
        </head><body>
        <div class="container">
            <div style="text-align:right;"><span class="navit-badge">🪙 {navits} Navits</span></div>
            <div id="clock" class="clock">00:00:00</div>
            <div class="widget-grid">
                <div class="card">
                    <h3>📝 Notes</h3>
                    <textarea style="height: 150px; resize: none;" oninput="saveNotes(this.value)">{notes}</textarea>
                </div>
                {extra_widgets}
                <div class="card" style="text-align:center;">
                    <h3>🚀 Navigation</h3>
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        <a href="navi://settings" class="btn">⚙️ Settings</a>
                        <a href="navi://navits" class="btn btn-gold">🏆 Navits</a>
                        <a href="navi://pw" class="btn">🌐 My Sites</a>
                        <a href="navi://dlw" class="btn">⬇️ Downloads</a>
                        <a href="navi://history" class="btn">🕒 History</a>
                        <a href="navi://cws" class="btn">🧩 Extensions</a>
                    </div>
                </div>
            </div>
        </div></body></html>"""

# --- Editors & Viewers ---
class SourceViewer(QDialog):
    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.resize(800,600)
        t = QPlainTextEdit(content)
        t.setReadOnly(True)
        t.setStyleSheet("font-family: Consolas; font-size: 14px;")
        l = QVBoxLayout()
        l.addWidget(t)
        self.setLayout(l)

class CodeEditorWindow(QWidget):
    def __init__(self, browser_main, mode="site", key_to_edit=None):
        super().__init__()
        self.browser_main = browser_main
        self.mode = mode
        self.key_to_edit = key_to_edit
        self.setWindowTitle(f"Navi Editor")
        self.resize(900, 700)
        self.setup_ui()

    def setup_ui(self):
        l = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")
        if self.key_to_edit: self.name_input.setReadOnly(True)
        l.addWidget(QLabel("Name:"))
        l.addWidget(self.name_input)
        
        if self.mode == "site":
            self.title_input = QLineEdit(); self.title_input.setPlaceholderText("Title")
            l.addWidget(QLabel("Title:")); l.addWidget(self.title_input)

        self.content_input = QTextEdit()
        l.addWidget(QLabel("Code:"))
        l.addWidget(self.content_input)

        btn = QPushButton("Save"); btn.setStyleSheet("background:#198754;color:white;padding:10px;")
        btn.clicked.connect(self.save)
        l.addWidget(btn)
        self.setLayout(l)
        self.load()

    def load(self):
        if not self.key_to_edit: return
        if self.mode == "site":
            d = self.browser_main.data['sites'].get(self.key_to_edit)
            if d:
                suffix = self.browser_main.data['settings'].get('custom_suffix', '.pw-navi')
                self.name_input.setText(self.key_to_edit.replace(suffix, ""))
                self.title_input.setText(d['title'])
                self.content_input.setText(d['html_content'])
        else:
            d = self.browser_main.data['extensions'].get(self.key_to_edit)
            if d: self.name_input.setText(self.key_to_edit); self.content_input.setText(d['code'])

    def save(self):
        n = self.name_input.text().strip()
        c = self.content_input.toPlainText()
        if not n: return
        
        if self.mode == "site":
            suffix = self.browser_main.data['settings'].get('custom_suffix', '.pw-navi')
            full = f"{n.lower()}{suffix}" if not n.endswith(suffix) else n.lower()
            self.browser_main.data['sites'][full] = {'domain': full, 'title': self.title_input.text(), 'html_content': c}
            self.browser_main.add_new_tab(QUrl(f"local://{full}/"))
        else:
            self.browser_main.data['extensions'][n] = {'code': c, 'active': True}
        
        self.browser_main.save_to_disk()
        self.close()

# --- Browser Tab ---
class BrowserTab(QWebEngineView):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        
        # Youtube Timer
        self.yt_timer = QTimer(self)
        self.yt_timer.timeout.connect(self.check_youtube_watch)
        self.yt_timer.start(60000) # Check every minute
        self.yt_minutes = 0
        self.current_yt_url = ""

        # Profile
        p = QWebEngineProfile.defaultProfile()
        p.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        self.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.LocalStorageEnabled, True)

        self.setPage(NaviWebPage(self))
        self.page().loadFinished.connect(self.on_load_finished)
        self.urlChanged.connect(self.on_url_changed)

    def on_url_changed(self, url):
        u_str = url.toString()
        if "youtube.com/watch" not in u_str:
            self.yt_minutes = 0
            self.current_yt_url = ""
        else:
            if u_str != self.current_yt_url:
                self.yt_minutes = 0
                self.current_yt_url = u_str

    def check_youtube_watch(self):
        if "youtube.com/watch" in self.url().toString():
            self.yt_minutes += 1
            if self.yt_minutes == 15:
                self.parent_window.add_navits(1, "Watched YouTube (15m)")
                self.yt_minutes = 0 # Reset or keep counting? Let's reset for "every 15m" logic

    def on_load_finished(self, ok):
        if not ok: return
        
        # Extensions
        for name, ext in self.parent_window.data['extensions'].items():
            if ext['active']: self.page().runJavaScript(ext['code'])
        
        # History & Navits (Search Rewards)
        url = self.url().toString()
        host = self.url().host()
        
        # Reward Logic (Rate limited in parent)
        if "google.com" in host: self.parent_window.attempt_search_reward(1)
        elif "duckduckgo.com" in host: self.parent_window.attempt_search_reward(1)
        elif "ecosia.org" in host: self.parent_window.attempt_search_reward(2)

        if not url.startswith("local://") and not url.startswith("navi://"):
            self.parent_window.add_to_history(url, self.title())

    def createWindow(self, _type): return self.parent_window.add_new_tab()

# --- Main Window ---
class NaviBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser Ultimate v4")
        self.resize(1300, 900)
        
        # Defaults
        self.data = {
            'sites': {}, 'extensions': {}, 'history': [], 'downloads': [],
            'settings': {'theme': 'light', 'wholesome_switch': True, 'home_notes': '', 'custom_suffix': '.pw-navi'},
            'proxy': {'type': 'Google', 'key': '', 'url': ''},
            'navits': 0, 'inventory': [], 'last_active': time.time(),
            'last_reward_time': 0
        }
        
        self.load_from_disk()
        self.check_dead_mans_switch()
        self.setup_ui()
        self.apply_theme()
        
        self.add_new_tab(QUrl("local://navi/"))

    def setup_ui(self):
        tb = QToolBar(); tb.setMovable(False); self.addToolBar(tb)

        # Nav
        for t, f in [("←", self.go_back), ("→", self.go_forward), ("⟳", self.reload_page), ("🏠", self.go_home)]:
            b = QPushButton(t); b.setFixedSize(35,35); b.clicked.connect(f); tb.addWidget(b)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter address...")
        self.url_bar.returnPressed.connect(self.navigate)
        tb.addWidget(self.url_bar)

        # Tools
        for t, f, tip in [("⬇️", self.download_page, "DL"), ("< >", self.inspect_page, "Src"), ("+", self.add_new_tab_safe, "New Tab")]:
            b = QPushButton(t); b.setToolTip(tip); b.setFixedSize(35,35); b.clicked.connect(f); tb.addWidget(b)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.setCentralWidget(self.tabs)

    # --- Navits Logic ---
    def attempt_search_reward(self, amount):
        now = time.time()
        # 60 second cooldown on search rewards
        if now - self.data.get('last_reward_time', 0) > 60:
            self.add_navits(amount, "Search Reward")
            self.data['last_reward_time'] = now
    
    def add_navits(self, amount, reason=""):
        self.data['navits'] = self.data.get('navits', 0) + amount
        print(f"Earned {amount} Navits: {reason} (Total: {self.data['navits']})")
        self.save_to_disk()

    # --- Feature Logic ---
    def check_dead_mans_switch(self):
        if not self.data['settings']['wholesome_switch']: return
        if time.time() - self.data.get('last_active', 0) > TWO_WEEKS_SECONDS:
            QMessageBox.information(self, "Welcome Back", "Optimizing your experience...")
            self.data['history'] = get_wholesome_history()
        self.data['last_active'] = time.time()
        self.save_to_disk()

    def add_to_history(self, url, title):
        if self.data['history'] and self.data['history'][0]['url'] == url: return
        self.data['history'].insert(0, {'url': url, 'title': title, 'time': time.time()})
        self.data['history'] = self.data['history'][:1000]
        self.save_to_disk()

    # --- Safe Tab Adding (Crash Fix) ---
    def add_new_tab_safe(self):
        try:
            self.add_new_tab()
        except Exception as e:
            print(f"Error adding tab: {e}")

    def download_page(self):
        t = self.tabs.currentWidget()
        if t: t.page().toHtml(lambda h: self.save_download(t.title(), h))

    def save_download(self, t, h):
        self.data['downloads'].append({'title': t, 'html': h, 'date': time.time(), 'id': str(int(time.time()))})
        self.save_to_disk(); QMessageBox.information(self, "Saved", "Page saved offline!")

    def inspect_page(self):
        t = self.tabs.currentWidget()
        if t: t.page().toHtml(lambda h: SourceViewer(h, self).exec_())

    # --- Routing ---
    def handle_internal_pages(self, url, browser):
        cmd = url.lower().replace("navi://", "").strip("/")
        theme = self.data['settings']['theme']
        
        if cmd == "" or cmd == "home":
            unlocked = "widgets" in self.data['inventory']
            browser.setHtml(InternalPages.home(theme, self.data['settings']['home_notes'], self.data.get('navits',0), unlocked), QUrl("local://navi/"))
        elif cmd == "navits":
            self.render_navits(browser)
        elif cmd == "navits/buy":
            self.render_store(browser)
        elif cmd == "settings":
            self.render_settings(browser)
        elif cmd == "pw":
            self.render_sites(browser)
        elif cmd == "cws":
            self.render_extensions(browser)
        elif cmd == "history":
            self.render_history(browser)
        elif cmd == "dlw":
            self.render_downloads(browser)
        elif cmd == "info":
             # Fixed syntax error with triple quotes
            browser.setHtml(f"""<html><head><style>{InternalPages.css(theme)}</style></head><body><div class="container"><h1>Info</h1><div class="card">Navi Browser v4<br><br><a href="https://discord.gg/64um79VVMa" class="btn" style="background:#5865F2">Discord</a></div></div></body></html>""", QUrl("local://navi/info"))
            
        # Commands
        elif cmd.startswith("save_notes/"):
            self.data['settings']['home_notes'] = QUrl.fromPercentEncoding(url.split("save_notes/")[1].encode())
            self.save_to_disk()
        elif cmd.startswith("settings/set_theme/"):
            t = url.split("set_theme/")[1]
            self.data['settings']['theme'] = t
            self.apply_theme()
            self.save_to_disk(); self.render_settings(browser)
        elif cmd.startswith("settings/set_suffix/"):
            s = QUrl.fromPercentEncoding(url.split("set_suffix/")[1].encode())
            if not s.startswith("."): s = "." + s
            if not s.endswith(".navi"): 
                QMessageBox.warning(self, "Invalid", "Suffix must be empty or just a word, code adds .navi")
            else:
                self.data['settings']['custom_suffix'] = s
                self.save_to_disk()
            self.render_settings(browser)
        elif cmd.startswith("store/buy/"):
            item = url.split("buy/")[1]
            self.buy_item(item)
            self.render_store(browser)

        # Editors
        elif cmd == "pw/new": CodeEditorWindow(self, "site").show()
        elif cmd.startswith("pw/edit/"): CodeEditorWindow(self, "site", QUrl.fromPercentEncoding(url.split("edit/")[1].encode())).show()
        elif cmd.startswith("pw/delete/"):
            d = QUrl.fromPercentEncoding(url.split("delete/")[1].encode())
            if d in self.data['sites']: del self.data['sites'][d]; self.save_to_disk()
            self.render_sites(browser)
        elif cmd == "cws/new": CodeEditorWindow(self, "ext").show()
        elif cmd.startswith("cws/edit/"): CodeEditorWindow(self, "ext", QUrl.fromPercentEncoding(url.split("edit/")[1].encode())).show()
        elif cmd.startswith("cws/toggle/"):
            n = QUrl.fromPercentEncoding(url.split("toggle/")[1].encode())
            if n in self.data['extensions']: 
                self.data['extensions'][n]['active'] = not self.data['extensions'][n]['active']
                self.save_to_disk()
            self.render_extensions(browser)

    def buy_item(self, item_id):
        prices = {"christmas": 150, "halloween": 150, "suffix": 250, "widgets": 200}
        
        # Seasonal Check
        if item_id in ["christmas", "halloween"] and not is_seasonal(item_id):
            QMessageBox.warning(self, "Unavailable", "This item is not currently available!")
            return

        price = prices.get(item_id, 9999)
        balance = self.data.get('navits', 0)

        if item_id in self.data['inventory']:
            QMessageBox.information(self, "Owned", "You already own this item.")
            return

        if balance >= price:
            self.data['navits'] -= price
            self.data['inventory'].append(item_id)
            self.save_to_disk()
            QMessageBox.information(self, "Success", f"Bought {item_id}!")
        else:
            QMessageBox.warning(self, "Poor", f"Need {price} Navits. You have {balance}.")

    # --- Renderers ---
    def render_navits(self, b):
        t = self.data['settings']['theme']
        # Fixed syntax error with triple quotes
        html = f"""<html><head><style>{InternalPages.css(t)}</style></head><body><div class="container">
        <h1>🏆 Navits System</h1>
        <div class="card">
            <h2>Balance: {self.data.get('navits', 0)} Navits</h2>
            <p>Earn points by browsing and watching!</p>
            <ul>
                <li>Google/DuckDuckGo Search: +1</li>
                <li>Ecosia Search: +2</li>
                <li>YouTube (15 mins): +1</li>
            </ul>
            <a href="navi://navits/buy" class="btn btn-gold">Go to Store</a>
        </div></div></body></html>"""
        b.setHtml(html, QUrl("local://navi/navits"))

    def render_store(self, b):
        t = self.data['settings']['theme']
        inv = self.data['inventory']
        
        # Items logic
        items_html = ""
        
        # Christmas
        btn_cls = "btn-success" if is_seasonal("christmas") else "btn-danger"
        lbl = "Buy (150 N)" if "christmas" not in inv else "Owned"
        action = "navi://store/buy/christmas" if "christmas" not in inv else "#"
        items_html += f"""<div class="card"><h3>🎄 Christmas Theme</h3><p>Seasonal (Dec-Jan)</p><a href="{action}" class="btn {btn_cls}">{lbl}</a></div>"""

        # Halloween
        btn_cls = "btn-success" if is_seasonal("halloween") else "btn-danger"
        lbl = "Buy (150 N)" if "halloween" not in inv else "Owned"
        action = "navi://store/buy/halloween" if "halloween" not in inv else "#"
        items_html += f"""<div class="card"><h3>🎃 Halloween Theme</h3><p>Seasonal (Oct)</p><a href="{action}" class="btn {btn_cls}">{lbl}</a></div>"""

        # Suffix
        lbl = "Buy (250 N)" if "suffix" not in inv else "Owned"
        action = "navi://store/buy/suffix" if "suffix" not in inv else "#"
        items_html += f"""<div class="card"><h3>🔗 Custom Domain Suffix</h3><p>Change .pw-navi to your own suffix!</p><a href="{action}" class="btn">{lbl}</a></div>"""

        # Widgets
        lbl = "Buy (200 N)" if "widgets" not in inv else "Owned"
        action = "navi://store/buy/widgets" if "widgets" not in inv else "#"
        items_html += f"""<div class="card"><h3>🧩 Pro Widgets</h3><p>Calculator & Calendar on start page.</p><a href="{action}" class="btn">{lbl}</a></div>"""

        # Fixed syntax error with triple quotes
        b.setHtml(f"""<html><head><style>{InternalPages.css(t)}</style></head><body><div class="container"><h1>🛒 Navits Store</h1><p>Balance: {self.data.get('navits',0)}</p><div class="widget-grid">{items_html}</div></div></body></html>""", QUrl("local://navi/store"))

    def render_settings(self, b):
        s = self.data['settings']
        t = s['theme']
        inv = self.data['inventory']
        
        themes_html = """<a href="navi://settings/set_theme/light" class="btn">Light</a> <a href="navi://settings/set_theme/dark" class="btn" style="background:#333">Dark</a>"""
        if "christmas" in inv: themes_html += """ <a href="navi://settings/set_theme/christmas" class="btn" style="background:green">Christmas</a>"""
        if "halloween" in inv: themes_html += """ <a href="navi://settings/set_theme/halloween" class="btn" style="background:orange">Halloween</a>"""

        suffix_html = ""
        if "suffix" in inv:
            suffix_html = f"""<div class="card"><h3>🔗 Custom Suffix</h3><input id="suf" value="{s.get('custom_suffix', '.pw-navi')}"><button class="btn" onclick="window.location='navi://settings/set_suffix/'+encodeURIComponent(document.getElementById('suf').value)">Update</button></div>"""

        # Fixed syntax error with triple quotes
        html = f"""<html><head><style>{InternalPages.css(t)}</style></head><body><div class="container"><h1>Settings</h1><div class="card"><h3>🎨 Theme</h3>{themes_html}</div>{suffix_html}</div></body></html>"""
        b.setHtml(html, QUrl("local://navi/settings"))

    def render_sites(self, b):
        t = self.data['settings']['theme']
        r = ""
        for d, v in self.data['sites'].items(): r += f"""<div class="card"><b>{v['title']}</b> ({d})<br><br><a href="{d}" class="btn">Visit</a> <a href="navi://pw/edit/{d}" class="btn btn-success">Edit</a> <a href="navi://pw/delete/{d}" class="btn btn-danger">Delete</a></div>"""
        # Fixed syntax error with triple quotes
        b.setHtml(f"""<html><head><style>{InternalPages.css(t)}</style></head><body><div class="container"><h1>My Sites</h1><a href="navi://pw/new" class="btn">+ New</a><br><br>{r}</div></body></html>""", QUrl("local://navi/pw"))

    def render_extensions(self, b):
        t = self.data['settings']['theme']
        r = ""
        for k, v in self.data['extensions'].items(): 
            c = "green" if v['active'] else "gray"
            r += f"""<div class="card" style="border-left:5px solid {c}"><h3>{k}</h3><a href="navi://cws/toggle/{k}" class="btn">Toggle</a> <a href="navi://cws/edit/{k}" class="btn">Edit</a></div>"""
        # Fixed syntax error with triple quotes
        b.setHtml(f"""<html><head><style>{InternalPages.css(t)}</style></head><body><div class="container"><h1>Extensions</h1><a href="navi://cws/new" class="btn">+ New</a><br><br>{r}</div></body></html>""", QUrl("local://navi/cws"))

    def render_history(self, b):
        t = self.data['settings']['theme']
        r = ""
        for h in self.data['history']: r += f"""<div class="card"><a href="{h['url']}"><b>{h.get('title','Page')}</b></a><br><small>{h['url']}</small></div>"""
        # Fixed syntax error with triple quotes
        b.setHtml(f"""<html><head><style>{InternalPages.css(t)}</style></head><body><div class="container"><h1>History</h1>{r}</div></body></html>""", QUrl("local://navi/history"))

    def render_downloads(self, b):
        t = self.data['settings']['theme']
        r = ""
        for d in self.data['downloads']: r += f"""<div class="card"><h3>{d['title']}</h3><a href="navi://dlw/view/{d['id']}" class="btn">View</a> <a href="navi://dlw/delete/{d['id']}" class="btn btn-danger">Delete</a></div>"""
        # Fixed syntax error with triple quotes
        b.setHtml(f"""<html><head><style>{InternalPages.css(t)}</style></head><body><div class="container"><h1>Downloads</h1>{r}</div></body></html>""", QUrl("local://navi/dlw"))

    # --- Std Funcs ---
    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None: qurl = QUrl("local://navi/")
        b = BrowserTab(self); b.setUrl(qurl)
        b.urlChanged.connect(lambda q, b=b: self.update_url_bar_for_tab(q, b))
        b.titleChanged.connect(lambda t, b=b: self.update_tab_title(t, b))
        i = self.tabs.addTab(b, label); self.tabs.setCurrentIndex(i)

    def close_tab(self, i): 
        if self.tabs.count() > 1: self.tabs.removeTab(i)
    def update_tab_title(self, t, b): 
        i = self.tabs.indexOf(b); 
        if i!=-1: self.tabs.setTabText(i, t[:15])
    def go_back(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().back()
    def go_forward(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().forward()
    def reload_page(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().reload()
    def go_home(self): 
        if self.tabs.currentWidget(): self.tabs.currentWidget().setUrl(QUrl("local://navi/"))
    def update_url_bar(self, i): 
        if i>=0: self.update_bar_text(self.tabs.widget(i).url().toString())
    def update_url_bar_for_tab(self, q, b):
        if b==self.tabs.currentWidget(): self.update_bar_text(q.toString())
        if q.scheme()=="navi": self.handle_internal_pages(q.toString(), b)
    def update_bar_text(self, url):
        if url.startswith("local://navi/"): self.url_bar.setText(url.replace("local://navi/", "navi://").rstrip("/"))
        elif not url.startswith("local://"): self.url_bar.setText(url)
    
    def navigate(self):
        text = self.url_bar.text().strip()
        browser = self.tabs.currentWidget()
        if not browser: return
        
        if text.lower().startswith("navi://"): self.handle_internal_pages(text, browser)
        else:
            # Custom Suffix Support
            suffix = self.data['settings'].get('custom_suffix', '.pw-navi')
            if text.lower().endswith(suffix):
                d = self.data['sites'].get(text.lower())
                if d: browser.setHtml(d['html_content'], QUrl(f"local://{text}/"))
                return

            u = QUrl(text)
            if "." not in text: u = QUrl(f"https://www.google.com/search?q={text}")
            elif "://" not in text: u = QUrl("https://" + text)
            browser.setUrl(u)

    def save_to_disk(self):
        try:
            with open(DATA_FILE, 'w') as f: json.dump(self.data, f)
        except: pass
    
    def load_from_disk(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f: 
                    loaded = json.load(f)
                    self.data.update(loaded)
                    
                    # --- MIGRATION LOGIC (The Fix) ---
                    # Ensure all new keys exist in old data files
                    if 'settings' not in self.data: self.data['settings'] = {}
                    if 'theme' not in self.data['settings']: self.data['settings']['theme'] = 'light'
                    if 'wholesome_switch' not in self.data['settings']: self.data['settings']['wholesome_switch'] = True
                    if 'custom_suffix' not in self.data['settings']: self.data['settings']['custom_suffix'] = '.pw-navi'
                    
                    if 'inventory' not in self.data: self.data['inventory'] = []
                    if 'navits' not in self.data: self.data['navits'] = 0
                    if 'sites' not in self.data: self.data['sites'] = {}
                    if 'extensions' not in self.data: self.data['extensions'] = {}
                    if 'history' not in self.data: self.data['history'] = []
                    if 'downloads' not in self.data: self.data['downloads'] = []
            except: pass

    def apply_theme(self):
        # Now self.data['settings']['theme'] is guaranteed to exist
        self.setStyleSheet(ModernStyles.get(self.data['settings']['theme']))
        if self.tabs.currentWidget(): self.tabs.currentWidget().reload()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Navi Browser")
    window = NaviBrowser()
    window.show()
    sys.exit(app.exec_())

