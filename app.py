#!/usr/bin/env python3
"""
Speech Therapy Application — Built with PySide6
Features: Sound Practice, Tongue Twisters, Breathing Exercises,
          Minimal Pairs, Progress Tracking, Audio Recording & Waveform
"""

import sys
import json
import os
import math
import random
from datetime import datetime, timedelta
from collections import defaultdict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QProgressBar, QComboBox, QTextEdit, QScrollArea,
    QFrame, QGridLayout, QSizePolicy, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer, QSize, QRectF, QPointF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QFont, QLinearGradient,
    QRadialGradient, QPainterPath
)

import numpy as np

try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

# ─────────────────────── DATA ───────────────────────

PHONEMES = {
    "R Sound": {
        "description": "Practice the /r/ sound in different word positions",
        "initial": ["red", "run", "rain", "ring", "rope", "rabbit", "rocket", "rainbow", "ruler", "river"],
        "medial": ["carrot", "parrot", "forest", "orange", "garage", "mirror", "zero", "cherry"],
        "final": ["car", "star", "door", "bear", "fire", "four", "hair", "jar"],
        "sentences": ["The red rabbit ran rapidly.", "Rain falls on the roof.", "Roses are red and pretty."]
    },
    "S Sound": {
        "description": "Practice the /s/ sound in different word positions",
        "initial": ["sun", "sit", "sand", "sing", "soap", "snake", "spider", "star", "swing", "school"],
        "medial": ["basket", "castle", "glasses", "monster", "pencil", "dinosaur", "whisper", "listen"],
        "final": ["bus", "glass", "grass", "mouse", "nose", "rice", "dress", "horse"],
        "sentences": ["Six silly snakes slithered.", "The sun shines brightly.", "Sally sells sea shells."]
    },
    "L Sound": {
        "description": "Practice the /l/ sound in different word positions",
        "initial": ["lamp", "leaf", "lion", "lock", "look", "love", "lucky", "lemon", "ladder", "lady"],
        "medial": ["balloon", "yellow", "elephant", "pillow", "jelly", "flower", "glasses", "bubble"],
        "final": ["ball", "bell", "fall", "hill", "pool", "smile", "tall", "wall"],
        "sentences": ["Lily loves lemon lollipops.", "Look at the little lamp.", "The balloon flew over the hill."]
    },
    "TH Sound": {
        "description": "Practice the /th/ sound (voiced and voiceless)",
        "initial": ["think", "three", "thumb", "thorn", "thick", "thin", "thirsty", "thought", "thousand", "Thursday"],
        "medial": ["bathroom", "birthday", "earthquake", "something", "anything", "nothing", "toothbrush", "weather"],
        "final": ["bath", "both", "cloth", "math", "mouth", "north", "south", "teeth"],
        "sentences": ["Three thick thistles throbbed.", "Think about this Thursday.", "My thumb is thicker than yours."]
    },
    "SH Sound": {
        "description": "Practice the /sh/ sound in different word positions",
        "initial": ["shoe", "ship", "shop", "shut", "shark", "sheep", "shell", "shirt", "shine", "shower"],
        "medial": ["ocean", "nation", "station", "motion", "special", "mushroom", "sunshine", "fraction"],
        "final": ["fish", "dish", "wash", "brush", "push", "splash", "crash", "flash"],
        "sentences": ["She sells seashells by the shore.", "The sheep was shy and shook.", "Shut the door and wash the dish."]
    },
    "CH Sound": {
        "description": "Practice the /ch/ sound in different word positions",
        "initial": ["chair", "change", "charm", "chase", "cheap", "cheese", "cherry", "chicken", "children", "chocolate"],
        "medial": ["kitchen", "teacher", "picture", "nature", "feature", "furniture", "adventure", "creature"],
        "final": ["beach", "bench", "branch", "catch", "lunch", "match", "peach", "watch"],
        "sentences": ["Children chase each other on the beach.", "The teacher chose chocolate cheese.", "Charles chose a cherry for lunch."]
    },
    "K Sound": {
        "description": "Practice the /k/ sound in different word positions",
        "initial": ["cake", "call", "came", "cap", "car", "card", "care", "cat", "key", "king"],
        "medial": ["bacon", "baker", "bucket", "chicken", "jacket", "market", "monkey", "pocket"],
        "final": ["back", "book", "cake", "clock", "cook", "duck", "lake", "milk"],
        "sentences": ["The cat caught a cake.", "Cathy can cook chicken.", "King Carl came to the castle."]
    },
    "G Sound": {
        "description": "Practice the /g/ sound in different word positions",
        "initial": ["game", "gate", "get", "girl", "give", "go", "goat", "good", "grass", "green"],
        "medial": ["august", "beggar", "eagle", "hungry", "jaguar", "letter", "legal", "tiger"],
        "final": ["bag", "big", "bug", "dig", "dog", "egg", "flag", "frog"],
        "sentences": ["The green frog grabbed a bug.", "Gary gave a good game.", "A big goat got out of the gate."]
    },
}

TONGUE_TWISTERS = {
    "Easy": [
        "Red lorry, yellow lorry.",
        "Six sleek swans swam swiftly southwards.",
        "She sees cheese.",
        "Four fine fresh fish for you.",
        "Which wristwatches are Swiss wristwatches?",
        "Unique New York, unique New York.",
        "A proper copper coffee pot.",
        "Good blood, bad blood.",
    ],
    "Medium": [
        "Peter Piper picked a peck of pickled peppers.",
        "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
        "She sells seashells by the seashore.",
        "Fuzzy Wuzzy was a bear. Fuzzy Wuzzy had no hair.",
        "I saw Susie sitting in a shoeshine shop.",
        "Can you can a canned can into an uncanned can?",
        "A proper copper coffee pot.",
        "The sixth sick sheikh's sixth sheep's sick.",
    ],
    "Hard": [
        "The thirty-three thieves thought that they thrilled the throne throughout Thursday.",
        "A skunk sat on a stump and thunk the stump stunk, but the stump thunk the skunk stunk.",
        "Betty Botter bought some butter, but she said the butter's bitter.",
        "How many boards could the Mongols hoard if the Mongol hordes got bored?",
        "Pad kid poured curd pulled cod.",
        "A Tudor who tooted a flute tried to tutor two tooters to toot.",
        "The myth of Miss Muffet's mutual mirth.",
        "Six thick thistle sticks. Six thick thistles stick.",
    ]
}

