#######################################################################################
# SPELL CHECKING PORTION OF THE CODE FROM:
#######################################################################################
"""QPlainTextEdit With Inline Spell Check
Original PyQt4 Version:
    https://nachtimwald.com/2009/08/22/qplaintextedit-with-in-line-spell-check/
Copyright 2009 John Schember
Copyright 2018 Stephan Sokolow
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#######################################################################################
# THANKS FOR THE GREAT JOB ON THE SPELL CHECKER! 
# - Jason Reek 

import sys 
import enchant
from enchant import tokenize
from enchant.errors import TokenizerNotFoundError

from PySide2.QtWidgets import (QApplication, QStyle, QStylePainter, QStyleOptionTab, QMainWindow, QLineEdit, QMenu, QDialog, QAction, QFormLayout,
                               QMessageBox, QTextEdit, QDockWidget, QMenu, QComboBox, QFrame, QListWidget, QTabWidget, QToolTip, QTabBar, QAbstractItemView, 
                               QVBoxLayout, QGridLayout, QWidget, QLabel, QPushButton, QHBoxLayout, QTableWidgetItem, QFileDialog, QActionGroup, QSizePolicy, QAction)
from PySide2.QtGui import (QSyntaxHighlighter, QIcon, QFocusEvent, QTextBlockUserData, QTextCursor, QPalette, QTextCharFormat, QBrush, QFont, QColor, QDesktopServices)
from PySide2.QtCore import (Qt, QEvent, QRegExp, QTimer)
from sn_dict_database import DefinitionsDatabase
import os 

def trim_suggestions(word, suggs, maxlen, calcdist=None):
    """API Polyfill for earlier versions of PyEnchant.
    TODO: Make this actually do some sorting
    """
    return suggs[:maxlen]

# Basic GUI widgets
#---------------------------------------------------------------------------------------------------------
class BreakLine(QFrame):
    """Adds a horizontal breakline into the layout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(self.HLine)
        self.setFrameShadow(self.Sunken)

class VBreakLine(QFrame):
    """Adds a vertical breakline into the layout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(self.VLine)
        self.setFrameShadow(self.Sunken)
        self.setContentsMargins(5, 0, 1, 0)
        self.setStyleSheet("background-color: #777777;")

class VerticalFiller(QWidget):
    """Fills in the remaining empty vertical space in a layout."""
    def __init__(self, parent=None):
        super(VerticalFiller, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

class HorizontalFiller(QWidget):
    """Fills in the remaining empty horizontal space in a layout."""
    def __init__(self, parent=None):
        super(HorizontalFiller, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

# Spell checker and definition highlighting. 
#---------------------------------------------------------------------------------------------------------
class EnchantHighlighter(QSyntaxHighlighter):
    """QSyntaxHighlighter subclass which consults a PyEnchant dictionary"""
    tokenizer = None
    token_filters = (tokenize.EmailFilter, tokenize.URLFilter)

    # Define the spellcheck style once and just assign it as necessary
    # XXX: Does QSyntaxHighlighter.setFormat handle keeping this from
    #      clobbering styles set in the data itself?
    err_format = QTextCharFormat()
    err_format.setUnderlineColor(Qt.red)
    err_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

    def __init__(self, database=None, *args):
        QSyntaxHighlighter.__init__(self, *args)

        self._on = True 

        # Access to (esoteric) dictionary databases
        self._database = database
        
        # Rules for specifically handling the esoteric words and definitions. 
        if self._database is not None:
            self.updateRules()

        # Initialize private members
        self._sp_dict = None
        self._chunkers = []

    def updateRules(self):
        try:
            keywordFormat = QTextCharFormat()
            keywordFormat.setForeground(QColor("#000099"))
            keywordFormat.setFontWeight(QFont.Bold)
            keywordFormat.setFontUnderline(True)
            keywordFormat.setAnchor(True)
 
            dict_words = self._database.getAllDictWords()
            keywordPatterns = ["\\b"+word+"\\b" for word in dict_words]
            keywordPatterns.extend(["\\b"+word.upper()+"\\b" for word in dict_words])
            keywordPatterns.extend(["\\b"+word.lower()+"\\b" for word in dict_words])
            self.highlightingRules = [(QRegExp(pattern), keywordFormat) for pattern in keywordPatterns]
        
        except Exception as e:
            print("Failed to update the highlighting rules:",e)

    def chunkers(self):
        """Gets the chunkers in use"""
        return self._chunkers

    def dict(self):
        """Gets the spelling dictionary in use"""
        return self._sp_dict

    def setChunkers(self, chunkers):
        """Sets the list of chunkers to be used"""
        self._chunkers = chunkers
        self.setDict(self.dict())
        # FIXME: Revert self._chunkers on failure to ensure consistent state

    def setDict(self, sp_dict):
        """Sets the spelling dictionary to be used"""
        try:
            self.tokenizer = tokenize.get_tokenizer(sp_dict.tag,
                chunkers=self._chunkers, filters=self.token_filters)
        except TokenizerNotFoundError:
            # Fall back to the "good for most euro languages" English tokenizer
            self.tokenizer = tokenize.get_tokenizer(
                chunkers=self._chunkers, filters=self.token_filters)
        self._sp_dict = sp_dict

        self.rehighlight()
    
    def turnOff(self):
        self._on = False
        self.rehighlight()  

    def turnOn(self):
        self._on = True 
        self.rehighlight()
    
    def isOn(self):
        return self._on 

    def databaseHighlighting(self, text):
        for pattern, format_v in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format_v)
                index = expression.indexIn(text, index + length)

    def highlightBlock(self, text):
        if self._on:
            """Overridden QSyntaxHighlighter method to apply the highlight"""
            if not self._sp_dict:
                return

            # Database highlighting 
            if self._database is not None:
                self.databaseHighlighting(text)

            # Build a list of all misspelled words and highlight them
            misspellings = []
            for (word, pos) in self.tokenizer(text):
                if not self._sp_dict.check(word):
                    self.setFormat(pos, len(word), self.err_format)
                    misspellings.append((pos, pos + len(word)))
            


            # Store the list so the context menu can reuse this tokenization pass
            # (Block-relative values so editing other blocks won't invalidate them)
            data = QTextBlockUserData()
            data.misspelled = misspellings
            self.setCurrentBlockUserData(data)

# Important structure for handling mutliple documents. Tread carefully when editing. 
#---------------------------------------------------------------------------------------------------------
class PageTabs(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent=None)
        self._parent = parent

        self._add_tab = QPushButton()
        self._add_tab.setIcon(QIcon(os.path.join('images', 'edit-plus.png')))
        self._add_tab.setFlat(True)
        self._add_tab.clicked.connect(self.newPage)
        self.setCornerWidget(self._add_tab)
        self.setMovable(True)
        self.tabBar().tabMoved.connect(self.updateTabPostions)

        self.wait_for_new_to_complete = False

    def showUnsavedIcon(self, index):
        self.setTabIcon(index, QIcon(os.path.join('images', 'warning.png')))
        self.setTabToolTip(index, '"Document needs to be saved.')
    
    def showSavedIcon(self, index):
        self.setTabIcon(index, QIcon(os.path.join('images', 'edit-new-paper.png')))
    
    def checkTabIconState(self):
        for tab_index in range(0, self.tabBar().count()):
            if not self._parent._notepads[self.tabText(tab_index)].isSaved():
                self.showUnsavedIcon(tab_index)
              
    def updateTabPostions(self):
        """Keeps track of notepad pages and tab positions."""
        for tab_pos, tab_name in enumerate(self.tabNames()):
            self._parent._pages[tab_name] = tab_pos

    def tabNames(self):
        """Returns a list of tab names."""
        return [self.tabText(i) for i in range(0, self.tabBar().count())]
    
    def _removeSelectedTab(self, index):
        """ Removes a notepad page tab. """ 
        def removeSelectedTab():
            save_msg = None 
            all_files_saved, file_list = self._parent.areDocumentsSaved()
            tab_name = self.tabText(index)
            if not all_files_saved and tab_name in file_list:
                save_msg = self._parent.saveWarning(tab_name)
                if save_msg == QMessageBox.Yes:
                    self._parent.fileSave()
                
            if save_msg is None or (save_msg is not None and save_msg != QMessageBox.Cancel):
                self.removeTab(index)
                self._parent.updateTabPages(removed_tab=True, removed_tab_name=tab_name)

        return removeSelectedTab

    # (LEGACY)
    '''
    def _setNewTabName(self, index):
        def setNewTabName():
            tab_name_dialog = NewTabNameDialog(self, self.tabNames())
            tab_name_dialog.exec_()
            old_tab_name = self.tabText(index)
            new_tab_name = None
            if not tab_name_dialog.isCanceled():
                new_tab_name = tab_name_dialog.getTabName()
                self.setTabText(index, new_tab_name)
                self._parent._notepads[old_tab_name].setTabName(new_tab_name)
                self._parent.updateTabPages(update_notebook=True)
        return setNewTabName
    '''
    def newPage(self):
        """ Inserts a new page for the user to work on. """
        tab_name_dialog = NewTabNameDialog(self, self.tabNames())
        tab_name_dialog.exec_()
        new_notepad = None
        new_tab_index = None 
        tab_name = tab_name_dialog.getTabName()
        if not tab_name_dialog.isCanceled():
            page = QWidget(self)
            page.setContentsMargins(25, 10, 25, 0)
            page_layout = QHBoxLayout(page)
 
            new_notepad = NoteTextBox(parent=self._parent)
            new_notepad.setTabName(tab_name)
            self._parent._notepads[tab_name] = new_notepad
            # Again, add the H fillers to center the notepad document.
            page_layout.addWidget(HorizontalFiller())
            page_layout.addWidget(new_notepad)
            page_layout.addWidget(HorizontalFiller())
            new_tab_index = self.addTab(page, QIcon(os.path.join('images', 'edit-new-paper.png')), tab_name)

            new_notepad.textChanged.connect(new_notepad.unsaved)
            new_notepad.textChanged.connect(self._parent._bottom_bar.wordCount)
            new_notepad.textChanged.connect(self._parent._utility_toolbar.updateSearch)
            new_notepad.textChanged.connect(self.checkTabIconState)
            self.currentChanged.connect(new_notepad.tabChange)
             
            self._parent.updateTabPages()
            self._parent._font_toolbar.connectNotepad(new_notepad)
            self.setCurrentIndex(new_tab_index)
            new_notepad.setSaved(True)
            new_notepad.tab_changed = False
        
    def contextMenuEvent(self, event):
        """Context menu of tab options. """
        tab_index = self.tabBar().tabAt(event.pos())
        tab_menu = None 
        # Currently over a tab  
        if tab_index > -1:
            #rename_action = QAction("Rename", self)
            #rename_action.triggered.connect(self._setNewTabName(tab_index))
            remove_tab_action = QAction(QIcon(os.path.join('images', 'edit-delete.png')), "Close", self)
            remove_tab_action.triggered.connect(self._removeSelectedTab(tab_index))
            tab_menu = QMenu(self)
            #tab_menu.addAction(rename_action)
            tab_menu.addSeparator()
            tab_menu.addAction(remove_tab_action)
            if tab_index == 0:
                remove_tab_action.setDisabled(True)
        # In tab bar, but not over any tabs
        else:
            new_page_action = QAction("Insert New Page", self)
            new_page_action.triggered.connect(self.newPage)
            tab_menu = QMenu(self)
            tab_menu.addAction(new_page_action)

        tab_menu.exec_(event.globalPos())
        self.focusInEvent(QFocusEvent(QEvent.FocusIn))

    def clearAll(self):
        """
        This is executed when "New" is selected from "File". This basically nukes 
        all of the pages present, but not before a warning is issued. 
        """
        self.wait_for_new_to_complete = True 
        self.clear()
        new_page_name = "New Page"
        new_page = QWidget(self)
        new_page_layout = QGridLayout(new_page)
        new_page.setContentsMargins(25, 10, 25, 0)
        self._parent._notepads = {new_page_name: NoteTextBox(parent=self._parent, tab_name=new_page_name)}
        self._parent._pages = {new_page_name: 0}
        new_page_layout.addWidget(self._parent._notepads[new_page_name])
        self._parent._font_toolbar.connectNotepad(self._parent._notepads[new_page_name])
        self._parent._notepads[new_page_name].textChanged.connect(self._parent._bottom_bar.wordCount)
        self._parent._notepads[new_page_name].textChanged.connect(self._parent._notepads[new_page_name].unsaved)
        self._parent._notepads[new_page_name].textChanged.connect(self._parent._utility_toolbar.updateSearch)
        self._parent._notepads[new_page_name].textChanged.connect(self.checkTabIconState)
        self.currentChanged.connect(self._parent._notepads[new_page_name].tabChange)
        self.addTab(new_page, QIcon(os.path.join('images', 'edit-new-paper.png')), new_page_name)
        self._parent._notepads[new_page_name].tab_changed = False
        self.wait_for_new_to_complete = False 

# The main document editor, this is where the user does most of their work. 
#---------------------------------------------------------------------------------------------------------
class NoteTextBox(QTextEdit):
    """ The main document editor, this is where the user does most of their work."""
    # Clamping value for words like "regex" which suggest so many things that
    # the menu runs from the top to the bottom of the screen and spills over
    # into a second column.
    max_suggestions = 20
    def __init__(self, parent=None, tab_name=None, *args):
        QTextEdit.__init__(self, *args)
        self._tab_name = tab_name
        self._parent = parent 

        self.tab_changed = False 

        # Set tab width
        f_metrics = self.fontMetrics()
        space_width = f_metrics.width(' ')
        self._SAVED_ = True 
        self._save_path = None

        self.setTabStopDistance(space_width * 13)

        self.setStyleSheet("""
            QTextEdit 
            {
                font: 12pt;
                font-family: Times New Roman;
                color: #000000;
                background-color: #FFFFFF;
                border: 1 solid #777777;
            }
            """)
        self.setMinimumWidth(800)
        self.setMaximumWidth(800)

        self.setFormat()
        
        self._database = parent._database
        # Start with a default dictionary based on the current locale.
        self.highlighter = EnchantHighlighter(self._database, self.document())
        self.highlighter.setDict(enchant.Dict())
        self.setAcceptRichText(True)
        self._definition_box = parent._definition_box
        
        self.anchor = None 
        self._current_word = None

        # PARENT METHODS 
        self.getWords = parent.getWordsInListBox 
    
    def savePath(self):
        """Returns the current save path to this document."""
        return self._save_path
    
    def setSavePath(self, save_path):
        """Set a save path to this document."""
        self._save_path = save_path
        
    def unsaved(self):
        """Signal method for keeping track of unsaved documents"""
        if self.tab_changed:
            self.tab_changed = False 
        else:
            self._SAVED_ = False 
    
    def isSaved(self):
        """Returns true if this document is currently saved."""
        return self._SAVED_

    def setSaved(self, saved):
        """Set the current document's save state."""
        self._SAVED_ = saved
        if self._SAVED_:
            self._parent._page_tabs.showSavedIcon(self._parent._pages[self._tab_name])

    def turnHighlightingOff(self):
        """Turn off highlighting. """
        self.highlighter.turnOff()

    def turnHighlightingOn(self):
        """Turn on highlighting."""
        self.highlighter.turnOn()

    def tabChange(self, index):
        self.tab_changed = True 

    def setFormat(self):
        """Reset the formatting to the default margin spacing. """
        editor_format = self.document().rootFrame().frameFormat()
        editor_format.setTopMargin(100)
        editor_format.setBottomMargin(100)
        editor_format.setRightMargin(100)
        editor_format.setLeftMargin(100)
        self.document().rootFrame().setFrameFormat(editor_format)
    
    def clearAllFormat(self):
        """Clears all the formatting on the current document."""
        text = self.toPlainText()
        self.clear()
        self.setAcceptRichText(False)
        self.setPlainText(text)
        self.setFormat()
        self.setAcceptRichText(True)
        
    def setTabName(self, tab_name):
        """ 
        Set the tab name associated with this document. Warning, do not use this
        without properly updating the page and notepad dictionaries. 
        """
        self._tab_name = tab_name
    
    def tabName(self):
        """Returns the tab name associated with this document."""
        return self._tab_name

    def contextMenuEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        self.setTextCursor(cursor)
        word = cursor.selectedText()
        cursor.clearSelection()
        self.setTextCursor(cursor)

        if word:
            online_word_search_action = QAction('Look up "{wd}" definition online'.format(wd=word))
            online_word_search_action.triggered.connect(self._searchWordDefintionOnWeb(word))

        reset = QAction(QIcon(os.path.join('images', 'reset.png')), "Reset Page Margins", self)
        reset.triggered.connect(self.setFormat)
        remove_formatting = QAction("Clear All Format", self)

        toggle_highlighting = QAction("Highlighting")
        toggle_highlighting.setCheckable(True)
        toggle_highlighting.setChecked(self.highlighter.isOn())
        toggle_highlighting.toggled.connect(self.toggleHighlightertoggleOption)

        """Custom context menu handler to add a spelling suggestions submenu"""
        popup_menu = self.createSpellcheckContextMenu(event.pos())
        popup_menu.addSeparator()
        popup_menu.addAction(reset)
        popup_menu.addSeparator()
        if word:
            popup_menu.insertSeparator(popup_menu.actions()[0])
            popup_menu.insertAction(popup_menu.actions()[0], online_word_search_action)

            #popup_menu.addAction(online_word_search_action)
        popup_menu.addSeparator()
        popup_menu.addAction(toggle_highlighting)

        popup_menu.exec_(event.globalPos())
    
    # The main menu highlighter toggler gets toggled!
    def toggleHighlightertoggleOption(self):
        """A super long named method that simply turns on/off the edit menu highlighting toggle."""
        self._parent._turn_OnOff_high_action.toggle()


        # Fix bug observed in Qt 5.2.1 on *buntu 14.04 LTS where:
        # 1. The cursor remains invisible after closing the context menu
        # 2. Keyboard input causes it to appear, but it doesn't blink
        # 3. Switching focus away from and back to the window fixes it
        self.focusInEvent(QFocusEvent(QEvent.FocusIn))
    
    def createSpellcheckContextMenu(self, pos):
        """Create and return an augmented default context menu.
        This may be used as an alternative to the QPoint-taking form of
        ``createStandardContextMenu`` and will work on pre-5.5 Qt.
        """
        try:  # Recommended for Qt 5.5+ (Allows contextual Qt-provided entries)
            menu = self.createStandardContextMenu(pos)
        except TypeError:  # Before Qt 5.5
            menu = self.createStandardContextMenu()

        # Add a submenu for setting the spell-check language
        menu.addSeparator()
        menu.addMenu(self.createLanguagesMenu(menu))
        menu.addMenu(self.createFormatsMenu(menu))

        # Try to retrieve a menu of corrections for the right-clicked word
        spell_menu = self.createCorrectionsMenu(
            self.cursorForMisspelling(pos), menu)

        if spell_menu:
            menu.insertSeparator(menu.actions()[0])
            menu.insertMenu(menu.actions()[0], spell_menu)

        return menu
    
    def createCorrectionsMenu(self, cursor, parent=None):
        """Create and return a menu for correcting the selected word."""
        if not cursor:
            return None

        text = cursor.selectedText()
        suggests = trim_suggestions(text,
                                    self.highlighter.dict().suggest(text),
                                    self.max_suggestions)

        spell_menu = QMenu('Spelling Suggestions', parent)
        for word in suggests:
            action = QAction(word, spell_menu)
            action.setData((cursor, word))
            spell_menu.addAction(action)

        # Only return the menu if it's non-empty
        if spell_menu.actions():
            spell_menu.triggered.connect(self.cb_correct_word)
            return spell_menu

        return None
    
    def createLanguagesMenu(self, parent=None):
        """Create and return a menu for selecting the spell-check language."""
        curr_lang = self.highlighter.dict().tag
        lang_menu = QMenu("Language", parent)
        lang_actions = QActionGroup(lang_menu)

        for lang in enchant.list_languages():
            action = lang_actions.addAction(lang)
            action.setCheckable(True)
            action.setChecked(lang == curr_lang)
            action.setData(lang)
            lang_menu.addAction(action)

        lang_menu.triggered.connect(self.cb_set_language)
        return lang_menu

    def formatWordForDictionary(self, word):
        try:
            if len(word):
                first_letter = word[0].upper()
                format_word = word.lower()
                format_word = format_word[1:len(word)]
                format_word = "".join([first_letter, format_word])
                return format_word
        except Exception as e:
            print("Failed to format word:",e)
        return word

    def createFormatsMenu(self, parent=None):
        """Create and return a menu for selecting the spell-check language."""
        fmt_menu = QMenu("Format", parent)
        fmt_actions = QActionGroup(fmt_menu)

        curr_format = self.highlighter.chunkers()
        for name, chunkers in (('Text', []), ('HTML', [tokenize.HTMLChunker])):
            action = fmt_actions.addAction(name)
            action.setCheckable(True)
            action.setChecked(chunkers == curr_format)
            action.setData(chunkers)
            fmt_menu.addAction(action)

        fmt_menu.triggered.connect(self.cb_set_format)
        return fmt_menu
    
    def cursorForMisspelling(self, pos):
        """Return a cursor selecting the misspelled word at ``pos`` or ``None``
        This leverages the fact that QPlainTextEdit already has a system for
        processing its contents in limited-size blocks to keep things fast.
        """
        cursor = self.cursorForPosition(pos)
        misspelled_words = getattr(cursor.block().userData(), 'misspelled', [])

        # If the cursor is within a misspelling, select the word
        for (start, end) in misspelled_words:
            if start <= cursor.positionInBlock() <= end:
                block_pos = cursor.block().position()

                cursor.setPosition(block_pos + start, QTextCursor.MoveAnchor)
                cursor.setPosition(block_pos + end, QTextCursor.KeepAnchor)
                break

        if cursor.hasSelection():
            return cursor
        else:
            return None

    def cb_set_language(self, action):
        """Event handler for 'Language' menu entries."""
        lang = action.data()
        self.highlighter.setDict(enchant.Dict(lang))
    
    def cb_correct_word(self, action):  # pylint: disable=no-self-use
        """Event handler for 'Spelling Suggestions' entries."""
        cursor, word = action.data()

        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()

    def cb_set_format(self, action):
        """Event handler for 'Language' menu entries."""
        chunkers = action.data()
        self.highlighter.setChunkers(chunkers)
        # TODO: Emit an event so this menu can trigger other things

    def mouseDoubleClickEvent(self, event):
        """When clicking on a highlighted definition word, it will show up in the definition display box."""
        if event.button() == Qt.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            cursor.select(QTextCursor.WordUnderCursor)
            self.setTextCursor(cursor)
            word = cursor.selectedText()
            cursor.clearSelection()
            self.setTextCursor(cursor)

            if word.isalpha():
                word = self.formatWordForDictionary(word)
                if word in self.getWords():
                    definition = self._database.getDefinition(word[0], word)
                    if definition != None and len(definition):
                        self._definition_box.setText("<b><u>"+word+"</u></b> - "+definition)
                        
        return super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """This handles the definition tooltip (if enabled from the dictionary menu)."""
        if event.button() == Qt.LeftButton and self._parent._definition_tool_tips:
            cursor = self.cursorForPosition(event.pos())
            cursor.select(QTextCursor.WordUnderCursor)
            self.setTextCursor(cursor)
            word = cursor.selectedText()
            cursor.clearSelection()
            self.setTextCursor(cursor)
            tool_tip = QToolTip() 

            if word.isalpha():
                word = self.formatWordForDictionary(word)
                if word in self.getWords():
                    definition = self._database.getDefinition(word[0], word)
                    if definition != None and len(definition):
                        tool_tip.showText(event.globalPos(), "<b><u>"+word+"</u></b> - "+definition, msecShowTime=90000)

        return super().mousePressEvent(event)

    def _searchWordDefintionOnWeb(self, word):
        def searchWordDefintionOnWeb():
            word_search_path = ''.join(['https://duckduckgo.com/?q=define%3A+', word,'&atb=v204-1&ia=definition'])
            self._parent._view.load(word_search_path)
        return searchWordDefintionOnWeb

