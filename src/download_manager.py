"""
NoScript Browser - Download Manager
Handles file download interception from Chromium web requests, user save location selection,
and download progress tracking.
"""

import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from PyQt6.QtCore import Qt, QUrl


class DownloadManager:
    """
    Intercepts QWebEngineDownloadRequest signals and manages active file downloads.
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.active_downloads = []

    def handle_download_requested(self, download):
        """
        Slot triggered when Chromium initiates a file download.
        """
        suggested_filename = download.downloadFileName() or "download"
        default_dir = os.path.expanduser("~/Downloads")
        os.makedirs(default_dir, exist_ok=True)
        default_path = os.path.join(default_dir, suggested_filename)

        save_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Save File",
            default_path,
            "All Files (*.*)",
        )

        if not save_path:
            download.cancel()
            return

        download.setDownloadDirectory(os.path.dirname(save_path))
        download.setDownloadFileName(os.path.basename(save_path))

        # Progress Dialog
        progress = QProgressDialog(
            f"Downloading {os.path.basename(save_path)}...",
            "Cancel",
            0,
            100,
            self.parent,
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        def update_progress():
            received = download.receivedBytes()
            total = download.totalBytes()
            if total > 0:
                percent = int((received / total) * 100)
                progress.setValue(percent)

        def download_finished():
            progress.close()
            if download.state() == download.DownloadState.DownloadCompleted:
                if self.parent and hasattr(self.parent, "db"):
                    file_size = download.totalBytes() or 0
                    url_str = download.url().toString()
                    self.parent.db.add_download(
                        os.path.basename(save_path), save_path, url_str, file_size
                    )

                QMessageBox.information(
                    self.parent,
                    "Download Complete",
                    f"File downloaded successfully to:\n{save_path}",
                )
            elif download.state() == download.DownloadState.DownloadCancelled:
                pass
            else:
                QMessageBox.warning(
                    self.parent,
                    "Download Failed",
                    "The file download failed or was interrupted.",
                )

        download.receivedBytesChanged.connect(update_progress)
        download.isFinishedChanged.connect(download_finished)
        progress.canceled.connect(download.cancel)

        download.accept()