MINIMAL_PAIRS = {
    "R vs L": [
        ("right", "light"), ("red", "led"), ("ray", "lay"),
        ("rip", "lip"), ("rock", "lock"), ("ring", "ling"),
        ("rake", "lake"), ("rove", "love"), ("road", "load"),
        ("rot", "lot"), ("rust", "lust"), ("rail", "lail"),
    ],
    "S vs SH": [
        ("see", "she"), ("sip", "ship"), ("sew", "show"),
        ("same", "shame"), ("sell", "shell"), ("save", "shave"),
        ("self", "shelf"), ("sop", "shop"), ("sign", "shine"),
        ("sore", "shore"), ("suit", "shoot"), ("mass", "mash"),
    ],
    "S vs TH": [
        ("sink", "think"), ("sick", "thick"), ("sin", "thin"),
        ("mass", "math"), ("pass", "path"), ("moss", "moth"),
        ("face", "faith"), ("worse", "worth"), ("tense", "tenth"),
        ("force", "forth"), ("guess", "guest"), ("sort", "thought"),
    ],
    "F vs V": [
        ("fan", "van"), ("fine", "vine"), ("fail", "veil"),
        ("fat", "vat"), ("few", "view"), ("leaf", "leave"),
        ("safe", "save"), ("proof", "prove"), ("belief", "believe"),
        ("half", "have"), ("calf", "calve"), ("life", "live"),
    ],
    "CH vs SH": [
        ("chin", "shin"), ("chain", "sheen"), ("chip", "ship"),
        ("cheap", "sheep"), ("choose", "shoes"), ("chop", "shop"),
        ("cheer", "shear"), ("match", "mash"), ("rich", "rish"),
        ("batch", "bash"), ("wrench", "rens"), ("watch", "wash"),
    ],
    "P vs B": [
        ("pat", "bat"), ("pin", "bin"), ("park", "bark"),
        ("pig", "big"), ("pear", "bear"), ("pit", "bit"),
        ("pack", "back"), ("peach", "beach"), ("puff", "buff"),
        ("cap", "cab"), ("rope", "robe"), ("tap", "tab"),
    ],
}

# ─────────────────────── STYLESHEET ───────────────────────

STYLESHEET = """
QMainWindow { background-color: #f0f4f8; }
QLabel { color: #2d3748; }

QPushButton {
    background-color: #4299e1; color: white; border: none;
    border-radius: 8px; padding: 10px 20px;
    font-size: 14px; font-weight: bold;
}
QPushButton:hover { background-color: #3182ce; }
QPushButton:pressed { background-color: #2b6cb0; }

QPushButton#navButton {
    background-color: transparent; color: #a0aec0; border: none;
    border-radius: 12px; padding: 12px 16px; text-align: left;
    font-size: 14px; font-weight: normal;
}
QPushButton#navButton:hover { background-color: rgba(66,153,225,0.1); color: #4299e1; }
QPushButton#navButton:checked { background-color: rgba(66,153,225,0.15); color: #4299e1; font-weight: bold; }

QPushButton#categoryButton {
    background-color: white; color: #4a5568; border: 2px solid #e2e8f0;
    border-radius: 12px; padding: 12px; font-size: 14px; min-height: 40px;
}
QPushButton#categoryButton:hover { border-color: #4299e1; color: #4299e1; background-color: #ebf8ff; }
QPushButton#categoryButton:checked { border-color: #4299e1; color: #4299e1; background-color: #ebf8ff; }

QPushButton#recordButton {
    background-color: #e53e3e; color: white; border: none; border-radius: 50%;
    padding: 0; min-width: 64px; max-width: 64px; min-height: 64px; max-height: 64px; font-size: 24px;
}
QPushButton#recordButton:hover { background-color: #c53030; }

QPushButton#successBtn { background-color: #48bb78; color: white; border-radius: 8px; padding: 10px 20px; font-size: 13px; }
QPushButton#successBtn:hover { background-color: #38a169; }
QPushButton#closeBtn   { background-color: #ecc94b; color: white; border-radius: 8px; padding: 10px 20px; font-size: 13px; }
QPushButton#closeBtn:hover   { background-color: #d69e2e; }
QPushButton#retryBtn   { background-color: #e53e3e; color: white; border-radius: 8px; padding: 10px 20px; font-size: 13px; }
QPushButton#retryBtn:hover   { background-color: #c53030; }

QGroupBox {
    background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;
    margin-top: 12px; padding: 16px; padding-top: 28px;
    font-size: 14px; font-weight: bold; color: #4a5568;
}
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 8px; color: #2d3748; }

QListWidget {
    background-color: white; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 8px; outline: none;
}
QListWidget::item { padding: 10px; border-radius: 8px; color: #4a5568; }
QListWidget::item:selected { background-color: #ebf8ff; color: #2b6cb0; }
QListWidget::item:hover { background-color: #f7fafc; }

QComboBox {
    background-color: white; border: 2px solid #e2e8f0; border-radius: 8px;
    padding: 8px 16px; min-width: 120px; color: #4a5568;
}
QComboBox:hover { border-color: #4299e1; }
QComboBox::drop-down { border: none; }

QSlider::groove:horizontal { height: 8px; background: #e2e8f0; border-radius: 4px; }
QSlider::handle:horizontal { background: #4299e1; width: 20px; height: 20px; margin: -6px 0; border-radius: 10px; }

QProgressBar {
    background-color: #e2e8f0; border: none; border-radius: 6px;
    text-align: center; color: #4a5568; font-weight: bold; height: 22px;
}
QProgressBar::chunk { background-color: #48bb78; border-radius: 6px; }

QScrollArea { border: none; background-color: transparent; }

QTextEdit {
    background-color: white; border: 2px solid #e2e8f0; border-radius: 12px;
    padding: 16px; color: #2d3748; font-size: 20px;
}

QSpinBox {
    background-color: white; border: 2px solid #e2e8f0; border-radius: 8px;
    padding: 6px 10px; color: #4a5568; min-width: 80px;
}
QSpinBox:hover { border-color: #4299e1; }
"""

# ─────────────────────── CUSTOM WIDGETS ───────────────────────