# A modified simpler version of the NoteTextBox, this version is used for when the user is filling
# in the "add new definition" dialog. 
#---------------------------------------------------------------------------------------------------------
class DefinitionTextBox(QTextEdit):
    """
    A modified simpler version of the NoteTextBox, this version is used for when the user is filling
    in the "add new definition" dialog. 
    """
    max_suggestions = 20
    def __init__(self, parent=None, *args):
        QTextEdit.__init__(self, *args)
        
        self.highlighter = EnchantHighlighter(None, self.document())
        self.highlighter.setDict(enchant.Dict())
        
        self.anchor = None 
    
    def contextMenuEvent(self, event):
        """Custom context menu handler to add a spelling suggestions submenu."""
        popup_menu = self.createSpellcheckContextMenu(event.pos())
        popup_menu.exec_(event.globalPos())
    
        # Fix bug observed in Qt 5.2.1 on *buntu 14.04 LTS where:
        # 1. The cursor remains invisible after closing the context menu
        # 2. Keyboard input causes it to appear, but it doesn't blink
        # 3. Switching focus away from and back to the window fixes it
        self.focusInEvent(QFocusEvent(QEvent.FocusIn))
    
    def createSpellcheckContextMenu(self, pos):
        """Create and return an augmented default context menu.
        This may be used as an alternative to the QPoint-taking form of
        ``createStandardContextMenu`` and will work on pre-5.5 Qt.
        """
        try:  # Recommended for Qt 5.5+ (Allows contextual Qt-provided entries)
            menu = self.createStandardContextMenu(pos)
        except TypeError:  # Before Qt 5.5
            menu = self.createStandardContextMenu()

        # Add a submenu for setting the spell-check language
        menu.addSeparator()
        menu.addMenu(self.createLanguagesMenu(menu))
        menu.addMenu(self.createFormatsMenu(menu))

        # Try to retrieve a menu of corrections for the right-clicked word
        spell_menu = self.createCorrectionsMenu(
            self.cursorForMisspelling(pos), menu)

        if spell_menu:
            menu.insertSeparator(menu.actions()[0])
            menu.insertMenu(menu.actions()[0], spell_menu)

        return menu
    
    def createCorrectionsMenu(self, cursor, parent=None):
        """Create and return a menu for correcting the selected word."""
        if not cursor:
            return None

        text = cursor.selectedText()
        suggests = trim_suggestions(text,
                                    self.highlighter.dict().suggest(text),
                                    self.max_suggestions)

        spell_menu = QMenu('Spelling Suggestions', parent)
        for word in suggests:
            action = QAction(word, spell_menu)
            action.setData((cursor, word))
            spell_menu.addAction(action)

        # Only return the menu if it's non-empty
        if spell_menu.actions():
            spell_menu.triggered.connect(self.cb_correct_word)
            return spell_menu

        return None
    
    def createLanguagesMenu(self, parent=None):
        """Create and return a menu for selecting the spell-check language."""
        curr_lang = self.highlighter.dict().tag
        lang_menu = QMenu("Language", parent)
        lang_actions = QActionGroup(lang_menu)

        for lang in enchant.list_languages():
            action = lang_actions.addAction(lang)
            action.setCheckable(True)
            action.setChecked(lang == curr_lang)
            action.setData(lang)
            lang_menu.addAction(action)

        lang_menu.triggered.connect(self.cb_set_language)
        return lang_menu
    
    def createFormatsMenu(self, parent=None):
        """Create and return a menu for selecting the spell-check language."""
        fmt_menu = QMenu("Format", parent)
        fmt_actions = QActionGroup(fmt_menu)

        curr_format = self.highlighter.chunkers()
        for name, chunkers in (('Text', []), ('HTML', [tokenize.HTMLChunker])):
            action = fmt_actions.addAction(name)
            action.setCheckable(True)
            action.setChecked(chunkers == curr_format)
            action.setData(chunkers)
            fmt_menu.addAction(action)

        fmt_menu.triggered.connect(self.cb_set_format)
        return fmt_menu

