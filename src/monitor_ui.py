# monitor_ui.py
"""
╔══════════════════════════════════════════════════════════════════╗
║              SYSTEM MONITOR  —  Frontend UI Module               ║
╚══════════════════════════════════════════════════════════════════╝

USAGE IN YOUR MAIN SCRIPT:
─────────────────────────────────────────────────────────────────
    import monitor_ui

    monitor_ui.sectionA("CPU Core Monitor")
    monitor_ui.sectionB(8, ["Active"]*4 + ["Idle"]*4, ["3.2 GHz"]*8)
    monitor_ui.sectionC(72.5, 45, 95)
    monitor_ui.run()        ← blocks here until the window closes

─────────────────────────────────────────────────────────────────
BUTTON CLICK CALLBACK  (Section B)
─────────────────────────────────────────────────────────────────
    def on_core_click(index: int):
        print(f"Core {index} clicked!")

    monitor_ui.sectionB(8, statuses, freqs, on_click=on_core_click)

    The callback receives the zero-based block index as its only argument.
─────────────────────────────────────────────────────────────────
"""

import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QGridLayout, QSizePolicy,
    QAbstractButton,
)
from PySide6.QtCore  import Qt, QSize, QRectF, QPointF, QTimer
from PySide6.QtGui   import (
    QPainter, QColor, QPen, QFont,
    QPainterPath, QLinearGradient, QBrush,
    QRadialGradient,
)

# ──────────────────────────────────────────────────────────────────────────────
#  PALETTE  (all colours live here — change freely)
# ──────────────────────────────────────────────────────────────────────────────
_BG         = QColor("#08080f")   # window background
_PANEL_C    = QColor("#0d0d18")   # section-C panel
_CARD       = QColor("#13132a")   # block / card fill
_CARD_HOV   = QColor("#1a1a30")   # block hover
_CARD_PRS   = QColor("#0f0f1e")   # block pressed
_BORDER     = QColor("#202035")   # idle border
_BORDER_HOV = QColor("#7b6cf6")   # hover border  (violet)
_ACCENT     = QColor("#7b6cf6")   # primary accent (violet)
_TEAL       = QColor("#00dfc0")   # secondary accent (teal)
_TEXT       = QColor("#d8daf2")   # primary text
_DIM        = QColor("#484870")   # muted / label text
_GREEN      = QColor("#00e5a0")   # status active
_RED        = QColor("#ff4f7b")   # status inactive
_FREQ_CLR   = QColor("#5db8ff")   # frequency value
_HEADER_BG  = QColor("#0b0b16")   # top header

_COLS = 3   # number of columns in the Section-B grid

# ──────────────────────────────────────────────────────────────────────────────
#  GLOBAL STATE
# ──────────────────────────────────────────────────────────────────────────────
_app: QApplication | None = None
_win: "MainWindow | None" = None


def _bootstrap() -> None:
    global _app, _win
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
        # hide ALL scrollbars globally while keeping wheel-scroll
        _app.setStyleSheet("""
            QScrollBar:vertical   { width:  0px; border: none; background: transparent; }
            QScrollBar:horizontal { height: 0px; border: none; background: transparent; }
        """)
    if _win is None:
        _win = _MainWindow()
        _win.show()


