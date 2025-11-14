import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QMessageBox # Used for proper message and confirmation boxes
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

# --- Personal Website Builder Window ---
class WebsiteBuilderWindow(QWidget):
    def __init__(self, browser_main, domain_to_edit=None):
        super().__init__()
        self.browser_main = browser_main
        self.domain_to_edit = domain_to_edit
        self.setWindowTitle(f"Personal Website Builder - {domain_to_edit or 'New Site'}")
        self.setGeometry(200, 200, 800, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Domain Input
        domain_layout = QHBoxLayout()
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("your-site-name")
        
        # Lock domain input when editing existing sites
        if self.domain_to_edit:
            self.domain_input.setReadOnly(True)
            domain_layout.addWidget(QLabel("Domain (Locked):"))
        else:
            domain_layout.addWidget(QLabel("Domain:"))
            
        domain_layout.addWidget(self.domain_input)
        domain_layout.addWidget(QLabel(".pw-Navi (Required Suffix)"))
        layout.addLayout(domain_layout)

        # Title Input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("My Awesome Personal Page")
        layout.addWidget(QLabel("Page Title (for management):"))
        layout.addWidget(self.title_input)

        # Content Input (FULL HTML/CSS/JS Area)
        layout.addWidget(QLabel("Page Content (Full HTML Document, including <style>/<script>):"))
        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText(
            "Enter your FULL HTML document here. Start with <!DOCTYPE html> and include <head> and <body> tags for CSS/JS to work."
        )
        layout.addWidget(self.content_input)

        # Save Button
        save_btn = QPushButton("Save & Preview Site")
        save_btn.setStyleSheet("background-color: #2ECC71; color: white; padding: 10px; font-weight: bold; border-radius: 5px;")
        save_btn.clicked.connect(self.save_data)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def load_data(self):
        """Loads existing site data into the form if editing."""
        if self.domain_to_edit:
            site_data = self.browser_main.personal_websites.get(self.domain_to_edit.lower())
            if site_data:
                # Strip the suffix for display in the input box
                self.domain_input.setText(self.domain_to_edit.replace(".pw-navi", ""))
                self.title_input.setText(site_data.get('title', ''))
                self.content_input.setText(site_data.get('html_content', ''))

    def show_error(self, message):
        """Custom message box for errors."""
        error_box = QMessageBox()
        error_box.setWindowTitle("Error")
        error_box.setText(message)
        error_box.setIcon(QMessageBox.Critical)
        error_box.exec_()
        
    def save_data(self):
        """Saves data to the main browser instance and triggers a preview."""
        domain_prefix = self.domain_input.text().strip().lower()
        
        if not domain_prefix:
            self.show_error("Domain prefix cannot be empty.")
            return

        full_domain = f"{domain_prefix}.pw-navi"
        html_content = self.content_input.toPlainText().strip()
        
        # Check for duplication only if creating a NEW site
        if not self.domain_to_edit and full_domain in self.browser_main.personal_websites:
            self.show_error(f"Domain '{full_domain}' already exists. Please choose a different name or edit the existing site.")
            return
        
        # Basic check to encourage full HTML structure
        if not html_content.startswith('<!DOCTYPE html>'):
             if QMessageBox.question(self, "Warning",
                                     "It looks like you didn't start with <!DOCTYPE html>. Your site might not render CSS/JS correctly. Continue?",
                                     QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
                 return

        self.browser_main.personal_websites[full_domain] = {
            'domain': full_domain,
            'title': self.title_input.text().strip() or "Untitled Navi Page",
            'html_content': html_content
        }
        
        print(f"Personal Website saved/updated: {full_domain}")

        # Automatically navigate to the new custom domain after saving
        self.browser_main.url_bar.setText(full_domain)
        self.browser_main.navigate_to_url()
        self.close()

# --- Main Browser Application ---
class SimpleBrowser(QMainWindow):
    personal_websites = {
        'welcome.pw-navi': {
            'title': 'Welcome to your Navi Site!',
            'html_content': '''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to your Navi Site!</title>
                <style>
                    body { font-family: 'Inter', sans-serif; background-color: #e6f3ff; color: #333; padding: 20px; text-align: center; }
                    .container { max-width: 800px; margin: 50px auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.2); }
                    h1 { color: #1e90ff; margin-bottom: 20px; }
                    button { padding: 12px 25px; background-color: #ff6347; color: white; border: none; border-radius: 6px; cursor: pointer; transition: background-color 0.3s; font-size: 1.1em; }
                    button:hover { background-color: #e5533a; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✨ Navi Browser - Hello World! ✨</h1>
                    <p>This is a custom, full-HTML site. Try editing the source!</p>
                    <p>Visit <code>Navi://pw</code> to see your list of sites.</p>
                    <button onclick="document.getElementById('msg').textContent='JS executed: Welcome to the future!';" >Run JavaScript</button>
                    <p id="msg" style="margin-top: 20px; color: #007bff; font-weight: bold;"></p>
                </div>
            </body>
            </html>
            '''
        }
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navi Browser")
        self.setGeometry(100, 100, 1200, 800)

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.setCentralWidget(self.browser)

        # --- Navbar Setup ---
        navbar = QToolBar("Navigation")
        navbar.setMovable(False)
        self.addToolBar(navbar)

        # Navigation Buttons
        back_btn = QAction("← Back", self); back_btn.triggered.connect(self.browser.back); navbar.addAction(back_btn)
        forward_btn = QAction("→ Forward", self); forward_btn.triggered.connect(self.browser.forward); navbar.addAction(forward_btn)
        reload_btn = QAction("⟳ Reload", self); reload_btn.triggered.connect(self.browser.reload); navbar.addAction(reload_btn)
        stop_btn = QAction("🛑 Stop", self); stop_btn.triggered.connect(self.browser.stop); navbar.addAction(stop_btn)
        home_btn = QAction("🏠 Home", self); home_btn.triggered.connect(self.navigate_home); navbar.addAction(home_btn)
        
        # Builder/Manager Button
        builder_btn = QAction("🌐 Builder", self)
        # Clicking the Builder button now navigates to the manager page
        builder_btn.triggered.connect(lambda: self.navigate_to_url_bar_text("Navi://pw"))
        navbar.addAction(builder_btn)

        # Web Store Button
        cws_btn = QAction("🛒 Store", self)
        cws_btn.triggered.connect(lambda: self.navigate_to_url_bar_text("Navi://cws"))
        navbar.addAction(cws_btn)

        # URL/Search Bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # --- Signal Connections ---
        self.browser.urlChanged.connect(self.update_url)
        self.browser.titleChanged.connect(self.setWindowTitle)
        
        self.builder_window = None # Keep a reference to the builder window

    def navigate_to_url_bar_text(self, text):
        """Helper to set text and navigate programmatically."""
        self.url_bar.setText(text)
        self.navigate_to_url(is_internal_click=True) # Treat this as an internal action

    def show_message(self, title, message, icon=QMessageBox.Information):
        """Custom message box for feedback."""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.exec_()

    def show_website_builder(self, domain_to_edit=None):
        """Opens the personal website builder window."""
        # Clean up and show new window
        if self.builder_window:
            self.builder_window.close()
            self.builder_window = None
            
        self.builder_window = WebsiteBuilderWindow(self, domain_to_edit)
        self.builder_window.show()
        self.builder_window.activateWindow()

    # --- Internal Page Handlers ---

    def load_personal_websites_manager(self):
        """Generates and loads the Navi://pw management page."""
        sites_list = ""
        for domain, data in self.personal_websites.items():
            # Use Navi:// protocol links for delete and edit actions
            delete_link = f'Navi://pw/delete/{domain}'
            edit_link = f'Navi://pw/edit/{domain}'
            
            sites_list += f"""
                <li style="margin-bottom: 15px; padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex-grow: 1;">
                        <a href="{domain}" style="font-weight: bold; color: #1e90ff; text-decoration: none;">{data['title']}</a> 
                        <span style="color: #666; font-size: 0.9em; margin-left: 10px;">({domain})</span>
                    </div>
                    <div>
                        <a href="{edit_link}" style="background-color: #FFA500; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none; margin-right: 8px;">Edit</a>
                        <a href="{delete_link}" style="background-color: #DC143C; color: white; padding: 5px 10px; border-radius: 4px; text-decoration: none;">Delete</a>
                    </div>
                </li>
            """
        
        manager_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Personal Website Manager - Navi://pw</title>
            <style>
                body {{ font-family: 'Inter', sans-serif; background-color: #f7f7f7; color: #333; padding: 30px; }}
                .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 6px 15px rgba(0,0,0,0.1); }}
                h1 {{ color: #007bff; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
                ul {{ list-style: none; padding: 0; }}
                .add-btn {{ background-color: #2ECC71; color: white; padding: 10px 15px; border-radius: 5px; text-decoration: none; display: inline-block; margin-top: 15px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 Personal Website Manager (`Navi://pw`)</h1>
                <p>Manage all your local, custom-built `.pw-Navi` sites here. Click a domain to view it, or click **Edit/Delete** to manage.</p>
                <a href="Navi://pw/new" class="add-btn">➕ Create New Site</a>
                <h2>Your Sites ({len(self.personal_websites)})</h2>
                <ul>{sites_list}</ul>
            </div>
        </body>
        </html>
        """
        # We use QUrl("about:blank") as a base URL to ensure internal links are not misresolved
        self.browser.setHtml(manager_html, QUrl("about:blank")) 
        self.setWindowTitle("Personal Website Manager")

    def delete_personal_website(self, domain):
        """Handles the deletion of a personal website with confirmation."""
        domain = domain.lower()
        
        if domain not in self.personal_websites:
            self.show_message("Error", f"Could not find website '{domain}' to delete.", QMessageBox.Warning)
            return

        # Use QMessageBox for confirmation (instead of alert/confirm)
        reply = QMessageBox.question(self, 'Confirm Deletion', 
                                     f"Are you sure you want to permanently delete '{domain}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            del self.personal_websites[domain]
            self.show_message("Site Deleted", f"The website '{domain}' has been successfully deleted.", QMessageBox.Information)
        
        # Navigate back to the management page to refresh the list
        self.load_personal_websites_manager()

    def navigate_home(self):
        """Navigates to the default home page."""
        self.browser.setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self, is_internal_click=False):
        """
        Navigates to the entered URL, performs a search, or loads the custom site/internal page.
        """
        url = self.url_bar.text().strip()
        
        # --- Internal Protocol Handling ---
        if url.lower().startswith("navi://"):
            command = url[7:].lower()
            
            if command == "pw" or command == "pw/":
                self.load_personal_websites_manager()
                return
            
            if command == "pw/new":
                self.show_website_builder(domain_to_edit=None) # Create new site
                return
            
            # Handle Edit requests: Navi://pw/edit/domain.pw-navi
            if command.startswith("pw/edit/"):
                domain_to_edit = command[8:]
                self.show_website_builder(domain_to_edit) # Edit existing site
                return
            
            # Handle deletion requests: Navi://pw/delete/domain.pw-navi
            if command.startswith("pw/delete/"):
                domain_to_delete = command[10:]
                self.delete_personal_website(domain_to_delete)
                return

            # Handle Chrome Web Store request
            if command == "cws" or command == "cws/":
                # Navigate to the actual web store link as requested
                self.browser.setUrl(QUrl("https://chrome.google.com/webstore"))
                return

        # --- Custom Domain Check ---
        if url.lower().endswith(".pw-navi"):
            site_data = self.personal_websites.get(url.lower())
            if site_data:
                # Load custom HTML directly into the browser
                self.browser.setHtml(site_data['html_content'], QUrl(f"local://{url}/")) 
                self.setWindowTitle(site_data.get('title', 'Navi Site'))
                return

        # Regular navigation/search logic
        if url.startswith(("http://", "https://")):
            self.browser.setUrl(QUrl(url))
        elif "." in url:
            self.browser.setUrl(QUrl("http://" + url))
        else:
            search_query = url.replace(" ", "+")
            search_url = f"https://www.google.com/search?q={search_query}"
            self.browser.setUrl(QUrl(search_url))

    def update_url(self, q):
        """
        Updates the text in the address bar when the browser navigates. 
        Crucially, it intercepts Navi:// links (from clicks) and triggers navigation.
        """
        url_str = q.toString()

        # Check if the browser is navigating to a custom internal protocol URL
        is_navi_command = url_str.lower().startswith("navi://")

        if is_navi_command:
            # If it's a Navi:// command (likely from an internal link click),
            # update the URL bar and immediately execute the command logic.
            self.url_bar.setText(url_str)
            self.url_bar.setCursorPosition(0)
            self.navigate_to_url(is_internal_click=True)
            # The browser tried to navigate to navi://, we handled it, so we stop further processing
            return

        # Update URL bar for external web pages and the internal "local://" pages
        if not url_str.startswith("local://"):
            self.url_bar.setText(url_str)
            self.url_bar.setCursorPosition(0)


if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    QApplication.setApplicationName("Navi Browser")
    window = SimpleBrowser()
    window.show()
    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass

