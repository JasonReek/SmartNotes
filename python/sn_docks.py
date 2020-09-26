from PySide2.QtWidgets import (QLineEdit, QWidget, QGridLayout, QHBoxLayout, QDockWidget, QLabel, QPushButton, QMessageBox, QShortcut)
from PySide2.QtWebEngineWidgets import (QWebEngineView, QWebEngineSettings)
from PySide2.QtCore import (Qt)
from PySide2.QtGui import (QKeySequence, QIcon)

from sn_widgets import (HorizontalFiller, VerticalFiller)

import os 
from time import sleep 

class SearchToolBar(QWidget):
    def __init__(self, parent=None, view=None):
        super().__init__(parent)
        self._parent = parent 
        self._view = view 
        self._layout = QHBoxLayout(self)
        self.setStyleSheet("""
            QLineEdit{background-color: #232323; border: 1px solid #999999;}
            QLineEdit:focus {border: 1px solid #FFFFFF;}
        """)

        # Search Bar 
        self._search_bar = QLineEdit(self)
        self._view.urlChanged.connect(self.setNewUrlOnPageChange)

        self._find_text_entry = QLineEdit(self)
        self._find_text_entry.textChanged.connect(self.textEditFindWebText)
        

        self.addAction(self._view.page().action(self._view.page().Reload))

  
        #self.addAction(self._parent._view.page().action(self._parent._view.page().Back))
        #self.addAction(self._parent._view.page().action(self._parent._view.page().Forward))

        self._find_text_entry.setMaximumWidth(150)
        self._find_text_button = QPushButton(self)
        self._find_text_button.setFlat(True)
        self._find_text_label = QLabel("   Find text:")
        self._find_text_button.setIcon(QIcon(os.path.join('images', 'find.png')))
        self._find_text_button.clicked.connect(self.findWebText)
        self._find_shortcut = QShortcut(QKeySequence("Ctrl+f"), self)
        self._find_shortcut.activated.connect(self.findTextShortcut)
        self._last_word = ""

        self._layout.addWidget(self._search_bar)
        self._layout.addWidget(self._find_text_label)

    def setNewUrlOnPageChange(self, url):
        url_text = url.toString()
        self._search_bar.setText(url_text)

    def searchBar(self):
        return self._search_bar

    def setSearchUrl(self, url):
        self._search_bar.setText(url)

    def currentUrl(self):
        return self._search_bar.text()

    def findBar(self):
        find_bar = QWidget(self)
        find_bar.setStyleSheet("""
            QLineEdit{background-color: #232323; border: 1px solid #999999;}
            QLineEdit:focus {border: 1px solid #FFFFFF;}
        """)
        find_lay = QHBoxLayout(find_bar)
        find_lay.addWidget(HorizontalFiller(self))
        find_lay.addWidget(self._find_text_label)
        find_lay.addWidget(self._find_text_entry)
        find_lay.addWidget(self._find_text_button)
        return find_bar

    def findTextShortcut(self):
        #if self._parent._html_editor.htmlWriter().hasFocus():
        #    self._parent._html_toolbar._find_text_entry.setFocus()
        #else:
        self._find_text_entry.setFocus()
    
    def textEditFindWebText(self, text):
        self._last_word = text
        if text:
            if self._last_word in text:
                self.findWebText()
                self._last_word = text
        else:
            self.findWebText()
       
    def findWebText(self):
        find_text = self._find_text_entry.text()
        self._view.findText(find_text)