# An inline readonly terminal for trouble shooting purposes. 
#---------------------------------------------------------------------------------------------------------
class Terminal(QTextEdit):
    """An inline readonly terminal for trouble shooting purposes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit 
            {
                font: 12pt;
                color: #EDEDED;
                background-color: #000000;
                border: 1 solid #777777;
            }
            """)
        self.setReadOnly(True)
    
    def insertBlueArrows(self):
        self.setTextColor(Qt.blue)
        self.insertPlainText("\n>> ")
        self.setTextColor(QColor("#EDEDED"))
    
    def contextMenuEvent(self, event):
        clear_text = QAction("Clear")
        clear_text.triggered.connect(self.clear)
        popup_menu = self.createStandardContextMenu(event.pos())
        popup_menu.addSeparator()
        popup_menu.addAction(clear_text)
        if not len(self.toPlainText()):
            clear_text.setDisabled(True)
        popup_menu.exec_(event.globalPos())
        self.focusInEvent(QFocusEvent(QEvent.FocusIn))

# The main display for when a definition is clicked. 
#---------------------------------------------------------------------------------------------------------        
class DefinitionBox(QTextEdit):
    """The main display for when a definition is clicked."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAcceptRichText(True)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit 
            {
                font: 12pt;
                color: #EFEFEF;
                background-color: #232323;
                border: 1 solid #777777;
            }
            """)

    def contextMenuEvent(self, event):
        clear_text = QAction("Clear Defintion")
        clear_text.triggered.connect(self.clear)
        popup_menu = self.createStandardContextMenu(event.pos())
        popup_menu.addSeparator()
        popup_menu.addAction(clear_text)
        if not len(self.toPlainText()):
            clear_text.setDisabled(True)
        popup_menu.exec_(event.globalPos())
        self.focusInEvent(QFocusEvent(QEvent.FocusIn))

