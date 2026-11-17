"""Filigrane "vinyle" pour les listes vides (Face A / Face B).

Le mixin `WatermarkMixin` dessine, derriere une liste vide :
  - une onde sonore tres discrete, traversant la zone de bord a bord ;
  - un disque vinyle avec sillons et etiquette centrale (FACE A / FACE B) ;
  - un titre et un sous-titre explicatifs.

Tout est derive de la palette Qt courante : le rendu suit donc les themes
clair et sombre. Le disque ne tourne que pendant un glisser-deposer, le timer
est sinon arrete (aucun cout au repos).
"""

import math

from .qt_compat import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
    QPointF,
    QRadialGradient,
    QRectF,
    Qt,
    QTimer,
)

# Parametres de rendu (opacites volontairement faibles : c'est un filigrane).
SPIN_SECONDS_PER_TURN = 8.0
SPIN_FPS = 30
WAVE_BARS = 90


def _enum(owner, group, name):
    """Acces compatible PyQt5 / PyQt6 aux enumerations."""
    container = getattr(owner, group, owner)
    return getattr(container, name)


class WatermarkMixin:
    """A melanger a un QAbstractItemView (QTreeWidget, QListWidget...).

    Appeler `_init_watermark()` dans le constructeur de la classe hote, puis
    `_paint_watermark_if_empty()` au debut de `paintEvent`.
    """

    def _init_watermark(
        self,
        face: str = "A",
        title: str = "",
        subtitle: str = "",
        hover_title: str = "",
        accent: str = "#4a90d9",
    ) -> None:
        self._wm_face = face
        self._wm_title = title
        self._wm_subtitle = subtitle
        self._wm_hover_title = hover_title
        self._wm_accent = QColor(accent)
        self._wm_hover = False
        self._wm_angle = 0.0

        self._wm_timer = QTimer(self)
        self._wm_timer.setInterval(int(1000 / SPIN_FPS))
        self._wm_timer.timeout.connect(self._wm_rotate)

    # ------------------------------------------------------------------ API
    def set_watermark_texts(
        self, title: str, subtitle: str, hover_title: str = ""
    ) -> None:
        """Met a jour les textes (utilise lors du changement de langue)."""
        self._wm_title = title
        self._wm_subtitle = subtitle
        self._wm_hover_title = hover_title
        self.viewport().update()

    def set_watermark_hover(self, hovering: bool) -> None:
        if hovering == self._wm_hover:
            return
        self._wm_hover = hovering
        if hovering:
            self._wm_timer.start()
        else:
            self._wm_timer.stop()
        self.viewport().update()

    # ------------------------------------------------------------- interne
    def _wm_rotate(self) -> None:
        self._wm_angle = (
            self._wm_angle + 360.0 / (SPIN_SECONDS_PER_TURN * SPIN_FPS)
        ) % 360.0
        self.viewport().update()

    def _is_watermark_visible(self) -> bool:
        return self.topLevelItemCount() == 0 if hasattr(self, "topLevelItemCount") else self.count() == 0

    def _paint_watermark_if_empty(self) -> None:
        if not self._is_watermark_visible():
            return
        painter = QPainter(self.viewport())
        try:
            painter.setRenderHint(_enum(QPainter, "RenderHint", "Antialiasing"))
            self._paint_watermark(painter)
        finally:
            painter.end()

    def _base_color(self) -> QColor:
        role = _enum(self.palette().__class__, "ColorRole", "Text")
        return QColor(self.palette().color(role))

    def _paint_watermark(self, painter: QPainter) -> None:
        width = self.viewport().width()
        height = self.viewport().height()
        if width < 120 or height < 140:
            return  # zone trop petite : on ne dessine rien plutot que mal

        base = self._base_color()
        radius = min(width * 0.30, height * 0.24)
        cx, cy = width / 2.0, height * 0.38

        self._draw_wave(painter, base, width, cy)

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._wm_angle)
        self._draw_disc(painter, base, radius)
        painter.restore()

        self._draw_texts(painter, base, width, cy + radius + 22)

    def _draw_wave(self, painter, base: QColor, width: float, cy: float) -> None:
        step = width / WAVE_BARS
        pen_width = max(1.5, step * 0.45)
        round_cap = _enum(Qt, "PenCapStyle", "RoundCap")
        for i in range(WAVE_BARS):
            t = i / (WAVE_BARS - 1)
            envelope = math.sin(t * math.pi)  # nul aux bords
            amplitude = 0.4 + 0.6 * abs(math.sin(i * 0.55) * math.cos(i * 0.21))
            half = 5 + 36 * envelope * amplitude
            color = QColor(base)
            color.setAlphaF(0.09 * envelope)
            pen = QPen(color)
            pen.setWidthF(pen_width)
            pen.setCapStyle(round_cap)
            painter.setPen(pen)
            x = i * step + step / 2.0
            painter.drawLine(QPointF(x, cy - half), QPointF(x, cy + half))

    def _draw_disc(self, painter, base: QColor, radius: float) -> None:
        boost = 0.10 if self._wm_hover else 0.0
        no_pen = _enum(Qt, "PenStyle", "NoPen")
        no_brush = _enum(Qt, "BrushStyle", "NoBrush")

        # Corps du disque (degrade radial).
        gradient = QRadialGradient(QPointF(0, 0), radius)
        inner, outer = QColor(base), QColor(base)
        inner.setAlphaF(0.15 + boost)
        outer.setAlphaF(0.06 + boost)
        gradient.setColorAt(0.0, inner)
        gradient.setColorAt(1.0, outer)
        painter.setPen(no_pen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        # Sillons.
        groove = QColor(base)
        groove.setAlphaF(0.12)
        painter.setPen(QPen(groove, 1))
        painter.setBrush(no_brush)
        for k in range(1, 9):
            r = radius * (0.42 + k * 0.065)
            painter.drawEllipse(QPointF(0, 0), r, r)

        # Etiquette centrale.
        label_radius = radius * 0.34
        label = QColor(self._wm_accent)
        label.setAlphaF(0.55 if self._wm_hover else 0.30)
        painter.setPen(no_pen)
        painter.setBrush(label)
        painter.drawEllipse(QPointF(0, 0), label_radius, label_radius)

        # Texte "FACE A" / "FACE B".
        font = QFont(self.font())
        font.setPointSizeF(max(6.5, radius * 0.075))
        font.setBold(True)
        font.setLetterSpacing(_enum(QFont, "SpacingType", "AbsoluteSpacing"), 1.5)
        painter.setFont(font)
        text_color = QColor(base)
        text_color.setAlphaF(0.60)
        painter.setPen(text_color)
        painter.drawText(
            QRectF(-label_radius, -label_radius, 2 * label_radius, 2 * label_radius),
            _enum(Qt, "AlignmentFlag", "AlignCenter"),
            f"FACE {self._wm_face}",
        )

        # Trou central.
        painter.setPen(no_pen)
        painter.setBrush(self.palette().base())
        hole = max(2.0, radius * 0.03)
        painter.drawEllipse(QPointF(0, 0), hole, hole)

    def _draw_texts(self, painter, base: QColor, width: float, y: float) -> None:
        align = _enum(Qt, "AlignmentFlag", "AlignCenter")
        base_size = self.font().pointSizeF()
        if base_size <= 0:
            base_size = 10.0

        title = self._wm_title
        if self._wm_hover and self._wm_hover_title:
            title = self._wm_hover_title
        title_color = QColor(base)
        title_color.setAlphaF(0.85 if self._wm_hover else 0.55)
        title_font = QFont(self.font())
        title_font.setPointSizeF(base_size * 1.25)
        painter.setFont(title_font)
        painter.setPen(title_color)
        painter.drawText(QRectF(8, y, width - 16, 26), align, title)

        if self._wm_subtitle:
            sub_color = QColor(base)
            sub_color.setAlphaF(0.35)
            sub_font = QFont(self.font())
            sub_font.setPointSizeF(base_size * 0.9)
            sub_font.setLetterSpacing(
                _enum(QFont, "SpacingType", "AbsoluteSpacing"), 1.2
            )
            painter.setFont(sub_font)
            painter.setPen(sub_color)
            painter.drawText(QRectF(8, y + 26, width - 16, 22), align, self._wm_subtitle)
