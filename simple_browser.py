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
    QHBoxLayout
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings

# --- Constants ---
DATA_FILE = "navi_data.json"
TWO_WEEKS_SECONDS = 1209600

# --- Wholesome History Generator ---
def get_wholesome_history():
    return [
        {"url": "https://www.google.com/search?q=how+to+make+my+parents+proud", "time": time.time(), "title": "Self Improvement"},
        {"url": "https://www.google.com/search?q=local+animal+shelter+donations", "time": time.time() - 100, "title": "Charity"},
        {"url": "https://www.youtube.com/watch?v=cute_puppies", "time": time.time() - 200, "title": "Stress Relief"},
        {"url": "https://www.wikipedia.org/wiki/Peace", "time": time.time() - 1000, "title": "Education"},
    ]

# --- Styles ---
class ModernStyles:
    @staticmethod
    def get(dark_mode):
        bg = "#212529" if dark_mode else "#f8f9fa"
        fg = "#f8f9fa" if dark_mode else "#212529"
        input_bg = "#343a40" if dark_mode else "#ffffff"
        border = "#495057" if dark_mode else "#dee2e6"
        btn_hover = "#495057" if dark_mode else "#e9ecef"
        
        return f"""
        QMainWindow {{ background-color: {bg}; color: {fg}; }}
        QWidget {{ color: {fg}; }}
        QTabWidget::pane {{ border: 0; background: {bg}; }}
        QTabBar::tab {{
            background: {input_bg}; color: {fg}; padding: 8px 20px;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{ background: {bg}; border-bottom: 2px solid #0d6efd; font-weight: bold; }}
        QToolBar {{ background: {bg}; border-bottom: 1px solid {border}; spacing: 5px; }}
        QLineEdit {{
            background: {input_bg}; border: 1px solid {border}; border-radius: 15px;
            padding: 6px 15px; color: {fg};
        }}
        QPushButton {{
            background-color: transparent; border-radius: 5px; padding: 5px;
            color: {fg}; font-weight: bold; font-size: 14px;
        }}
        QPushButton:hover {{ background-color: {btn_hover}; }}
        QMenu {{ background: {input_bg}; color: {fg}; border: 1px solid {border}; }}
        QMenu::item:selected {{ background: #0d6efd; color: white; }}
        QPlainTextEdit {{ background: {input_bg}; color: {fg}; border: 1px solid {border}; }}
        """

# --- Custom Web Engine ---
class NaviWebPage(QWebEnginePage):
    # Fix for "Websites don't load" - Ignore SSL Errors
    def certificateError(self, error):
        return True 

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() == "navi":
            view = self.view()
            if view and hasattr(view, 'parent_window'):
                view.parent_window.handle_internal_pages(url.toString(), view)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

