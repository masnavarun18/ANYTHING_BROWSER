# 🌐 ANYTHING BROWSER

A high-performance, modern Windows desktop web browser built with **Python 3.12**, **PyQt6**, and the **Chromium Embedded Framework (QtWebEngine)**.

![ANYTHING BROWSER Logo](assets/logo.png)

---

## 🌟 Key Features

- **⚡ Fast Chromium Engine**: Powered by QtWebEngine with full JavaScript, HTML5 video, CSS3, WebGL, and PDF support.
- **👤 User Profiles & Accounts**: Sign in or create a user account with persistent SQLite profile data and password hashing (`SHA-256`).
- **⚙️ Chrome-Style Settings Manager**: Customize custom homepages, default search engines (Google, Bing, DuckDuckGo, Yahoo, Ecosia), and default download directories.
- **🛡️ Built-in Ad-Blocker & Extension Manager**: Auto-loads Chromium extensions (e.g. uBlock Origin) and blocks tracking servers.
- **🧩 Extension Support (`🧩`)**: Load unpacked Chrome extensions directly into Chromium using the interactive Extension Manager dialog.
- **🖼️ Picture Saving Engine**: Right-click any picture to **Save Image As...**, copy link, or open in new tab.
- **📥 Download Manager (`📥`)**: Download progress dialogs and persistent download history with one-click **Open File** and **Open Folder** actions.
- **🎤 Voice Search & Microphone Access**: Integrated microphone permissions for Google and YouTube voice search (`🎤`).
- **🌙 Dark & Light Mode Theme Engine**: Toggle native dark and light themes dynamically.
- **🔍 Real-Time Page Zoom (`A+` / `A-`)**: Smooth zoom scaling from 50% to 300%.

---

## 🚀 How to Run from Source

### Prerequisites
- Python 3.12 (or 3.10+)
- Windows 10 or Windows 11

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/masnavarun18/ANYTHING_BROWSER.git
   cd ANYTHING_BROWSER
   ```

2. **Install Dependencies**:
   ```bash
   pip install PyQt6 pyinstaller
   ```

3. **Run Application**:
   ```bash
   python src/main.py
   ```

---

## 📦 Building Standalone Windows Executable

To compile a standalone `.exe` bundle that runs on any Windows PC without needing Python installed:

```bash
python build.py
```

The compiled standalone executable bundle will be located at:
`dist/AnythingBrowser/AnythingBrowser.exe`

---

## 📁 Project Architecture

```
ANYTHING/
├── src/
│   ├── main.py              # Application entry point
│   ├── browser_window.py    # Multi-tab UI, navigation toolbar, profile & settings dialogs
│   ├── chromium_engine.py   # Chromium CEF profile, User-Agent, extension loader, & security
│   ├── bookmarks_history.py # SQLite database for history, bookmarks, users, & settings
│   ├── download_manager.py  # Download progress & manager
│   └── content_filter.py    # Resource parser & filter engine
├── assets/
│   ├── logo.png             # Application logo (512x512)
│   └── logo.ico             # Windows ICO icon
├── installer/
│   ├── setup_builder.py     # Windows setup installer generator
│   └── install.ps1          # PowerShell setup script
├── tests/                   # Unit test suite
├── build.py                 # PyInstaller automated compiler
└── README.md
```

---

## 📄 License
This project is open-source and available under the **MIT License**.
