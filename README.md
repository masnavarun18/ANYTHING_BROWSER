# 🌐 ANYTHING BROWSER (Windows & Android)

A high-performance, modern cross-platform web browser supporting both **Windows Desktop PCs** (Python 3.12 + PyQt6 Chromium) and **Android Mobile Devices** (Kotlin + Jetpack Compose + Android WebView).

![ANYTHING BROWSER Logo](assets/logo.png)

---

## 🌟 Key Features

- **⚡ Fast Chromium Engine**: Powered by QtWebEngine (Windows) and Android WebView with full JavaScript, HTML5 video, CSS3, WebGL, and PDF support.
- **👤 User Profiles & Accounts**: Sign in or create a user account with persistent SQLite profile data and password hashing (`SHA-256`).
- **⚙️ Chrome-Style Settings Manager**: Customize custom homepages, default search engines (Google, Bing, DuckDuckGo, Yahoo, Ecosia), and default download directories.
- **🛡️ Built-in Ad-Blocker & Extension Manager (`🧩`)**: Auto-loads Chromium extensions (e.g. uBlock Origin) and blocks tracking servers.
- **🖼️ Picture Saving Engine**: Right-click or long-press any picture on any website to **Save Image As...**, copy link, or view in new tab.
- **📥 Download History Manager (`📥`)**: Track downloads with one-click **Open File** and **Open Folder** actions in Windows File Explorer and Android Download Manager.
- **🎤 Voice Search & Microphone Access**: Integrated microphone permissions for Google and YouTube voice search (`🎤`).
- **🌙 Dark & Light Mode Theme Engine**: Toggle native dark and light themes dynamically.
- **🔍 Real-Time Page Zoom (`A+` / `A-`)**: Smooth zoom scaling from 50% to 300%.

---

## 💻 Running Windows Desktop App

### Prerequisites
- Python 3.12 (or 3.10+)
- Windows 10 or Windows 11

### Step 1: Run from Source
```bash
pip install PyQt6 pyinstaller
python src/main.py
```

### Step 2: Build Windows `.exe` Executable
To compile a standalone `.exe` bundle that runs on any Windows PC without needing Python installed:
```bash
python build.py
```
Output executable: `dist/AnythingBrowser/AnythingBrowser.exe`

---

## 📱 Building & Running Android Mobile App

### Prerequisites
- Android Studio (Hedgehog or newer)
- Android SDK 34 (Android 14) / Min SDK 26 (Android 8.0)
- Kotlin 1.9+ & Jetpack Compose

### Step 1: Open in Android Studio
1. Open Android Studio.
2. Select **Open an Existing Project** and choose the `android/` directory inside this repository.

### Step 2: Build & Run APK
1. Connect your Android phone via USB or start an Android Virtual Device (AVD).
2. Click **Run 'app'** (`Shift + F10`) or run from terminal:
   ```bash
   cd android
   ./gradlew assembleDebug
   ```
Output APK: `android/app/build/outputs/apk/debug/app-debug.apk`

---

## 📁 Project Architecture

```
ANYTHING/
├── src/                    # 💻 Windows Desktop Application (Python + PyQt6)
│   ├── main.py              # Windows app entry point
│   ├── browser_window.py    # Multi-tab UI, navigation toolbar, profile & settings
│   ├── chromium_engine.py   # Chromium CEF profile, User-Agent, & extension loader
│   ├── bookmarks_history.py # SQLite database for history, bookmarks, users, & settings
│   ├── download_manager.py  # Download progress & manager
│   └── content_filter.py    # Resource parser & filter engine
├── android/                # 📱 Android Mobile Application (Kotlin + Jetpack Compose)
│   ├── app/
│   │   ├── src/main/java/com/anything/browser/
│   │   │   ├── MainActivity.kt        # Compose UI & Tab Manager
│   │   │   ├── BrowserWebView.kt      # Android WebView, WebChromeClient, & Fullscreen
│   │   │   └── ProfileDatabase.kt     # Room SQLite Database
│   │   └── AndroidManifest.xml
│   ├── build.gradle.kts
│   └── settings.gradle.kts
├── assets/                 # 🎨 Shared Logos & Icons (logo.png, logo.ico)
├── build.py                # 📦 Windows PyInstaller Compiler
└── README.md               # 📖 Project Documentation
```

---

## 📄 License
This project is open-source and available under the **MIT License**.