# --- Internal Pages HTML Generator ---
class InternalPages:
    @staticmethod
    def css(dark_mode):
        bg = "#2b3035" if dark_mode else "#f8f9fa"
        card_bg = "#343a40" if dark_mode else "#ffffff"
        text = "#f8f9fa" if dark_mode else "#212529"
        border = "#495057" if dark_mode else "#dee2e6"
        return f"""
        body {{ font-family: 'Segoe UI', sans-serif; background: {bg}; color: {text}; padding: 40px; margin: 0; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #0d6efd; font-weight: 300; }}
        .card {{ background: {card_bg}; padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid {border}; }}
        .btn {{ padding: 10px 20px; background: #0d6efd; color: white; border: none; border-radius: 6px; text-decoration: none; cursor: pointer; display: inline-block; }}
        .btn:hover {{ background: #0b5ed7; }}
        .btn-danger {{ background: #dc3545; }}
        .btn-success {{ background: #198754; }}
        input, select, textarea {{ 
            padding: 12px; width: 100%; margin: 10px 0; border-radius: 6px; 
            border: 1px solid {border}; background: {bg}; color: {text}; box-sizing: border-box; 
        }}
        .widget-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }}
        .clock {{ font-size: 3em; font-weight: bold; text-align: center; margin: 20px 0; }}
        .switch {{ position: relative; display: inline-block; width: 60px; height: 34px; }}
        .switch input {{ opacity: 0; width: 0; height: 0; }}
        .slider {{ position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 34px; }}
        .slider:before {{ position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }}
        input:checked + .slider {{ background-color: #2196F3; }}
        input:checked + .slider:before {{ transform: translateX(26px); }}
        """

    @staticmethod
    def home(dark_mode, notes):
        return f"""<html><head><style>{InternalPages.css(dark_mode)}</style>
        <script>
            function updateClock() {{
                const now = new Date();
                document.getElementById('clock').innerText = now.toLocaleTimeString();
            }}
            setInterval(updateClock, 1000);
            function saveNotes(val) {{
                window.location = 'navi://save_notes/' + encodeURIComponent(val);
            }}
        </script>
        </head><body>
        <div class="container">
            <div id="clock" class="clock">00:00:00</div>
            <div class="widget-grid">
                <div class="card">
                    <h3>📝 Quick Notes</h3>
                    <textarea style="height: 150px; resize: none;" oninput="saveNotes(this.value)">{notes}</textarea>
                </div>
                <div class="card" style="text-align:center;">
                    <h3>🚀 Navigation</h3>
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        <a href="navi://settings" class="btn">⚙️ Settings</a>
                        <a href="navi://pw" class="btn">🌐 My Sites</a>
                        <a href="navi://dlw" class="btn">⬇️ Downloads</a>
                        <a href="navi://history" class="btn">🕒 History</a>
                        <a href="navi://cws" class="btn">🧩 Extensions</a>
                        <a href="navi://info" class="btn">ℹ️ Info</a>
                    </div>
                </div>
            </div>
        </div></body></html>"""

# --- Source Code Viewer ---
class SourceViewer(QDialog):
    def __init__(self, html_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inspect Source")
        self.resize(800, 600)
        layout = QVBoxLayout()
        text_edit = QPlainTextEdit()
        text_edit.setPlainText(html_content)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 14px;")
        layout.addWidget(text_edit)
        self.setLayout(layout)

# --- Code Editor (Site/Ext) ---
class CodeEditorWindow(QWidget):
    def __init__(self, browser_main, mode="site", key_to_edit=None):
        super().__init__()
        self.browser_main = browser_main
        self.mode = mode
        self.key_to_edit = key_to_edit
        self.setWindowTitle(f"Navi Editor - {mode.capitalize()}")
        self.resize(900, 700)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")
        if self.key_to_edit: self.name_input.setReadOnly(True)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)
        
        if self.mode == "site":
            self.title_input = QLineEdit()
            self.title_input.setPlaceholderText("Page Title")
            layout.addWidget(QLabel("Title:"))
            layout.addWidget(self.title_input)

        self.content_input = QTextEdit()
        layout.addWidget(QLabel("Code:"))
        layout.addWidget(self.content_input)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("background: #198754; color: white; padding: 10px; font-weight: bold;")
        save_btn.clicked.connect(self.save_data)
        layout.addWidget(save_btn)
        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        if not self.key_to_edit: return
        if self.mode == "site":
            data = self.browser_main.data['sites'].get(self.key_to_edit)
            if data:
                self.name_input.setText(self.key_to_edit.replace(".pw-navi", ""))
                self.title_input.setText(data.get('title', ''))
                self.content_input.setText(data.get('html_content', ''))
        else:
            data = self.browser_main.data['extensions'].get(self.key_to_edit)
            if data:
                self.name_input.setText(self.key_to_edit)
                self.content_input.setText(data.get('code', ''))

    def save_data(self):
        name = self.name_input.text().strip()
        code = self.content_input.toPlainText()
        if not name: return

        if self.mode == "site":
            full = f"{name.lower()}.pw-navi" if not name.endswith(".pw-navi") else name.lower()
            self.browser_main.data['sites'][full] = {'domain': full, 'title': self.title_input.text(), 'html_content': code}
            self.browser_main.add_new_tab(QUrl(f"local://{full}/"))
        else:
            self.browser_main.data['extensions'][name] = {'code': code, 'active': True}
            
        self.browser_main.save_to_disk()
        self.close()

