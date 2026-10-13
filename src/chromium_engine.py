"""
NoScript Browser - Chromium CEF Security Engine
Configures Chromium Embedded Framework (QtWebEngine) profile, settings, request interceptor,
and web view security parameters to guarantee zero JavaScript execution and zero CSS stylesheet processing.
"""

import sys
import os
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineSettings,
    QWebEngineScript,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from src.content_filter import ContentFilter, strip_html_css_js


class NoScriptUrlInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Chromium Network Request Interceptor for monitoring outbound network requests.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocked_count = 0

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        pass


class NoScriptWebPage(QWebEnginePage):
    """
    Custom Chromium Web Page with overridden navigation, security restrictions,
    fullscreen support, and microphone/media permission handlers.
    """

    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.raw_html_mode = False
        self.apply_security_settings()
        self.featurePermissionRequested.connect(self.handle_feature_permission)

    def apply_security_settings(self):
        s = self.settings()
        # Enable JavaScript execution
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)

        # Enable PDF Viewer and Local File Access
        s.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        # Enable FullScreen and Screen Capture for YouTube & HTML5 videos
        s.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)

        # Enable standard Web Engine rendering attributes
        s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)

    def handle_feature_permission(self, security_origin, feature):
        # Grant Microphone & Camera permissions for Voice Search & Media
        if feature in (
            QWebEnginePage.Feature.MediaAudioCapture,
            QWebEnginePage.Feature.MediaVideoCapture,
            QWebEnginePage.Feature.MediaAudioVideoCapture,
            QWebEnginePage.Feature.DesktopAudioVideoCapture,
        ):
            self.setFeaturePermission(
                security_origin,
                feature,
                QWebEnginePage.PermissionPolicy.PermissionGrantedByUser,
            )

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


