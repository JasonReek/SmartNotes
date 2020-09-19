from PySide2.QtWidgets import (QApplication, QMainWindow, QLineEdit, QDialog, QAction, QFormLayout, QMessageBox, QTextEdit, QDockWidget, QMenu, QComboBox, QFrame, QListWidget, 
                               QTabWidget, QAbstractItemView, QActionGroup, QColorDialog, QToolBar, QFontComboBox, QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton, QAction)
from PySide2.QtGui import (QTextCharFormat, QIntValidator, QKeySequence, QBrush, QTextListFormat, QFont, QColor, QIcon, QPixmap, QColor)
from PySide2.QtCore import (Qt)
from sn_widgets import VBreakLine
import os 
import re


class HighlighterButton(QPushButton):
    def __init__(self, color="yellow"):
        super().__init__()
        self.color = color
        self.setStyleSheet("QPushButton{background-color: "+color+"; width: 8; height: 8;}")
        self.setToolTip(str(color))

    def setColor(self, color):
        self.setStyleSheet("QPushButton{background-color: "+color+"; width: 8; height: 8;}")
        self.setToolTip(str(color))

class FontToolBar(QToolBar):
    def __init__(self, title="Font", parent=None):
        super().__init__(title, parent)
        self._parent = parent 
        self.setObjectName("ftoolbar")
        self.setStyleSheet(""" 
            QWidget[objectName^="ftoolbar"]{background-color: #777777;}
            QPushButton{background-color: #777777;}
            QToolButton{background-color: #777777;};
        """)
        
        font = QFont()
        font.setPointSize(12)
        font.setFamily("Times New Roman")
        self._font_families = QFontComboBox()
        self._font_families.setCurrentFont(font)
        self._font_families.currentFontChanged.connect(self.keepFontSize)

    
        self._font_sizes = QComboBox()

        self._font_sizes.setEditable(True)
        validator = QIntValidator()
        self._font_sizes.setValidator(validator)
        FONT_SIZES = ['8', '9', '11', '12', '14', '16', '18', '20', '22', '24', '26', '28', '36', '48', '72']
        self._font_sizes.addItems(FONT_SIZES)
        self._font_sizes.activated.connect(self.changeFontSize)
        self._font_sizes.setCurrentIndex(3)
        
        self.addWidget(QLabel(" Font: "))
        self.addWidget(self._font_families)
        self.addWidget(self._font_sizes)

        # Bold Button
        self.bold_action = QAction(QIcon(os.path.join("images", "edit-bold.png")), "Bold", self)
        self.bold_action.setStatusTip("Bold")
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        self.addAction(self.bold_action)

        # Italic Button
        self.italic_action = QAction(QIcon(os.path.join("images", "edit-italic.png")), "Italic", self)
        self.italic_action.setStatusTip("Italic")
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        self.addAction(self.italic_action)

        # Underline Button
        self.underline_action = QAction(QIcon(os.path.join("images", "edit-underline.png")), "Underline", self)
        self.underline_action.setStatusTip("Underline")
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        self.addAction(self.underline_action)
        self.addWidget(VBreakLine(self))

        # Font Color Button
        self.font_color_action = QAction(QIcon(os.path.join("images", "edit-color.png")), "Font Color", self)
        self.font_color_button = HighlighterButton(color="#000000")
        self.font_color_action.setStatusTip("Font Color")
        self.font_color_action.triggered.connect(self.changeFontColor)
        self.font_color_button.clicked.connect(self.changeFontColor)
        self.addAction(self.font_color_action)
        self.addWidget(self.font_color_button)
        self.addWidget(VBreakLine(self))

        # HighLighter Color Button 
        self.highlighter_action = QAction(QIcon(os.path.join("images", "edit-highlighter.png")), "Highlight Color")
        self.highlighter_button = HighlighterButton(color="yellow")
        self.highlighter_action.setStatusTip("Highlighter")
        self.highlighter_action.triggered.connect(self.changeHighlighterColor)
        self.highlighter_button.clicked.connect(self.changeHighlighterColor)
        self.addAction(self.highlighter_action)
        self.addWidget(self.highlighter_button)
        self.addWidget(VBreakLine(self))
    
    def keepFontSize(self):
        font_size = int(self._font_sizes.currentText())
        if self._font_families.currentFont().pointSize() != font_size:
            font = QFont()
            font.setPointSize(font_size)
            self._font_families.setCurrentFont(font)
    
    def connectNotepad(self, notedpad):
        self._font_families.currentFontChanged.connect(notedpad.setCurrentFont)
        self.bold_action.toggled.connect(lambda x: notedpad.setFontWeight(QFont.Bold if x else QFont.Normal))
        self.italic_action.toggled.connect(notedpad.setFontItalic)
        self.underline_action.toggled.connect(notedpad.setFontUnderline)

    def changeFontSize(self):
        font_format = QTextCharFormat()
        font_size = int(self._font_sizes.currentText())
        font_format.setFontPointSize(font_size)
        cursor = self._parent.activeNotepad().textCursor()
        cursor.mergeBlockCharFormat(font_format)

        self._parent.activeNotepad().setTextCursor(cursor)
        self._parent.activeNotepad().setFontPointSize(font_size)
  
    def changeFontColor(self):
        color_dialog = QColorDialog()
        color = color_dialog.getColor()
        hex_color = None
        if color.isValid():
            hex_color = color.name()
            self.font_color_button.setColor(hex_color)
            q_color = QColor(hex_color)
            self._parent.activeNotepad().setTextColor(q_color)
    
    def changeHighlighterColor(self):
        color_dialog = QColorDialog()
        color = color_dialog.getColor()
        hex_color = None
        if color.isValid():
            hex_color = color.name()
            self.highlighter_button.setColor(hex_color)
            q_color = QColor(hex_color)
            self._parent.activeNotepad().setTextBackgroundColor(q_color)
 
