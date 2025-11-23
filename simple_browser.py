import sys
import json
import os
import time
import random
from PyQt5.QtCore import QUrl, Qt, QSize, QDateTime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit,
    QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit,
    QMessageBox, QTabWidget, QMenu, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

# --- Constants ---
DATA_FILE = "navi_data.json"
TWO_WEEKS_SECONDS = 1209600  # 14 days in seconds

# --- Wholesome Generator ---
def get_wholesome_history():
    return [
        {"url": "https://www.google.com/search?q=how+to+make+my+parents+proud", "time": time.time(), "title": "Google Search"},
        {"url": "https://www.google.com/search?q=local+animal+shelter+donations", "time": time.time() - 100, "title": "Charity"},
        {"url": "https://www.youtube.com/watch?v=cute_puppies", "time": time.time() - 200, "title": "Cute Puppies"},
        {"url": "https://www.google.com/search?q=best+birthday+gifts+for+mom", "time": time.time() - 500, "title": "Shopping"},
        {"url": "https://www.wikipedia.org/wiki/Peace", "time": time.time() - 1000, "title": "Learning"},
    ]

# --- Styles ---
class ModernStyles:
    @staticmethod
    def get(dark_mode):
        bg = "#212529" if dark_mode else "#f8f9fa"
        fg = "#f8f9fa" if dark_mode else "#212529"
        input_bg = "#343a40" if dark_mode else "#ffffff"
        border = "#495057" if dark_mode else "#dee2e6"
        
        return f"""
        QMainWindow {{ background-color: {bg}; }}
        QWidget {{ color: {fg}; }}
        QTabWidget::pane {{ border: 0; background: {bg}; }}
        QTabBar::tab {{
            background: {input_bg}; color: {fg}; padding: 8px 20px;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{ background: {bg}; border-bottom: 2px solid #0d6efd; font-weight: bold; }}
        QLineEdit {{
            background: {input_bg}; border: 1px solid {border}; border-radius: 15px;
            padding: 6px 15px; color: {fg};
        }}
        QTableWidget {{ background: {input_bg}; gridline-color: {border}; color: {fg}; }}
        QHeaderView::section {{ background: {bg}; padding: 5px; border: none; color: {fg}; }}
        """

# --- Custom Page Handler ---
class NaviWebPage(QWebEnginePage):
    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if url.scheme() == "navi":
            view = self.view()
            if view and hasattr(view, 'parent_window'):
                view.parent_window.handle_internal_pages(url.toString(), view)
            return False
        return super().acceptNavigationRequest(url, _type, isMainFrame)

# --- Internal HTML ---
class InternalPages:
    @staticmethod
    def css(dark_mode):
        bg = "#2b3035" if dark_mode else "#f8f9fa"
        card_bg = "#343a40" if dark_mode else "#ffffff"
        text = "#f8f9fa" if dark_mode else "#212529"
        return f"""
        body {{ font-family: sans-serif; background: {bg}; color: {text}; padding: 40px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ color: #0d6efd; }}
        .card {{ background: {card_bg}; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .btn {{ padding: 8px 15px; background: #0d6efd; color: white; border: none; border-radius: 5px; text-decoration: none; cursor: pointer; }}
        .btn-danger {{ background: #dc3545; }}
        input, select {{ padding: 10px; width: 100%; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc; }}
        .nav-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .nav-item {{ background: {card_bg}; padding: 20px; text-align: center; border-radius: 12px; display: block; color: {text}; text-decoration: none; }}
        .nav-item:hover {{ border: 1px solid #0d6efd; }}
        """

    @staticmethod
    def home(dark_mode):
        return f"""<html><head><style>{InternalPages.css(dark_mode)}</style></head><body>
        <div class="container" style="text-align: center; margin-top: 10vh;">
            <h1>Navi Browser</h1>
            <div class="nav-grid">
                <a href="navi://pw" class="nav-item"><b>My Sites</b><br>Builder</a>
                <a href="navi://cws" class="nav-item"><b>Extensions</b><br>Scripts</a>
                <a href="navi://history" class="nav-item"><b>History</b><br>Log</a>
                <a href="navi://proxy" class="nav-item"><b>Proxy</b><br>Config</a>
                <a href="navi://info" class="nav-item"><b>Info</b><br>About</a>
            </div>
        </div></body></html>"""

