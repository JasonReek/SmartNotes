from PySide2.QtWidgets import (QAction, QMessageBox, QFileDialog)
from PySide2.QtGui import (QIcon, QKeySequence)
#from PySide2.QtCore import 
from PySide2.QtPrintSupport import (QPrinter, QPrintDialog, QPrintPreviewDialog)
from sn_widgets import (NewDictionaryDialog, NewDefinitionDialog)
import os 
from time import sleep 
import chardet

def splitext(p):
    return os.path.splitext(p)[1].lower()

class WindowMenu:
    def __init__(self):
        # Window Menu
        self._main_menu = self.menuBar()

        # FLAGS 
        self._definition_tool_tips = False

        # FILE -----------------------------------------
        self._file_menu = self._main_menu.addMenu("File")

        self._new_command = QAction(QIcon(os.path.join('images', 'edit-new-paper.png')), "New", self)
        self._new_command.triggered.connect(self.newPage)
        self._new_command.setShortcut(QKeySequence.New)
        self._file_menu.addAction(self._new_command)
        self._file_menu.addSeparator()

        # Open 
        self._open_command = QAction(QIcon(os.path.join('images', 'blue-folder-open-document.png')), "Open", self)
        self._open_command.triggered.connect(self.fileOpen)
        self._file_menu.addAction(self._open_command)

        # Save 
        self._save_command = QAction(QIcon(os.path.join('images', 'disk.png')), "Save", self)
        self._save_command.triggered.connect(self.fileSave)
        self._save_command.setShortcut(QKeySequence.Save)
        self._file_menu.addAction(self._save_command)

        # Save As
        self._saveAs_command = QAction(QIcon(os.path.join('images', 'disk--pencil.png')), "Save As", self)
        self._saveAs_command.triggered.connect(self.fileSaveAs)
        self._saveAs_command.setShortcut(QKeySequence.SaveAs)
        self._file_menu.addAction(self._saveAs_command)
        
        # Exit
        self._file_menu.addSeparator()
        self._exit_command = QAction("Exit", self)
        self._exit_command.triggered.connect(self.close)
        self._file_menu.addAction(self._exit_command)

        # EDIT -----------------------------------------
        self._edit_menu = self._main_menu.addMenu("Edit")
        self._edit_menu.addSeparator()
        
        # Toggle Highlighting
        self._turn_OnOff_high_action = QAction("Highlighting", self)
        self._turn_OnOff_high_action.setCheckable(True)
        self._turn_OnOff_high_action.setChecked(True)
        self._turn_OnOff_high_action.toggled.connect(self.turnOnOffHighlighting)
        self._edit_menu.addAction(self._turn_OnOff_high_action)

        # VIEW -----------------------------------------
        self._view_menu = self._main_menu.addMenu("View")

        self._toolbar_sub_view_menu = self._view_menu.addMenu("Toolbars")
        self._toolbar_sub_view_menu.addAction(self._font_toolbar.toggleViewAction())
        self._toolbar_sub_view_menu.addAction(self._align_toolbar.toggleViewAction())
        self._toolbar_sub_view_menu.addAction(self._logic_toolbar.toggleViewAction())
        self._toolbar_sub_view_menu.addSeparator()
        self._toolbar_sub_view_menu.addAction(self._utility_toolbar.toggleViewAction())
        
        self._view_menu.addSeparator()
        self._docks_sub_view_menu = self._view_menu.addMenu("Docks")
        self._docks_sub_view_menu.addAction(self._def_dock.toggleViewAction())
        self._docks_sub_view_menu.addAction(self._word_dock.toggleViewAction())
        self._docks_sub_view_menu.addAction(self._html_dock.toggleViewAction())
        self._docks_sub_view_menu.addAction(self._web_dock.toggleViewAction())
        self._docks_sub_view_menu.addSeparator()
        self._docks_sub_view_menu.addAction(self._terminal_dock.toggleViewAction())

        # HELP -----------------------------------------
        """
            -An about section needs to be madeself.
            -A help html file needs to be created as well. 
        """

        # DICTIONARIES ----------------------------------
        self._dict_menu = self._main_menu.addMenu("Dictionaries")

        # Add New Definition
        self._def_command = QAction(QIcon(os.path.join('images', 'edit-def.png')), "Add New Definition", self)
        self._def_command.triggered.connect(self.enterNewDefinition)
        self._dict_menu.addAction(self._def_command)
        self._dict_menu.addSeparator()

        # Add New Dictionary
        self._dict_command = QAction(QIcon(os.path.join('images', 'dict-edit.png')),"Add New Dictionary", self)
        self._dict_command.triggered.connect(self.enterNewDictionary)
        self._dict_menu.addAction(self._dict_command)

        # Turn Dictionary Tooltips on/off
        self._dict_tooltips_command = QAction("Use Dictonary Tool Tips", self)
        self._dict_tooltips_command.setCheckable(True)
        self._dict_tooltips_command.toggled.connect(self.setDictionaryToolTips)
        self._dict_tooltips_command.setChecked(False)
        self._dict_menu.addSeparator()
        self._dict_menu.addAction(self._dict_tooltips_command)

    def newPageSaveWarning(self, file_list):
        """Warning message that pops up when the user has unsaved documents when attempting to click "New"."""
        msg = QMessageBox()
        f_list = '\n'.join(file_list)
        msg.setWindowTitle("Unsaved File(s)")
        msg.setIcon(msg.Warning)
        msg.setText('One or more files have been modified, would you like to save?')
        msg.setDetailedText("Unsaved Files:\n{fl}".format(fl=f_list))
        msg.setStandardButtons(msg.Yes | msg.No) 
        return msg.exec_()

    def newPage(self):
        """Clears all the current documents and starts with a fresh new one."""
        all_files_saved, file_list = self.areDocumentsSaved()
        if not all_files_saved:
            msg = self.newPageSaveWarning(file_list)
            if msg == QMessageBox.No:
                self._page_tabs.clearAll()
        else:
            self._page_tabs.clearAll()

    def dialogCritical(self, s):
        """Error handling message pop up for trouble shooting."""
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def turnOnOffHighlighting(self, toggled):
        """ Turns on/off the syntax highlighting for the spell checker and dictionary highlights. 
            Idealy used when saving a document into a .pdf to avoid the formatting. 
        """
        if toggled:
            self.activeNotepad().turnHighlightingOn()
        else:
            self.activeNotepad().turnHighlightingOff()

    def saveWarning(self, file_name):
        """ A save warning message that pops up when the user has an unsaved modified document.""" 
        msg = QMessageBox()
        msg.setWindowTitle("Unsaved File")
        msg.setIcon(msg.Warning)
        msg.setText('"{fn}" has been modified, would you like to save?'.format(fn=file_name))
        msg.setStandardButtons(msg.Yes | msg.No | msg.Cancel) 
        return msg.exec_()

    def fileEncodingChardet(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read()) 
                return result['encoding'] 
        except Exception as error:
            self.terminal("File encoding error: {e}".format(e=error)) 

    def fileEncoding(self, file_path):
        try:
            with open(file_path) as src_file:
                return src_file.encoding 
        except Exception as error:
            self.terminal("File encoding error: {e}".format(e=error))

    def fileOpen(self):
        """ The file opening handler.""" 
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Smart Note documents (*.smtn);; Text documents (*.txt);; All files (*.*)")

        if path:
            not_a_reload = True 
            basename = os.path.basename(path)
            current_tab_name = self.activeNotepad().tabName()
            all_files_saved, file_list = self.areDocumentsSaved()
            if not all_files_saved and current_tab_name in file_list:
                save_msg = self.saveWarning(current_tab_name)
                if save_msg == QMessageBox.Yes:
                    self.fileSave()

            if basename in self._page_tabs.tabNames():
                if basename != self.activeNotepad().tabName():
                    self.dialogCritical("File already open!")
                    return
                else:
                    # Ask for save dialog if file has changes
                    not_a_reload = False 

            try:
                enc = self.fileEncodingChardet(path)
                with open(path, 'rU', encoding=enc) as f:
                    text = f.read()

            except Exception as e:
                self.terminal(str(e))

            else:
                self.activeNotepad().setSavePath(path)
                if self.activeNotepad().savePath().lower().endswith((".smtn", ".htm", ".html")):
                    self.activeNotepad().setHtml(text)
                else:
                    self.activeNotepad().setText(text)
            
            if not_a_reload:
                self.activeNotepad().setTabName(basename)
                self._page_tabs.setTabText(self._page_tabs.currentIndex(), basename)
                self.updateTabPages(update_notebook=True)
                self.activeNotepad().setFormat()
            self.activeNotepad().setSaved(True)

    def fileSave(self):
        """File save handler."""
        if self.activeNotepad().savePath() is None:
            # If we do not have a path, we need to use Save As.
            return self.fileSaveAs()

        text = self.activeNotepad().toHtml() if self.activeNotepad().savePath().lower().endswith((".smtn", ".htm", ".html")) else self.activeNotepad().toPlainText()
        try:
            path = self.activeNotepad().savePath()
            enc = self.fileEncodingChardet(path)
            with open(path, 'w', encoding=enc) as f:
                f.write(text)
                f.flush()
                os.fsync(f)

                self.activeNotepad().setSaved(True)

        except Exception as e:
            self.terminal(str(e))

    def fileSaveAs(self):
        """File save as handler."""
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Smart Note documents (*.smtn);; PDF files (*.pdf);; Text documents (*.txt); All files (*.*)")
        new_tab_name = os.path.basename(path)
        if not path:
            # If dialog is cancelled, will return ''
            return
        while self.tabOpenOtherThanFirst(new_tab_name):
            self.dialogCritical("That file name is already open, try another name.")
            path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Smart Note documents (*.smtn);; PDF files (*.pdf);; Text documents (*.txt); All files (*.*)")
            new_tab_name = os.path.basename(path)

        # PDF Saved
        if path.lower().endswith('.pdf'):
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            self.activeNotepad().document().print_(printer)
            sleep(1)

        else:
            self.activeNotepad().setSavePath(path)
            text = self.activeNotepad().toHtml() if self.activeNotepad().savePath().lower().endswith((".smtn", ".htm", ".html")) else self.activeNotepad().toPlainText()
            try:
                enc = self.fileEncodingChardet(self.activeNotepad().savePath())
                with open(self.activeNotepad().savePath(), 'w', encoding=enc) as f:
                    f.write(text)
                    f.flush()
                    os.fsync(f)

            except Exception as e:
                self.terminal(str(e))

            else:
                self.activeNotepad().setSaved(True)
                self.activeNotepad().setTabName(new_tab_name)
                self._page_tabs.setTabText(self._page_tabs.currentIndex(), new_tab_name)
                self.updateTabPages(update_notebook=True)

    def tabOpen(self, tab_name):
        """Checks if the selected tab name already exists within the tabs."""
        for other_tab_name in self._page_tabs.tabNames():
            if tab_name == other_tab_name:
                return True
        return False 
    
    def tabOpenOtherThanFirst(self, tab_name):
        """Checks if the selected tab name already exists within the tabs other than the first tab."""
        for tab_index, other_tab_name in enumerate(self._page_tabs.tabNames()):
            if tab_name == other_tab_name and tab_index:
                return True
        return False 

    def setDictionaryToolTips(self, checked):
        """When checked, the document definition tooltips will show when the user
           holds down a right clicks the word. 
        """
        self._definition_tool_tips = checked

    def enterNewDefinition(self):
        """Enters a user inputed word definition in the current dictionary."""
        definition_dialog = NewDefinitionDialog(self)
        definition_dialog.exec_()
        definition_name = None 
        definition = None 
        if not definition_dialog.isCanceled():
            definition_name = definition_dialog.getDefinitionName()
            definition = definition_dialog.getDefinition()
            letter = definition_name[0]
            if not self._database.checkIfLetterExists(letter):
                self._database.insertNewTableLetter(letter)
            self._database.addDefinition(letter, definition_name, definition)
            self.updateWordsListBox()
            self.activeNotepad().highlighter.updateRules()

    def enterNewDictionary(self):
        """Enters a user named dictionary."""
        dictionary_dialog = NewDictionaryDialog()
        dictionary_dialog.exec_()
        if not dictionary_dialog.isCanceled():
            self._database.addNewDatabase(dictionary_dialog.getDictionaryName()+".db")
            self.updateDatabaseNames()

    