class WaveformWidget(QWidget):
    """Displays a live audio waveform."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data = np.array([])
        self.setMinimumHeight(120)
        self.setMaximumHeight(160)

    def set_data(self, data):
        self.audio_data = data
        self.update()

    def clear(self):
        self.audio_data = np.array([])
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor("#1a202c"))
        painter.setPen(QPen(QColor("#2d3748"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)

        center_y = self.height() / 2
        painter.setPen(QPen(QColor("#4a5568"), 1, Qt.DashLine))
        painter.drawLine(0, int(center_y), self.width(), int(center_y))

        if len(self.audio_data) > 0:
            pen = QPen(QColor("#4299e1"), 2)
            painter.setPen(pen)
            w, h = self.width(), self.height()
            step = max(1, len(self.audio_data) // w)
            points = []
            for i in range(0, min(len(self.audio_data), w * step), step):
                x = (i / len(self.audio_data)) * w
                y = center_y + self.audio_data[i] * (h * 0.4)
                points.append(QPointF(x, y))

            if len(points) > 1:
                path = QPainterPath()
                path.moveTo(points[0])
                for p in points[1:]:
                    path.lineTo(p)

                fill_path = QPainterPath(path)
                fill_path.lineTo(points[-1].x(), center_y)
                fill_path.lineTo(points[0].x(), center_y)
                fill_path.closeSubpath()

                gradient = QLinearGradient(0, 0, 0, h)
                gradient.setColorAt(0, QColor(66, 153, 225, 100))
                gradient.setColorAt(0.5, QColor(66, 153, 225, 30))
                gradient.setColorAt(1, QColor(66, 153, 225, 100))

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(gradient))
                painter.drawPath(fill_path)

                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(path)

        # Placeholder text
        if len(self.audio_data) == 0:
            painter.setPen(QColor("#718096"))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             "Record your voice to see the waveform")

        painter.end()


class BreathingCircle(QWidget):
    """Animated breathing guide — expands / holds / contracts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.phase = 0
        self.scale = 0.5
        self.animating = False
        self.breath_text = "Press Start"
        self.breath_timer = 0
        self.inhale_time = 4
        self.hold_time = 4
        self.exhale_time = 6
        self.cycle_count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)

    def start(self):
        self.animating = True
        self.phase = 0
        self.breath_timer = 0
        self.breath_text = "Breathe In"
        self.cycle_count = 0
        self.timer.start(50)
        self.update()

    def stop(self):
        self.animating = False
        self.timer.stop()
        self.scale = 0.5
        self.breath_text = "Press Start"
        self.update()

    def _ease(self, t):
        return t * t * (3 - 2 * t)

    def _animate(self):
        self.breath_timer += 50
        if self.phase == 0:
            progress = min(self.breath_timer / (self.inhale_time * 1000), 1.0)
            self.scale = 0.5 + 0.5 * self._ease(progress)
            remaining = max(0, self.inhale_time - self.breath_timer / 1000)
            self.breath_text = f"Breathe In\n{remaining:.1f}s"
            if progress >= 1.0:
                self.phase = 1
                self.breath_timer = 0
        elif self.phase == 1:
            self.scale = 1.0
            remaining = max(0, self.hold_time - self.breath_timer / 1000)
            self.breath_text = f"Hold\n{remaining:.1f}s"
            if progress := min(self.breath_timer / (self.hold_time * 1000), 1.0) >= 1.0:
                self.phase = 2
                self.breath_timer = 0
        elif self.phase == 2:
            progress = min(self.breath_timer / (self.exhale_time * 1000), 1.0)
            self.scale = 1.0 - 0.5 * self._ease(progress)
            remaining = max(0, self.exhale_time - self.breath_timer / 1000)
            self.breath_text = f"Breathe Out\n{remaining:.1f}s"
            if progress >= 1.0:
                self.phase = 0
                self.breath_timer = 0
                self.cycle_count += 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        base_r = min(self.width(), self.height()) / 2 - 30

        phase_colors = [QColor("#4299e1"), QColor("#ed8936"), QColor("#48bb78")]
        color = phase_colors[self.phase] if self.animating else QColor("#a0aec0")

        # Glow rings
        for i in range(6):
            r = base_r * self.scale + i * 4
            gc = QColor(color)
            gc.setAlpha(max(0, 35 - i * 6))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gc))
            painter.drawEllipse(QPointF(cx, cy), r, r)

        # Main circle
        gradient = QRadialGradient(cx, cy, base_r * self.scale)
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 200))
        gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 60))
        painter.setPen(QPen(color, 3))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(cx, cy), base_r * self.scale, base_r * self.scale)

        # Text
        painter.setPen(QColor("#2d3748"))
        for i, line in enumerate(self.breath_text.split("\n")):
            fsize = 16 if i == 0 else 12
            weight = QFont.Bold if i == 0 else QFont.Normal
            painter.setFont(QFont("Segoe UI", fsize, weight))
            y_off = -15 + i * 28
            painter.drawText(QRectF(cx - 120, cy + y_off - 14, 240, 28),
                             Qt.AlignCenter, line)

        # Cycle counter
        if self.animating:
            painter.setPen(QColor("#718096"))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(QRectF(cx - 60, cy + base_r * self.scale + 10, 120, 24),
                             Qt.AlignCenter, f"Cycle {self.cycle_count + 1}")
        painter.end()