# --- Browser Tab ---
class BrowserTab(QWebEngineView):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        
        # Enhanced Profile Settings
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpCacheType(QWebEngineProfile.MemoryHttpCache)
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)

        self.setPage(NaviWebPage(self))
        self.page().loadFinished.connect(self.on_load_finished)

    def on_load_finished(self, ok):
        if not ok: return
        for name, ext in self.parent_window.data['extensions'].items():
            if ext['active']: self.page().runJavaScript(ext['code'])
        
        url = self.url().toString()
        if not url.startswith("local://") and not url.startswith("navi://"):
            self.parent_window.add_to_history(url, self.title())

    def createWindow(self, _type):
        return self.parent_window.add_new_tab()

# --- Main Window ---
class NaviBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser Ultimate")
        self.resize(1300, 900)
        
        # Data & Defaults
        self.data = {
            'sites': {}, 'extensions': {}, 'history': [], 'downloads': [],
            'settings': {'dark_mode': False, 'wholesome_switch': True, 'home_notes': ''},
            'proxy': {'type': 'Google', 'key': '', 'url': ''},
            'last_active': time.time()
        }
        
        self.load_from_disk()
        self.check_dead_mans_switch()
        self.setup_ui()
        self.apply_theme()
        
        # Start Page
        self.add_new_tab(QUrl("local://navi/"))

    def setup_ui(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Main Nav
        actions = [("←", self.go_back), ("→", self.go_forward), ("⟳", self.reload_page), ("🏠", self.go_home)]
        for t, f in actions:
            btn = QPushButton(t)
            btn.setFixedSize(35, 35)
            btn.clicked.connect(f)
            toolbar.addWidget(btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter address...")
        self.url_bar.returnPressed.connect(self.navigate)
        toolbar.addWidget(self.url_bar)

        # Tools
        tools = [
            ("⬇️", self.download_page, "Download Offline"),
            ("< >", self.inspect_page, "View Source"),
            ("+", self.add_new_tab, "New Tab")
        ]
        for t, f, tip in tools:
            btn = QPushButton(t)
            btn.setToolTip(tip)
            btn.setFixedSize(35, 35)
            btn.clicked.connect(f)
            toolbar.addWidget(btn)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.setCentralWidget(self.tabs)

    # --- Feature Logic ---
    def check_dead_mans_switch(self):
        if not self.data['settings']['wholesome_switch']: return
        
        now = time.time()
        last = self.data.get('last_active', now)
        if now - last > TWO_WEEKS_SECONDS:
            QMessageBox.information(self, "Welcome Back", "Optimizing your experience...")
            self.data['history'] = get_wholesome_history()
        self.data['last_active'] = now
        self.save_to_disk()

    def add_to_history(self, url, title):
        if self.data['history'] and self.data['history'][0]['url'] == url: return
        self.data['history'].insert(0, {'url': url, 'title': title, 'time': time.time()})
        self.data['history'] = self.data['history'][:1000]
        self.save_to_disk()

    def download_page(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        tab.page().toHtml(lambda html: self.save_download(tab.title(), html))

    def save_download(self, title, html):
        self.data['downloads'].append({
            'title': title, 'html': html, 'date': time.time(),
            'id': str(int(time.time()))
        })
        self.save_to_disk()
        QMessageBox.information(self, "Saved", "Page saved for offline viewing!")

    def inspect_page(self):
        tab = self.tabs.currentWidget()
        if not tab: return
        tab.page().toHtml(lambda html: SourceViewer(html, self).exec_())

    # --- Internal Page Routing ---
    def handle_internal_pages(self, url, browser):
        cmd = url.lower().replace("navi://", "").strip("/")
        dm = self.data['settings']['dark_mode']
        
        if cmd == "" or cmd == "home":
            browser.setHtml(InternalPages.home(dm, self.data['settings']['home_notes']), QUrl("local://navi/"))
        elif cmd == "settings":
            self.render_settings(browser)
        elif cmd == "dlw":
            self.render_downloads(browser)
        elif cmd == "history":
            self.render_history(browser)
        elif cmd == "pw":
            self.render_sites(browser)
        elif cmd == "cws":
            self.render_extensions(browser)
        elif cmd == "proxy":
            self.render_proxy(browser)
        elif cmd == "info":
            self.render_info(browser)
            
        # Commands
        elif cmd.startswith("save_notes/"):
            note = QUrl.fromPercentEncoding(url.split("save_notes/")[1].encode())
            self.data['settings']['home_notes'] = note
            self.save_to_disk()
        elif cmd.startswith("settings/toggle/"):
            setting = url.split("toggle/")[1]
            if setting in self.data['settings']:
                self.data['settings'][setting] = not self.data['settings'][setting]
                if setting == 'dark_mode': self.apply_theme()
                self.save_to_disk()
                self.render_settings(browser)
        elif cmd.startswith("dlw/view/"):
            did = url.split("view/")[1]
            page = next((d for d in self.data['downloads'] if d['id'] == did), None)
            if page: browser.setHtml(page['html'], QUrl("local://offline"))
        elif cmd.startswith("dlw/delete/"):
            did = url.split("delete/")[1]
            self.data['downloads'] = [d for d in self.data['downloads'] if d['id'] != did]
            self.save_to_disk()
            self.render_downloads(browser)
        
        # Editors
        elif cmd == "pw/new":
            self.editor = CodeEditorWindow(self, "site"); self.editor.show()
        elif cmd.startswith("pw/edit/"):
            d = QUrl.fromPercentEncoding(url.split("edit/")[1].encode())
            self.editor = CodeEditorWindow(self, "site", d); self.editor.show()
        elif cmd.startswith("pw/delete/"):
            d = QUrl.fromPercentEncoding(url.split("delete/")[1].encode())
            if d in self.data['sites']: del self.data['sites'][d]; self.save_to_disk()
            self.render_sites(browser)
            
        elif cmd == "cws/new":
            self.editor = CodeEditorWindow(self, "ext"); self.editor.show()
        elif cmd.startswith("cws/edit/"):
            n = QUrl.fromPercentEncoding(url.split("edit/")[1].encode())
            self.editor = CodeEditorWindow(self, "ext", n); self.editor.show()
        elif cmd.startswith("cws/toggle/"):
            n = QUrl.fromPercentEncoding(url.split("toggle/")[1].encode())
            if n in self.data['extensions']:
                self.data['extensions'][n]['active'] = not self.data['extensions'][n]['active']
                self.save_to_disk()
            self.render_extensions(browser)

    # --- Renderers ---
    def render_settings(self, browser):
        s = self.data['settings']
        dm = s['dark_mode']
        html = f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container">
        <h1>Settings</h1>
        <div class="card">
            <h3>🎨 Appearance</h3>
            <label class="switch"><input type="checkbox" {'checked' if s['dark_mode'] else ''} onclick="window.location='navi://settings/toggle/dark_mode'"><span class="slider"></span></label> Dark Mode
        </div>
        <div class="card">
            <h3>👻 Privacy & Safety</h3>
            <label class="switch"><input type="checkbox" {'checked' if s['wholesome_switch'] else ''} onclick="window.location='navi://settings/toggle/wholesome_switch'"><span class="slider"></span></label> 
            <b>Dead Man's Switch (Wholesome History)</b><br>
            <small>If inactive for 14 days, replace history with wholesome content.</small>
        </div>
        </div></body></html>"""
        browser.setHtml(html, QUrl("local://navi/settings"))

    def render_downloads(self, browser):
        dm = self.data['settings']['dark_mode']
        rows = ""
        for d in self.data['downloads']:
            date = datetime.fromtimestamp(d['date']).strftime('%Y-%m-%d %H:%M')
            rows += f"""<div class="card"><h3>{d['title']}</h3><small>{date}</small><br><br>
            <a href="navi://dlw/view/{d['id']}" class="btn">View Offline</a> 
            <a href="navi://dlw/delete/{d['id']}" class="btn btn-danger">Delete</a></div>"""
        
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>Offline Downloads</h1>{rows or 'No downloads yet.'}</div></body></html>""", QUrl("local://navi/dlw"))

    def render_history(self, browser):
        dm = self.data['settings']['dark_mode']
        rows = ""
        for h in self.data['history']:
            t = datetime.fromtimestamp(h['time']).strftime('%b %d, %H:%M')
            rows += f"""<div class="card"><a href="{h['url']}"><b>{h.get('title','Page')}</b></a><br><small>{h['url']} - {t}</small></div>"""
        
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>History</h1>{rows}</div></body></html>""", QUrl("local://navi/history"))

    def render_sites(self, browser):
        dm = self.data['settings']['dark_mode']
        rows = ""
        for d, v in self.data['sites'].items():
            rows += f"""<div class="card"><b>{v['title']}</b> ({d}) <br><br><a href="{d}" class="btn">Visit</a> <a href="navi://pw/edit/{d}" class="btn btn-success">Edit</a> <a href="navi://pw/delete/{d}" class="btn btn-danger">Delete</a></div>"""
        
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>My Sites</h1><a href="navi://pw/new" class="btn">+ New Site</a><br><br>{rows}</div></body></html>""", QUrl("local://navi/pw"))

    def render_extensions(self, browser):
        dm = self.data['settings']['dark_mode']
        rows = ""
        for k, v in self.data['extensions'].items():
            clr = "green" if v['active'] else "gray"
            rows += f"""<div class="card" style="border-left:5px solid {clr}"><h3>{k}</h3><button class="btn" onclick="window.location='navi://cws/toggle/{k}'">Toggle</button> <button class="btn" onclick="window.location='navi://cws/edit/{k}'">Edit</button></div>"""
        
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>Extensions</h1><a href="navi://cws/new" class="btn">+ New Ext</a><br><br>{rows}</div></body></html>""", QUrl("local://navi/cws"))
    
    def render_proxy(self, browser):
        dm = self.data['settings']['dark_mode']
        p = self.data['proxy']
        html = f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>Proxy</h1><div class="card"><label>Type</label><select id="t"><option>Google</option><option>Cloudflare</option></select><label>Key</label><input id="k" value="{p['key']}"><label>URL</label><input id="u"><button class="btn" onclick="run()">Go</button></div></div>
        <script>function run() {{ window.location='navi://proxy/run/'+document.getElementById('t').value+'/'+encodeURIComponent(document.getElementById('k').value)+'/'+encodeURIComponent(document.getElementById('u').value); }}</script></body></html>"""
        browser.setHtml(html, QUrl("local://navi/proxy"))

    def render_info(self, browser):
        dm = self.data['settings']['dark_mode']
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>About Navi</h1><div class="card">Version: Ultimate v3<br><br><a href="https://discord.gg/64um79VVMa" class="btn" style="background:#5865F2">Discord</a></div></div></body></html>""", QUrl("local://navi/info"))

    # --- Standard Funcs ---
    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None: qurl = QUrl("local://navi/")
        browser = BrowserTab(self)
        browser.setUrl(qurl)
        browser.urlChanged.connect(lambda q, b=browser: self.update_url_bar_for_tab(q, b))
        browser.titleChanged.connect(lambda t, b=browser: self.update_tab_title(t, b))
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

    def close_tab(self, i): 
        if self.tabs.count() > 1: self.tabs.removeTab(i)
    def update_tab_title(self, t, b): 
        i = self.tabs.indexOf(b); 
        if i!=-1: self.tabs.setTabText(i, t[:15])
    def go_back(self): self.tabs.currentWidget().back()
    def go_forward(self): self.tabs.currentWidget().forward()
    def reload_page(self): self.tabs.currentWidget().reload()
    def go_home(self): self.tabs.currentWidget().setUrl(QUrl("local://navi/"))
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
        if text.lower().startswith("navi://"): self.handle_internal_pages(text, browser)
        elif text.lower().endswith(".pw-navi"):
            d = self.data['sites'].get(text.lower())
            if d: browser.setHtml(d['html_content'], QUrl(f"local://{text}/"))
        else:
            url = QUrl(text)
            if "." not in text: url = QUrl(f"https://www.google.com/search?q={text}")
            elif "://" not in text: url = QUrl("https://" + text)
            browser.setUrl(url)

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
                    if 'settings' not in self.data: self.data['settings'] = {'dark_mode':False, 'wholesome_switch':True, 'home_notes':''}
                    if 'downloads' not in self.data: self.data['downloads'] = []
            except: pass

    def apply_theme(self):
        self.setStyleSheet(ModernStyles.get(self.data['settings']['dark_mode']))
        self.reload_page()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Navi Browser")
    window = NaviBrowser()
    window.show()
    sys.exit(app.exec_())