class Docks:
    def __init__(self, WordListBox, DefinitionBox, HtmlWriter, Terminal, HorizontalFiller):

        # Definition Dock
        #--------------------------------------------------------------------------------------------
        self._def_column = QWidget(self)
        self._def_layout = QGridLayout(self._def_column)
        self._def_dock = QDockWidget("Definition", self)
        #self._def_dock.setFeatures(self._def_dock.features() & ~QDockWidget.DockWidgetClosable)
        self._def_dock.setWidget(self._def_column)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._def_dock)


        # Definition List Dock
        #--------------------------------------------------------------------------------------------
        self._word_column = QWidget(self)
        self._word_layout = QGridLayout(self._word_column)
        self._word_dock = QDockWidget("Listed Definitions")
        
        self._word_listbox = WordListBox(self)
        self._word_listbox.itemClicked.connect(self.selectNewDefinition)

        #self._word_dock.setFeatures(self._def_dock.features() & ~QDockWidget.DockWidgetClosable)
        self._word_dock.setWidget(self._word_column)
        self.addDockWidget(Qt.LeftDockWidgetArea, self._word_dock)
        self.updateWordsListBox()

        #Web Dock
        #-------------------------------------------------------------------------------------------- 
        self._view = QWebEngineView()

        # Loading the page. 
        self.setDefaultUrl()

        self._search_bar = SearchToolBar(parent=self, view=self._view)
        self._search_bar.searchBar().returnPressed.connect(self.webSearch)

        # Setting up the web dock
        web_widget = QWidget(self)
        web_layout = QGridLayout(web_widget)
        # Place the web view in a widget. 
        web_layout.addWidget(self._search_bar)
        web_layout.addWidget(self._view)
        web_layout.addWidget(self._search_bar.findBar())
        web_layout.addWidget(VerticalFiller(self))
        

        self._web_dock = QDockWidget("Web Browser", self)
        self._web_dock.setWidget(web_widget)
        self._web_dock.visibilityChanged.connect(self.webDockHandler)
      
        self.addDockWidget(Qt.RightDockWidgetArea, self._web_dock)


        
        # Html Editior Dock
        #--------------------------------------------------------------------------------------------
        self._html_editor = HtmlWriter(parent=self) 
        self._html_insert_button = QPushButton("Insert Html")
        self._html_insert_button.clicked.connect(self._html_editor.enterHtml)

        html_editor_widget = QWidget(self)
        html_editor_layout = QGridLayout(html_editor_widget)
        html_editor_layout.addWidget(QLabel("Enter Html to insert special formats (e.g. tables) into the document."))
        html_editor_layout.addWidget(self._html_editor, 1, 0)
        button_row = QWidget(self)
        button_lay = QHBoxLayout(button_row)
        button_lay.addWidget(HorizontalFiller(self))
        button_lay.addWidget(self._html_insert_button)

        html_editor_layout.addWidget(button_row, 2, 0)
        self._html_dock = QDockWidget("Html Editor", self)
        self._html_dock.setWidget(html_editor_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self._html_dock)


        # Terminal Dock
        #--------------------------------------------------------------------------------------------
        self.TERMINAL = Terminal(self)
        self._terminal_dock = QDockWidget("Terminal", self)
        self._terminal_dock.setWidget(self.TERMINAL)
        self.addDockWidget(Qt.BottomDockWidgetArea, self._terminal_dock)
        self._terminal_dock.setVisible(False)

    def webDockHandler(self, visbility):
        """Resets the url when the user closes out the web dock. This is too limit web noise."""
        if not visbility:
            self.setDefaultUrl()

    def setDefaultUrl(self):
        """ Set the default url to DuckDuckGo search page."""
        self._view.load("https://duckduckgo.com/")    


    def webSearch(self):
        self._view.load(self._search_bar.currentUrl())

    def selectNewDefinition(self, item):
        """
        When a definition is selected from the defintion word list, this method will
        write the new definition in the definiton box.
        """
        word = item.text()
        definition = self._database.getDefinition(word[0], word)
        if definition != None and len(definition):
            self._definition_box.setText("<b><u>"+word+"</u></b> - "+definition)

    def updateWordsListBox(self):
        """Updates the definition word list when dictionary is changed or a new word is added."""
        self._word_listbox.clear()
        for word in list(sorted(self._database.getAllDictWords())):
            self._word_listbox.addItem(word)
 
    def getWordsInListBox(self):
        """Returns a list of words from the presently selected dictionary."""
        words = []
        for row in range(0, self._word_listbox.count()):
            words.append(self._word_listbox.item(row).text())
        return words 

    def changeDatabase(self):
        """
        When a new dictionary database is selected, this will update the highlighter 
        to adjust to the new definitions. 
        """
        database_name = self._database_combo.currentText()
        self._database.setNewDatabase(database_name)
        self.activeNotepad().highlighter.updateRules()
        self.updateWordsListBox()
        self._definition_box.clear()
        self.activeNotepad().highlighter.rehighlight()

    def updateDatabaseNames(self):
        """Populates the dictionary combobox with the currently available dictionaries."""

        # Keep the current selected dictionary when adding new dictionaries to the list. 
        current_dict_text = self._database_combo.currentText()
        text_location = 0
        
        self._database_combo.clear()
        databases = sorted([file_name.split(".")[0] for file_name in os.listdir(self.DATABASE_PATH)])
        self._database_combo.addItems(databases)
        text_location = self._database_combo.findText(current_dict_text)
        self._database_combo.setCurrentIndex(text_location)

    def terminal(self, message):
        """Sends a message to the terminal dock."""
        self.TERMINAL.insertBlueArrows()
        self.TERMINAL.insertPlainText(message)


