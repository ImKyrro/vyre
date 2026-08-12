PALETTE = {
    "bg": "#0d0f14",
    "surface": "#141720",
    "surface_alt": "#1a1e29",
    "surface_hover": "#20242f",
    "border": "#262b38",
    "border_strong": "#333a49",
    "text": "#e8eaf0",
    "text_dim": "#8b93a6",
    "text_faint": "#5c6479",
    "accent": "#7c5cff",
    "accent_hover": "#8f74ff",
    "accent_press": "#6a4bf0",
    "success": "#3fb87f",
    "danger": "#f0566a",
    "danger_hover": "#f56d7e",
}


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
    QLabel#Wordmark {{
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 1px;
        color: {p['text']};
    }}
    QLabel#WordmarkAccent {{
        color: {p['accent']};
    }}
    QLabel#Tagline {{
        color: {p['text_faint']};
        font-size: 11px;
        letter-spacing: 2px;
    }}
    QLabel#SectionLabel {{
        color: {p['text_faint']};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
    }}
    QLabel#EmptyTitle {{
        color: {p['text_dim']};
        font-size: 15px;
        font-weight: 600;
    }}
    QLabel#EmptyBody {{
        color: {p['text_faint']};
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
    QPushButton:pressed {{
        background-color: {p['surface']};
    }}
    QPushButton:disabled {{
        color: {p['text_faint']};
        background-color: {p['surface']};
    }}
    QPushButton#Primary {{
        background-color: {p['accent']};
        border: none;
        color: #ffffff;
    }}
    QPushButton#Primary:hover {{
        background-color: {p['accent_hover']};
    }}
    QPushButton#Primary:pressed {{
        background-color: {p['accent_press']};
    }}
    QPushButton#Danger {{
        background-color: transparent;
        border: 1px solid {p['danger']};
        color: {p['danger']};
    }}
    QPushButton#Danger:hover {{
        background-color: {p['danger']};
        color: #ffffff;
    }}
    QPushButton#Ghost {{
        background-color: transparent;
        border: none;
        color: {p['text_dim']};
        padding: 6px 10px;
    }}
    QPushButton#Ghost:hover {{
        background-color: {p['surface_hover']};
        color: {p['text']};
    }}
    QToolButton {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        color: {p['text_dim']};
        padding: 7px;
        font-size: 15px;
    }}
    QToolButton:hover {{
        background-color: {p['surface_hover']};
        color: {p['text']};
    }}
    QToolButton:disabled {{
        color: {p['text_faint']};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {p['bg']};
        border: 1px solid {p['border']};
        border-radius: 8px;
        padding: 9px 12px;
        color: {p['text']};
        font-size: 13px;
        selection-background-color: {p['accent']};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {p['accent']};
    }}
    QLineEdit#AddressBar {{
        background-color: {p['surface']};
        border-radius: 18px;
        padding: 8px 16px;
    }}
    QLineEdit#Search {{
        background-color: {p['bg']};
        border-radius: 18px;
        padding: 8px 14px;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {p['border_strong']};
        border-radius: 5px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {p['text_faint']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}
    QLabel#DialogTitle {{
        font-size: 18px;
        font-weight: 700;
    }}
    QLabel#DialogHint {{
        color: {p['text_dim']};
        font-size: 12px;
    }}
    QLabel#FieldLabel {{
        color: {p['text_dim']};
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#StatusText {{
        color: {p['text_dim']};
        font-size: 12px;
    }}
    QLabel#Toast {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border_strong']};
        border-radius: 8px;
        padding: 8px 14px;
        color: {p['text']};
        font-size: 12px;
    }}
    QMenu {{
        background-color: {p['surface_alt']};
        border: 1px solid {p['border_strong']};
        border-radius: 8px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 8px 20px;
        border-radius: 6px;
        color: {p['text']};
    }}
    QMenu::item:selected {{
        background-color: {p['accent']};
        color: #ffffff;
    }}
    QMenu::separator {{
        height: 1px;
        background: {p['border']};
        margin: 6px 8px;
    }}
    QToolTip {{
        background-color: {p['surface_alt']};
        color: {p['text']};
        border: 1px solid {p['border_strong']};
        padding: 6px 8px;
        border-radius: 6px;
    }}
    QTabWidget::pane {{
        border: 1px solid {p['border']};
        border-radius: 10px;
        top: -1px;
        background-color: {p['surface']};
    }}
    QTabBar {{
        qproperty-drawBase: 0;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {p['text_dim']};
        padding: 8px 14px;
        margin-right: 4px;
        border: 1px solid transparent;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-size: 12px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        color: {p['text']};
        background: {p['surface']};
        border: 1px solid {p['border']};
        border-bottom-color: {p['surface']};
    }}
    QTabBar::tab:hover:!selected {{
        color: {p['text']};
    }}
    """