class AlignToolBar(QToolBar):
    def __init__(self, title="Text Alignment", parent=None):
        super().__init__(title, parent)
        
        self._parent = parent 
        self.setObjectName("alitoolbar")
        self.setStyleSheet(""" 
            QWidget[objectName^="alitoolbar"]{background-color: #777777;}
            QPushButton{background-color: #777777;}
            QToolButton{background-color: #777777;};
        """)

        # ALIGNMENT FORMATTING
        #*********************

        # Align Actions
        #------------------------------------------------------------
        self.alignl_action = QAction(QIcon(os.path.join('images', 'edit-alignment.png')), "Align left", self)
        self.alignc_action = QAction(QIcon(os.path.join('images', 'edit-alignment-center.png')), "Align center", self)
        self.alignr_action = QAction(QIcon(os.path.join('images', 'edit-alignment-right.png')), "Align right", self)
        self.alignj_action = QAction(QIcon(os.path.join('images', 'edit-alignment-justify.png')), "Justify", self)

        # Align Settings 
        #------------------------------------------------------------

        # Align Left
        self.alignl_action.setStatusTip("Align text left")
        self.alignl_action.setCheckable(True)
        self.alignl_action.toggled.connect(lambda toggled: self._parent.activeNotepad().setAlignment(Qt.AlignLeft if toggled else Qt.AlignJustify))

        # Align Center
        self.alignc_action.setStatusTip("Align text center")
        self.alignc_action.setCheckable(True)
        self.alignc_action.toggled.connect(lambda toggled: self._parent.activeNotepad().setAlignment(Qt.AlignCenter if toggled else Qt.AlignLeft))

        # Align Right
        self.alignr_action.setStatusTip("Align text right")
        self.alignr_action.setCheckable(True)
        self.alignr_action.toggled.connect(lambda toggled: self._parent.activeNotepad().setAlignment(Qt.AlignRight if toggled else Qt.AlignLeft))

        # Justify
        self.alignj_action.setStatusTip("Justify text")
        self.alignj_action.setCheckable(True)
        self.alignj_action.toggled.connect(lambda toggled: self._parent.activeNotepad().setAlignment(Qt.AlignJustify if toggled else Qt.AlignLeft))

        # Align Group
        ###############################################
        self.align_group = QActionGroup(self)
        self.align_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)

        self.align_group.addAction(self.alignl_action)
        self.align_group.addAction(self.alignc_action)
        self.align_group.addAction(self.alignr_action)
        self.align_group.addAction(self.alignj_action)

        # Add actions to the tool bar
        self.addAction(self.alignl_action)
        self.addAction(self.alignc_action)
        self.addAction(self.alignr_action)
        self.addAction(self.alignj_action)
        ###############################################

        # LIST FORMATTING
        #*****************

        # List Actions
        #------------------------------------------------------------
        self.list_action = QAction(QIcon(os.path.join('images', 'edit-list.png')), "List", self)
        self.ord_list_action = QAction(QIcon(os.path.join('images', 'edit-list-order.png')), "Ordered List", self)

        # List Widgets
        #------------------------------------------------------------
        self.list_style_combo = QComboBox() 
        self.ord_list_style_combo = QComboBox() 


        # List Settings
        #------------------------------------------------------------

        # List
        self.list_action.setStatusTip("Create list")
        self.list_action.setCheckable(True)
        self.list_action.toggled.connect(self.createList)
        
        # List Style
        list_styles = ["Disc", "Circle", "Square"]
        self.list_style_combo.addItems(list_styles)
        self.list_style_combo.activated.connect(self.changeListStyle)
        
        # Ordered List
        self.ord_list_action.setStatusTip("Create ordered list")
        self.ord_list_action.setCheckable(True)
        self.ord_list_action.toggled.connect(self.createOrdList)
        
        # Ordered List Style
        ord_list_styles = ["Decimal", "Lower Alpha", "Upper Alpha", "Lower Roman", "Upper Roman"]
        self.ord_list_style_combo.addItems(ord_list_styles)
        self.ord_list_style_combo.activated.connect(self.changeOrdListStyle)
        

        # Align Group (and widgets)
        ###############################################
        self.list_group = QActionGroup(self)
        self.list_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)

        self.list_group.addAction(self.list_action)
        self.list_group.addAction(self.ord_list_action)

        # Add Actions and Widgets to the tool bar
        self.addAction(self.list_action)
        self.addWidget(self.list_style_combo)
        self.addAction(self.ord_list_action)
        self.addWidget(self.ord_list_style_combo)
        ###############################################
        

    def createList(self, toggled):
        cursor = self._parent.activeNotepad().textCursor()
        list_format = QTextListFormat()
        list_styles = {"Disc": QTextListFormat.ListDisc,
                       "Circle": QTextListFormat.ListCircle,
                       "Square": QTextListFormat.ListSquare}
        style = list_styles[self.list_style_combo.currentText()]
        if toggled:
            list_format.setStyle(style)
            cursor.createList(list_format)
            self._parent.activeNotepad().setTextCursor(cursor)
        else:
            current_list = cursor.currentList()
            if current_list:
                list_format.setIndent(0)
                list_format.setStyle(style)
                current_list.setFormat(list_format)
                for i in range(current_list.count()-1, -1, -1):
                    current_list.removeItem(i)
    
    def changeListStyle(self):
        cursor = self._parent.activeNotepad().textCursor()
        current_list = cursor.currentList()
        list_format = QTextListFormat()
        list_styles = {"Disc": QTextListFormat.ListDisc,
                       "Circle": QTextListFormat.ListCircle,
                       "Square": QTextListFormat.ListSquare}
        style = list_styles[self.list_style_combo.currentText()]
        list_format.setStyle(style)
        current_list.setFormat(list_format)
        self._parent.activeNotepad().setTextCursor(cursor)

    def createOrdList(self, toggled):
        cursor = self._parent.activeNotepad().textCursor()
        ord_list_format = QTextListFormat()
        ord_list_styles = {"Decimal": QTextListFormat.ListDecimal,
                       "Lower Alpha": QTextListFormat.ListLowerAlpha,
                       "Upper Alpha": QTextListFormat.ListUpperAlpha,
                       "Lower Roman": QTextListFormat.ListLowerRoman,
                       "Upper Roman": QTextListFormat.ListUpperRoman}
        style = ord_list_styles[self.ord_list_style_combo.currentText()]
        if toggled:
            ord_list_format.setStyle(style)
            cursor.createList(ord_list_format)
            self._parent.activeNotepad().setTextCursor(cursor)
        else:
            current_list = cursor.currentList()
            if current_list:
                ord_list_format.setIndent(0)
                ord_list_format.setStyle(style)
                current_list.setFormat(ord_list_format)
                for i in range(current_list.count()-1, -1, -1):
                    current_list.removeItem(i)
    
    def changeOrdListStyle(self):
        cursor = self._parent.activeNotepad().textCursor()
        current_list = cursor.currentList()
        list_format = QTextListFormat()
        ord_list_styles = {"Decimal": QTextListFormat.ListDecimal,
                       "Lower Alpha": QTextListFormat.ListLowerAlpha,
                       "Upper Alpha": QTextListFormat.ListUpperAlpha,
                       "Lower Roman": QTextListFormat.ListLowerRoman,
                       "Upper Roman": QTextListFormat.ListUpperRoman}
        style = ord_list_styles[self.ord_list_style_combo.currentText()]
        list_format.setStyle(style)
        current_list.setFormat(list_format)
        self._parent.activeNotepad().setTextCursor(cursor)
        

    

