"""
NoScript Browser - Desktop Application Window
Implements the main desktop UI, multi-tab navigation, address bar, dark mode, font sizing,
bookmarks, history, and status bar metrics.
"""

import os
import sys
import time
import urllib.request
import urllib.parse
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction, QKeySequence, QColor
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QToolBar,
    QLineEdit,
    QPushButton,
    QStatusBar,
    QLabel,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFileDialog,
    QMenu,
    QCompleter,
    QApplication,
    QWidget,
    QFormLayout,
    QComboBox,
    QGroupBox,
)

from src.chromium_engine import configure_chromium_profile, NoScriptWebView
from src.content_filter import strip_html_css_js
from src.bookmarks_history import BookmarksHistoryManager
from src.download_manager import DownloadManager


class PageFetchThread(QThread):
    finished_signal = pyqtSignal(dict)
    error_signal = pyqtSignal(str, str)

    def __init__(self, url_str: str, parent=None):
        super().__init__(parent)
        self.url_str = url_str

    def run(self):
        try:
            url_str = self.url_str
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }

            req = urllib.request.Request(url_str, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_bytes = response.read()
                encoding = response.headers.get_content_charset() or "utf-8"
                raw_html = raw_bytes.decode(encoding, errors="replace")
                final_url = response.geturl()

            filtered = strip_html_css_js(raw_html, base_url=final_url)

            # Auto-follow Google session verification link if present
            if "google.com" in final_url and "trouble accessing" in filtered.get("clean_text", "").lower():
                for link in filtered.get("links", []):
                    if "click here" in link.get("text", "").lower() or "google.com/search" in link.get("url", ""):
                        retry_url = link["url"]
                        req2 = urllib.request.Request(
                            retry_url,
                            headers={
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept-Language": "en-US,en;q=0.9",
                            },
                        )
                        with urllib.request.urlopen(req2, timeout=10) as resp2:
                            raw_html2 = resp2.read().decode(resp2.headers.get_content_charset() or "utf-8", errors="replace")
                            filtered = strip_html_css_js(raw_html2, base_url=resp2.geturl())
                            final_url = resp2.geturl()
                        break

            filtered["final_url"] = final_url
            self.finished_signal.emit(filtered)
        except Exception as e:
            self.error_signal.emit(self.url_str, str(e))


class HistoryDialog(QDialog):
    """
    Dialog displaying user browsing history with search and clear functionality.
    """

    def __init__(self, db_manager: BookmarksHistoryManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Browsing History - ANYTHING BROWSER")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self.clear_history)
        btn_layout.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        self.load_history()

    def load_history(self):
        self.list_widget.clear()
        entries = self.db.get_history(limit=100)
        for item in entries:
            list_item = QListWidgetItem(f"{item['title']} - {item['url']}")
            list_item.setData(Qt.ItemDataRole.UserRole, item['url'])
            self.list_widget.addItem(list_item)

    def on_item_double_clicked(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url and self.parent():
            self.parent().open_url_in_current_tab(url)
            self.accept()

    def clear_history(self):
        self.db.clear_history()
        self.load_history()


class BookmarksDialog(QDialog):
    """
    Dialog displaying saved bookmarks with search and delete options.
    """

    def __init__(self, db_manager: BookmarksHistoryManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle("Bookmarks - ANYTHING BROWSER")
        self.resize(600, 400)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        delete_btn = QPushButton("Remove Selected")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        self.load_bookmarks()

    def load_bookmarks(self):
        self.list_widget.clear()
        entries = self.db.get_bookmarks()
        for item in entries:
            list_item = QListWidgetItem(f"{item['title']} ({item['url']})")
            list_item.setData(Qt.ItemDataRole.UserRole, item['url'])
            self.list_widget.addItem(list_item)

    def on_item_double_clicked(self, item):
        url = item.data(Qt.ItemDataRole.UserRole)
        if url and self.parent():
            self.parent().open_url_in_current_tab(url)
            self.accept()

    def delete_selected(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            url = current_item.data(Qt.ItemDataRole.UserRole)
            self.db.remove_bookmark(url)
            self.load_bookmarks()


class ExtensionManagerDialog(QDialog):
    """
    Dialog for managing built-in and custom Chrome extensions.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Extension Manager - ANYTHING BROWSER")
        self.resize(680, 480)

        layout = QVBoxLayout(self)

        title_label = QLabel("🧩 Installed & Active Browser Extensions")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        ublock_status = "Active - Loaded from C:\\Users\\masna\\Downloads\\uBlock0_1.75.1b11.chromium" if os.path.exists(r"C:\Users\masna\Downloads\uBlock0_1.75.1b11.chromium") else "Not Loaded"

        exts = [
            ("🛡️ uBlock Origin v1.75.1 (Official Chromium Extension)", f"{ublock_status}"),
            ("🛑 Network Ad & Tracker Interceptor", "Active - Blocks DoubleClick, Google Ads, and tracking scripts"),
            ("🌙 Force Dark Mode Engine", "Active - Native Chromium high-contrast dark theme generator"),
            ("🎤 Voice Search & Microphone Access", "Active - Grants audio capture permissions for Google/YouTube voice search"),
            ("📄 Local PDF Viewer & File Engine", "Active - Renders PDF documents and local files natively"),
        ]

        for name, desc in exts:
            item = QListWidgetItem(f"{name}\n    {desc}")
            self.list_widget.addItem(item)

        btn_layout = QHBoxLayout()

        load_folder_btn = QPushButton("📁 Load Unpacked Extension Folder")
        load_folder_btn.clicked.connect(self.load_unpacked_extension)
        btn_layout.addWidget(load_folder_btn)

        web_store_btn = QPushButton("🌐 Open Chrome Web Store")
        web_store_btn.clicked.connect(self.open_web_store)
        btn_layout.addWidget(web_store_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def load_unpacked_extension(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Unpacked Extension Folder")
        if folder:
            if self.parent() and hasattr(self.parent(), "profile"):
                try:
                    self.parent().profile.extensionManager().loadExtension(folder)
                    QMessageBox.information(
                        self,
                        "Extension Loaded",
                        f"Successfully loaded extension from:\n{folder}",
                    )
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Extension Error",
                        f"Failed to load extension:\n{str(e)}",
                    )

    def open_web_store(self):
        if self.parent():
            self.parent().add_new_tab("https://chromewebstore.google.com")
            self.accept()


class DownloadHistoryDialog(QDialog):
    """
    Dialog for displaying download history and managing downloaded files.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Download Manager & History - ANYTHING BROWSER")
        self.resize(750, 480)

        layout = QVBoxLayout(self)

        title_label = QLabel("📥 Download History")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()

        open_file_btn = QPushButton("▶️ Open File")
        open_file_btn.clicked.connect(self.open_selected_file)
        btn_layout.addWidget(open_file_btn)

        open_folder_btn = QPushButton("📁 Open Containing Folder")
        open_folder_btn.clicked.connect(self.open_selected_folder)
        btn_layout.addWidget(open_folder_btn)

        delete_btn = QPushButton("🗑️ Remove Entry")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(delete_btn)

        clear_btn = QPushButton("🧹 Clear All History")
        clear_btn.clicked.connect(self.clear_all)
        btn_layout.addWidget(clear_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        self.load_downloads()

    def load_downloads(self):
        self.list_widget.clear()
        downloads = self.db.get_downloads()
        for item in downloads:
            size_mb = f"{item['file_size'] / (1024 * 1024):.2f} MB" if item['file_size'] > 0 else "Unknown Size"
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['created_at']))
            list_item = QListWidgetItem(f"📄 {item['filename']} ({size_mb})\n    Path: {item['save_path']} | Date: {time_str}")
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(list_item)

    def open_selected_file(self):
        current = self.list_widget.currentItem()
        if current:
            item = current.data(Qt.ItemDataRole.UserRole)
            save_path = item.get("save_path")
            if save_path and os.path.exists(save_path):
                try:
                    os.startfile(save_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to open file:\n{str(e)}")
            else:
                QMessageBox.warning(self, "File Not Found", f"The file no longer exists at:\n{save_path}")

    def open_selected_folder(self):
        current = self.list_widget.currentItem()
        if current:
            item = current.data(Qt.ItemDataRole.UserRole)
            save_path = item.get("save_path")
            if save_path and os.path.exists(save_path):
                import subprocess
                subprocess.Popen(["explorer", "/select,", os.path.normpath(save_path)])
            elif save_path:
                folder = os.path.dirname(save_path)
                if os.path.exists(folder):
                    os.startfile(folder)
                else:
                    QMessageBox.warning(self, "Folder Not Found", f"Folder does not exist:\n{folder}")

    def delete_selected(self):
        current = self.list_widget.currentItem()
        if current:
            item = current.data(Qt.ItemDataRole.UserRole)
            self.db.remove_download(item["id"])
            self.load_downloads()

    def clear_all(self):
        self.db.clear_downloads()
        self.load_downloads()


class LoginRegisterDialog(QDialog):
    """
    Dialog for user login and account creation.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("User Profile Sign In & Account Creation - ANYTHING BROWSER")
        self.setFixedSize(480, 420)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("👤 ANYTHING BROWSER Profile")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #0078d4;")
        main_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.tabs = QTabWidget()

        # Tab 1: Sign In
        login_widget = QWidget()
        login_layout = QFormLayout(login_widget)
        login_layout.setSpacing(12)

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter username")
        login_layout.addRow("Username:", self.login_username)

        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password.setPlaceholderText("Enter password")
        login_layout.addRow("Password:", self.login_password)

        login_btn = QPushButton("🔑 Sign In")
        login_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #0078d4; color: white;")
        login_btn.clicked.connect(self.handle_login)
        login_layout.addRow("", login_btn)

        self.tabs.addTab(login_widget, "🔑 Sign In")

        # Tab 2: Create Account
        reg_widget = QWidget()
        reg_layout = QFormLayout(reg_widget)
        reg_layout.setSpacing(12)

        self.reg_fullname = QLineEdit()
        self.reg_fullname.setPlaceholderText("Full name (e.g. Varun)")
        reg_layout.addRow("Full Name:", self.reg_fullname)

        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Choose username")
        reg_layout.addRow("Username:", self.reg_username)

        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password.setPlaceholderText("Choose password")
        reg_layout.addRow("Password:", self.reg_password)

        self.reg_confirm = QLineEdit()
        self.reg_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_confirm.setPlaceholderText("Confirm password")
        reg_layout.addRow("Confirm Password:", self.reg_confirm)

        reg_btn = QPushButton("📝 Create Account")
        reg_btn.setStyleSheet("padding: 8px; font-weight: bold; background-color: #107c41; color: white;")
        reg_btn.clicked.connect(self.handle_register)
        reg_layout.addRow("", reg_btn)

        self.tabs.addTab(reg_widget, "📝 Create Account")

        main_layout.addWidget(self.tabs)

    def handle_login(self):
        username = self.login_username.text().strip()
        password = self.login_password.text()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password.")
            return

        user, msg = self.db.authenticate_user(username, password)
        if user:
            QMessageBox.information(self, "Welcome", f"Signed in successfully as {user['full_name']} (@{user['username']})!")
            self.accept()
        else:
            QMessageBox.warning(self, "Sign In Failed", msg)

    def handle_register(self):
        fullname = self.reg_fullname.text().strip()
        username = self.reg_username.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please fill in all required fields.")
            return

        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match. Please re-enter.")
            return

        ok, msg = self.db.create_user(username, password, fullname)
        if ok:
            QMessageBox.information(self, "Account Created", f"Account created for {username}! You are now signed in.")
            self.accept()
        else:
            QMessageBox.warning(self, "Registration Failed", msg)


class SettingsDialog(QDialog):
    """
    Chrome-style Browser Settings & Management Dialog.
    """

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Settings & Management - ANYTHING BROWSER")
        self.resize(650, 480)

        main_layout = QVBoxLayout(self)

        title_label = QLabel("⚙️ ANYTHING BROWSER Settings")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #0078d4;")
        main_layout.addWidget(title_label)

        self.tabs = QTabWidget()

        # Tab 1: Profile & Account
        profile_widget = QWidget()
        p_layout = QVBoxLayout(profile_widget)

        user = self.db.get_active_user()
        self.profile_info_label = QLabel()
        if user:
            self.profile_info_label.setText(f"👤 Signed in as: <b>{user['full_name']}</b> (@{user['username']})")
        else:
            self.profile_info_label.setText("👤 Signed in as: <b>Guest User</b>")
        self.profile_info_label.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        p_layout.addWidget(self.profile_info_label)

        p_btn_layout = QHBoxLayout()
        sign_in_btn = QPushButton("🔑 Sign In / Create Account")
        sign_in_btn.clicked.connect(self.open_login_dialog)
        p_btn_layout.addWidget(sign_in_btn)

        sign_out_btn = QPushButton("🚪 Sign Out")
        sign_out_btn.clicked.connect(self.handle_sign_out)
        p_btn_layout.addWidget(sign_out_btn)

        p_layout.addLayout(p_btn_layout)
        p_layout.addStretch()
        self.tabs.addTab(profile_widget, "👤 Profile")

        # Tab 2: Appearance & Search
        app_widget = QWidget()
        a_layout = QFormLayout(app_widget)

        self.homepage_input = QLineEdit()
        self.homepage_input.setText(self.db.get_setting("homepage", "https://www.google.com"))
        a_layout.addRow("Custom Homepage URL:", self.homepage_input)

        self.search_combo = QComboBox()
        self.search_combo.addItems(["Google", "Bing", "DuckDuckGo", "Yahoo", "Ecosia"])
        curr_search = self.db.get_setting("search_engine", "Google")
        idx = self.search_combo.findText(curr_search)
        if idx >= 0:
            self.search_combo.setCurrentIndex(idx)
        a_layout.addRow("Default Search Engine:", self.search_combo)

        save_app_btn = QPushButton("💾 Save Preferences")
        save_app_btn.clicked.connect(self.save_preferences)
        a_layout.addRow("", save_app_btn)

        self.tabs.addTab(app_widget, "🎨 Appearance & Search")

        # Tab 3: Downloads Location
        dl_widget = QWidget()
        d_layout = QFormLayout(dl_widget)

        self.dl_dir_input = QLineEdit()
        default_dl = os.path.expanduser("~/Downloads")
        self.dl_dir_input.setText(self.db.get_setting("download_dir", default_dl))

        dl_browse_layout = QHBoxLayout()
        dl_browse_layout.addWidget(self.dl_dir_input)

        browse_btn = QPushButton("📁 Browse...")
        browse_btn.clicked.connect(self.browse_download_dir)
        dl_browse_layout.addWidget(browse_btn)

        d_layout.addRow("Download Folder Location:", dl_browse_layout)

        save_dl_btn = QPushButton("💾 Save Download Path")
        save_dl_btn.clicked.connect(self.save_download_path)
        d_layout.addRow("", save_dl_btn)

        self.tabs.addTab(dl_widget, "📥 Downloads")

        # Tab 4: Privacy & Data
        priv_widget = QWidget()
        priv_layout = QVBoxLayout(priv_widget)

        clear_hist_btn = QPushButton("📜 Clear Browsing History")
        clear_hist_btn.clicked.connect(self.clear_history_data)
        priv_layout.addWidget(clear_hist_btn)

        clear_bm_btn = QPushButton("🔖 Clear Bookmarks")
        clear_bm_btn.clicked.connect(self.clear_bookmarks_data)
        priv_layout.addWidget(clear_bm_btn)

        clear_dl_btn = QPushButton("📥 Clear Download History")
        clear_dl_btn.clicked.connect(self.clear_downloads_data)
        priv_layout.addWidget(clear_dl_btn)

        priv_layout.addStretch()
        self.tabs.addTab(priv_widget, "🛡️ Privacy & Data")

        main_layout.addWidget(self.tabs)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        main_layout.addWidget(close_btn)

    def open_login_dialog(self):
        dlg = LoginRegisterDialog(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            user = self.db.get_active_user()
            if user:
                self.profile_info_label.setText(f"👤 Signed in as: <b>{user['full_name']}</b> (@{user['username']})")
                if self.parent() and hasattr(self.parent(), "update_profile_button_label"):
                    self.parent().update_profile_button_label()

    def handle_sign_out(self):
        self.db.logout_active_user()
        self.profile_info_label.setText("👤 Signed in as: <b>Guest User</b>")
        if self.parent() and hasattr(self.parent(), "update_profile_button_label"):
            self.parent().update_profile_button_label()
        QMessageBox.information(self, "Signed Out", "You have been signed out.")

    def save_preferences(self):
        homepage = self.homepage_input.text().strip()
        search_engine = self.search_combo.currentText()
        if homepage:
            self.db.set_setting("homepage", homepage)
            if self.parent():
                self.parent().DEFAULT_HOME = homepage
        self.db.set_setting("search_engine", search_engine)
        QMessageBox.information(self, "Saved", "Preferences saved successfully!")

    def browse_download_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if folder:
            self.dl_dir_input.setText(folder)

    def save_download_path(self):
        path = self.dl_dir_input.text().strip()
        if path and os.path.exists(path):
            self.db.set_setting("download_dir", path)
            QMessageBox.information(self, "Saved", "Download path saved successfully!")

    def clear_history_data(self):
        self.db.clear_history()
        QMessageBox.information(self, "Cleared", "Browsing history cleared!")

    def clear_bookmarks_data(self):
        with self.db._get_connection() as conn:
            conn.cursor().execute("DELETE FROM bookmarks")
            conn.commit()
        QMessageBox.information(self, "Cleared", "Bookmarks cleared!")

    def clear_downloads_data(self):
        self.db.clear_downloads()
        QMessageBox.information(self, "Cleared", "Download history cleared!")


class BrowserMainWindow(QMainWindow):
    """
    Main Desktop Window for ANYTHING BROWSER.
    """

    DEFAULT_HOME = "https://www.google.com"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ANYTHING BROWSER")
        self.resize(1200, 800)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Database & Profile Setup
        self.db = BookmarksHistoryManager()
        self.profile = configure_chromium_profile()
        self.download_manager = DownloadManager(self)
        self.profile.downloadRequested.connect(
            self.download_manager.handle_download_requested
        )

        self.is_dark_mode = False
        self.zoom_factor = 1.0

        self.init_ui()

    def init_ui(self):
        # Navigation Toolbar
        self.toolbar = QToolBar("Navigation", self)
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        # Action Buttons
        self.back_btn = QPushButton("←")
        self.back_btn.setToolTip("Back")
        self.back_btn.setFixedWidth(32)
        self.back_btn.clicked.connect(self.navigate_back)
        self.toolbar.addWidget(self.back_btn)

        self.forward_btn = QPushButton("→")
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.setFixedWidth(32)
        self.forward_btn.clicked.connect(self.navigate_forward)
        self.toolbar.addWidget(self.forward_btn)

        self.reload_btn = QPushButton("↻")
        self.reload_btn.setToolTip("Reload")
        self.reload_btn.setFixedWidth(32)
        self.reload_btn.clicked.connect(self.reload_tab)
        self.toolbar.addWidget(self.reload_btn)

        self.home_btn = QPushButton("⌂")
        self.home_btn.setToolTip("Home")
        self.home_btn.setFixedWidth(32)
        self.home_btn.clicked.connect(self.go_home)
        self.toolbar.addWidget(self.home_btn)

        # Address Bar
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search terms...")
        self.url_bar.returnPressed.connect(self.on_url_submitted)
        self.toolbar.addWidget(self.url_bar)

        self.bookmark_btn = QPushButton("☆")
        self.bookmark_btn.setToolTip("Bookmark Page")
        self.bookmark_btn.setFixedWidth(32)
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        self.toolbar.addWidget(self.bookmark_btn)

        # View Options
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setToolTip("Toggle Dark/Light Mode")
        self.theme_btn.setFixedWidth(32)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.toolbar.addWidget(self.theme_btn)

        self.font_inc_btn = QPushButton("A+")
        self.font_inc_btn.setToolTip("Increase Text & Page Zoom")
        self.font_inc_btn.setFixedWidth(32)
        self.font_inc_btn.clicked.connect(lambda: self.change_font_size(0.15))
        self.toolbar.addWidget(self.font_inc_btn)

        self.font_dec_btn = QPushButton("A-")
        self.font_dec_btn.setToolTip("Decrease Text & Page Zoom")
        self.font_dec_btn.setFixedWidth(32)
        self.font_dec_btn.clicked.connect(lambda: self.change_font_size(-0.15))
        self.toolbar.addWidget(self.font_dec_btn)

        # History, Bookmarks, Extensions, and Download buttons
        self.download_btn = QPushButton("📥")
        self.download_btn.setToolTip("Downloads & Download History")
        self.download_btn.setFixedWidth(32)
        self.download_btn.clicked.connect(self.open_downloads)
        self.toolbar.addWidget(self.download_btn)

        self.hist_btn = QPushButton("📜")
        self.hist_btn.setToolTip("Browsing History")
        self.hist_btn.setFixedWidth(32)
        self.hist_btn.clicked.connect(self.open_history)
        self.toolbar.addWidget(self.hist_btn)

        self.bm_list_btn = QPushButton("🔖")
        self.bm_list_btn.setToolTip("Saved Bookmarks")
        self.bm_list_btn.setFixedWidth(32)
        self.bm_list_btn.clicked.connect(self.open_bookmarks)
        self.toolbar.addWidget(self.bm_list_btn)

        self.ext_btn = QPushButton("🧩")
        self.ext_btn.setToolTip("Chrome Web Store & Extensions")
        self.ext_btn.setFixedWidth(32)
        self.ext_btn.clicked.connect(self.open_chrome_web_store)
        self.toolbar.addWidget(self.ext_btn)

        # Settings & Profile Buttons
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setToolTip("Settings & Browser Management")
        self.settings_btn.setFixedWidth(32)
        self.settings_btn.clicked.connect(self.open_settings)
        self.toolbar.addWidget(self.settings_btn)

        self.profile_btn = QPushButton("👤")
        self.profile_btn.setToolTip("User Profile & Sign In")
        self.profile_btn.clicked.connect(self.open_profile_menu)
        self.toolbar.addWidget(self.profile_btn)
        self.update_profile_button_label()

        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setToolTip("New Tab")
        self.new_tab_btn.setFixedWidth(32)
        self.new_tab_btn.clicked.connect(self.add_new_tab)
        self.toolbar.addWidget(self.new_tab_btn)

        # Multi-Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.security_label = QLabel(" 🌐 Chromium Engine | High Performance ")
        self.security_label.setStyleSheet("font-weight: bold; color: #008000;")
        self.status_bar.addWidget(self.security_label)

        self.metrics_label = QLabel("Ready")
        self.status_bar.addPermanentWidget(self.metrics_label)

        # Shortcuts
        self.setup_shortcuts()

        # Open initial Home Tab
        self.add_new_tab(url=self.DEFAULT_HOME)

    def setup_shortcuts(self):
        new_tab_seq = QKeySequence("Ctrl+T")
        new_tab_action = QAction(self)
        new_tab_action.setShortcut(new_tab_seq)
        new_tab_action.triggered.connect(lambda: self.add_new_tab())
        self.addAction(new_tab_action)

        close_tab_seq = QKeySequence("Ctrl+W")
        close_tab_action = QAction(self)
        close_tab_action.setShortcut(close_tab_seq)
        close_tab_action.triggered.connect(lambda: self.close_tab(self.tabs.currentIndex()))
        self.addAction(close_tab_action)

        reload_seq = QKeySequence("Ctrl+R")
        reload_action = QAction(self)
        reload_action.setShortcut(reload_seq)
        reload_action.triggered.connect(self.reload_tab)
        self.addAction(reload_action)

    def current_view(self) -> NoScriptWebView:
        return self.tabs.currentWidget()

    def add_new_tab(self, url: str = DEFAULT_HOME):
        view = NoScriptWebView(self.profile, self)
        view.browser_window = self
        view.is_dark_mode = self.is_dark_mode
        view.setZoomFactor(self.zoom_factor)

        if self.is_dark_mode:
            view.page().setBackgroundColor(QColor(18, 18, 18))
            view.settings().setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, True)
        else:
            view.page().setBackgroundColor(QColor(255, 255, 255))
            view.settings().setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, False)

        # Connect url, title, and page load finished events
        view.urlChanged.connect(lambda u: self.update_url_bar(u, view))
        view.titleChanged.connect(lambda t: self.update_tab_title(t, view))
        view.loadFinished.connect(lambda ok: self.apply_theme_to_view(view))

        index = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(index)

        if url:
            self.load_url_in_view(view, url)

    def apply_theme_to_view(self, view: NoScriptWebView):
        if not view:
            return
        if self.is_dark_mode:
            view.page().setBackgroundColor(QColor(18, 18, 18))
            view.settings().setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, True)
            js_code = """
            (function() {
                let s = document.getElementById('anything-mode-css');
                if (s) { s.remove(); }
            })();
            """
        else:
            view.page().setBackgroundColor(QColor(255, 255, 255))
            view.settings().setAttribute(QWebEngineSettings.WebAttribute.ForceDarkMode, False)
            js_code = """
            (function() {
                let s = document.getElementById('anything-mode-css');
                if (s) { s.remove(); }
            })();
            """
        view.page().runJavaScript(js_code)

    def update_tab_title(self, title: str, view: NoScriptWebView):
        idx = self.tabs.indexOf(view)
        if idx >= 0:
            self.tabs.setTabText(idx, title[:20] if title else "Web Page")
            self.db.add_history(view.url().toString(), title or view.url().toString())

    def close_tab(self, index: int):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.close()

    def on_tab_changed(self, index: int):
        view = self.current_view()
        if view:
            url = view.url().toString()
            self.url_bar.setText(url)
            self.update_bookmark_icon(url)

    def navigate_back(self):
        view = self.current_view()
        if view and view.history().canGoBack():
            view.history().back()

    def navigate_forward(self):
        view = self.current_view()
        if view and view.history().canGoForward():
            view.history().forward()

    def reload_tab(self):
        view = self.current_view()
        if view:
            view.reload()

    def go_home(self):
        view = self.current_view()
        if view:
            self.load_url_in_view(view, self.DEFAULT_HOME)

    def on_url_submitted(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        clean_text = text.replace('"', '').strip()
        if clean_text.startswith("file://"):
            target_url = clean_text
        elif os.path.exists(clean_text) or (len(clean_text) > 2 and clean_text[1:3] == ":\\"):
            target_url = QUrl.fromLocalFile(clean_text).toString()
        elif text.startswith("http://") or text.startswith("https://"):
            target_url = text
        elif "." in text and " " not in text:
            target_url = "https://" + text
        else:
            query = urllib.parse.quote(text)
            target_url = f"https://www.google.com/search?q={query}"

        view = self.current_view()
        if view:
            self.load_url_in_view(view, target_url)

    def open_url_in_current_tab(self, url: str):
        self.url_bar.setText(url)
        self.on_url_submitted()

    def load_url_in_view(self, view: NoScriptWebView, url_str: str):
        self.status_bar.showMessage(f"Loading {url_str}...")
        if url_str.startswith("file://"):
            view.load(QUrl(url_str))
        else:
            view.setUrl(QUrl(url_str))
        self.url_bar.setText(url_str)
        self.update_bookmark_icon(url_str)
        blocked = self.profile._interceptor.blocked_count
        self.metrics_label.setText(f" 🛡️ Ads Blocked: {blocked} ")

    def update_url_bar(self, qurl: QUrl, view: NoScriptWebView):
        if view == self.current_view():
            self.url_bar.setText(qurl.toString())
            self.update_bookmark_icon(qurl.toString())

    def update_bookmark_icon(self, url: str):
        if self.db.is_bookmarked(url):
            self.bookmark_btn.setText("★")
        else:
            self.bookmark_btn.setText("☆")

    def toggle_bookmark(self):
        view = self.current_view()
        if not view:
            return
        url = view.url().toString()
        title = self.tabs.tabText(self.tabs.currentIndex())

        if self.db.is_bookmarked(url):
            self.db.remove_bookmark(url)
            self.bookmark_btn.setText("☆")
            self.status_bar.showMessage("Bookmark removed.", 2000)
        else:
            self.db.add_bookmark(url, title)
            self.bookmark_btn.setText("★")
            self.status_bar.showMessage("Bookmark added!", 2000)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.theme_btn.setText("☀️" if self.is_dark_mode else "🌙")

        # Set Chromium profile dark mode attribute
        self.profile.settings().setAttribute(
            QWebEngineSettings.WebAttribute.ForceDarkMode, self.is_dark_mode
        )

        # Apply pitch black / clean white mode style to application window UI
        if self.is_dark_mode:
            self.setStyleSheet(
                """
                QMainWindow, QDialog, QToolBar { background-color: #000000; color: #ffffff; }
                QLineEdit { background-color: #121212; color: #ffffff; border: 1px solid #333333; padding: 6px; }
                QPushButton { background-color: #1a1a1a; color: #ffffff; border: 1px solid #444444; padding: 6px; }
                QPushButton:hover { background-color: #2a2a2a; }
                QTabWidget::pane { border: 1px solid #222222; background-color: #000000; }
                QTabBar::tab { background: #121212; color: #888888; padding: 6px 12px; }
                QTabBar::tab:selected { background: #000000; color: #ffffff; font-weight: bold; border-bottom: 2px solid #0078d4; }
                QStatusBar { background-color: #000000; color: #aaaaaa; }
                """
            )
        else:
            self.setStyleSheet(
                """
                QMainWindow, QDialog, QToolBar { background-color: #ffffff; color: #000000; }
                QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; padding: 6px; }
                QPushButton { background-color: #f0f0f5; color: #000000; border: 1px solid #cccccc; padding: 6px; }
                QPushButton:hover { background-color: #e0e0e8; }
                QTabWidget::pane { border: 1px solid #cccccc; background-color: #ffffff; }
                QTabBar::tab { background: #e8e8ed; color: #555555; padding: 6px 12px; }
                QTabBar::tab:selected { background: #ffffff; color: #000000; font-weight: bold; border-bottom: 2px solid #0078d4; }
                QStatusBar { background-color: #ffffff; color: #333333; }
                """
            )

        # Apply dark/light mode to all open tabs
        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if isinstance(view, NoScriptWebView):
                self.apply_theme_to_view(view)
                view.reload()

    def change_font_size(self, delta: float):
        self.zoom_factor = round(max(0.5, min(3.0, self.zoom_factor + delta)), 2)
        percentage = int(self.zoom_factor * 100)

        for i in range(self.tabs.count()):
            view = self.tabs.widget(i)
            if isinstance(view, NoScriptWebView):
                view.setZoomFactor(self.zoom_factor)

        self.status_bar.showMessage(f"Text & Page Zoom: {percentage}%", 2500)

    def open_history(self):
        dlg = HistoryDialog(self.db, self)
        dlg.exec()

    def open_bookmarks(self):
        dlg = BookmarksDialog(self.db, self)
        dlg.exec()

    def open_chrome_web_store(self):
        dlg = ExtensionManagerDialog(self)
        dlg.exec()

    def open_downloads(self):
        dlg = DownloadHistoryDialog(self.db, self)
        dlg.exec()

    def update_profile_button_label(self):
        user = self.db.get_active_user()
        if user:
            self.profile_btn.setText(f"👤 {user['full_name']}")
            self.profile_btn.setToolTip(f"Signed in as {user['full_name']} (@{user['username']})")
        else:
            self.profile_btn.setText("👤 Guest")
            self.profile_btn.setToolTip("Signed in as Guest - Click to Sign In / Register")

    def open_profile_menu(self):
        menu = QMenu(self)
        user = self.db.get_active_user()

        if user:
            profile_action = QAction(f"👤 Account: {user['full_name']} (@{user['username']})", self)
            profile_action.setEnabled(False)
            menu.addAction(profile_action)

            settings_action = QAction("⚙️ Settings", self)
            settings_action.triggered.connect(self.open_settings)
            menu.addAction(settings_action)

            sign_out_action = QAction("🚪 Sign Out", self)
            sign_out_action.triggered.connect(self.logout_user)
            menu.addAction(sign_out_action)
        else:
            login_action = QAction("🔑 Sign In / Create Account", self)
            login_action.triggered.connect(self.open_login_dialog)
            menu.addAction(login_action)

            settings_action = QAction("⚙️ Settings", self)
            settings_action.triggered.connect(self.open_settings)
            menu.addAction(settings_action)

        menu.exec(self.profile_btn.mapToGlobal(self.profile_btn.rect().bottomLeft()))

    def open_login_dialog(self):
        dlg = LoginRegisterDialog(self.db, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.update_profile_button_label()

    def logout_user(self):
        self.db.logout_active_user()
        self.update_profile_button_label()
        QMessageBox.information(self, "Signed Out", "You have been signed out.")

    def open_settings(self):
        dlg = SettingsDialog(self.db, self)
        dlg.exec()
        self.update_profile_button_label()