# --- Windows (Builder & Extension Editor) ---
class CodeEditorWindow(QWidget):
    def __init__(self, browser_main, mode="site", key_to_edit=None):
        super().__init__()
        self.browser_main = browser_main
        self.mode = mode # 'site' or 'extension'
        self.key_to_edit = key_to_edit
        self.setWindowTitle(f"Navi Editor - {mode.capitalize()}")
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Domain Name" if self.mode == "site" else "Extension Name")
        if self.key_to_edit: self.name_input.setReadOnly(True)
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)

        if self.mode == "site":
            self.title_input = QLineEdit()
            self.title_input.setPlaceholderText("Page Title")
            layout.addWidget(QLabel("Title:"))
            layout.addWidget(self.title_input)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("<html>...</html>" if self.mode == "site" else "alert('Hello');")
        layout.addWidget(QLabel("Code:"))
        layout.addWidget(self.content_input)

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("background: #2ECC71; color: white; padding: 10px; font-weight: bold;")
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
        elif self.mode == "extension":
            data = self.browser_main.data['extensions'].get(self.key_to_edit)
            if data:
                self.name_input.setText(self.key_to_edit)
                self.content_input.setText(data.get('code', ''))

    def save_data(self):
        name = self.name_input.text().strip()
        code = self.content_input.toPlainText()
        
        if not name: return

        if self.mode == "site":
            full_domain = f"{name.lower()}.pw-navi" if not name.endswith(".pw-navi") else name.lower()
            self.browser_main.data['sites'][full_domain] = {
                'domain': full_domain,
                'title': self.title_input.text(),
                'html_content': code
            }
            self.browser_main.add_new_tab(QUrl(f"local://{full_domain}/"))
        else:
            self.browser_main.data['extensions'][name] = {'code': code, 'active': True}
            self.browser_main.reload_current_tab()
            
        self.browser_main.save_to_disk()
        self.close()