# ──────────────────────────────────────────────────────────────────────────────
#  WIDGET: Section-A header
# ──────────────────────────────────────────────────────────────────────────────
class _Header(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setFixedHeight(62)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        # base fill
        p.fillRect(0, 0, W, H, _HEADER_BG)

        # subtle gradient overlay
        grad = QLinearGradient(0, 0, W, 0)
        grad.setColorAt(0.0, QColor(123, 108, 246, 30))
        grad.setColorAt(1.0, QColor(0,   223, 192, 10))
        p.fillRect(0, 0, W, H, grad)

        # left accent bar
        bar = QPainterPath()
        bar.addRoundedRect(QRectF(0, 8, 4, H - 16), 2, 2)
        p.fillPath(bar, _ACCENT)

        # bottom separator line
        p.fillRect(0, H - 1, W, 1, _BORDER)

        # title text
        p.setPen(QPen(_TEXT))
        font = QFont("Orbitron", 13, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        if not p.fontMetrics().horizontalAdvance(self.title):
            font = QFont("Segoe UI", 14, QFont.Bold)   # fallback
        p.setFont(font)
        p.drawText(20, 0, W - 40, H, Qt.AlignVCenter | Qt.AlignLeft, self.title)
        p.end()


# ──────────────────────────────────────────────────────────────────────────────
#  WIDGET: Core block button  (Section B)
# ──────────────────────────────────────────────────────────────────────────────
class _Block(QAbstractButton):
    """Square button showing STATUS + FREQ for one CPU core."""

    SZ = 160   # fixed square size in px

    def __init__(self, idx: int, status: str, frequency: str, parent=None):
        super().__init__(parent)
        self.idx = idx
        self.status_txt = status
        self.freq_txt   = frequency
        self._hov = False
        self._prs = False

        self.setFixedSize(self.SZ, self.SZ)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover)

    # ── hover / press tracking ──────────────────────────
    def enterEvent(self, e):  self._hov = True;  self.update()
    def leaveEvent(self, e):  self._hov = False; self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._prs = True; self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._prs = False; self.update()
        super().mouseReleaseEvent(e)

    def sizeHint(self): return QSize(self.SZ, self.SZ)

    # ── paint ───────────────────────────────────────────
    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W = H = self.SZ

        # ── card background ──────────────────────────────
        card_rect = QRectF(1.5, 1.5, W - 3, H - 3)
        path = QPainterPath()
        path.addRoundedRect(card_rect, 14, 14)

        if self._prs:
            bg = _CARD_PRS
        elif self._hov:
            # gradient on hover
            g = QLinearGradient(0, 0, W, H)
            g.setColorAt(0.0, QColor(123, 108, 246, 35))
            g.setColorAt(1.0, QColor(0,   223, 192, 15))
            p.fillPath(path, _CARD_HOV)
            p.fillPath(path, g)
            bg = None
        else:
            bg = _CARD

        if bg is not None:
            p.fillPath(path, bg)

        # ── border ───────────────────────────────────────
        bdr = _BORDER_HOV if self._hov else _BORDER
        p.setPen(QPen(bdr, 1.5 if self._hov else 1.0))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

        # ── tiny glow pill top-right on hover ────────────
        if self._hov:
            pill = QRectF(W - 32, 10, 20, 6)
            pill_path = QPainterPath()
            pill_path.addRoundedRect(pill, 3, 3)
            p.fillPath(pill_path, QColor(123, 108, 246, 80))

        # ── CORE  N  (top-left label) ─────────────────────
        p.setPen(QPen(_DIM))
        f_tag = QFont("Segoe UI", 7, QFont.Bold)
        f_tag.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
        p.setFont(f_tag)
        p.drawText(QRectF(13, 12, W - 26, 15), Qt.AlignLeft, f"CORE  {self.idx}")

        # ── top divider ──────────────────────────────────
        p.setPen(QPen(QColor("#1c1c32"), 1))
        p.drawLine(QPointF(13, 33), QPointF(W - 13, 33))

        # ── STATUS section ───────────────────────────────
        f_lbl = QFont("Segoe UI", 6, QFont.Bold)
        f_lbl.setLetterSpacing(QFont.AbsoluteSpacing, 1.8)
        p.setFont(f_lbl)
        p.setPen(QPen(_DIM))
        p.drawText(QRectF(13, 40, W - 26, 13), Qt.AlignLeft, "STATUS")

        is_up = self.status_txt.strip().lower() in (
            "active", "online", "running", "on", "1", "up", "busy"
        )
        status_clr = _GREEN if is_up else _RED

        # coloured dot indicator
        dot_x, dot_y = 13, 57
        p.setBrush(QBrush(status_clr))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(dot_x, dot_y + 3, 6, 6))

        f_val = QFont("Segoe UI", 10, QFont.Bold)
        p.setFont(f_val)
        p.setPen(QPen(status_clr))
        p.drawText(QRectF(24, 54, W - 37, 22), Qt.AlignLeft | Qt.AlignVCenter,
                   self.status_txt)

        # ── mid divider ───────────────────────────────────
        p.setPen(QPen(QColor("#1c1c32"), 1))
        p.drawLine(QPointF(13, 88), QPointF(W - 13, 88))

        # ── FREQ section ──────────────────────────────────
        f_lbl2 = QFont("Segoe UI", 6, QFont.Bold)
        f_lbl2.setLetterSpacing(QFont.AbsoluteSpacing, 1.8)
        p.setFont(f_lbl2)
        p.setPen(QPen(_DIM))
        p.drawText(QRectF(13, 94, W - 26, 13), Qt.AlignLeft, "FREQ")

        f_freq = QFont("Segoe UI", 13, QFont.Bold)
        p.setFont(f_freq)
        p.setPen(QPen(_FREQ_CLR))
        p.drawText(QRectF(13, 108, W - 26, 38),
                   Qt.AlignLeft | Qt.AlignVCenter, self.freq_txt)

        p.end()