class BarChartWidget(QWidget):
    """Custom-painted bar chart for the Progress page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self.title = "Practice History"
        self.setMinimumHeight(260)

    def set_data(self, data, title="Practice History"):
        self.data = data
        self.title = title
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))
        painter.setPen(QPen(QColor("#e2e8f0"), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)

        # Title
        painter.setPen(QColor("#2d3748"))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(20, 32, self.title)

        ml, mr, mt, mb = 50, 20, 50, 40
        cx, cy = ml, mt
        cw = self.width() - ml - mr
        ch = self.height() - mt - mb
        if cw <= 0 or ch <= 0 or not self.data:
            painter.end()
            return

        max_val = max(self.data.values()) if self.data else 1
        if max_val == 0:
            max_val = 1

        # Grid
        painter.setPen(QPen(QColor("#edf2f7"), 1, Qt.DotLine))
        for i in range(5):
            y = cy + ch - (i / 4) * ch
            painter.drawLine(int(cx), int(y), int(cx + cw), int(y))
            painter.setPen(QColor("#a0aec0"))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(0, int(y) - 8, ml - 6, 20,
                             Qt.AlignRight | Qt.AlignVCenter, str(int(max_val * i / 4)))
            painter.setPen(QPen(QColor("#edf2f7"), 1, Qt.DotLine))

        bar_colors = [QColor("#4299e1"), QColor("#48bb78"), QColor("#ed8936"),
                      QColor("#9f7aea"), QColor("#f56565"), QColor("#38b2ac"), QColor("#ecc94b")]
        n = len(self.data)
        bw = min(56, (cw - (n + 1) * 10) / n)
        total_w = n * bw + (n + 1) * 10
        sx = cx + (cw - total_w) / 2 + 10

        for i, (label, value) in enumerate(self.data.items()):
            bh = (value / max_val) * ch if max_val > 0 else 0
            x = sx + i * (bw + 10)
            y = cy + ch - bh

            color = bar_colors[i % len(bar_colors)]
            grad = QLinearGradient(x, y, x, cy + ch)
            grad.setColorAt(0, color)
            grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 130))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(x, y, bw, max(bh, 0)), 4, 4)

            painter.setPen(QColor("#4a5568"))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(QRectF(x, y - 18, bw, 18), Qt.AlignCenter, str(value))

            painter.setPen(QColor("#718096"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(x - 5, cy + ch + 5, bw + 10, 28),
                             Qt.AlignCenter, label)
        painter.end()


# ─────────────────────── PAGES ───────────────────────


class DashboardPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build()

    def _stat_card(self, emoji, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background-color: white; border: 1px solid #e2e8f0;
            border-radius: 12px; border-left: 4px solid {color}; }}""")
        lo = QVBoxLayout(card)
        lo.setSpacing(4)
        lo.setContentsMargins(16, 14, 16, 14)
        e = QLabel(emoji); e.setFont(QFont("Segoe UI", 22)); lo.addWidget(e)
        t = QLabel(title); t.setFont(QFont("Segoe UI", 11)); t.setStyleSheet("color:#718096;"); lo.addWidget(t)
        v = QLabel(value); v.setFont(QFont("Segoe UI", 20, QFont.Bold)); v.setStyleSheet(f"color:{color};")
        v.setObjectName("val"); lo.addWidget(v)
        return card

    def _build(self):
        lo = QVBoxLayout(self); lo.setSpacing(18); lo.setContentsMargins(32, 24, 32, 24)

        lo.addWidget(self._title("Welcome to Speech Therapy", 28))
        lo.addWidget(self._subtitle("Practice consistently for the best results. Track your progress below."))

        # Stats row
        stats = QHBoxLayout(); stats.setSpacing(14)
        card_defs = [
            ("🎯", "Today", "0 min", "#4299e1"),
            ("📅", "This Week", "0 min", "#48bb78"),
            ("🔥", "Streak", "0 days", "#ed8936"),
            ("⭐", "Sessions", "0", "#9f7aea"),
        ]
        self.stat_cards = []
        for e, t, v, c in card_defs:
            card = self._stat_card(e, t, v, c)
            stats.addWidget(card)
            self.stat_cards.append((card, t, c))
        lo.addLayout(stats)

        # Daily goal
        g = QGroupBox("Daily Goal"); gl = QVBoxLayout(g)
        self.goal_label = QLabel("0 / 15 minutes"); self.goal_label.setFont(QFont("Segoe UI", 12))
        self.goal_bar = QProgressBar(); self.goal_bar.setRange(0, 100); self.goal_bar.setValue(0)
        gl.addWidget(self.goal_label); gl.addWidget(self.goal_bar)
        lo.addWidget(g)

        # Quick tips
        tips = QGroupBox("Tips for Effective Practice")
        tips_lo = QVBoxLayout(tips)
        tips_lo.addWidget(QLabel(
            "• Practice for at least 15 minutes daily\n"
            "• Start with slow, accurate productions before speed\n"
            "• Record yourself to track improvement\n"
            "• Take breaks — fatigue reduces accuracy\n"
            "• Use a mirror to check mouth positioning"))
        lo.addWidget(tips)
        lo.addStretch()

    @staticmethod
    def _title(text, size=24):
        l = QLabel(text); l.setFont(QFont("Segoe UI", size, QFont.Bold))
        l.setStyleSheet("color:#2d3748;"); return l

    @staticmethod
    def _subtitle(text):
        l = QLabel(text); l.setFont(QFont("Segoe UI", 12))
        l.setStyleSheet("color:#718096;"); return l

    def refresh(self):
        today = datetime.now().strftime("%Y-%m-%d")
        today_min = self.app_state.get_daily_minutes(today)
        week_min = sum(self.app_state.get_daily_minutes(d) for d in self.app_state.session_log)
        streak = self.app_state.get_streak()
        total = sum(len(v) for v in self.app_state.session_log.values())

        vals = [f"{today_min:.0f} min", f"{week_min:.0f} min", f"{streak} days", str(total)]
        for i, (card, _, _) in enumerate(self.stat_cards):
            v = card.findChild(QLabel, "val")
            if v:
                v.setText(vals[i])

        goal = 15
        self.goal_label.setText(f"{today_min:.0f} / {goal} minutes")
        self.goal_bar.setValue(min(int((today_min / goal) * 100), 100))


