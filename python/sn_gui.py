from PySide2.QtWidgets import (QMainWindow, QMessageBox, QToolBar, QPushButton, QTabWidget, QDockWidget, QVBoxLayout, QAction, QLineEdit, QComboBox, QGridLayout, QWidget, QLabel, QHBoxLayout)
from sn_widgets import (NoteTextBox, Terminal, DefinitionBox, WordListBox, PageTabs, HorizontalFiller)
from sn_dict_database import DefinitionsDatabase
from sn_windowmenu import WindowMenu
from PySide2.QtCore import (Qt)
from PySide2.QtGui import (QIcon)
from sn_toolbars import (FontToolBar, AlignToolBar, LogicSymbolToolbar)
from sn_htmleditor import (HtmlWriter)
from sn_docks import Docks
from sn_recovery import NotepadRecovery
import os 
from datetime import datetime

class MainWindow(QMainWindow, WindowMenu, Docks, NotepadRecovery):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Smart Notes - Version 1.0")
        
        # Central Widget
        self._main_widget = QWidget(self)
        self._main_widget.setContentsMargins(25, 10, 25, 0)
        self._main_layout = QHBoxLayout(self._main_widget)
   

        # Separate notepad pages, work on more than one document at time!
        #---------------------------------------------------------------------------------------------------------
        """ Note: For future use, add a feature that when the page switchs 
            one can set a specific dictionary for the document they're working on.
        """
        self._pages = None 
        self._notepads = {}

        tab_name = "New Page"

        self._page_tabs = PageTabs(self)
        self._page_tabs.addTab(self._main_widget, QIcon(os.path.join('images', 'edit-new-paper.png')), tab_name)

        # Esoteric Definition Database (HELPFUL FOR PHILOSPHY LOVERS)
        #---------------------------------------------------------------------------------------------------------
        self.DATABASE_PATH = "dictionary_databases"
        self._database = DefinitionsDatabase()
        self._definition_box = DefinitionBox("", self)

        self._database_name = QLabel("Select Dictionary:")
        databases = [file_name.split(".")[0] for file_name in os.listdir(self.DATABASE_PATH)]
        self._database_combo = QComboBox()
        self._database_combo.addItems(databases)
        self._database_combo.currentIndexChanged.connect(self.changeDatabase)

        # Temp Notepad for starting out
        #---------------------------------------------------------------------------------------------------------
        text_editor = NoteTextBox(parent=self)
        text_editor.setTabName(tab_name)
        text_editor.textChanged.connect(text_editor.unsaved)
        text_editor.textChanged.connect(self._page_tabs.checkTabIconState)
        self._page_tabs.currentChanged.connect(text_editor.tabChange)

        self._notepads = {tab_name: text_editor}

        #Bottom Bar
        #---------------------------------------------------------------------------------------------------------
        self._bottom_bar = BottomBar(parent=self)
        self.addToolBar(Qt.ToolBarArea().BottomToolBarArea, self._bottom_bar)
        
        # Connect methods that fire when user clicks on a different notepad tab. 
        #--------------------------------------------------------------------------
        self._page_tabs.currentChanged.connect(self._bottom_bar.wordCount)
        self._page_tabs.currentChanged.connect(self.updateBottomBarPageIndex)
        self._page_tabs.currentChanged.connect(self.updateHiglighter)
        #--------------------------------------------------------------------------
        
        # Method to keep track of tab indexs to notepads
        self.updateTabPages()

        # Unused for now
        self._current_definition = ""

        # DOCK WIDGETS
        Docks.__init__(self, WordListBox, DefinitionBox, HtmlWriter, Terminal, HorizontalFiller)

        self._database_combo.setCurrentIndex(2)

        # Font Handling Toolbar
        #---------------------------------------------------------------------------------------------------------
        self._font_toolbar = FontToolBar(parent=self)
        self._font_toolbar.connectNotepad(text_editor) 
        self._align_toolbar = AlignToolBar(parent=self)
        self._logic_toolbar = LogicSymbolToolbar(parent=self)

        # Utility Toolbar
        #---------------------------------------------------------------------------------------------------------
        self._utility_toolbar = UtilityToolBar(parent=self)
        self.addToolBar(self._utility_toolbar)
        self.addToolBar(self._font_toolbar)
        self.addToolBar(self._align_toolbar)
        self.addToolBar(self._logic_toolbar)
        text_editor.textChanged.connect(self._utility_toolbar.updateSearch)

        # Display the widgets
        #---------------------------------------------------------------------------------------------------------
        self.displayWidgets()
        self.setCentralWidget(self._page_tabs)

        # Init. Window Menu
        WindowMenu.__init__(self)

        NotepadRecovery.__init__(self)

        text_editor.setSaved(True)
    
    def closeEvent(self, event):
        try:
            
            # Create a Logs directory if one does not exist. 
            if not os.path.isdir("Logs"):
                os.mkdir("Logs")
            date = date = datetime.now()
            f_date = date.strftime("%d-%b-%Y(%Hhr-%Mmin-%Ssec)")
            saved, saves = self.savesNeeded(f_date)
            
            # Log Event 
            log_text = self.TERMINAL.toPlainText()
            log_save = "Logs/Log_{dt}.txt".format(dt=f_date)
            with open(log_save, 'w') as log_file:
                log_file.write(log_text)

            if not saved:
                save_msg = self.newPageSaveWarning(saves) 
                if save_msg == QMessageBox.Yes:
                    event.ignore()
                else:
                    event.accept()

            
        except Exception as e:
            self.dialogCritical(str(e))

    # For trouble shooting 
    def savesNeeded(self, date):
        saved, saves = self.areDocumentsSaved()
        self.terminal("Save event at {dt}".format(dt=date))
        self.terminal("Is it saved: {sd} | Save files: {sv}".format(sd=saved, sv=saves))
        return saved, saves 
        
    def areDocumentsSaved(self):
        """
        Checks if documents are saved. If not, it will return false, and
        return a list of the document names that were not saved. Else, it
        will return true, and offer a list of all the names.
        """
        try:
            unsaved_notepads = []
            for notepad_name, notepad in self._notepads.items():
                if not notepad.isSaved():
                    unsaved_notepads.append(notepad_name)
            
            if unsaved_notepads:
                return (False, unsaved_notepads)    
            return (True, list(self._notepads.keys()))  
        except Exception as e:
            self.terminal(str(e))
        return (None, None)

    def updateBottomBarPageIndex(self):
        """Updates the page and word count bottom display."""
        self._bottom_bar._page_count_label.setText("     Page {ci} of {ct}     ".format(ct=self._page_tabs.tabBar().count(), ci=(self._page_tabs.currentIndex()+1)))
    
    def updateTabPages(self, update_notebook=False, removed_tab=False, removed_tab_name=""):
        """Keeps track of the notepad pages and tab locations when moved or deleted."""
        tab_count = self._page_tabs.tabBar().count()
        last_pages = self._pages
        
        if last_pages is not None and update_notebook:
            # Update Notepads
            self._notepads = {self._notepads[old_tab_name].tabName():self._notepads[old_tab_name] for old_tab_name in last_pages}
            # Update Page Indexing 
        self._pages = {self._page_tabs.tabText(index):index for index in range(0, tab_count)}
        self.updateBottomBarPageIndex()
        
        if removed_tab:
            del self._notepads[removed_tab_name]

    def updateHiglighter(self):
        """Updates the syntax highlighting when changes are made."""
        if self.activeNotepad() is not None:
            self.activeNotepad().highlighter.updateRules()
            self.activeNotepad().highlighter.rehighlight()

    def displayWidgets(self):
        """ Display the main window widgets."""
        # CENTER THE NOTEPAD DOCUMENT WITH TWO H FILLERS
        self._main_layout.addWidget(HorizontalFiller(self))
        self._main_layout.addWidget(self.activeNotepad())
        self._main_layout.addWidget(HorizontalFiller(self))
        self._def_layout.addWidget(self._definition_box)
        self._word_layout.addWidget(self._word_listbox, 0, 0)
        self._word_layout.addWidget(QLabel("Active Dictionary:"), 1, 0)
        self._word_layout.addWidget(self._database_combo, 2, 0)
    
    #*IMPORTANT 
    #---------------------------------------------------------------------------------------------------------
    def activeNotepad(self):
        """
        *CURRENT NOTEPAD DOCUMENT - Crucial method that keeps track of the current document being worked on 
        by the user.
        """
        if not self._page_tabs.wait_for_new_to_complete:
            current_page_name = self._page_tabs.tabText(self._page_tabs.currentIndex())
            return self._notepads[current_page_name]
        return None 
    #---------------------------------------------------------------------------------------------------------