# All the words from the current dictionary are populated and viewed here. 
#---------------------------------------------------------------------------------------------------------
class WordListBox(QListWidget):
    """All the words from the current dictionary are populated and viewed here."""
    def __init__(self, parent):
        super().__init__(parent)
        self._parent = parent 
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self._database = parent._database
        self._updateWordListBox = parent.updateWordsListBox
        self.setAlternatingRowColors(True)
        self.setObjectName("wlist")
        self.setStyleSheet("""
            QWidget[objectName^="wlist"]
            {
                alternate-background-color: #111111; 
                background-color: #232323;
            }
        """); 
 
    def contextMenuEvent(self, event):
        """ Displays in a context menu the options to remove or add a new word to the currently selected dictionary."""
        if self.count():
            # Check if any items are selected
            menu = QMenu()
            if len(self.selectedItems()):
                if self.itemAt(event.pos()):                    
                    selected_text = self.currentItem().text()
                    remove_action = menu.addAction(QIcon(os.path.join('images', 'edit-delete.png')), 'Remove "{st}"'.format(st=selected_text))
                    remove_action.triggered.connect(self.removeSelectedDefintion)
                    menu.addSeparator()
            
            new_def_action = QAction(QIcon(os.path.join('images', 'edit-def.png')), "Add New Definition", self)
            new_def_action.triggered.connect(self._parent.enterNewDefinition)
            menu.addAction(new_def_action)
            menu_show = menu.exec_(self.mapToGlobal(event.pos()))

    def removeSelectedDefintion(self):
        """Removes the currently selected definition from the dictionary."""
        selected_text = self.currentItem().text()
        if len(selected_text):
            msg = self.removeWarningMessage(selected_text)
            if msg == QMessageBox.Yes:
                letter = selected_text[0]
                self._database.removeDefinition(letter, selected_text)
                self._updateWordListBox()
        
    def removeWarningMessage(self, definition):
        """Provides a warning message before removing a definition."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Remove Definition?")
        msg.setText('Are you sure you want to remove "{de}?"\nThe definition will be permanently removed if you click "Ok."'.format(de=definition))
        msg.setIcon(msg.Warning)
        msg.setStandardButtons(msg.Yes | msg.No)
        return msg.exec_()                        

# A dialog for entering a new definition into the selected dictionary. 
#---------------------------------------------------------------------------------------------------------
class NewDefinitionDialog(QDialog):
    """A dialog for entering a new definition into the selected dictionary."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        self._database = parent._database
        self.setWindowTitle("Enter New Definition to Dictionary")

        self._select_dictionary = QComboBox()
        self._select_dictionary.addItems(self._database.getDatabaseNames())
        self._definition_name = QLineEdit() 
        self._definition_name.setObjectName("defname")
        self._definition_name.setStyleSheet('QWidget[objectName^="defname"]{background-color: #FFFFFF; color: #000000;}')
        self._definition = DefinitionTextBox(self)
        self._definition.setObjectName("thedef")
        self._definition.setStyleSheet('QWidget[objectName^="thedef"]{background-color: #FFFFFF; color: #000000;}')

        button_row = QWidget(self)
        button_layout = QHBoxLayout(button_row)
        self._enter_button = QPushButton("Enter")
        self._enter_button.clicked.connect(self.enter)
        self._cancel_button = QPushButton("Cancel")
        self._canceled = True 
        self._cancel_button.clicked.connect(self.close) 
        
        button_layout.addWidget(self._enter_button)
        button_layout.addWidget(self._cancel_button) 

        layout.addRow(QLabel("Select the dictionary you would like to add the definition:"))
        layout.addRow(self._select_dictionary)
        layout.addRow(BreakLine(self))
        layout.addRow("Enter the defintion name:", self._definition_name)
        layout.addRow("Enter the definition:", self._definition)
        layout.addRow(button_row)
    
    def isCanceled(self):
        """Returns true if the dialog is canceled."""
        return self._canceled
    
    def getDefinitionName(self):
        """Returns the entered definition name."""
        return self._definition_name.text()

    def getDefinition(self):
        """Returns the entered definition."""
        return self._definition.toPlainText()

    def getDatabase(self):
        """Returns the current selected database.""" 
        return self._select_dictionary.currentText()

    def enter(self):
        """Processes the entered user data.""" 
        if len(self.getDefinitionName()) and len(self.getDefinition()):
            self._canceled = False
            self._database.setNewDatabase(self.getDatabase())
            self.close()
        else:
            self.enterCheckMsg()
    
    def enterCheckMsg(self):
        """Warning message if the user entered nothing or the definition already exists.""" 
        msg = QMessageBox(self)
        msg.setWindowTitle("Empty Entry")
        msg.setText("No defintion name or definition was entered.")
        msg.setIcon(msg.Warning)
        msg.setStandardButtons(msg.Ok)
        msg.exec_()

