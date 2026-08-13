PALETTE = {
    "bg": "#0a0a0b",
    "surface": "#101012",
    "surface_alt": "#17171a",
    "surface_hover": "#1d1d21",
    "border": "#232327",
    "border_strong": "#303036",
    "text": "#f2f2f3",
    "text_dim": "#9a9aa2",
    "text_faint": "#5f5f68",
    "accent": "#e5484d",
    "accent_hover": "#f05a5f",
    "accent_press": "#cf3b40",
    "accent_soft": "#2a1416",
    "online": "#3fb950",
    "success": "#3fb950",
    "studio": "#d29922",
    "offline": "#5f5f68",
    "danger": "#ff6b6b",
    "info": "#4c8dff",
}


def status_color(kind: str) -> str:
    return {
        "online": PALETTE["online"],
        "ingame": PALETTE["online"],
        "studio": PALETTE["studio"],
        "offline": PALETTE["offline"],
    }.get(kind, PALETTE["offline"])


def stylesheet() -> str:
    p = PALETTE
    return f"""
    * {{
        font-family: "Segoe UI", "Inter", sans-serif;
        color: {p['text']};
        outline: none;
    }}
    QMainWindow, QDialog, QWidget#Root {{
        background-color: {p['bg']};
    }}
    QWidget#Sidebar {{
        background-color: {p['surface']};
        border-right: 1px solid {p['border']};
    }}
    QWidget#DetailPane {{
        background-color: {p['bg']};
    }}
    QWidget#Card {{
        background-color: {p['surface']};
        border: 1px solid {p['border']};
        border-radius: 12px;
    }}
    QWidget#TopBar {{
        background-color: {p['surface']};
        border-bottom: 1px solid {p['border']};
    }}
    QLabel#Wordmark {{
        font-size: 21px;
        font-weight: 800;
        letter-spacing: 3px;
        color: {p['text']};
    }}
    QLabel#Tagline {{
        color: {p['text_faint']};
        font-size: 10px;
        letter-spacing: 3px;
        font-weight: 700;
    }}
    QLabel#SectionLabel {{
        color: {p['text_faint']};
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1.5px;
    }}
    QLabel#H1 {{
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.3px;
    }}
    QLabel#H2 {{
        font-size: 16px;
        font-weight: 700;
    }}
    QLabel#Muted {{
        color: {p['text_dim']};
        font-size: 12px;
    }}
    QLabel#Faint {{
        color: {p['text_faint']};
        font-size: 12px;
    }}
    QLabel#EmptyTitle {{
        color: {p['text_dim']};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#StatValue {{
        font-size: 18px;
        font-weight: 800;
    }}
    QLabel#StatLabel {{
        color: {p['text_faint']};
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel#DialogTitle {{
        font-size: 18px;
        font-weight: 800;
    }}
    QLabel#DialogHint, QLabel#FieldLabel {{
        color: {p['text_dim']};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#StatusText {{
        color: {p['text_dim']};
        font-size: 12px;
    }}
    QPushButton {{
        background-color: {p['surface_alt']};
        color: {p['text']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 9px 14px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {p['surface_hover']};
        border-color: {p['border_strong']};
    }}
    QPushButton:pressed {{ background-color: {p['surface']}; }}
    QPushButton:disabled {{ color: {p['text_faint']}; background-color: {p['surface']}; }}
    QPushButton#Primary {{
        background-color: {p['accent']};
        border: 1px solid {p['accent']};
        color: #ffffff;
    }}
    QPushButton#Primary:hover {{ background-color: {p['accent_hover']}; border-color: {p['accent_hover']}; }}
    QPushButton#Primary:pressed {{ background-color: {p['accent_press']}; }}
    QPushButton#Primary:disabled {{ background-color: {p['accent_soft']}; border-color: {p['accent_soft']}; color: {p['text_faint']}; }}
    QPushButton#Danger {{
        background-color: transparent;
        border: 1px solid {p['danger']};
        color: {p['danger']};
    }}
    QPushButton#Danger:hover {{ background-color: {p['danger']}; color: #ffffff; }}
    QPushButton#Ghost {{
        background-color: transparent;
        border: none;
        color: {p['text_dim']};
        padding: 7px 10px;
    }}
    QPushButton#Ghost:hover {{ background-color: {p['surface_hover']}; color: {p['text']}; }}
    QToolButton {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        color: {p['text_dim']};
        padding: 7px;
        font-size: 15px;
    }}
    QToolButton:hover {{ background-color: {p['surface_hover']}; color: {p['text']}; }}
    QToolButton:disabled {{ color: {p['text_faint']}; }}
    QToolButton#Star {{ font-size: 16px; padding: 2px; }}
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
        background-color: {p['bg']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 9px 12px;
        color: {p['text']};
        font-size: 13px;
        selection-background-color: {p['accent']};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border-color: {p['accent']};
    }}
    QLineEdit#AddressBar {{ background-color: {p['bg']}; border-radius: 18px; padding: 8px 16px; }}
    QLineEdit#Search {{ background-color: {p['bg']}; border-radius: 18px; padding: 8px 14px; }}
    QComboBox::drop-down {{ border: none; width: 22px; }}
    QComboBox::down-arrow {{ image: none; }}
    QComboBox QAbstractItemView {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border_strong']};
        border-radius: 8px;
        selection-background-color: {p['accent']};
        padding: 4px;
    }}
    QCheckBox {{ color: {p['text']}; font-size: 13px; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border: 1px solid {p['border_strong']};
        border-radius: 5px;
        background: {p['bg']};
    }}
    QCheckBox::indicator:checked {{
        background: {p['accent']};
        border-color: {p['accent']};
    }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {p['border_strong']}; border-radius: 5px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: {p['text_faint']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
    QScrollBar::handle:horizontal {{ background: {p['border_strong']}; border-radius: 5px; min-width: 28px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QTableWidget, QTableView {{
        background-color: {p['bg']};
        border: 1px solid {p['border']};
        border-radius: 10px;
        gridline-color: {p['border']};
        selection-background-color: {p['accent_soft']};
        selection-color: {p['text']};
    }}
    QTableView::item {{ padding: 6px 8px; }}
    QHeaderView::section {{
        background-color: {p['surface_alt']};
        color: {p['text_dim']};
        border: none;
        border-bottom: 1px solid {p['border']};
        padding: 8px;
        font-size: 11px;
        font-weight: 700;
    }}
    QTabWidget::pane {{
        border: none;
        border-top: 1px solid {p['border']};
        top: -1px;
        background: transparent;
    }}
    QTabBar {{ qproperty-drawBase: 0; }}
    QTabBar::tab {{
        background: transparent;
        color: {p['text_dim']};
        padding: 9px 16px;
        margin-right: 2px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 12px;
        font-weight: 700;
    }}
    QTabBar::tab:selected {{
        color: {p['text']};
        border-bottom: 2px solid {p['accent']};
    }}
    QTabBar::tab:hover:!selected {{ color: {p['text']}; }}
    QMenu {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border_strong']};
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{ padding: 8px 22px; border-radius: 6px; color: {p['text']}; }}
    QMenu::item:selected {{ background-color: {p['accent']}; color: #ffffff; }}
    QMenu::separator {{ height: 1px; background: {p['border']}; margin: 6px 8px; }}
    QToolTip {{
        background-color: {p['surface_alt']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        padding: 6px 8px;
        border-radius: 6px;
    }}
    QLabel#Toast {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border_strong']};
        border-radius: 10px;
        padding: 9px 16px;
        color: {p['text']};
        font-size: 12px;
        font-weight: 600;
    }}
    """