# ──────────────────────────────────────────────────────────────────────────────
#  WIDGET: Donut pie chart  (Section C)
# ──────────────────────────────────────────────────────────────────────────────
class _PieChart(QWidget):
    def __init__(self, pct: float, parent=None):
        super().__init__(parent)
        self.pct = max(0.0, min(100.0, float(pct)))
        self.setFixedSize(200, 200)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        W, H = self.width(), self.height()

        ring = 18
        margin = 20
        rect = QRectF(margin, margin, W - 2 * margin, H - 2 * margin)

        # ── radial glow behind ring ───────────────────────
        rg = QRadialGradient(W / 2, H / 2, W / 2)
        rg.setColorAt(0.55, QColor(123, 108, 246, 20))
        rg.setColorAt(1.00, QColor(0, 0, 0, 0))
        p.setBrush(QBrush(rg))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QRectF(0, 0, W, H))

        # ── track ring ────────────────────────────────────
        p.setPen(QPen(QColor("#1a1a30"), ring, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawArc(rect, 0, 360 * 16)

        # ── filled arc ────────────────────────────────────
        if self.pct > 0:
            span = int(self.pct / 100.0 * 360 * 16)
            filled_pen = QPen(_ACCENT, ring, Qt.SolidLine, Qt.RoundCap)
            p.setPen(filled_pen)
            p.drawArc(rect, 90 * 16, -span)

        # ── centre percentage ─────────────────────────────
        p.setPen(QPen(_TEXT))
        p.setFont(QFont("Segoe UI", 20, QFont.Bold))
        p.drawText(rect, Qt.AlignCenter, f"{self.pct:.1f}%")

        # ── sub-label ─────────────────────────────────────
        sub_rect = QRectF(0, rect.bottom() - 6, W, 18)
        p.setPen(QPen(_DIM))
        p.setFont(QFont("Segoe UI", 7))
        p.drawText(sub_rect, Qt.AlignCenter, "")

        p.end()


# ──────────────────────────────────────────────────────────────────────────────
#  WIDGET: PL value card  (Section C)
# ──────────────────────────────────────────────────────────────────────────────
class _PLCard(QWidget):
    def __init__(self, label: str, value, unit: str = "W", parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setMinimumHeight(82)
        self.setMaximumHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        vl = QVBoxLayout(self)
        vl.setContentsMargins(16, 10, 16, 10)
        vl.setSpacing(4)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            "background: transparent;"
            "color: rgba(72,72,112,255);"
            "font-size: 7pt; font-weight: 700; letter-spacing: 2px;"
        )
        vl.addWidget(lbl)

        row = QWidget()
        row.setStyleSheet("background: transparent;")
        row.setAutoFillBackground(False)
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(5)

        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(
            f"background: transparent; color: {_TEAL.name()};"
            " font-size: 22pt; font-weight: 700;"
        )
        val_lbl.setAutoFillBackground(False)

        unit_lbl = QLabel(unit)
        unit_lbl.setStyleSheet(
            "background: transparent; color: rgba(72,72,112,255);"
            " font-size: 10pt;"
        )
        unit_lbl.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        unit_lbl.setAutoFillBackground(False)

        rl.addWidget(val_lbl)
        rl.addWidget(unit_lbl)
        rl.addStretch()
        vl.addWidget(row)

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(2, 2, self.width() - 4, self.height() - 4)
        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)
        p.fillPath(path, _CARD)
        p.setPen(QPen(_BORDER, 1.5))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)
        p.end()