# A dialog for adding a new dictionary. 
#---------------------------------------------------------------------------------------------------------
class NewDictionaryDialog(QDialog):
    """A dialog for adding a new dictionary."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        self.setWindowTitle("Enter New Dictionary Database")

        self.DATABASE_PATH = "dictionary_databases"
        self._dictionary_name = QLineEdit()
        self._dictionary_name.setPlaceholderText("Enter dictionary name... (e.g. Hegel)")

        button_row = QWidget(self)
        button_layout = QHBoxLayout(button_row)
        self._enter_button = QPushButton("Enter")
        self._enter_button.clicked.connect(self.enter)
        self._cancel_button = QPushButton("Cancel")
        self._canceled = True 
        self._cancel_button.clicked.connect(self.close) 

        button_layout.addWidget(self._enter_button)
        button_layout.addWidget(self._cancel_button) 
      
        layout.addRow("Dictionary Name:", self._dictionary_name)
        layout.addRow(button_row)
    
    def isCanceled(self):
        """Returns true if the dialog is canceled."""
        return self._canceled
    
    def enter(self):
        current_dictionaries = [file_name.split(".")[0] for file_name in os.listdir(self.DATABASE_PATH)]
        """Handles the user input for entering a new dictionary."""
        dictionary_name = self.getDictionaryName()
        if dictionary_name and dictionary_name not in current_dictionaries:
            self._canceled = False
            self.close()
        else:
            self.enterCheckMsg()

    def getDictionaryName(self):
        """Returns the user entered dictionary name."""
        return self._dictionary_name.text()

    def enterCheckMsg(self):
        """Warning message for when the user enters nothing or the dictionary already exists."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Empty Entry")
        msg.setText("No dictionary name was entered or the name already exists.")
        msg.setIcon(msg.Warning)
        msg.setStandardButtons(msg.Ok)
        msg.exec_()


