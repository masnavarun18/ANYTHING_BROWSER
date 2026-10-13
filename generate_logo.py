"""
ANYTHING BROWSER - Logo Generator Script
Generates a high-resolution, anti-aliased 512x512 PNG and ICO icon for ANYTHING BROWSER.
"""

import os
import sys
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import (
    QImage,
    QPainter,
    QColor,
    QBrush,
    QPen,
    QLinearGradient,
    QFont,
    QPainterPath,
    QIcon,
)


def create_anything_browser_logo():
    app = QApplication(sys.argv)
    size = 512
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    # 1. Background Squircle with Deep Gradient
    rect = QRectF(16, 16, size - 32, size - 32)
    bg_gradient = QLinearGradient(0, 0, size, size)
    bg_gradient.setColorAt(0.0, QColor("#0f172a"))  # Slate Deep Dark
    bg_gradient.setColorAt(0.5, QColor("#1e1b4b"))  # Deep Indigo
    bg_gradient.setColorAt(1.0, QColor("#030712"))  # Obsidian Black

    painter.setBrush(QBrush(bg_gradient))
    painter.setPen(QPen(QColor("#334155"), 4))
    painter.drawRoundedRect(rect, 96, 96)

    # 2. Outer Glowing Orbital Ring (Browser / Globe Theme)
    center = QPointF(size / 2, size / 2)
    ring_radius = 180.0

    ring_gradient = QLinearGradient(100, 100, 400, 400)
    ring_gradient.setColorAt(0.0, QColor("#00f2fe"))  # Electric Cyan
    ring_gradient.setColorAt(0.5, QColor("#4facfe"))  # Sky Blue
    ring_gradient.setColorAt(1.0, QColor("#7f00ff"))  # Neon Violet

    ring_pen = QPen(QBrush(ring_gradient), 18)
    ring_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(ring_pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Draw Orbital Arc
    painter.drawArc(
        QRectF(center.x() - ring_radius, center.y() - ring_radius, ring_radius * 2, ring_radius * 2),
        30 * 16,
        300 * 16,
    )

    # Orbital Node Points
    node_pen = QPen(QColor("#ffffff"), 2)
    painter.setPen(node_pen)
    painter.setBrush(QBrush(QColor("#00f2fe")))
    painter.drawEllipse(QPointF(center.x() + ring_radius * 0.86, center.y() - ring_radius * 0.5), 14, 14)

    # 3. Center Stylized "A" Monogram Emblem
    path = QPainterPath()
    # Left leg
    path.moveTo(center.x() - 90, center.y() + 110)
    path.lineTo(center.x(), center.y() - 110)
    # Right leg
    path.lineTo(center.x() + 90, center.y() + 110)
    path.lineTo(center.x() + 50, center.y() + 110)
    path.lineTo(center.x() + 30, center.y() + 60)
    path.lineTo(center.x() - 30, center.y() + 60)
    path.lineTo(center.x() - 50, center.y() + 110)
    path.closeSubpath()

    # Inner triangle cutout
    path.moveTo(center.x(), center.y() - 40)
    path.lineTo(center.x() + 18, center.y() + 20)
    path.lineTo(center.x() - 18, center.y() + 20)
    path.closeSubpath()

    # Metallic Gradient Fill for "A" Emblem
    emblem_gradient = QLinearGradient(center.x(), center.y() - 110, center.x(), center.y() + 110)
    emblem_gradient.setColorAt(0.0, QColor("#ffffff"))
    emblem_gradient.setColorAt(0.3, QColor("#38bdf8"))  # Light Cyan
    emblem_gradient.setColorAt(0.7, QColor("#818cf8"))  # Violet
    emblem_gradient.setColorAt(1.0, QColor("#c084fc"))  # Bright Purple

    painter.setPen(QPen(QColor("#ffffff"), 2))
    painter.setBrush(QBrush(emblem_gradient))
    painter.drawPath(path)

    # 4. Horizontal Glowing Speed Bar in "A"
    bar_rect = QRectF(center.x() - 70, center.y() + 15, 140, 14)
    bar_gradient = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)
    bar_gradient.setColorAt(0.0, QColor("#38bdf8"))
    bar_gradient.setColorAt(1.0, QColor("#f43f5e"))  # Vibrant Rose

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(bar_gradient))
    painter.drawRoundedRect(bar_rect, 7, 7)

    painter.end()

    # Save PNG and ICO
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    os.makedirs(assets_dir, exist_ok=True)

    png_path = os.path.join(assets_dir, "logo.png")
    ico_path = os.path.join(assets_dir, "logo.ico")

    image.save(png_path, "PNG")

    # Generate ICO format via QIcon
    icon = QIcon(png_path)
    pixmap = icon.pixmap(256, 256)
    pixmap.save(ico_path, "ICO")

    print("==================================================")
    print("ANYTHING BROWSER Logo Generated Successfully!")
    print(f"PNG Logo: {png_path}")
    print(f"ICO Icon: {ico_path}")
    print("==================================================")


if __name__ == "__main__":
    create_anything_browser_logo()
