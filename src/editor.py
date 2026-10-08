import base64

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import (
    QAction, QColor, QFont, QIcon, QImage, QKeySequence,
    QTextCharFormat, QTextCursor, QTextDocument, QTextImageFormat, QTextListFormat,
)
from PyQt6.QtWidgets import (
    QColorDialog, QComboBox, QFileDialog, QFontComboBox,
    QHBoxLayout, QTextEdit, QToolBar, QToolButton, QVBoxLayout, QWidget,
)

from .html_utils import prepare_email_html


class RichTextEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = self._build_toolbar()
        layout.addWidget(self.toolbar)

        self.editor = QTextEdit()
        self.editor.setMinimumHeight(260)
        self.editor.setAcceptRichText(True)
        self.editor.setPlaceholderText(
            "Compose your email here…\n\nTip: Use {{Name}} where you want each vendor's name inserted automatically."
        )
        self.editor.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 1px solid #d1d5db;
                border-top: none;
                border-radius: 0 0 6px 6px;
                padding: 12px;
                color: #1f2937;
            }
        """)
        # Default font matches the toolbar and is what recipients see in Outlook
        self.editor.document().setDefaultFont(QFont("Calibri", 12))
        # Force dark text regardless of system theme
        self.editor.document().setDefaultStyleSheet("body { color: #1f2937; background: #ffffff; }")
        palette = self.editor.palette()
        from PyQt6.QtGui import QPalette
        palette.setColor(QPalette.ColorRole.Text, QColor("#1f2937"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        self.editor.setPalette(palette)

        self.editor.currentCharFormatChanged.connect(self._update_toolbar_state)
        self.editor.cursorPositionChanged.connect(self._update_alignment_state)
        layout.addWidget(self.editor)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def toHtml(self) -> str:
        return self.editor.toHtml()

    def toEmailHtml(self) -> str:
        """HTML rewritten so Outlook shows the same formatting as the editor."""
        return prepare_email_html(self.editor.toHtml())

    def isEmpty(self) -> bool:
        return self.editor.document().isEmpty()

    def setHtml(self, html: str):
        self.editor.setHtml(html)

    def clear(self):
        self.editor.clear()

    # ------------------------------------------------------------------
    # Toolbar construction
    # ------------------------------------------------------------------

    def _build_toolbar(self) -> QToolBar:
        tb = QToolBar()
        tb.setMovable(False)
        tb.setStyleSheet("""
            QToolBar {
                background: #f3f4f6;
                border: 1px solid #d1d5db;
                border-radius: 6px 6px 0 0;
                padding: 4px 6px;
                spacing: 2px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 13px;
                color: #374151;
            }
            QToolButton:hover { background: #e5e7eb; border-color: #d1d5db; }
            QToolButton:checked { background: #dbeafe; border-color: #93c5fd; color: #1d4ed8; }
            QComboBox {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 2px 6px;
                background: #ffffff;
                color: #1f2937;
                font-size: 12px;
                min-width: 48px;
            }
            QFontComboBox {
                border: 1px solid #d1d5db;
                border-radius: 4px;
                padding: 2px 4px;
                background: #ffffff;
                color: #1f2937;
                font-size: 12px;
                min-width: 120px;
            }
            QComboBox QAbstractItemView,
            QFontComboBox QAbstractItemView {
                background: #ffffff;
                color: #1f2937;
                selection-background-color: #eff6ff;
                selection-color: #1d4ed8;
                border: 1px solid #d1d5db;
            }
        """)

        # Font family
        self.font_combo = QFontComboBox()
        self.font_combo.setCurrentFont(QFont("Calibri"))
        self.font_combo.currentFontChanged.connect(self._set_font_family)
        tb.addWidget(self.font_combo)

        # Font size
        self.size_combo = QComboBox()
        for s in ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]:
            self.size_combo.addItem(s)
        self.size_combo.setCurrentText("12")
        self.size_combo.currentTextChanged.connect(self._set_font_size)
        tb.addWidget(self.size_combo)

        tb.addSeparator()

        # Bold
        self.act_bold = QAction("B", tb)
        self.act_bold.setCheckable(True)
        self.act_bold.setShortcut(QKeySequence.StandardKey.Bold)
        self.act_bold.triggered.connect(self._toggle_bold)
        btn_bold = tb.addAction(self.act_bold)
        tb.widgetForAction(self.act_bold).setFont(QFont("Arial", 11, QFont.Weight.Bold))

        # Italic
        self.act_italic = QAction("I", tb)
        self.act_italic.setCheckable(True)
        self.act_italic.setShortcut(QKeySequence.StandardKey.Italic)
        self.act_italic.triggered.connect(self._toggle_italic)
        tb.addAction(self.act_italic)
        tb.widgetForAction(self.act_italic).setFont(QFont("Arial", 11, QFont.Weight.Normal, True))

        # Underline
        self.act_underline = QAction("U", tb)
        self.act_underline.setCheckable(True)
        self.act_underline.setShortcut(QKeySequence.StandardKey.Underline)
        self.act_underline.triggered.connect(self._toggle_underline)
        tb.addAction(self.act_underline)

        tb.addSeparator()

        # Text colour
        self.color_btn = QToolButton()
        self.color_btn.setText("A▾")
        self.color_btn.setToolTip("Text colour")
        self._text_color = QColor("#000000")
        self.color_btn.clicked.connect(self._pick_text_color)
        tb.addWidget(self.color_btn)

        # Highlight colour
        self.highlight_btn = QToolButton()
        self.highlight_btn.setText("H▾")
        self.highlight_btn.setToolTip("Highlight colour")
        self.highlight_btn.clicked.connect(self._pick_highlight_color)
        tb.addWidget(self.highlight_btn)

        tb.addSeparator()

        # Alignment
        self.act_left = QAction("⬛L", tb)
        self.act_left.setCheckable(True)
        self.act_left.setToolTip("Align left")
        self.act_left.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))

        self.act_center = QAction("▥C", tb)
        self.act_center.setCheckable(True)
        self.act_center.setToolTip("Align centre")
        self.act_center.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignHCenter))

        self.act_right = QAction("⬛R", tb)
        self.act_right.setCheckable(True)
        self.act_right.setToolTip("Align right")
        self.act_right.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))

        self.act_justify = QAction("☰J", tb)
        self.act_justify.setCheckable(True)
        self.act_justify.setToolTip("Justify")
        self.act_justify.triggered.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignJustify))

        for act in (self.act_left, self.act_center, self.act_right, self.act_justify):
            tb.addAction(act)
        self.act_left.setChecked(True)

        tb.addSeparator()

        # Bullet list
        act_bullet = QAction("• List", tb)
        act_bullet.setToolTip("Bullet list")
        act_bullet.triggered.connect(self._insert_bullet_list)
        tb.addAction(act_bullet)

        # Numbered list
        act_numbered = QAction("1. List", tb)
        act_numbered.setToolTip("Numbered list")
        act_numbered.triggered.connect(self._insert_numbered_list)
        tb.addAction(act_numbered)

        tb.addSeparator()

        # Insert image
        act_img = QAction("🖼 Image", tb)
        act_img.setToolTip("Insert image into email body")
        act_img.triggered.connect(self._insert_image)
        tb.addAction(act_img)

        return tb

    # ------------------------------------------------------------------
    # Formatting actions
    # ------------------------------------------------------------------

    def _set_font_family(self, font: QFont):
        fmt = QTextCharFormat()
        fmt.setFontFamilies([font.family()])
        self._merge_format(fmt)

    def _set_font_size(self, size_str: str):
        try:
            size = int(size_str)
        except ValueError:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._merge_format(fmt)

    def _toggle_bold(self, checked: bool):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if checked else QFont.Weight.Normal)
        self._merge_format(fmt)

    def _toggle_italic(self, checked: bool):
        fmt = QTextCharFormat()
        fmt.setFontItalic(checked)
        self._merge_format(fmt)

    def _toggle_underline(self, checked: bool):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(checked)
        self._merge_format(fmt)

    def _pick_text_color(self):
        color = QColorDialog.getColor(self._text_color, self, "Text Colour")
        if color.isValid():
            self._text_color = color
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._merge_format(fmt)
            self.color_btn.setStyleSheet(f"color: {color.name()};")

    def _pick_highlight_color(self):
        color = QColorDialog.getColor(QColor("#ffff00"), self, "Highlight Colour")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            self._merge_format(fmt)

    def _set_alignment(self, alignment):
        self.editor.setAlignment(alignment)
        self._update_alignment_state()

    def _update_alignment_state(self):
        alignment = self.editor.alignment()
        self.act_center.setChecked(bool(alignment & Qt.AlignmentFlag.AlignHCenter))
        self.act_right.setChecked(bool(alignment & Qt.AlignmentFlag.AlignRight))
        self.act_justify.setChecked(bool(alignment & Qt.AlignmentFlag.AlignJustify))
        self.act_left.setChecked(not (
            self.act_center.isChecked() or self.act_right.isChecked() or self.act_justify.isChecked()
        ))

    def _insert_bullet_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.Style.ListDisc)
        cursor.createList(fmt)

    def _insert_numbered_list(self):
        cursor = self.editor.textCursor()
        fmt = QTextListFormat()
        fmt.setStyle(QTextListFormat.Style.ListDecimal)
        cursor.createList(fmt)

    def _insert_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Insert Image", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
        )
        if not path:
            return
        with open(path, "rb") as f:
            data = f.read()
        ext = path.rsplit(".", 1)[-1].lower()
        b64 = base64.b64encode(data).decode()
        data_uri = f"data:image/{ext};base64,{b64}"

        img = QImage(path)
        if img.isNull():
            return
        self.editor.document().addResource(
            QTextDocument.ResourceType.ImageResource, QUrl(data_uri), img
        )
        # Scale down if very large; the size is written into the HTML so
        # Outlook shows the image at the same size as the editor
        fmt = QTextImageFormat()
        fmt.setName(data_uri)
        width, height = img.width(), img.height()
        if width > 600:
            height = round(height * 600 / width)
            width = 600
        fmt.setWidth(width)
        fmt.setHeight(height)
        self.editor.textCursor().insertImage(fmt)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _merge_format(self, fmt: QTextCharFormat):
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        self.editor.mergeCurrentCharFormat(fmt)

    def _update_toolbar_state(self, fmt: QTextCharFormat):
        self.act_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.act_italic.setChecked(fmt.fontItalic())
        self.act_underline.setChecked(fmt.fontUnderline())
        if fmt.fontPointSize() > 0:
            self.size_combo.setCurrentText(str(int(fmt.fontPointSize())))
        families = fmt.fontFamilies()
        if families:
            self.font_combo.setCurrentFont(QFont(families[0]))