# ──────────────────────────────────────────────────────────────────────────────
#  WIDGET: Small section label  (Section C)
# ──────────────────────────────────────────────────────────────────────────────
class _SecLabel(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text.upper()
        self.setFixedHeight(20)
        self.setAutoFillBackground(False)

    def paintEvent(self, _ev):
        p = QPainter(self)
        f = QFont("Segoe UI", 7, QFont.Bold)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        p.setFont(f)
        p.setPen(QPen(_DIM))
        p.drawText(0, 0, self.width(), self.height(),
                   Qt.AlignVCenter | Qt.AlignLeft, self.text)
        p.end()


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ──────────────────────────────────────────────────────────────────────────────
class _MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Horizon 1.0 experimental")
        self.resize(900, 650)
        self.setMinimumSize(900, 550)
        self.setMaximumWidth(900)
        self.setMaximumHeight(650)

        # root widget
        root = QWidget()
        root.setAutoFillBackground(True)
        p = root.palette()
        p.setColor(root.backgroundRole(), _BG)
        root.setPalette(p)
        self.setCentralWidget(root)

        self._root_l = QVBoxLayout(root)
        self._root_l.setSpacing(0)
        self._root_l.setContentsMargins(0, 0, 0, 0)

        self._header_w: _Header | None = None  # Section A slot

        # ── content row (B + C) ──────────────────────────
        content = QWidget()
        content.setAutoFillBackground(False)
        cl = QHBoxLayout(content)
        cl.setSpacing(0)
        cl.setContentsMargins(0, 0, 0, 0)

        # Section B — scrollable grid (75%)
        self._b_scroll = QScrollArea()
        self._b_scroll.setWidgetResizable(True)
        self._b_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._b_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._b_scroll.setStyleSheet("background: transparent; border: none;")

        self._b_inner = QWidget()
        self._b_inner.setStyleSheet("background: transparent;")
        self._b_inner.setAutoFillBackground(False)
        self._b_grid = QGridLayout(self._b_inner)
        self._b_grid.setSpacing(14)
        self._b_grid.setContentsMargins(22, 22, 22, 22)
        self._b_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._b_scroll.setWidget(self._b_inner)

        # Section C — scrollable panel (25%)
        self._c_scroll = QScrollArea()
        self._c_scroll.setWidgetResizable(True)
        self._c_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._c_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._c_scroll.setStyleSheet(
            f"background: {_PANEL_C.name()}; border: none;"
            f" border-left: 1px solid {_BORDER.name()};"
        )

        self._c_inner = QWidget()
        self._c_inner.setAutoFillBackground(True)
        cp = self._c_inner.palette()
        cp.setColor(self._c_inner.backgroundRole(), _PANEL_C)
        self._c_inner.setPalette(cp)
        self._c_vl = QVBoxLayout(self._c_inner)
        self._c_vl.setSpacing(12)
        self._c_vl.setContentsMargins(18, 20, 18, 20)
        self._c_vl.setAlignment(Qt.AlignTop)
        self._c_scroll.setWidget(self._c_inner)

        cl.addWidget(self._b_scroll, 75)
        cl.addWidget(self._c_scroll, 25)

        self._root_l.addWidget(content, 1)

    # ────────────────────────────────────────────────────────
    #  Setters (called by the public API functions)
    # ────────────────────────────────────────────────────────

    def set_section_a(self, title: str) -> None:
        if self._header_w is not None:
            self._root_l.removeWidget(self._header_w)
            self._header_w.deleteLater()
        self._header_w = _Header(title)
        self._root_l.insertWidget(0, self._header_w)

    def set_section_b(self, n: int, status: list, frequency: list,
                      on_click=None) -> None:
        # wipe existing blocks
        while self._b_grid.count():
            item = self._b_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i in range(n):
            s = status[i]    if i < len(status)    else "Unknown"
            f = frequency[i] if i < len(frequency) else "N/A"
            blk = _Block(i, s, f)

            # ── connect click callback ──────────────────────
            if on_click is not None:
                _i = i
                blk.clicked.connect(lambda checked=False, x=_i: on_click(x))

            self._b_grid.addWidget(blk, i // _COLS, i % _COLS)

    def set_section_c(self, percentage: float, pl1, pl2) -> None:
        # wipe existing content
        while self._c_vl.count():
            item = self._c_vl.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ── panel title ──────────────────────────────────────
        title = QLabel("CPU Metrics")
        title.setStyleSheet(
            f"color: {_TEXT.name()}; font-size: 13pt; font-weight: 700;"
            " background: transparent;"
        )
        title.setAutoFillBackground(False)
        self._c_vl.addWidget(title)

        # ── spacer ───────────────────────────────────────────
        self._c_vl.addSpacing(4)

        # ── pie chart ────────────────────────────────────────
        self._c_vl.addWidget(_SecLabel("CPU Frequency Load"))
        self._c_vl.addSpacing(4)

        pie = _PieChart(percentage)
        wrap = QWidget()
        wrap.setAutoFillBackground(False)
        wrap.setStyleSheet("background: transparent;")
        wl = QHBoxLayout(wrap)
        wl.setAlignment(Qt.AlignCenter)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.addWidget(pie)
        self._c_vl.addWidget(wrap)

        # ── divider ──────────────────────────────────────────
        self._c_vl.addSpacing(6)
        div = QWidget()
        div.setFixedHeight(1)
        div.setAutoFillBackground(True)
        dp = div.palette()
        dp.setColor(div.backgroundRole(), _BORDER)
        div.setPalette(dp)
        self._c_vl.addWidget(div)
        self._c_vl.addSpacing(6)

        # ── power limits ─────────────────────────────────────
        self._c_vl.addWidget(_SecLabel("Power Limits"))
        self._c_vl.addSpacing(4)
        self._c_vl.addWidget(_PLCard("PL1  ·  Long-term",  pl1))
        self._c_vl.addSpacing(8)
        self._c_vl.addWidget(_PLCard("PL2  ·  Short-term", pl2))

        self._c_vl.addStretch()


# ──────────────────────────────────────────────────────────────────────────────
#  PUBLIC API  ←  only these three functions matter
# ──────────────────────────────────────────────────────────────────────────────

def sectionA(title: str) -> None:
    """
    Build / update the header bar (Section A).

    Parameters
    ----------
    title : str
        Text displayed in the header.

    Example
    -------
        monitor_ui.sectionA("CPU Core Monitor")
    """
    _bootstrap()
    _win.set_section_a(title)


def sectionB(n: int, status: list, frequency: list, on_click=None) -> None:
    """
    Build / update the core-block grid (Section B  —  left 75 %).

    Parameters
    ----------
    n         : int        Number of square block-buttons to render.
    status    : list[str]  Status string for each block  (e.g. "Active", "Idle").
                           Blocks are coloured green when the value is one of:
                           "active", "online", "running", "on", "1", "up", "busy".
                           All other values render red.
    frequency : list[str]  Frequency string for each block  (e.g. "3.2 GHz").
    on_click  : callable   Optional — called when a block button is clicked.
                           Signature:  on_click(index: int)
                           'index' is the zero-based position of the clicked block.

    Example
    -------
        def handle(i):
            print(f"Core {i} clicked")

        monitor_ui.sectionB(8, statuses, freqs, on_click=handle)
    """
    _bootstrap()
    _win.set_section_b(n, status, frequency, on_click)


def sectionC(percentage: float, pl1, pl2) -> None:
    """
    Build / update the metrics panel (Section C  —  right 25 %).

    Parameters
    ----------
    percentage : float  CPU frequency load for the donut chart  (0 – 100).
    pl1               : PL1 long-term power limit value  (shown in Watts).
    pl2               : PL2 short-term power limit value (shown in Watts).

    Example
    -------
        monitor_ui.sectionC(72.5, 45, 95)
    """
    _bootstrap()
    _win.set_section_c(percentage, pl1, pl2)


def run() -> None:
    """
    Start the Qt event loop.
    Call this ONCE after all three sections have been set up.
    This call blocks until the window is closed.

    Example
    -------
        monitor_ui.run()
    """
    _bootstrap()
    sys.exit(_app.exec())
