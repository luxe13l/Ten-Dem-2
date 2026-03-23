"""Message bubble widget."""
from __future__ import annotations
import os
from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QPoint, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QPainter, QPainterPath, QPixmap
from PyQt6.QtWidgets import QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from src.database.messages_db import QUICK_REACTIONS
from src.models.message import Message, MessageStatus, MessageType
from src.styles import FONT_FAMILY
from src.styles.themes import get_theme_colors

class ClickableLabel(QLabel):
    """Лейбл, который эмитит сигнал при клике."""
    clicked = pyqtSignal()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        # Важно: вызываем базовый метод, чтобы текст всё ещё можно было выделять мышкой, если нужно
        super().mousePressEvent(event)

class MessageBubble(QWidget):
    clicked = pyqtSignal(str)
    photo_requested = pyqtSignal(str)
    reaction_clicked = pyqtSignal(str, str)
    context_menu_requested = pyqtSignal(QPoint)
    
    def __init__(self, message: Message, is_own: bool, current_user_uid: str = "", theme_name: str = "dark", parent=None):
        super().__init__(parent)
        self.message = message
        self.is_own = is_own
        self.current_user_uid = current_user_uid
        self.theme_name = theme_name or "dark"
        self.colors = get_theme_colors(self.theme_name)
        self._animation: QPropertyAnimation | None = None
        self.build_ui()
        self.refresh()
        self.play_appear_animation()
 
    def build_ui(self):
        self.setStyleSheet("background: transparent;")
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.root.setSpacing(0)

        self.row = QHBoxLayout()
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(8)
        if self.is_own:
            self.row.addStretch()

        # Контейнер для сообщения + реакции
        self.bubble_container = QWidget()
        self.bubble_container.setStyleSheet("background: transparent;")
        self.bubble_layout = QVBoxLayout(self.bubble_container)
        self.bubble_layout.setContentsMargins(0, 0, 0, 0)
        self.bubble_layout.setSpacing(0)

        self.card = QFrame()
        self.card.setMaximumWidth(560)
        self.card.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.card.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.card.customContextMenuRequested.connect(lambda pos: self._forward_context_menu(self.card, pos))
        
        # Контейнер для контента сообщения + реакции внутри
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(0)
        
        self.bubble_layout.addWidget(self.card)
        self.row.addWidget(self.bubble_container)
        if not self.is_own:
            self.row.addStretch()

        self.selection_badge = QLabel("✓")
        self.selection_badge.setFixedSize(24, 24)
        self.selection_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.row.addWidget(self.selection_badge, 0, Qt.AlignmentFlag.AlignBottom)
        self.root.addLayout(self.row)

        # Контент сообщения
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(16, 12, 16, 12)
        self.content_layout.setSpacing(8)
        self.card_layout.addLayout(self.content_layout)

        self.forwarded_label = QLabel()
        self.forwarded_label.hide()
        self.forwarded_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.forwarded_label.customContextMenuRequested.connect(lambda pos: self._forward_context_menu(self.forwarded_label, pos))
        self.content_layout.addWidget(self.forwarded_label)

        self.photo_label = ClickableLabel()
        self.photo_label.setMinimumSize(240, 140)
        self.photo_label.setMaximumSize(360, 260)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.photo_label.clicked.connect(lambda: self.photo_requested.emit(self.message.id))
        self.photo_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.photo_label.customContextMenuRequested.connect(lambda pos: self._forward_context_menu(self.photo_label, pos))
        self.photo_label.hide()
        self.content_layout.addWidget(self.photo_label)

        # ✅ ИСПРАВЛЕНИЕ: Используем ClickableLabel для текста и подключаем сигнал
        self.content_label = ClickableLabel()
        self.content_label.setWordWrap(True)
        self.content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.content_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.content_label.customContextMenuRequested.connect(lambda pos: self._forward_context_menu(self.content_label, pos))
        # Теперь клик по тексту тоже вызывает общий клик пузыря
        self.content_label.clicked.connect(lambda: self.clicked.emit(self.message.id))
        self.content_layout.addWidget(self.content_label)

        self.poll_label = QLabel()
        self.poll_label.setWordWrap(True)
        self.poll_label.hide()
        self.poll_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.poll_label.customContextMenuRequested.connect(lambda pos: self._forward_context_menu(self.poll_label, pos))
        self.content_layout.addWidget(self.poll_label)

        self.meta_label = QLabel()
        self.meta_label.setAlignment(Qt.AlignmentFlag.AlignRight if self.is_own else Qt.AlignmentFlag.AlignLeft)
        self.meta_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.meta_label.customContextMenuRequested.connect(lambda pos: self._forward_context_menu(self.meta_label, pos))
        self.content_layout.addWidget(self.meta_label)

        # Реакции — ВНУТРИ карточки сообщения (в правом нижнем углу)
        self.reactions_wrap = QWidget()
        self.reactions_wrap.setStyleSheet("background: transparent;")
        self.reactions_row = QHBoxLayout(self.reactions_wrap)
        self.reactions_row.setContentsMargins(8, 4, 8, 8)
        self.reactions_row.setSpacing(4)
        self.reactions_wrap.hide()
        self.card_layout.addWidget(self.reactions_wrap, 0, Qt.AlignmentFlag.AlignRight)

    def mousePressEvent(self, event):
        # Клик по пустому месту внутри пузыря тоже выбирает сообщение
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.message.id)
        super().mousePressEvent(event)

    def _forward_context_menu(self, widget: QWidget, pos: QPoint):
        global_pos = widget.mapToGlobal(pos)
        local_pos = self.mapFromGlobal(global_pos)
        self.context_menu_requested.emit(local_pos)

    def refresh(self):
        self.colors = get_theme_colors(self.theme_name)
        
        # ЦВЕТА СООБЩЕНИЙ — тёмно-серые
        bg = self.colors["message_own_bg"] if self.is_own else self.colors["message_other_bg"]
        text = self.colors.get("message_own_text", "#FFFFFF") if self.is_own else self.colors.get("message_other_text", self.colors["text_primary"])
        meta = self.colors.get("message_meta_own", "#8B8B90") if self.is_own else self.colors["text_tertiary"]
        
        if self.is_own and self.message.status == MessageStatus.READ:
            meta_color = self.colors.get("read_check", "#57B58A")
        elif self.is_own and self.message.status == MessageStatus.DELIVERED:
            meta_color = self.colors.get("delivered_check", "#8A8A92")
        else:
            meta_color = meta

        # ✅ УБРАЛИ ОБВОДКУ. Вместо неё меняем фон при выделении.
        if self.message.is_selected:
            bg = self.colors["bg_tertiary"] 
        
        self.card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg};
                border-radius: 22px;
                border: none;
            }}
            """
        )
        self.content_label.setStyleSheet(f"color: {text}; font-size: 15px; font-family: {FONT_FAMILY}; background: transparent;")
        self.meta_label.setStyleSheet(f"color: {meta_color}; font-size: 11px; font-family: {FONT_FAMILY}; background: transparent;")
        self.forwarded_label.setStyleSheet(f"color: {meta}; font-size: 11px; font-family: {FONT_FAMILY}; background: transparent;")
        self.poll_label.setStyleSheet(
            f"color: {text}; font-size: 13px; font-family: {FONT_FAMILY}; background-color: rgba(255,255,255,0.04); border-radius: 22px; padding: 10px 12px;"
        )
        
        # Скрываем бейджик выделения, так как теперь используем изменение фона
        self.selection_badge.setVisible(False) 

        self.forwarded_label.setVisible(bool(self.message.forwarded_from_uid))
        if self.message.forwarded_from_uid:
            self.forwarded_label.setText("Пересланное сообщение")

        self.content_label.setText(self._content_text())
        self.meta_label.setText(self._meta_text())
        self._refresh_photo_preview()
        self._refresh_poll()
        self._refresh_reactions()

    def update_message(self, message: Message):
        self.message = message
        self.refresh()

    def set_selection_state(self, enabled: bool, selected: bool):
        self.message.selection_enabled = enabled
        self.message.is_selected = selected
        self.refresh()

    def _refresh_photo_preview(self):
        should_show = self.message.message_type in {MessageType.PHOTO, MessageType.VIDEO}
        self.photo_label.setVisible(should_show)
        if not should_show:
            return

        source = self.message.file_url
        if source and os.path.exists(source):
            pixmap = QPixmap(source)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    QSize(320, 220),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.photo_label.setStyleSheet("background: transparent;")
                self.photo_label.setText("")
                self.photo_label.setPixmap(self._rounded_pixmap(scaled, 28))
                return

        self.photo_label.setText("Открыть медиа")
        self.photo_label.setPixmap(QPixmap())
        self.photo_label.setStyleSheet(
            f"background-color: {self.colors.get('message_media_placeholder_bg', 'rgba(255,255,255,0.06)')}; color: {self.colors['text_primary']}; border-radius: 28px;"
        )

    def _rounded_pixmap(self, pixmap: QPixmap, radius: int) -> QPixmap:
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rounded.rect()), radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        return rounded

    def _refresh_poll(self):
        if self.message.message_type != MessageType.POLL:
            self.poll_label.hide()
            return
        options = "\n".join(f"• {option}" for option in self.message.poll_options)
        self.poll_label.setText(options)
        self.poll_label.show()

    def _refresh_reactions(self):
        while self.reactions_row.count():
            item = self.reactions_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        reactions = self.message.reactions or {}
        
        # Группируем: один юзер = одна реакция
        user_reactions = {}
        for emoji, users in reactions.items():
            for user_uid in users:
                if user_uid not in user_reactions:
                    user_reactions[user_uid] = emoji
        
        # Считаем по эмодзи
        grouped = {}
        for user_uid, emoji in user_reactions.items():
            if emoji not in grouped:
                grouped[emoji] = []
            grouped[emoji].append(user_uid)

        visible = False
        for emoji, users in grouped.items():
            if not users:
                continue
            visible = True
            
            user_has_reaction = self.current_user_uid in users
            
            # ПОЛНОСТЬЮ ЗАКРУГЛЁННАЯ КАПСУЛА — ПОЧТИ ПРОЗРАЧНАЯ С СЕРЫМ ОТТЕНКОМ
            button = QPushButton(f"{emoji} {len(users)}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {'rgba(50, 50, 50, 0.5)' if user_has_reaction else 'rgba(40, 40, 40, 0.35)'};
                    color: {self.colors['text_primary']};
                    border: 1px solid {'rgba(80, 80, 80, 0.5)' if user_has_reaction else 'rgba(60, 60, 60, 0.3)'};
                    border-radius: 999px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {'rgba(60, 60, 60, 0.6)' if user_has_reaction else 'rgba(50, 50, 50, 0.45)'};
                }}
                """
            )
            button.setFixedHeight(24)
            button.clicked.connect(lambda _, value=emoji: self.reaction_clicked.emit(self.message.id, value))
            self.reactions_row.addWidget(button)
        
        self.reactions_wrap.setVisible(visible)

    def play_appear_animation(self):
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        self._animation = QPropertyAnimation(effect, b"opacity", self)
        self._animation.setDuration(180)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation.finished.connect(lambda: self.setGraphicsEffect(None))
        self._animation.start()

    def _content_text(self):
        if self.message.message_type == MessageType.PHOTO:
            return self.message.text or self.message.file_name or "Фото"
        if self.message.message_type == MessageType.FILE:
            return f"Файл: {self.message.file_name or self.message.text}".strip()
        if self.message.message_type == MessageType.VOICE:
            return "Голосовое сообщение"
        if self.message.message_type == MessageType.VIDEO:
            return self.message.text or "Видео"
        if self.message.message_type == MessageType.POLL:
            return self.message.text
        return self.message.text

    def _meta_text(self):
        parts = [self.message.timestamp.strftime("%H:%M")]
        if self.message.is_edited:
            parts.append("изменено")
        if self.is_own:
            parts.append("✓✓" if self.message.status in (MessageStatus.READ, MessageStatus.DELIVERED) else "✓")
        return "  ".join(parts)