class SoundPracticePage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.cur_phoneme = None
        self.cur_pos = "initial"
        self.cur_idx = 0
        self.is_recording = False
        self.rec_data = []
        self.rec_stream = None
        self.practice_results = []
        self.session_start = None
        self._build()

    def _build(self):
        top = QHBoxLayout(self); top.setSpacing(20); top.setContentsMargins(32, 24, 32, 24)

        # Left: phoneme list
        left = QVBoxLayout(); left.setSpacing(8)
        left.addWidget(self._label("Sound Practice", 24))
        left.addWidget(self._label("Select a sound to practice:", 12, "#718096"))

        self.phoneme_list = QListWidget()
        self.phoneme_list.setMinimumWidth(210)
        for name in PHONEMES:
            item = QListWidgetItem(f"🔊  {name}")
            item.setData(Qt.UserRole, name)
            self.phoneme_list.addItem(item)
        self.phoneme_list.currentItemChanged.connect(self._on_phoneme)
        left.addWidget(self.phoneme_list)
        top.addLayout(left, 1)

        # Right: practice area
        right = QVBoxLayout(); right.setSpacing(14)
        self.desc_lbl = QLabel("Select a sound from the list to begin practicing.")
        self.desc_lbl.setFont(QFont("Segoe UI", 13)); self.desc_lbl.setStyleSheet("color:#718096;")
        self.desc_lbl.setWordWrap(True); right.addWidget(self.desc_lbl)

        # Position buttons
        plo = QHBoxLayout()
        self.pos_btns = {}
        for p in ["initial", "medial", "final", "sentences"]:
            b = QPushButton(p.capitalize()); b.setCheckable(True); b.setObjectName("categoryButton")
            b.clicked.connect(lambda _, pos=p: self._set_pos(pos)); plo.addWidget(b); self.pos_btns[p] = b
        self.pos_btns["initial"].setChecked(True)
        right.addLayout(plo)

        # Word card
        self.word_card = QLabel("Select a sound to start")
        self.word_card.setAlignment(Qt.AlignCenter)
        self.word_card.setFont(QFont("Segoe UI", 36, QFont.Bold))
        self.word_card.setMinimumHeight(120)
        self.word_card.setStyleSheet(
            "background-color:white; color:#2d3748; border:2px solid #e2e8f0;"
            "border-radius:16px; padding:30px;")
        right.addWidget(self.word_card)

        # Nav
        nav = QHBoxLayout()
        pb = QPushButton("← Previous"); pb.clicked.connect(self._prev); nav.addWidget(pb)
        self.counter_lbl = QLabel("0 / 0"); self.counter_lbl.setAlignment(Qt.AlignCenter)
        self.counter_lbl.setFont(QFont("Segoe UI", 12)); self.counter_lbl.setStyleSheet("color:#718096;")
        nav.addWidget(self.counter_lbl)
        nb = QPushButton("Next →"); nb.clicked.connect(self._next); nav.addWidget(nb)
        right.addLayout(nav)

        # Waveform
        self.waveform = WaveformWidget(); right.addWidget(self.waveform)

        # Record
        rlo = QHBoxLayout(); rlo.setAlignment(Qt.AlignCenter)
        self.rec_btn = QPushButton("🎤"); self.rec_btn.setObjectName("recordButton")
        self.rec_btn.setCheckable(True); self.rec_btn.clicked.connect(self._toggle_rec)
        if not AUDIO_AVAILABLE:
            self.rec_btn.setEnabled(False); self.rec_btn.setToolTip("pip install sounddevice")
        rlo.addWidget(self.rec_btn)
        self.rec_lbl = QLabel("Press to record"); self.rec_lbl.setFont(QFont("Segoe UI", 11))
        self.rec_lbl.setStyleSheet("color:#718096;"); rlo.addWidget(self.rec_lbl)
        right.addLayout(rlo)

        # Self-assessment
        alo = QHBoxLayout(); alo.setAlignment(Qt.AlignCenter)
        alo.addWidget(QLabel("How did you do?"))
        sb = QPushButton("✓ Correct"); sb.setObjectName("successBtn"); sb.clicked.connect(self._mark_correct); alo.addWidget(sb)
        cb = QPushButton("~ Close");  cb.setObjectName("closeBtn");   cb.clicked.connect(self._mark_close);   alo.addWidget(cb)
        rb = QPushButton("✗ Retry");  rb.setObjectName("retryBtn");   rb.clicked.connect(self._mark_retry);   alo.addWidget(rb)
        right.addLayout(alo)

        self.score_lbl = QLabel("Session Score: 0/0")
        self.score_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.score_lbl.setStyleSheet("color:#4299e1;"); self.score_lbl.setAlignment(Qt.AlignCenter)
        right.addWidget(self.score_lbl)
        right.addStretch()
        top.addLayout(right, 2)

    @staticmethod
    def _label(text, size=14, color="#2d3748"):
        l = QLabel(text); l.setFont(QFont("Segoe UI", size, QFont.Bold if size > 16 else QFont.Normal))
        l.setStyleSheet(f"color:{color};"); return l

    def _on_phoneme(self, cur, _prev):
        if cur is None: return
        name = cur.data(Qt.UserRole)
        self.cur_phoneme = name; self.cur_idx = 0; self.practice_results = []
        self.desc_lbl.setText(f"<b>{name}</b> — {PHONEMES[name]['description']}")
        self._set_pos("initial"); self._refresh()
        self.session_start = datetime.now()

    def _set_pos(self, pos):
        self.cur_pos = pos; self.cur_idx = 0
        for p, b in self.pos_btns.items(): b.setChecked(p == pos)
        self._refresh()

    def _words(self):
        if not self.cur_phoneme: return []
        return PHONEMES[self.cur_phoneme].get(self.cur_pos, [])

    def _refresh(self):
        w = self._words()
        if not w:
            self.word_card.setText("—"); self.counter_lbl.setText("0 / 0"); return
        self.cur_idx = min(self.cur_idx, len(w) - 1)
        self.word_card.setText(w[self.cur_idx])
        self.counter_lbl.setText(f"{self.cur_idx + 1} / {len(w)}")
        self.waveform.clear()

    def _prev(self):
        if self.cur_idx > 0: self.cur_idx -= 1; self._refresh()

    def _next(self):
        if self.cur_idx < len(self._words()) - 1: self.cur_idx += 1; self._refresh()

    # Recording
    def _toggle_rec(self, checked):
        if checked: self._start_rec() 
        else: self._stop_rec()

    def _start_rec(self):
        self.is_recording = True; self.rec_data = []
        self.rec_lbl.setText("Recording…"); self.rec_lbl.setStyleSheet("color:#e53e3e;font-weight:bold;")
        try:
            self.rec_stream = sd.InputStream(samplerate=44100, channels=1,
                                             callback=self._audio_cb, blocksize=1024)
            self.rec_stream.start()
        except Exception as e:
            self.rec_lbl.setText(f"Error: {str(e)[:40]}")
            self.is_recording = False; self.rec_btn.setChecked(False)

    def _stop_rec(self):
        self.is_recording = False
        if self.rec_stream:
            self.rec_stream.stop(); self.rec_stream.close(); self.rec_stream = None
        self.rec_lbl.setText("Recording saved"); self.rec_lbl.setStyleSheet("color:#48bb78;")
        if self.rec_data:
            arr = np.concatenate(self.rec_data)
            self.waveform.set_data(arr)
            if self.session_start:
                dur = (datetime.now() - self.session_start).total_seconds() / 60
                self.app_state.log_session("Sound Practice", dur)

    def _audio_cb(self, indata, frames, time_info, status):
        if self.is_recording: self.rec_data.append(indata.copy().flatten())

    # Assessment
    def _mark_correct(self):
        self.practice_results.append(True); self._update_score(); self._next()

    def _mark_close(self):
        self.practice_results.append(False); self._update_score(); self._next()

    def _mark_retry(self):
        self._update_score()

    def _update_score(self):
        c = sum(self.practice_results); t = len(self.practice_results)
        pct = int((c / t) * 100) if t else 0
        self.score_lbl.setText(f"Session Score: {c}/{t} ({pct}%)")


class TongueTwisterPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.difficulty = "Easy"; self.idx = 0
        self.timer_secs = 0; self.timer_running = False
        self._build()

    def _build(self):
        lo = QVBoxLayout(self); lo.setSpacing(18); lo.setContentsMargins(32, 24, 32, 24)

        lo.addWidget(self._title("Tongue Twisters"))
        lo.addWidget(self._sub("Practice articulation with fun phrases — try to say them faster each time!"))

        # Difficulty
        dlo = QHBoxLayout(); dlo.addWidget(QLabel("Difficulty:"))
        self.diff_btns = {}
        for d in ["Easy", "Medium", "Hard"]:
            b = QPushButton(d); b.setCheckable(True); b.setObjectName("categoryButton")
            b.clicked.connect(lambda _, dd=d: self._set_diff(dd)); dlo.addWidget(b); self.diff_btns[d] = b
        dlo.addStretch(); lo.addLayout(dlo)

        # Display
        self.twister_display = QTextEdit(); self.twister_display.setReadOnly(True)
        self.twister_display.setAlignment(Qt.AlignCenter)
        self.twister_display.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.twister_display.setMinimumHeight(140); self.twister_display.setMaximumHeight(200)
        self.twister_display.setText("Select a difficulty level to start")
        lo.addWidget(self.twister_display)

        # Timer
        tlo = QHBoxLayout()
        self.timer_lbl = QLabel("00:00"); self.timer_lbl.setFont(QFont("Segoe UI", 36, QFont.Bold))
        self.timer_lbl.setStyleSheet("color:#4299e1;"); self.timer_lbl.setAlignment(Qt.AlignCenter)
        tlo.addWidget(self.timer_lbl)

        tblo = QVBoxLayout()
        self.start_btn = QPushButton("▶ Start Timer"); self.start_btn.setMinimumWidth(140)
        self.start_btn.clicked.connect(self._toggle_timer); tblo.addWidget(self.start_btn)
        rst = QPushButton("↺ Reset"); rst.setStyleSheet(
            "background-color:#718096;color:white;border-radius:8px;padding:10px 20px;")
        rst.clicked.connect(self._reset_timer); tblo.addWidget(rst)
        tlo.addLayout(tblo); lo.addLayout(tlo)

        # Navigation
        nav = QHBoxLayout()
        pb = QPushButton("← Previous"); pb.clicked.connect(self._prev); nav.addWidget(pb)
        self.counter = QLabel("0 / 0"); self.counter.setAlignment(Qt.AlignCenter)
        self.counter.setStyleSheet("color:#718096;"); nav.addWidget(self.counter)
        nb = QPushButton("Next →"); nb.clicked.connect(self._next); nav.addWidget(nb)
        lo.addLayout(nav)

        # Tips
        g = QGroupBox("Tips"); gl = QVBoxLayout(g)
        gl.addWidget(QLabel("• Start slowly and focus on accuracy\n"
                            "• Gradually increase speed\n"
                            "• Take a breath between attempts\n"
                            "• Practice difficult sounds separately first"))
        lo.addWidget(g); lo.addStretch()

        self.timer = QTimer(); self.timer.timeout.connect(self._tick)
        self._set_diff("Easy")

    @staticmethod
    def _title(t): l = QLabel(t); l.setFont(QFont("Segoe UI", 24, QFont.Bold)); l.setStyleSheet("color:#2d3748;"); return l
    @staticmethod
    def _sub(t): l = QLabel(t); l.setFont(QFont("Segoe UI", 12)); l.setStyleSheet("color:#718096;"); l.setWordWrap(True); return l

    def _set_diff(self, d):
        self.difficulty = d; self.idx = 0
        for k, b in self.diff_btns.items(): b.setChecked(k == d)
        self._refresh()

    def _twisters(self): return TONGUE_TWISTERS.get(self.difficulty, [])

    def _refresh(self):
        tw = self._twisters()
        if not tw: self.twister_display.setText("—"); self.counter.setText("0 / 0"); return
        self.idx = min(self.idx, len(tw) - 1)
        self.twister_display.setText(tw[self.idx])
        self.counter.setText(f"{self.idx + 1} / {len(tw)}")

    def _prev(self):
        if self.idx > 0: self.idx -= 1; self._refresh()

    def _next(self):
        if self.idx < len(self._twisters()) - 1: self.idx += 1; self._refresh()

    def _toggle_timer(self):
        if self.timer_running:
            self.timer_running = False; self.timer.stop()
            self.start_btn.setText("▶ Start Timer")
            self.app_state.log_session("Tongue Twisters", self.timer_secs / 60)
        else:
            self.timer_running = True; self.timer.start(1000)
            self.start_btn.setText("⏸ Pause")

    def _reset_timer(self):
        self.timer_running = False; self.timer.stop(); self.timer_secs = 0
        self.timer_lbl.setText("00:00"); self.start_btn.setText("▶ Start Timer")

    def _tick(self):
        self.timer_secs += 1
        self.timer_lbl.setText(f"{self.timer_secs // 60:02d}:{self.timer_secs % 60:02d}")


class BreathingPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build()

    def _build(self):
        lo = QVBoxLayout(self); lo.setSpacing(18); lo.setContentsMargins(32, 24, 32, 24)
        lo.setAlignment(Qt.AlignCenter)

        t = QLabel("Breathing Exercises"); t.setFont(QFont("Segoe UI", 24, QFont.Bold))
        t.setStyleSheet("color:#2d3748;"); t.setAlignment(Qt.AlignCenter); lo.addWidget(t)
        s = QLabel("Follow the circle. Breathe in as it grows, hold when steady, out as it shrinks.")
        s.setFont(QFont("Segoe UI", 12)); s.setStyleSheet("color:#718096;")
        s.setAlignment(Qt.AlignCenter); s.setWordWrap(True); lo.addWidget(s)

        self.circle = BreathingCircle(); lo.addWidget(self.circle, 1)

        # Settings
        slo = QHBoxLayout(); slo.setAlignment(Qt.AlignCenter)
        for label, attr, lo_val, hi_val, default in [
            ("Inhale:", "inhale_spin", 2, 8, 4),
            ("Hold:", "hold_spin", 0, 8, 4),
            ("Exhale:", "exhale_spin", 2, 10, 6),
        ]:
            slo.addWidget(QLabel(label))
            sp = QSpinBox(); sp.setRange(lo_val, hi_val); sp.setValue(default); sp.setSuffix(" sec")
            sp.valueChanged.connect(self._update_settings); slo.addWidget(sp)
            slo.addSpacing(16)
            setattr(self, attr, sp)
        lo.addLayout(slo)

        blo = QHBoxLayout(); blo.setAlignment(Qt.AlignCenter)
        self.start_btn = QPushButton("▶ Start"); self.start_btn.setMinimumWidth(140)
        self.start_btn.clicked.connect(self._toggle); blo.addWidget(self.start_btn)
        lo.addLayout(blo)

        info = QLabel("Breathing exercises help with breath control for speech.\n"
                       "Regular practice can improve voice quality and reduce speech anxiety.")
        info.setFont(QFont("Segoe UI", 11)); info.setStyleSheet("color:#a0aec0;")
        info.setAlignment(Qt.AlignCenter); lo.addWidget(info)

    def _update_settings(self):
        self.circle.inhale_time = self.inhale_spin.value()
        self.circle.hold_time = self.hold_spin.value()
        self.circle.exhale_time = self.exhale_spin.value()

    def _toggle(self):
        if self.circle.animating:
            self.circle.stop(); self.start_btn.setText("▶ Start")
            dur = self.circle.cycle_count * (
                self.circle.inhale_time + self.circle.hold_time + self.circle.exhale_time) / 60
            if dur > 0: self.app_state.log_session("Breathing Exercise", dur)
        else:
            self._update_settings(); self.circle.start(); self.start_btn.setText("⏹ Stop")


class MinimalPairsPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.category = None; self.idx = 0
        self.mode = "study"; self.score = 0; self.total = 0
        self.quiz_answer = None; self.quiz_other = None
        self._build()

    def _build(self):
        lo = QVBoxLayout(self); lo.setSpacing(18); lo.setContentsMargins(32, 24, 32, 24)

        lo.addWidget(self._title("Minimal Pairs"))
        lo.addWidget(self._sub("Practice distinguishing between similar sounds — two words that differ by only one phoneme."))

        # Mode
        mlo = QHBoxLayout(); mlo.addWidget(QLabel("Mode:"))
        self.study_btn = QPushButton("📖 Study"); self.study_btn.setCheckable(True)
        self.study_btn.setObjectName("categoryButton"); self.study_btn.setChecked(True)
        self.study_btn.clicked.connect(lambda: self._set_mode("study")); mlo.addWidget(self.study_btn)
        self.quiz_btn = QPushButton("🧠 Quiz"); self.quiz_btn.setCheckable(True)
        self.quiz_btn.setObjectName("categoryButton")
        self.quiz_btn.clicked.connect(lambda: self._set_mode("quiz")); mlo.addWidget(self.quiz_btn)
        mlo.addStretch(); lo.addLayout(mlo)

        # Category
        clo = QHBoxLayout(); clo.addWidget(QLabel("Category:"))
        self.cat_btns = {}
        for c in MINIMAL_PAIRS:
            b = QPushButton(c); b.setCheckable(True); b.setObjectName("categoryButton")
            b.clicked.connect(lambda _, cc=c: self._set_cat(cc)); clo.addWidget(b); self.cat_btns[c] = b
        clo.addStretch(); lo.addLayout(clo)

        # Pair display
        self.pair_frame = QFrame()
        self.pair_frame.setStyleSheet(
            "QFrame{background:white;border:2px solid #e2e8f0;border-radius:16px;padding:24px;}")
        pflo = QHBoxLayout(self.pair_frame)
        self.w1 = QLabel("Word 1"); self.w1.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self.w1.setAlignment(Qt.AlignCenter); self.w1.setStyleSheet("color:#4299e1;"); pflo.addWidget(self.w1)
        vs = QLabel("vs"); vs.setFont(QFont("Segoe UI", 20, QFont.Bold))
        vs.setAlignment(Qt.AlignCenter); vs.setStyleSheet("color:#a0aec0;"); pflo.addWidget(vs)
        self.w2 = QLabel("Word 2"); self.w2.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self.w2.setAlignment(Qt.AlignCenter); self.w2.setStyleSheet("color:#e53e3e;"); pflo.addWidget(self.w2)
        lo.addWidget(self.pair_frame)

        # Quiz answer buttons (hidden in study mode)
        self.quiz_frame = QFrame()
        qflo = QHBoxLayout(self.quiz_frame)
        self.qa_btn1 = QPushButton(); self.qa_btn1.setObjectName("categoryButton")
        self.qa_btn1.setMinimumHeight(60); self.qa_btn1.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.qa_btn1.clicked.connect(lambda: self._answer(0)); qflo.addWidget(self.qa_btn1)
        self.qa_btn2 = QPushButton(); self.qa_btn2.setObjectName("categoryButton")
        self.qa_btn2.setMinimumHeight(60); self.qa_btn2.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.qa_btn2.clicked.connect(lambda: self._answer(1)); qflo.addWidget(self.qa_btn2)
        self.quiz_frame.hide(); lo.addWidget(self.quiz_frame)

        self.quiz_lbl = QLabel(""); self.quiz_lbl.setFont(QFont("Segoe UI", 14))
        self.quiz_lbl.setAlignment(Qt.AlignCenter); self.quiz_lbl.setStyleSheet("color:#718096;")
        self.quiz_lbl.hide(); lo.addWidget(self.quiz_lbl)

        # Nav + score
        nlo = QHBoxLayout()
        pb = QPushButton("← Previous"); pb.clicked.connect(self._prev); nlo.addWidget(pb)
        self.pc = QLabel("0 / 0"); self.pc.setAlignment(Qt.AlignCenter); self.pc.setStyleSheet("color:#718096;"); nlo.addWidget(self.pc)
        nb = QPushButton("Next →"); nb.clicked.connect(self._next); nlo.addWidget(nb)
        self.sc = QLabel("Score: 0/0"); self.sc.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.sc.setStyleSheet("color:#48bb78;"); nlo.addWidget(self.sc)
        lo.addLayout(nlo); lo.addStretch()

        self._set_cat(list(MINIMAL_PAIRS.keys())[0])

    @staticmethod
    def _title(t): l = QLabel(t); l.setFont(QFont("Segoe UI", 24, QFont.Bold)); l.setStyleSheet("color:#2d3748;"); return l
    @staticmethod
    def _sub(t): l = QLabel(t); l.setFont(QFont("Segoe UI", 12)); l.setStyleSheet("color:#718096;"); l.setWordWrap(True); return l

    def _set_mode(self, m):
        self.mode = m
        self.study_btn.setChecked(m == "study"); self.quiz_btn.setChecked(m == "quiz")
        self.quiz_frame.setVisible(m == "quiz"); self.quiz_lbl.setVisible(m == "quiz")
        self.score = 0; self.total = 0; self._refresh()

    def _set_cat(self, c):
        self.category = c; self.idx = 0; self.score = 0; self.total = 0
        for k, b in self.cat_btns.items(): b.setChecked(k == c)
        self._refresh()

    def _pairs(self):
        return MINIMAL_PAIRS.get(self.category, [])

    def _refresh(self):
        ps = self._pairs()
        if not ps: self.w1.setText("—"); self.w2.setText("—"); self.pc.setText("0 / 0"); return
        self.idx = min(self.idx, len(ps) - 1)
        w1, w2 = ps[self.idx]
        if self.mode == "study":
            self.w1.setText(w1); self.w1.setStyleSheet("color:#4299e1;font-size:32pt;font-weight:bold;")
            self.w2.setText(w2); self.w2.setStyleSheet("color:#e53e3e;font-size:32pt;font-weight:bold;")
        else:
            self._start_quiz()
        self.pc.setText(f"{self.idx + 1} / {len(ps)}")
        self.sc.setText(f"Score: {self.score}/{self.total}")

    def _start_quiz(self):
        w1, w2 = self._pairs()[self.idx]
        if random.random() < 0.5:
            self.quiz_answer = w1; self.quiz_other = w2
        else:
            self.quiz_answer = w2; self.quiz_other = w1
        self.w1.setText(f'"{self.quiz_answer}"'); self.w1.setStyleSheet("color:#4299e1;font-size:32pt;font-weight:bold;")
        self.w2.setText("???"); self.w2.setStyleSheet("color:#a0aec0;font-size:32pt;font-weight:bold;")
        self.quiz_lbl.setText("Which word pairs with this?")
        # Shuffle answer buttons
        opts = [self.quiz_answer, self.quiz_other]
        random.shuffle(opts)
        self.qa_btn1.setText(opts[0]); self.qa_btn2.setText(opts[1])
        self.qa_btn1.setEnabled(True); self.qa_btn2.setEnabled(True)
        self.qa_btn1.setStyleSheet(""); self.qa_btn2.setStyleSheet("")

    def _answer(self, btn_idx):
        chosen = self.qa_btn1.text() if btn_idx == 0 else self.qa_btn2.text()
        self.total += 1
        correct = (chosen == self.quiz_answer)
        if correct:
            self.score += 1
            self.w2.setText(self.quiz_other)
            self.w2.setStyleSheet("color:#48bb78;font-size:32pt;font-weight:bold;")
            self.quiz_lbl.setText("✓ Correct!")
            self.quiz_lbl.setStyleSheet("color:#48bb78;font-size:14pt;font-weight:bold;")
        else:
            self.w2.setText(self.quiz_other)
            self.w2.setStyleSheet("color:#e53e3e;font-size:32pt;font-weight:bold;")
            self.quiz_lbl.setText(f"✗ The answer was: {self.quiz_other}")
            self.quiz_lbl.setStyleSheet("color:#e53e3e;font-size:14pt;font-weight:bold;")
        self.qa_btn1.setEnabled(False); self.qa_btn2.setEnabled(False)
        self.sc.setText(f"Score: {self.score}/{self.total}")
        self.app_state.log_session("Minimal Pairs", 0.2)

    def _prev(self):
        if self.idx > 0: self.idx -= 1; self._refresh()

    def _next(self):
        if self.idx < len(self._pairs()) - 1: self.idx += 1; self._refresh()


class ProgressPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build()

    def _build(self):
        lo = QVBoxLayout(self); lo.setSpacing(18); lo.setContentsMargins(32, 24, 32, 24)

        t = QLabel("Progress Tracker"); t.setFont(QFont("Segoe UI", 24, QFont.Bold))
        t.setStyleSheet("color:#2d3748;"); lo.addWidget(t)
        s = QLabel("Track your practice over time. Consistency is key!")
        s.setFont(QFont("Segoe UI", 12)); s.setStyleSheet("color:#718096;"); lo.addWidget(s)

        self.chart = BarChartWidget(); self.chart.setMinimumHeight(280); lo.addWidget(self.chart)

        # Category breakdown
        self.cat_chart = BarChartWidget(); self.cat_chart.setMinimumHeight(240); lo.addWidget(self.cat_chart)

        g = QGroupBox("Recent Sessions"); gl = QVBoxLayout(g)
        self.log_list = QListWidget(); self.log_list.setMinimumHeight(180); gl.addWidget(self.log_list)
        lo.addWidget(g)

        rb = QPushButton("Reset All Progress"); rb.setStyleSheet(
            "background-color:#e53e3e;color:white;border-radius:8px;padding:10px 20px;font-size:13px;")
        rb.clicked.connect(self._reset); lo.addWidget(rb, 0, Qt.AlignRight)
        lo.addStretch()

    def refresh(self):
        # Last 7 days chart
        days = {}
        for i in range(6, -1, -1):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            dn = (datetime.now() - timedelta(days=i)).strftime("%a")
            days[dn] = int(self.app_state.get_daily_minutes(d))
        self.chart.set_data(days, "Practice Minutes — Last 7 Days")

        # Category breakdown
        cat_totals = defaultdict(float)
        for sessions in self.app_state.session_log.values():
            for s in sessions:
                cat_totals[s.get("category", "Other")] += s.get("duration_min", 0)
        self.cat_chart.set_data(
            {k: int(v) for k, v in cat_totals.items()},
            "Practice by Category (minutes)")

        # Log
        self.log_list.clear()
        all_s = []
        for date, sessions in self.app_state.session_log.items():
            for s in sessions:
                all_s.append((date, s))
        all_s.sort(key=lambda x: x[0], reverse=True)
        for date, s in all_s[:30]:
            cat = s.get("category", "?"); dur = s.get("duration_min", 0)
            self.log_list.addItem(f"📅 {date}  |  {cat}  |  {dur:.1f} min")

    def _reset(self):
        if QMessageBox.question(self, "Reset Progress",
                "Are you sure you want to reset all progress? This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.app_state.reset(); self.refresh()


# ─────────────────────── APP STATE ───────────────────────

class AppState:
    SAVE_PATH = os.path.join(os.path.expanduser("~"), ".speech_therapy_progress.json")

    def __init__(self):
        self.session_log = defaultdict(list)  # {date: [{category, duration_min}, ...]}
        self._load()

    def log_session(self, category, duration_min):
        if duration_min <= 0: return
        today = datetime.now().strftime("%Y-%m-%d")
        self.session_log[today].append({"category": category, "duration_min": round(duration_min, 2)})
        self._save()

    def get_daily_minutes(self, date):
        return sum(s.get("duration_min", 0) for s in self.session_log.get(date, []))

    def get_streak(self):
        streak = 0
        for i in range(365):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if self.get_daily_minutes(d) > 0: streak += 1
            else: break
        return streak

    def _save(self):
        try:
            with open(self.SAVE_PATH, 'w') as f: json.dump(dict(self.session_log), f, indent=2)
        except Exception: pass

    def _load(self):
        try:
            if os.path.exists(self.SAVE_PATH):
                with open(self.SAVE_PATH) as f: self.session_log = defaultdict(list, json.load(f))
        except Exception: self.session_log = defaultdict(list)

    def reset(self):
        self.session_log = defaultdict(list); self._save()


# ─────────────────────── MAIN WINDOW ───────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app_state = AppState()
        self._build()
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.app_state._save)
        self.save_timer.start(30000)

    def _build(self):
        self.setWindowTitle("Speech Therapy App")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        central = QWidget(); self.setCentralWidget(central)
        main_lo = QHBoxLayout(central); main_lo.setSpacing(0); main_lo.setContentsMargins(0, 0, 0, 0)

        # ── Sidebar ──
        sidebar = QFrame(); sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("QFrame{background-color:#1a202c;border:none;}")
        sb_lo = QVBoxLayout(sidebar); sb_lo.setSpacing(4); sb_lo.setContentsMargins(12, 20, 12, 20)

        logo = QLabel("🗣️ Speech\n    Therapy")
        logo.setFont(QFont("Segoe UI", 18, QFont.Bold)); logo.setStyleSheet("color:white;margin-bottom:16px;")
        sb_lo.addWidget(logo)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color:#2d3748;max-height:1px;"); sb_lo.addWidget(sep)

        self.nav_btns = []
        for text, idx in [("🏠  Dashboard", 0), ("🎯  Sound Practice", 1),
                          ("👅  Tongue Twisters", 2), ("🫁  Breathing", 3),
                          ("👂  Minimal Pairs", 4), ("📊  Progress", 5)]:
            b = QPushButton(text); b.setObjectName("navButton"); b.setCheckable(True); b.setMinimumHeight(44)
            b.clicked.connect(lambda _, i=idx: self._nav(i))
            sb_lo.addWidget(b); self.nav_btns.append(b)

        sb_lo.addStretch()
        vl = QLabel("v1.0.0"); vl.setStyleSheet("color:#4a5568;font-size 10px;");
        sb_lo.addStretch()
        vl = QLabel("v1.0.0"); vl.setStyleSheet("color:#4a5568;font-size:11px;")
        vl.setAlignment(Qt.AlignCenter); sb_lo.addWidget(vl)
        main_lo.addWidget(sidebar)

        # ── Content area ──
        content = QWidget()
        content.setStyleSheet("background-color:#f0f4f8;")
        content_lo = QVBoxLayout(content); content_lo.setSpacing(0); content_lo.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        content_lo.addWidget(self.stack)
        main_lo.addWidget(content, 1)

        # ── Pages ──
        self.pages = [
            DashboardPage(self.app_state),
            SoundPracticePage(self.app_state),
            TongueTwisterPage(self.app_state),
            BreathingPage(self.app_state),
            MinimalPairsPage(self.app_state),
            ProgressPage(self.app_state),
        ]
        for p in self.pages:
            scroll = QScrollArea()
            scroll.setWidget(p)
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.stack.addWidget(scroll)

        self._nav(0)

    def _nav(self, idx):
        self.stack.setCurrentIndex(idx)
        for i, b in enumerate(self.nav_btns):
            b.setChecked(i == idx)
        # Refresh pages that need it
        if idx == 0:
            self.pages[0].refresh()
        elif idx == 5:
            self.pages[5].refresh()

    def closeEvent(self, event):
        self.app_state._save()
        event.accept()


# ─────────────────────── ENTRY POINT ───────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()