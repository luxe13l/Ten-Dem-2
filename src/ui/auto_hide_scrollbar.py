"""Auto-hiding scrollbar widgets."""

from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, QTimer, Qt
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QScrollBar


class AutoHideScrollBar(QScrollBar):
    def __init__(self, orientation=Qt.Orientation.Vertical, parent=None):
        super().__init__(orientation, parent)
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._animation = QPropertyAnimation(self._opacity, b"opacity", self)
        self._animation.setDuration(180)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(700)
        self._hide_timer.timeout.connect(self.fade_out)

        self.valueChanged.connect(self.reveal_temporarily)
        self.rangeChanged.connect(lambda *_: self.fade_out())
        self.sliderPressed.connect(self.show_now)
        self.sliderReleased.connect(self.reveal_temporarily)

    def show_now(self):
        self._hide_timer.stop()
        self._animation.stop()
        self._opacity.setOpacity(1.0)

    def reveal_temporarily(self):
        if self.maximum() <= 0:
            self.fade_out()
            return
        self._animation.stop()
        self._animation.setStartValue(self._opacity.opacity())
        self._animation.setEndValue(1.0)
        self._animation.start()
        self._hide_timer.start()

    def fade_out(self):
        self._hide_timer.stop()
        self._animation.stop()
        self._animation.setStartValue(self._opacity.opacity())
        self._animation.setEndValue(0.0)
        self._animation.start()