# --- Browser Tab ---
class BrowserTab(QWebEngineView):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setPage(NaviWebPage(self))
        self.page().loadFinished.connect(self.on_load_finished)

    def on_load_finished(self, ok):
        if not ok: return
        # Inject Extensions
        for name, ext in self.parent_window.data['extensions'].items():
            if ext['active']: self.page().runJavaScript(ext['code'])
        
        # Log History (if not internal)
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
        self.resize(1200, 800)
        
        self.data = {
            'sites': {}, 'extensions': {}, 
            'proxy': {'type': 'Google', 'key': '', 'url': ''},
            'history': [], 'last_active': time.time(),
            'dark_mode': False
        }
        
        self.load_from_disk()
        self.check_dead_mans_switch() # Check logic on startup
        
        self.setup_ui()
        self.apply_theme()
        self.add_new_tab(QUrl("local://navi/"))

    def setup_ui(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        actions = [("←", self.go_back), ("→", self.go_forward), ("⟳", self.reload_current_tab), ("🏠", self.go_home)]
        for t, f in actions:
            btn = QPushButton(t)
            btn.setFixedSize(30,30)
            btn.clicked.connect(f)
            toolbar.addWidget(btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate)
        toolbar.addWidget(self.url_bar)

        add_btn = QPushButton("+")
        add_btn.setFixedSize(30,30)
        add_btn.clicked.connect(lambda: self.add_new_tab())
        toolbar.addWidget(add_btn)

        menu_btn = QPushButton("☰")
        menu_btn.setFixedSize(30,30)
        menu = QMenu()
        menu.addAction("Toggle Dark Mode", self.toggle_theme)
        menu_btn.setMenu(menu)
        toolbar.addWidget(menu_btn)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.setCentralWidget(self.tabs)

    # --- Dead Man's Switch & History Logic ---
    def check_dead_mans_switch(self):
        now = time.time()
        last = self.data.get('last_active', now)
        
        # If absent for more than 2 weeks
        if now - last > TWO_WEEKS_SECONDS:
            QMessageBox.warning(self, "Welcome Back", "It's been a while! Cleaning up...")
            self.data['history'] = get_wholesome_history()
        else:
            # Normal prune: remove items older than 2 weeks
            self.data['history'] = [h for h in self.data['history'] if now - h['time'] < TWO_WEEKS_SECONDS]
            
        self.data['last_active'] = now
        self.save_to_disk()

    def add_to_history(self, url, title):
        # Prevent duplicates at top
        if self.data['history'] and self.data['history'][0]['url'] == url:
            return
        self.data['history'].insert(0, {'url': url, 'title': title, 'time': time.time()})
        self.data['history'] = self.data['history'][:1000] # Limit to 1000 entries
        self.save_to_disk()

    # --- Tab Logic ---
    def add_new_tab(self, qurl=None, label="New Tab"):
        if qurl is None: qurl = QUrl("local://navi/")
        browser = BrowserTab(self)
        browser.setUrl(qurl)
        browser.urlChanged.connect(lambda q, b=browser: self.update_url_bar_for_tab(q, b))
        browser.titleChanged.connect(lambda t, b=browser: self.update_tab_title(t, b))
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        return browser

    def close_tab(self, i):
        if self.tabs.count() > 1: self.tabs.removeTab(i)

    def update_tab_title(self, title, browser):
        i = self.tabs.indexOf(browser)
        if i != -1: self.tabs.setTabText(i, title[:15])

    # --- Navigation ---
    def go_back(self): self.tabs.currentWidget().back()
    def go_forward(self): self.tabs.currentWidget().forward()
    def reload_current_tab(self): self.tabs.currentWidget().reload()
    def go_home(self): self.tabs.currentWidget().setUrl(QUrl("local://navi/"))
    
    def navigate(self):
        text = self.url_bar.text().strip()
        browser = self.tabs.currentWidget()
        
        if text.lower().startswith("navi://"):
            self.handle_internal_pages(text, browser)
        elif text.lower().endswith(".pw-navi"):
            data = self.data['sites'].get(text.lower())
            if data: browser.setHtml(data['html_content'], QUrl(f"local://{text}/"))
        else:
            url = QUrl(text)
            if "." not in text: url = QUrl(f"https://www.google.com/search?q={text}")
            elif "://" not in text: url = QUrl("https://" + text)
            browser.setUrl(url)

    def update_url_bar(self, i):
        if i >= 0: self.update_bar_text(self.tabs.widget(i).url().toString())

    def update_url_bar_for_tab(self, q, browser):
        if browser == self.tabs.currentWidget(): self.update_bar_text(q.toString())
        if q.scheme() == "navi": self.handle_internal_pages(q.toString(), browser)

    def update_bar_text(self, url):
        if url.startswith("local://navi/"): self.url_bar.setText(url.replace("local://navi/", "navi://").rstrip("/"))
        elif not url.startswith("local://"): self.url_bar.setText(url)

    # --- Internal Pages ---
    def handle_internal_pages(self, url, browser):
        cmd = url.lower().replace("navi://", "").strip("/")
        dm = self.data['dark_mode']
        
        if cmd == "" or cmd == "home":
            browser.setHtml(InternalPages.home(dm), QUrl("local://navi/"))
        elif cmd == "history":
            self.render_history(browser)
        elif cmd == "pw":
            self.render_site_manager(browser)
        elif cmd == "cws":
            self.render_extension_manager(browser)
        elif cmd == "proxy":
            self.render_proxy(browser)
        elif cmd == "pw/new":
            self.editor = CodeEditorWindow(self, "site")
            self.editor.show()
        elif cmd == "cws/new":
            self.editor = CodeEditorWindow(self, "extension")
            self.editor.show()
        elif cmd.startswith("pw/edit/"):
            # Fixed parsing logic for domains
            domain = QUrl.fromPercentEncoding(url.split("pw/edit/")[1].encode())
            self.editor = CodeEditorWindow(self, "site", domain)
            self.editor.show()
        elif cmd.startswith("pw/delete/"):
            domain = QUrl.fromPercentEncoding(url.split("pw/delete/")[1].encode())
            if domain in self.data['sites']: 
                del self.data['sites'][domain]
                self.save_to_disk()
            self.render_site_manager(browser)
        elif cmd.startswith("cws/edit/"):
            name = QUrl.fromPercentEncoding(url.split("cws/edit/")[1].encode())
            self.editor = CodeEditorWindow(self, "extension", name)
            self.editor.show()
        elif cmd.startswith("cws/delete/"):
            name = QUrl.fromPercentEncoding(url.split("cws/delete/")[1].encode())
            if name in self.data['extensions']:
                del self.data['extensions'][name]
                self.save_to_disk()
            self.render_extension_manager(browser)
        elif cmd.startswith("cws/toggle/"):
            name = QUrl.fromPercentEncoding(url.split("cws/toggle/")[1].encode())
            if name in self.data['extensions']:
                self.data['extensions'][name]['active'] = not self.data['extensions'][name]['active']
                self.save_to_disk()
            self.render_extension_manager(browser)

    def render_history(self, browser):
        dm = self.data['dark_mode']
        rows = ""
        for h in self.data['history']:
            date_str = QDateTime.fromSecsSinceEpoch(int(h['time'])).toString("MMM d, hh:mm AP")
            rows += f"""<div class="card"><a href="{h['url']}"><b>{h.get('title', 'Page')}</b></a><br><small>{h['url']}</small><div style="text-align:right; font-size:0.8em; color:#888;">{date_str}</div></div>"""
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>History</h1><button class="btn btn-danger" onclick="window.location='navi://history/clear'">Clear History</button><br><br>{rows}</div></body></html>""", QUrl("local://navi/history"))

    def render_site_manager(self, browser):
        dm = self.data['dark_mode']
        rows = ""
        for d, v in self.data['sites'].items():
            rows += f"""<div class="card" style="display:flex; justify-content:space-between;"><div><b>{v['title']}</b><br>{d}</div><div><a href="{d}" class="btn">View</a> <a href="navi://pw/edit/{d}" class="btn" style="background:orange">Edit</a> <a href="navi://pw/delete/{d}" class="btn btn-danger">Delete</a></div></div>"""
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>My Sites</h1><a href="navi://pw/new" class="btn">+ New Site</a><br><br>{rows}</div></body></html>""", QUrl("local://navi/pw"))

    def render_extension_manager(self, browser):
        dm = self.data['dark_mode']
        rows = ""
        for k, v in self.data['extensions'].items():
            color = "green" if v['active'] else "red"
            rows += f"""<div class="card" style="border-left:5px solid {color}"><h3>{k}</h3><button class="btn" onclick="window.location='navi://cws/toggle/{k}'">Toggle</button> <button class="btn" onclick="window.location='navi://cws/edit/{k}'">Edit</button> <button class="btn btn-danger" onclick="window.location='navi://cws/delete/{k}'">Delete</button></div>"""
        browser.setHtml(f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>Extensions</h1><a href="navi://cws/new" class="btn">+ New Extension</a><br><br>{rows}</div></body></html>""", QUrl("local://navi/cws"))

    def render_proxy(self, browser):
        dm = self.data['dark_mode']
        p = self.data['proxy']
        html = f"""<html><head><style>{InternalPages.css(dm)}</style></head><body><div class="container"><h1>Proxy</h1><div class="card"><label>Type</label><select id="t"><option>Google</option><option>Cloudflare</option></select><label>Key</label><input id="k" value="{p['key']}"><label>URL</label><input id="u"><button class="btn" onclick="run()">Go</button></div></div>
        <script>function run() {{ window.location='navi://proxy/run/'+document.getElementById('t').value+'/'+encodeURIComponent(document.getElementById('k').value)+'/'+encodeURIComponent(document.getElementById('u').value); }}</script></body></html>"""
        browser.setHtml(html, QUrl("local://navi/proxy"))

    # --- Persistence ---
    def save_to_disk(self):
        try:
            with open(DATA_FILE, 'w') as f: json.dump(self.data, f)
        except: pass

    def load_from_disk(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f: self.data.update(json.load(f))
            except: pass

    def toggle_theme(self):
        self.data['dark_mode'] = not self.data['dark_mode']
        self.save_to_disk()
        self.setStyleSheet(ModernStyles.get(self.data['dark_mode']))
        self.reload_current_tab()
    
    def apply_theme(self):
        self.setStyleSheet(ModernStyles.get(self.data['dark_mode']))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Navi Browser")
    window = NaviBrowser()
    window.show()
    sys.exit(app.exec_())