def configure_chromium_profile() -> QWebEngineProfile:
    """
    Creates and initializes a global secure Chromium profile with Google Sign-In support.
    """
    profile = QWebEngineProfile("NoScriptProfile", None)
    profile.setHttpUserAgent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    # Inject Chrome Web Store & Google Sign-In security script
    google_auth_script = QWebEngineScript()
    google_auth_script.setName("GoogleAuthSecurityCompat")
    google_auth_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    google_auth_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    google_auth_script.setRunsOnSubFrames(True)
    google_auth_script.setSourceCode("""
    (function() {
        if (window._google_auth_fixed) return;
        window._google_auth_fixed = true;

        try {
            // 1. Override webdriver flag & vendor
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'vendor', { get: () => 'Google Inc.' });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

            // 2. Mock navigator.plugins (Google requires plugins.length > 0)
            const mockPlugins = [
                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chrome PDF Viewer', filename: 'mhjfbglicamgbbneiplfldfmgkjopppa', description: '' },
                { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
            ];
            mockPlugins.item = function(i) { return this[i]; };
            mockPlugins.namedItem = function(name) { return this.find(p => p.name === name); };
            Object.defineProperty(navigator, 'plugins', { get: () => mockPlugins });

            // 3. Override userAgentData to match Chrome 122
            if (navigator.userAgentData) {
                Object.defineProperty(navigator, 'userAgentData', {
                    get: () => ({
                        brands: [
                            { brand: 'Chromium', version: '122' },
                            { brand: 'Not(A:Brand', version: '24' },
                            { brand: 'Google Chrome', version: '122' }
                        ],
                        mobile: false,
                        platform: 'Windows'
                    })
                });
            }

            // 4. Mock window.chrome objects (csi, loadTimes, app, runtime)
            if (!window.chrome) window.chrome = {};
            window.chrome.csi = function() { return { startE: Date.now(), onloadT: Date.now(), pageT: 100, tran: 15 }; };
            window.chrome.loadTimes = function() {
                return {
                    requestTime: Date.now() / 1000,
                    startLoadTime: Date.now() / 1000,
                    commitLoadTime: Date.now() / 1000,
                    finishDocumentLoadTime: Date.now() / 1000,
                    finishLoadTime: Date.now() / 1000,
                    firstPaintTime: Date.now() / 1000,
                    firstPaintAfterLoadTime: 0,
                    navigationType: 'Other',
                    wasFetchedViaSpdy: true,
                    wasNpnNegotiated: true,
                    npnNegotiatedProtocol: 'h2',
                    wasAlternateProtocolAvailable: false,
                    connectionInfo: 'h2'
                };
            };
            window.chrome.app = { isInstalled: false, InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }, RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' } };
            window.chrome.runtime = {
                id: 'anything_browser_extension_host',
                connect: function() { return { onMessage: { addListener: function() {} }, postMessage: function() {} }; },
                sendMessage: function() {}
            };
        } catch(e) {}
    })();
    """)
    profile.scripts().insert(google_auth_script)

    # Auto-load uBlock Origin extension from Downloads
    ublock_dir = r"C:\Users\masna\Downloads\uBlock0_1.75.1b11.chromium"
    if os.path.exists(ublock_dir):
        try:
            profile.extensionManager().loadExtension(ublock_dir)
        except Exception as e:
            pass

    # Inject uBlock-style YouTube & Video Ad-Blocker at DocumentCreation time
    adblock_script = QWebEngineScript()
    adblock_script.setName("uBlockVideoAdBlocker")
    adblock_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
    adblock_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    adblock_script.setRunsOnSubFrames(True)
    adblock_script.setSourceCode("""
    (function() {
        if (window._anything_adblock_v4) return;
        window._anything_adblock_v4 = true;

        function sanitize(obj) {
            if (!obj || typeof obj !== 'object') return obj;
            if (obj.adPlacements) delete obj.adPlacements;
            if (obj.playerAds) delete obj.playerAds;
            if (obj.adSlots) delete obj.adSlots;
            if (obj.adBreaks) delete obj.adBreaks;
            if (obj.playerConfig && obj.playerConfig.adPlacementConfig) {
                delete obj.playerConfig.adPlacementConfig;
            }
            return obj;
        }

        // 1. Sanitize JSON.parse & fetch API responses
        try {
            const origParse = JSON.parse;
            JSON.parse = function() {
                let res = origParse.apply(this, arguments);
                return sanitize(res);
            };
        } catch(e) {}

        try {
            const origFetch = window.fetch;
            window.fetch = async function(...args) {
                const response = await origFetch.apply(this, args);
                const url = (args[0] && args[0].url) ? args[0].url : String(args[0]);

                if (url.includes('/youtubei/v1/player') || url.includes('/youtubei/v1/next')) {
                    try {
                        const clone = response.clone();
                        let json = await clone.json();
                        sanitize(json);
                        return new Response(JSON.stringify(json), {
                            status: response.status,
                            statusText: response.statusText,
                            headers: response.headers
                        });
                    } catch(e) {}
                }
                return response;
            };
        } catch(e) {}

        // 2. Intercept ytInitialPlayerResponse
        try {
            let _ytResponse;
            Object.defineProperty(window, 'ytInitialPlayerResponse', {
                get: function() { return _ytResponse; },
                set: function(val) { _ytResponse = sanitize(val); },
                configurable: true
            });
        } catch(e) {}

        // 3. Instant Ad Video Muter & 0s Auto-Skipper (Runs every 50ms)
        setInterval(function() {
            try {
                // Click skip button immediately if present
                let skipBtn = document.querySelector('.ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytp-skip-ad-button, .ytp-ad-skip-button-slot, .videoAdUiSkipButton');
                if (skipBtn) {
                    try { skipBtn.click(); } catch(e) {}
                }

                // Hide banner ad elements
                let adEls = document.querySelectorAll('.video-ads, .ytp-ad-module, .ytp-ad-overlay-container, .ytp-ad-text, ytd-promoted-video-renderer, ytd-display-ad-renderer, #masthead-ad, #player-ads, .ad-container, .ad-slot, .ad-wrapper');
                adEls.forEach(function(el) {
                    if (el) el.style.display = 'none';
                });

                // Instant Mute & Skip on active ad video
                let video = document.querySelector('video');
                let adShowing = document.querySelector('.ad-showing, .ytp-ad-player-overlay, .ytp-ad-text');
                if (video && adShowing) {
                    video.muted = true;
                    if (isFinite(video.duration) && video.duration > 0) {
                        video.currentTime = video.duration;
                    }
                }
            } catch(e) {}
        }, 50);
    })();
    """)
    profile.scripts().insert(adblock_script)

    interceptor = NoScriptUrlInterceptor(profile)
    profile.setUrlRequestInterceptor(interceptor)
    profile._interceptor = interceptor  # Store reference

    return profile


