from pathlib import Path
import sys
from PySide6.QtCore import Qt, QDate, QStandardPaths, QTimer
from PySide6.QtGui import QFontDatabase, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QFrame,
    QDialog,
    QFormLayout,
    QTextEdit,
    QDateEdit,
    QMessageBox,
    QFileDialog,
    QSpinBox,
    QDoubleSpinBox,
    QStackedWidget,
    QButtonGroup,
)


def label(text="", kind=""):
    widget = QLabel(str(text))
    widget.setTextFormat(Qt.PlainText)
    widget.setAlignment(Qt.AlignAbsolute | Qt.AlignRight | Qt.AlignVCenter)
    if kind:
        widget.setObjectName(kind)
    return widget


def button(text, callback=None, kind="primary"):
    widget = QPushButton(text)
    widget.setObjectName(kind)
    widget.setProperty("kind", kind)
    widget.setCursor(Qt.PointingHandCursor)
    if callback:
        widget.clicked.connect(callback)
    return widget


def line(placeholder=""):
    widget = QLineEdit()
    widget.setPlaceholderText(placeholder)
    widget.setMinimumHeight(42)
    return widget


def combo(items):
    widget = QComboBox()
    widget.setMinimumHeight(42)
    for value, text in items:
        widget.addItem(text, value)
    return widget


def date_edit():
    widget = QDateEdit(QDate.currentDate())
    widget.setCalendarPopup(True)
    widget.setDisplayFormat("yyyy/MM/dd")
    widget.setMinimumHeight(42)
    return widget


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.setSelectionMode(QAbstractItemView.SingleSelection)
    widget.setAlternatingRowColors(False)
    widget.verticalHeader().setVisible(False)
    widget.verticalHeader().setDefaultSectionSize(56)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    widget.setShowGrid(False)
    widget.setMinimumHeight(250)
    return widget


def fill_table(widget, rows, columns):
    widget.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, key in enumerate(columns):
            value = key(row) if callable(key) else row.get(key, "")
            item = QTableWidgetItem(str(value if value is not None else "—"))
            item.setTextAlignment(Qt.AlignAbsolute | Qt.AlignRight | Qt.AlignVCenter)
            item.setData(Qt.UserRole, row.get("id"))
            widget.setItem(i, j, item)


def panel():
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(16)
    return frame, layout


def form_dialog(parent, title):
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setMinimumWidth(500)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(26, 24, 26, 24)
    layout.setSpacing(18)
    layout.addWidget(label(title, "dialogTitle"))
    form = QFormLayout()
    form.setSpacing(13)
    form.setLabelAlignment(Qt.AlignAbsolute | Qt.AlignRight)
    layout.addLayout(form)
    error = label("", "error")
    error.setWordWrap(True)
    layout.addWidget(error)
    return dialog, layout, form, error


def show_error(parent, message):
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Warning)
    box.setWindowTitle("تعذر تنفيذ العملية")
    box.setTextFormat(Qt.PlainText)
    box.setText(str(message))
    box.exec()


def resource(name):
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / name


def application(name, color, dark):
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName(name)
    app.setOrganizationName("iprigner")
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")
    if resource("assets/icon.png").exists():
        app.setWindowIcon(QIcon(str(resource("assets/icon.png"))))
    for f in ["assets/font.ttf", "assets/font-bold.ttf"]:
        if resource(f).exists():
            QFontDatabase.addApplicationFont(str(resource(f)))
    app.setFont(QFont("Tajawal", 11))
    app.setStyleSheet(STYLE.replace("__COLOR__", color).replace("__DARK__", dark))
    return app


def default_data(name):
    return (
        Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
        / "records.sqlite3"
    )