# Some Additional Toolbars
"""
    Note: Will give them another home in the future. 
"""
class UtilityToolBar(QToolBar):
    """Contains the "find text" feature, and will be the home of future utilities."""
    def __init__(self, title="Find Text Toolbar", parent=None):
        super().__init__(title, parent)
        self._parent = parent
        self._not_refresh = True  

        self.setObjectName("bottoolbar")
        self.setStyleSheet(""" 
            QWidget[objectName^="bottoolbar"]{background-color: #333333;}
            QPushButton{background-color: #333333;}
            QToolButton{background-color: #333333;}
        """)
        self._last_textCursor_pos = 0
        self._find_iteration = 0

        self._find_text_label = QLabel("Find document text:")
        self._find_text_entry = QLineEdit(self)
        self._find_text_entry.textEdited.connect(self.findText)

        self._find_text_entry.setPlaceholderText("Search for...")
        self._find_action = QAction(QIcon(os.path.join('images', 'find.png')), "Find next occurence", self)
        self._find_action.triggered.connect(self.findText)
        self._find_text_count_label = QLabel("  0 of 0  ")

        self.addWidget(self._find_text_label)
        self.addWidget(self._find_text_entry)
        self.addWidget(self._find_text_count_label)
        self.addAction(self._find_action)

    def resetTextCursorPos(self):
        self._last_textCursor_pos = 0
        self._find_iteration = 0

    def findText(self, text=""):
        """ Iterates through the active document to find the selected word."""
        notepad = self._parent.activeNotepad()
        document = notepad.document()
        found_count = 0
        single_search = True 

        if text:
            find_text = text 
        else:
            find_text = self._find_text_entry.text()
            single_search = False 

        if find_text:
            found_count = (str(document.toPlainText()).lower()).count(find_text.lower())
        
        if self._not_refresh:
            if found_count:
                if single_search:
                    self._find_iteration = 1
                else:
                    self._find_iteration += 1
            else:
                self._find_iteration = 0

            if find_text:
                if single_search:
                    cursor = document.find(find_text, 0)
                else:
                    if self._last_textCursor_pos <= 0:
                        cursor = document.find(find_text, 0)
                    else:
                        cursor = document.find(find_text, self._last_textCursor_pos)
                    self._last_textCursor_pos = cursor.position()
                if not single_search:
                    self._last_textCursor_pos = cursor.position()
                
                if self._last_textCursor_pos == -1:
                    self.resetTextCursorPos()
        
                notepad.setTextCursor(cursor)
        

        
        self._find_text_count_label.setText("  {it} of {ct}  ".format(it=self._find_iteration, ct=found_count))

    def updateSearch(self):
        """Updates the findText to account for changes (e.g. text change or page change)."""
        self._not_refresh = False 
        self._find_action.trigger()
        self._not_refresh = True 

class BottomBar(QToolBar):
    """BOTTOM AREA - Contains the page counter and word counter."""
    def __init__(self, title="Bottom Bar", parent=None):
        super().__init__(title, parent)
        self._parent = parent 
        self.setObjectName("bottoolbar")
        self.setStyleSheet(""" 
            QWidget[objectName^="bottoolbar"]{background-color: #333333;}
            QPushButton{background-color: #333333;}
            QToolButton{background-color: #333333;}
        """)
        self.setFloatable(False)
        self.setMovable(False)

        self._word_count_label = QLabel("0 word(s)")
        self._page_count_label = QLabel("     Page 1 of 1     ")
     
        self._parent.activeNotepad().textChanged.connect(self.wordCount)
   
        self.addWidget(self._page_count_label)
        self.addWidget(self._word_count_label)
    
    def wordCount(self):
        if not self._parent.activeNotepad() is None:
            word_count = str(len(self._parent.activeNotepad().toPlainText().split()))
            self._word_count_label.setText("{wc} word(s)".format(wc=word_count))
        else:
            self._word_count_label.setText("0 word(s)")
            self._page_count_label.setText("     Page 1 of 1     ")
            