# A dialog for naming the current notepad document tab.  
#---------------------------------------------------------------------------------------------------------
class NewTabNameDialog(QDialog):
    """
    A dialog for naming the current notepad document tab. 
    """
    def __init__(self, parent=None, tab_names=[]):
        super().__init__(parent)
        layout = QFormLayout(self)
        self._current_tab_names = tab_names
        self.setWindowTitle("Enter New Page Tab Name")

        self._tab_name = QLineEdit()
        self._tab_name.setPlaceholderText("Enter name... ")
        self.createNewTabName()

        button_row = QWidget(self)
        button_layout = QHBoxLayout(button_row)
        self._enter_button = QPushButton("Enter")
        self._enter_button.clicked.connect(self.enter)
        self._cancel_button = QPushButton("Cancel")
        self._canceled = True 
        self._cancel_button.clicked.connect(self.close) 

        button_layout.addWidget(self._enter_button)
        button_layout.addWidget(self._cancel_button) 
      
        layout.addRow("Tab Name:", self._tab_name)
        layout.addRow(button_row)
    
    def createNewTabName(self):
        """Creates a new default tab name."""
        counter = 2
        name = "New Page 1"
        while name in self._current_tab_names:
            name = "New Page {c}".format(c=counter)
            counter += 1
        self._tab_name.setText(name)
            
     
    def isCanceled(self):
        """Returns true if the dialog is canceled."""
        return self._canceled
    
    def enter(self):
        """Handles the user input for the tab name."""
        tab_name = self.getTabName()
        if len(tab_name) and tab_name not in self._current_tab_names:
            self._canceled = False
            self.close()
        else:
            self.enterCheckMsg()

    def getTabName(self):
        """Returns the user entered tab name"""
        return self._tab_name.text()

    def enterCheckMsg(self):
        """Warning for entering nothing or a tab name that already exists."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Bad Name Entry")
        msg.setText("No name or a name that already exists was entered.")
        msg.setIcon(msg.Warning)
        msg.setStandardButtons(msg.Ok)
        msg.exec_()
    
    