"""Design system cho Dashboard V2: màu, kiểu chữ và khoảng cách thống nhất."""

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24}
COLORS = {
    "background": "#07111f",
    "panel": "#0e1c2e",
    "border": "#203249",
    "text": "#dce7f4",
    "muted": "#8298b1",
    "cyan": "#50d4ed",
    "blue": "#438fff",
    "valid": "#48d5b1",
    "warning": "#f0c36a",
    "error": "#ff7b87",
}


def apply_application_theme(app):
    """Bảng màu Qt thống nhất cho cả điều khiển chuẩn và nút tăng/giảm."""
    from PySide6.QtGui import QPalette, QColor

    if getattr(app, "_mechavision_theme_applied", False):
        return
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in [
        (QPalette.Window, COLORS["background"]),
        (QPalette.WindowText, COLORS["text"]),
        (QPalette.Base, "#081625"),
        (QPalette.AlternateBase, "#102135"),
        (QPalette.Text, COLORS["text"]),
        (QPalette.Button, "#14273d"),
        (QPalette.ButtonText, COLORS["text"]),
        (QPalette.Highlight, "#205475"),
        (QPalette.HighlightedText, "#ffffff"),
        (QPalette.ToolTipBase, "#18324b"),
        (QPalette.ToolTipText, "#e9f4ff"),
    ]:
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app._mechavision_theme_applied = True


STYLE = """
QWidget { color:#dce7f4; font-family:"Segoe UI"; font-size:12px; }
QMainWindow, QWidget#shell { background:#07111f; }
QFrame#sidebar { background:#0a1625; border-right:1px solid #1b2b40; }
QFrame#panel { background:#0e1c2e; border:1px solid #203249; border-radius:10px; }
QFrame#kpi { background:#0e1c2e; border:1px solid #203249; border-radius:9px; }
QFrame#notice { background:#101f31; border:1px solid #263c54; border-radius:8px; }
QLabel { background:transparent; border:none; }
QLabel#brand { color:#f0f6ff; font-size:17px; font-weight:700; letter-spacing:1px; }
QLabel#brand_icon { background:#153a51; color:#62d8ef; border:1px solid #28617c; border-radius:9px; font-size:19px; font-weight:700; }
QLabel#page_title { color:#f2f7ff; font-size:24px; font-weight:700; }
QLabel#panel_title { color:#e6effb; font-size:13px; font-weight:600; }
QLabel#eyebrow { color:#8298b1; font-size:10px; font-weight:600; letter-spacing:1px; }
QLabel#muted { color:#8298b1; font-size:11px; }
QLabel#kpi_value { color:#eff7ff; font-size:28px; font-weight:600; }
QLabel#kpi_state { color:#b6c9de; font-size:16px; font-weight:600; }
QLabel#badge { border-radius:5px; padding:5px 9px; font-size:10px; font-weight:600; background:#173148; color:#7fd4ed; }
QLabel#badge[tone="warning"] { background:#392d19; color:#f0c36a; }
QLabel#badge[tone="error"] { background:#3d202b; color:#ff939b; }
QLabel#badge[tone="muted"] { background:#1b2b3e; color:#a1b3c8; }
QLabel#badge[tone="valid"] { background:#13372f; color:#54d9b6; }
QPushButton { color:#c6d7e9; background:#14273d; border:1px solid #29415d; border-radius:6px; padding:8px 13px; font-weight:600; }
QPushButton:hover { background:#1e3953; border-color:#416782; }
QPushButton:pressed { background:#0a2035; }
QPushButton:disabled { color:#566d85; background:#101f30; border-color:#1c3047; }
QPushButton:focus { border:1px solid #4ac5e5; }
QPushButton#primary { background:#1684c1; border-color:#269bd9; color:#ffffff; }
QPushButton#primary:hover { background:#219bd6; }
QPushButton#primary:disabled { background:#163449; color:#57778e; border-color:#25465e; }
QPushButton#danger { background:#38232f; color:#f39ca4; border-color:#603744; }
QPushButton#danger:disabled { background:#171e2c; color:#665867; border-color:#293040; }
QPushButton#nav { text-align:left; background:transparent; border:1px solid transparent; border-radius:7px; padding:12px 11px; color:#8ba0b8; }
QPushButton#nav:hover { background:#11263a; color:#d7e7f6; }
QPushButton#nav:checked { background:#12354c; color:#6bdbf2; border:1px solid #1c5168; }
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QPlainTextEdit { background:#081625; color:#dce7f4; border:1px solid #2a405a; border-radius:6px; padding:7px 9px; selection-background-color:#205475; }
QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus { border-color:#35b1d2; }
QLineEdit:disabled,QComboBox:disabled { color:#667d94; border-color:#203147; }
QComboBox QAbstractItemView { background:#10243a; color:#dce7f4; selection-background-color:#1b4a66; }
QCheckBox { spacing:7px; color:#9db1c8; }
QCheckBox::indicator { width:14px; height:14px; border:1px solid #395570; border-radius:3px; background:#0a1929; }
QCheckBox::indicator:checked { background:#2ca4cb; border-color:#59c9e7; }
QTableWidget { background:#0e1c2e; alternate-background-color:#102135; color:#bfd0e2; border:none; gridline-color:#1c3047; selection-background-color:#1d405c; }
QTableWidget::item { padding:5px 7px; border-bottom:1px solid #1b2d43; }
QHeaderView::section { background:#11253b; color:#8da9c5; border:none; border-bottom:1px solid #2b425c; padding:7px; font-weight:600; font-size:11px; }
QTableCornerButton::section { background:#11253b; border:none; }
QScrollArea { border:none; background:transparent; }
QScrollBar:vertical { width:8px; background:#0a1523; margin:0; }
QScrollBar::handle:vertical { background:#2b435d; border-radius:4px; min-height:24px; }
QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height:0; }
QScrollBar:horizontal { height:8px; background:#0a1523; }
QScrollBar::handle:horizontal { background:#2b435d; border-radius:4px; }
QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal { width:0; }
QToolTip { background:#18324b; color:#e9f4ff; border:1px solid #395a77; padding:6px; }
"""