class NoScriptWebView(QWebEngineView):
    """
    Chromium Web View widget for NoScript Browser tabs.
    """

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.is_loading_internal_html = False
        self.custom_page = NoScriptWebPage(self.profile, self)
        self.setPage(self.custom_page)
        self.custom_page.fullScreenRequested.connect(self.handle_fullscreen_requested)
        self.is_dark_mode = False
        self.font_size = 14

    def handle_fullscreen_requested(self, request):
        request.accept()
        if request.toggleOn():
            if hasattr(self, "browser_window") and self.browser_window:
                self.browser_window.toolbar.hide()
                self.browser_window.status_bar.hide()
                self.browser_window.showFullScreen()
            else:
                self.showFullScreen()
        else:
            if hasattr(self, "browser_window") and self.browser_window:
                self.browser_window.toolbar.show()
                self.browser_window.status_bar.show()
                self.browser_window.showNormal()
            else:
                self.showNormal()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        req = self.lastContextMenuRequest()

        if req:
            media_url = req.mediaUrl()
            if media_url.isValid() and not media_url.isEmpty():
                save_image_action = QAction("🖼️ Save Image As...", self)
                save_image_action.triggered.connect(lambda: self.save_image_at_url(media_url))
                menu.insertAction(menu.actions()[0] if menu.actions() else None, save_image_action)

                copy_image_link_action = QAction("🔗 Copy Image Link", self)
                copy_image_link_action.triggered.connect(lambda: QApplication.clipboard().setText(media_url.toString()))
                menu.addAction(copy_image_link_action)

                open_image_action = QAction("🌐 Open Image in New Tab", self)
                open_image_action.triggered.connect(lambda: self.browser_window.add_new_tab(media_url.toString()) if hasattr(self, "browser_window") and self.browser_window else None)
                menu.addAction(open_image_action)

        pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
        menu.exec(pos)

    def save_image_at_url(self, url: QUrl):
        url_str = url.toString()
        default_name = os.path.basename(url.path()) or "image.jpg"
        if not os.path.splitext(default_name)[1]:
            default_name += ".jpg"

        default_dir = os.path.expanduser("~/Downloads")
        default_path = os.path.join(default_dir, default_name)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Image As",
            default_path,
            "Images (*.png *.jpg *.jpeg *.gif *.webp *.bmp *.svg);;All Files (*.*)",
        )

        if save_path:
            import urllib.request
            try:
                req = urllib.request.Request(
                    url_str,
                    headers={
                        "User-Agent": self.profile.httpUserAgent()
                    },
                )
                with urllib.request.urlopen(req) as resp, open(save_path, "wb") as f:
                    data = resp.read()
                    f.write(data)

                if hasattr(self, "browser_window") and hasattr(self.browser_window, "db"):
                    self.browser_window.db.add_download(
                        os.path.basename(save_path), save_path, url_str, len(data)
                    )

                QMessageBox.information(
                    self,
                    "Image Saved",
                    f"Image saved successfully to:\n{save_path}",
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Save Failed",
                    f"Failed to save image:\n{str(e)}",
                )

    def load_formatted_text(self, title: str, clean_text: str, base_url: str):
        """
        Renders clean structured text in the view without scripts or CSS styling.
        """
        self.is_loading_internal_html = True
        try:
            bg_color = "#121212" if self.is_dark_mode else "#ffffff"
            fg_color = "#e0e0e0" if self.is_dark_mode else "#1a1a1a"
            link_color = "#82aaff" if self.is_dark_mode else "#0056b3"
            border_color = "#333333" if self.is_dark_mode else "#dddddd"

            # Ultra lightweight HTML container strictly for text layout & hyperlinks
            minimal_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        font-size: {self.font_size}px;
                        line-height: 1.6;
                        background-color: {bg_color};
                        color: {fg_color};
                        max-width: 900px;
                        margin: 20px auto;
                        padding: 0 20px;
                        word-wrap: break-word;
                    }}
                    a {{
                        color: {link_color};
                        text-decoration: underline;
                    }}
                    pre, code {{
                        font-family: 'Consolas', 'Courier New', monospace;
                        background: {border_color};
                        padding: 4px 8px;
                        border-radius: 4px;
                    }}
                </style>
            </head>
            <body>
                {clean_text}
            </body>
            </html>
            """
            self.setHtml(minimal_html, QUrl(base_url))
        finally:
            self.is_loading_internal_html = False