class Shell(QMainWindow):
    def __init__(self, name, english, subtitle, pages):
        super().__init__()
        self.setWindowTitle(name + " | " + english + " — iprigner")
        self.resize(1280, 850)
        self.setMinimumSize(980, 680)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(24, 35, 24, 26)
        nav.setSpacing(12)
        nav.addWidget(label(name, "brand"))
        nav.addWidget(label(english, "english"))
        nav.addSpacing(48)
        nav.addWidget(label("مساحة العمل", "navHint"))
        self.stack = QStackedWidget()
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        for i, text in enumerate(pages):
            item = button(text, kind="nav")
            item.setCheckable(True)
            self.nav_group.addButton(item, i)
            nav.addWidget(item)
            if i == 0:
                item.setChecked(True)
            item.clicked.connect(
                lambda checked=False, index=i: self.stack.setCurrentIndex(index)
            )
        nav.addStretch()
        nav.addWidget(label("بياناتك على جهازك", "sidebarTitle"))
        hint = label("تطبيق محلي مستقل\nلا يتطلب حسابًا سحابيًا", "navHint")
        hint.setWordWrap(True)
        nav.addWidget(hint)
        nav.addSpacing(22)
        nav.addWidget(label("عبدالمجيد حسن كابلي", "sidebarTitle"))
        nav.addWidget(label("@iprigner", "navHint"))
        outer.addWidget(sidebar)
        body = QWidget()
        outer.addWidget(body, 1)
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(30, 25, 30, 20)
        body_layout.setSpacing(22)
        top = QHBoxLayout()
        top.addWidget(label("مساحة العمل / " + name, "muted"))
        top.addStretch()
        top.addWidget(
            label("●  محلي · " + QDate.currentDate().toString("yyyy/MM/dd"), "muted")
        )
        body_layout.addLayout(top)
        header = QVBoxLayout()
        header.setSpacing(8)
        header.addWidget(label(subtitle, "heading"))
        header.addWidget(label("تصميم واضح، وبيانات تحفظ كل التفاصيل.", "muted"))
        body_layout.addLayout(header)
        body_layout.addWidget(self.stack, 1)
        self.message = label("جاهز للعمل", "footer")
        body_layout.addWidget(self.message)

    def notify(self, text):
        self.message.setText(text)


def metrics(items):
    row = QHBoxLayout()
    row.setSpacing(16)
    values = []
    for title, hint in items:
        frame, layout = panel()
        layout.setSpacing(10)
        layout.addWidget(label(title, "muted"))
        value = label("0", "metric")
        layout.addWidget(value)
        layout.addWidget(label(hint, "small"))
        row.addWidget(frame, 1)
        values.append(value)
    return row, values


STYLE = r"""
QMainWindow,QDialog{background:#f4f6f9;color:#20303b}QWidget{font-family:Tajawal;font-size:14px;color:#20303b}QLabel{background:transparent}QLabel#heading{font-size:32px;font-weight:800}QLabel#dialogTitle{font-size:24px;font-weight:700}QLabel#muted{color:#788994;font-size:12px}QLabel#small{color:#8a98a2;font-size:11px}QLabel#footer{color:#7f8f99;font-size:11px;padding:5px}QLabel#error{color:#b23b46;font-size:12px}QLabel#metric{font-size:30px;font-weight:800;color:__COLOR__}QFrame#panel{background:#fff;border:1px solid #e0e7ed;border-radius:14px}QFrame#sidebar{background:__DARK__}QFrame#sidebar QLabel{color:#d9e2e9}QLabel#brand{font-size:38px;font-weight:800;color:#fff}QLabel#english{font-size:10px;color:#97adbb}QLabel#navHint{font-size:11px;color:#849aa9;}QLabel#sidebarTitle{font-size:13px;color:#d2e1eb;font-weight:600}QPushButton{border:0;border-radius:8px;min-height:42px;padding:2px 16px;font-size:13px}QPushButton[kind="primary"]{background:__COLOR__;color:white;font-weight:700}QPushButton[kind="primary"]:hover{background:__DARK__}QPushButton[kind="secondary"]{background:#eaf0f5;color:__COLOR__}QPushButton[kind="secondary"]:hover{background:#dce6ed}QPushButton[kind="danger"]{background:#fff0f0;color:#a63843}QPushButton[kind="nav"]{background:transparent;color:#91a7b7;text-align:right;padding:2px 14px;font-size:14px}QPushButton[kind="nav"]:checked{background:rgba(255,255,255,20);color:white;border-right:3px solid __COLOR__}QPushButton:disabled{background:#dce4e9;color:#98a7b2}QLineEdit,QTextEdit,QComboBox,QDateEdit,QSpinBox,QDoubleSpinBox{background:white;border:1px solid #d8e1e8;border-radius:8px;padding:8px 10px;selection-background-color:__COLOR__;min-height:24px}QLineEdit:focus,QTextEdit:focus,QComboBox:focus,QDateEdit:focus{border:1px solid __COLOR__}QComboBox::drop-down{border:0;width:24px}QTableWidget{background:white;border:0;selection-background-color:#e7eff8;selection-color:#20303b;alternate-background-color:#f8fafc}QTableWidget::item{padding:7px;border-bottom:1px solid #edf1f5}QHeaderView::section{background:#f5f8fa;color:#8494a0;border:0;padding:12px 8px;font-size:11px}QTableCornerButton::section{background:#f5f8fa;border:0}QScrollBar:vertical{background:transparent;width:9px;margin:0}QScrollBar::handle:vertical{background:#d0dce5;border-radius:4px;min-height:30px}QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}QToolTip{background:__DARK__;color:white;border:0;padding:6px}
"""
