"""Fullscreen photo viewer for chat media."""

from __future__ import annotations

import os
import shutil

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.styles.themes import get_theme_colors


class PhotoGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)
        self.setRenderHints(self.renderHints())
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setStyleSheet("background: transparent; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._zoom = 1.0

    def set_pixmap(self, pixmap: QPixmap):
        self.pixmap_item.setPixmap(pixmap)
        self.scene().setSceneRect(self.pixmap_item.boundingRect())
        self.resetTransform()
        self._zoom = 1.0
        self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        if self.pixmap_item.pixmap().isNull():
            return
        factor = 1.16 if event.angleDelta().y() > 0 else 0.86
        next_zoom = self._zoom * factor
        if next_zoom < 0.2 or next_zoom > 8:
            return
        self._zoom = next_zoom
        self.scale(factor, factor)


class PhotoViewerDialog(QDialog):
    def __init__(self, items: list[dict], current_index: int = 0, theme_name: str = "dark", parent=None):
        super().__init__(parent)
        self.items = items
        self.current_index = current_index
        self.theme_name = theme_name or "dark"
        self.colors = get_theme_colors(self.theme_name)
        self._swipe_start = QPoint()
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowType.Dialog, True)
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        overlay = "rgba(245, 247, 250, 0.74)" if self.theme_name == "light" else "rgba(5, 8, 14, 0.92)"
        self.setStyleSheet(f"background-color: {overlay};")
        self.build_ui()
        self.load_current()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(18)

        self.content = QFrame()
        panel_bg = "#FFFFFF" if self.theme_name == "light" else "#242428"
        self.content.setStyleSheet(
            f"QFrame {{ background-color: {panel_bg}; border-radius: 40px; }}"
        )
        root.addWidget(self.content, 1)

        frame_layout = QVBoxLayout(self.content)
        frame_layout.setContentsMargins(18, 18, 18, 18)
        frame_layout.setSpacing(16)

        top = QHBoxLayout()
        self.back_button = self._action_button("Назад")
        self.back_button.clicked.connect(self.close)
        top.addWidget(self.back_button)

        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            f"color: {self.colors['text_primary']}; font-size: 15px; font-weight: 600; background: transparent;"
        )
        top.addWidget(self.title_label, 1)

        self.download_button = self._action_button("Скачать")
        self.download_button.clicked.connect(self.download_current)
        top.addWidget(self.download_button)
        frame_layout.addLayout(top)

        center = QHBoxLayout()
        center.setSpacing(14)

        self.prev_button = self._nav_button("‹")
        self.prev_button.clicked.connect(self.show_previous)
        center.addWidget(self.prev_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self.image_view = PhotoGraphicsView()
        self.image_view.setMinimumSize(520, 360)
        center.addWidget(self.image_view, 1)

        self.next_button = self._nav_button("›")
        self.next_button.clicked.connect(self.show_next)
        center.addWidget(self.next_button, 0, Qt.AlignmentFlag.AlignVCenter)
        frame_layout.addLayout(center, 1)

        self.caption_label = QLabel()
        self.caption_label.setWordWrap(True)
        self.caption_label.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 13px; background: transparent;"
        )
        frame_layout.addWidget(self.caption_label)

    def _action_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_bg = "#EEF1F4" if self.theme_name == "light" else "#303036"
        button_hover = "#E3E8EE" if self.theme_name == "light" else "#3A3A42"
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {button_bg};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 999px;
                padding: 10px 14px;
            }}
            QPushButton:hover {{ background-color: {button_hover}; }}
            """
        )
        return button

    def _nav_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setFixedSize(48, 48)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_bg = "#EEF1F4" if self.theme_name == "light" else "#303036"
        button_hover = "#E3E8EE" if self.theme_name == "light" else "#3A3A42"
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {button_bg};
                color: {self.colors['text_primary']};
                border: none;
                border-radius: 999px;
                font-size: 26px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {button_hover}; }}
            """
        )
        return button

    def load_current(self):
        if not self.items:
            self.close()
            return
        self.current_index = max(0, min(self.current_index, len(self.items) - 1))
        item = self.items[self.current_index]
        file_path = item.get("file_url", "")
        self.title_label.setText(item.get("file_name") or f"Фото {self.current_index + 1}")
        self.caption_label.setText(item.get("text", ""))

        pixmap = QPixmap(file_path) if file_path and os.path.exists(file_path) else QPixmap()
        if pixmap.isNull():
            placeholder = QPixmap(900, 600)
            placeholder.fill(Qt.GlobalColor.transparent)
            self.image_view.set_pixmap(placeholder)
        else:
            self.image_view.set_pixmap(pixmap)

        self.prev_button.setVisible(len(self.items) > 1)
        self.next_button.setVisible(len(self.items) > 1)

    def show_previous(self):
        if len(self.items) < 2:
            return
        self.current_index = (self.current_index - 1) % len(self.items)
        self.load_current()

    def show_next(self):
        if len(self.items) < 2:
            return
        self.current_index = (self.current_index + 1) % len(self.items)
        self.load_current()

    def download_current(self):
        item = self.items[self.current_index]
        source = item.get("file_url", "")
        if not source or not os.path.exists(source):
            QMessageBox.warning(self, "Файл недоступен", "Исходный файл не найден.")
            return
        target, _ = QFileDialog.getSaveFileName(self, "Сохранить фото", item.get("file_name") or "photo.jpg")
        if not target:
            return
        try:
            shutil.copy2(source, target)
        except OSError as exc:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить файл: {exc}")

    def mousePressEvent(self, event):
        self._swipe_start = event.position().toPoint()
        if not self.content.geometry().contains(self._swipe_start):
            self.reject()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        delta = event.position().toPoint() - self._swipe_start
        if abs(delta.x()) > 80 and abs(delta.x()) > abs(delta.y()):
            if delta.x() > 0:
                self.show_previous()
            else:
                self.show_next()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.show_previous()
            return
        if event.key() == Qt.Key.Key_Right:
            self.show_next()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)
