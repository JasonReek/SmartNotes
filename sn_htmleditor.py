"""
    Big thanks out to Evgenij Legotskoj for his,
    "Qt/C++ - Lesson 058. Syntax highlighting of HTML code in QTextEdit" using that code 
    (and with modifications) I was able to convert it to python!

    -Jason
"""

from PySide2.QtWidgets import (QTextEdit, QMessageBox)
from PySide2.QtGui import (QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QBrush)
from PySide2.QtCore import (QRegExp, Qt) 
from enum import Enum 

class States(Enum):
    NONE = 0
    TAG = 1
    COMMENT = 2
    QUOTE = 3

class HtmlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.start_tag_rules = []
        self.end_tag_rules = []

        self.open_tag = QRegExp("<")
        self.close_tag = QRegExp(">")

        self.edge_tag_format = QTextCharFormat()
        self.edge_tag_format.setForeground(QBrush(QColor("#999999")))

        self.inside_tag_format = QTextCharFormat()
        self.inside_tag_format.setForeground(QBrush(QColor("#32A9DD"))) 

        self.comment_start_expression = QTextCharFormat() 
        self.commend_end_expression = QTextCharFormat() 
        self.multi_line_comment_format = QTextCharFormat() 

        self.quotes = QRegExp()
        self.quotation_format = QTextCharFormat()

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#2566ca"))

        keywordPatterns = ['<\\b!DOCTYPE\\b', '<\\ba\\b', '<\\babbr\\b', '<\\bacronym \\b', '<\\baddress\\b', 
        '<\\bapplet \\b', '<\\barea\\b', '<\\barticle\\b', '<\\baside\\b', '<\\baudio\\b', '<\\bb\\b', '<\\bbase\\b', '<\\bbasefont \\b', 
        '<\\bbdi\\b', '<\\bbdo\\b', '<\\bbig \\b', '<\\bblockquote\\b', '<\\bbody\\b', '<\\bbr\\b', '<\\bbutton\\b', '<\\bcanvas\\b', '<\\bcaption\\b', 
        '<\\bcenter \\b', '<\\bcite\\b', '<\\bcode\\b', '<\\bcol\\b', '<\\bcolgroup\\b', '<\\bcommand\\b', '<\\bdatalist\\b', '<\\bdd\\b', '<\\bdel\\b', 
        '<\\bdetails\\b', '<\\bdfn\\b', '<\\bdir\\b', '<\\bdiv\\b', '<\\bdl\\b', '<\\bdt\\b', '<\\bem\\b', '<\\bembed\\b', '<\\bfieldset\\b', '<\\bfigcaption\\b', 
        '<\\bfigure\\b', '<\\bfont\\b', '<\\bfooter\\b', '<\\bform\\b', '<\\bframe\\b', '<\\bframeset\\b', '<\\bh1\\b', '<\\bh2\\b', '<\\bh3\\b', '<\\bh4\\b', 
        '<\\bh5\\b', '<\\bh6\\b', '<\\bhead\\b', '<\\bheader\\b', '<\\bhgroup\\b', '<\\bhr\\b', '<\\bhtml\\b', '<\\bi\\b', '<\\biframe\\b', '<\\bimg\\b', 
        '<\\binput\\b', '<\\bins\\b', '<\\bkbd\\b', '<\\bkeygen\\b', '<\\blabel\\b', '<\\blegend\\b', '<\\bli\\b', '<\\blink\\b', '<\\bmap\\b', '<\\bmark\\b', 
        '<\\bmenu\\b', '<\\bmeta\\b', '<\\bmeter\\b', '<\\bnav\\b', '<\\bnoframes\\b', '<\\bnoscript\\b', '<\\bobject\\b', '<\\bol\\b', '<\\boptgroup\\b', 
        '<\\boption\\b', '<\\boutput\\b', '<\\bp\\b', '<\\bparam\\b', '<\\bpre\\b', '<\\bprogress\\b', '<\\bq\\b', '<\\brp\\b', '<\\brt\\b', '<\\bruby\\b', '<\\bs\\b', 
        '<\\bsamp\\b', '<\\bscript\\b', '<\\bsection\\b', '<\\bselect\\b', '<\\bsmall\\b', '<\\bsource\\b', '<\\bspan\\b', '<\\bstrike \\b', '<\\bstrong\\b', 
        '<\\bstyle\\b', '<\\bsub\\b', '<\\bsummary\\b', '<\\bsup\\b', '<\\btable\\b', '<\\btbody\\b', '<\\btd\\b', '<\\btextarea\\b', '<\\btfoot\\b', '<\\bth\\b', 
        '<\\bthead\\b', '<\\btime\\b', '<\\btitle\\b', '<\\btr\\b', '<\\btrack\\b', '<\\btt\\b', '<\\bu\\b', '<\\bul\\b', '<\\bvar\\b', '<\\bvideo\\b', '<\\bwbr\\b', 
        ]
        self.start_tag_rules = [(QRegExp(pattern), keywordFormat) for pattern in keywordPatterns]

        keywordPatterns_end = ['</\\ba\\b', '</\\babbr\\b', '</\\bacronym \\b', '</\\baddress\\b', '</\\bapplet \\b', '</\\barea\\b', '</\\barticle\\b', '</\\baside\\b', 
        '</\\baudio\\b', '</\\bb\\b', '</\\bbase\\b', '</\\bbasefont \\b', '</\\bbdi\\b', '</\\bbdo\\b', '</\\bbig \\b', '</\\bblockquote\\b', '</\\bbody\\b', 
        '</\\bbr\\b', '</\\bbutton\\b', '</\\bcanvas\\b', '</\\bcaption\\b', '</\\bcenter \\b', '</\\bcite\\b', '</\\bcode\\b', '</\\bcol\\b', '</\\bcolgroup\\b', 
        '</\\bcommand\\b', '</\\bdatalist\\b', '</\\bdd\\b', '</\\bdel\\b', '</\\bdetails\\b', '</\\bdfn\\b', '</\\bdir\\b', '</\\bdiv\\b', '</\\bdl\\b', '</\\bdt\\b', 
        '</\\bem\\b', '</\\bembed\\b', '</\\bfieldset\\b', '</\\bfigcaption\\b', '</\\bfigure\\b', '</\\bfont\\b', '</\\bfooter\\b', '</\\bform\\b', '</\\bframe\\b', 
        '</\\bframeset\\b', '</\\bh1\\b', '</\\bh2\\b', '</\\bh3\\b', '</\\bh4\\b', '</\\bh5\\b', '</\\bh6\\b', '</\\bhead\\b', '</\\bheader\\b', '</\\bhgroup\\b', 
        '</\\bhr\\b', '</\\bhtml\\b', '</\\bi\\b', '</\\biframe\\b', '</\\bimg\\b', '</\\binput\\b', '</\\bins\\b', '</\\bkbd\\b', '</\\bkeygen\\b', '</\\blabel\\b', 
        '</\\blegend\\b', '</\\bli\\b', '</\\blink\\b', '</\\bmap\\b', '</\\bmark\\b', '</\\bmenu\\b', '</\\bmeta\\b', '</\\bmeter\\b', '</\\bnav\\b', 
        '</\\bnoframes\\b', '</\\bnoscript\\b', '</\\bobject\\b', '</\\bol\\b', '</\\boptgroup\\b', '</\\boption\\b', '</\\boutput\\b', '</\\bp\\b', '</\\bparam\\b', 
        '</\\bpre\\b', '</\\bprogress\\b', '</\\bq\\b', '</\\brp\\b', '</\\brt\\b', '</\\bruby\\b', '</\\bs\\b', '</\\bsamp\\b', '</\\bscript\\b', '</\\bsection\\b', 
        '</\\bselect\\b', '</\\bsmall\\b', '</\\bsource\\b', '</\\bspan\\b', '</\\bstrike \\b', '</\\bstrong\\b', '</\\bstyle\\b', '</\\bsub\\b', '</\\bsummary\\b', 
        '</\\bsup\\b', '</\\btable\\b', '</\\btbody\\b', '</\\btd\\b', '</\\btextarea\\b', '</\\btfoot\\b', '</\\bth\\b', '</\\bthead\\b', '</\\btime\\b', 
        '</\\btitle\\b', '</\\btr\\b', '</\\btrack\\b', '</\\btt\\b', '</\\bu\\b', '</\\bul\\b', '</\\bvar\\b', '</\\bvideo\\b', '</\\bwbr\\b'
        ]
        self.end_tag_rules = [(QRegExp(pattern), keywordFormat) for pattern in keywordPatterns_end]
     
        self.multi_line_comment_format.setForeground(Qt.darkGray)
        self.comment_start_expression = QRegExp("<!--")
        self.comment_end_expression = QRegExp("-->")

        self.quotation_format.setForeground(QBrush(QColor("#FDA172")))
        self.quotes = QRegExp("\"")

    def highlightBlock(self, text):
        self.setCurrentBlockState(States.NONE.value)

        # TAG
        start_index = 0
        start_quote_index = 0
        end_quote_index = None
        quote_length = None 
        end_index = None 
        tag_length = None
        index = 0 
        length = None 
        start_comment_index = 0
        end_comment_index = 0
        comment_length = None 

        # If you're not within a tag
        if self.previousBlockState() != States.TAG.value and self.previousBlockState() != States.QUOTE.value:
            # So we'll try to find the beginning of the next tag. 
            start_index = self.open_tag.indexIn(text)
        
        # Taking the state of the previous text block
        sub_previous_tag = self.previousBlockState()
        while start_index >= 0:
            # we are looking for an end tag
            end_index = self.close_tag.indexIn(text, start_index)

            # If the end tag is not found, then we'll set the block state. 
            if end_index == -1:
                self.setCurrentBlockState(States.TAG.value)
                tag_length = len(text) - start_index
            else:
                tag_length = end_index - start_index + self.close_tag.matchedLength()
            
            # Set the formatting for a tag
            if sub_previous_tag != States.TAG.value:
                # Since the beginning of the tag to the end, if the previous status is not equal Tag
                self.setFormat(start_index, 1, self.edge_tag_format)
                self.setFormat(start_index + 1, tag_length - 1, self.inside_tag_format)
            else:
                # If you're already inside the tag from the start block
                # and before the end tag. 
                self.setFormat(start_index, tag_length, self.inside_tag_format)
                sub_previous_tag = States.NONE.value 
            
            # Format the symbol of the end tag. 
            self.setFormat(end_index, 1, self.edge_tag_format)

            # QUOTES
            start_quote_index = 0
            # If you are not in quotation marks with the previous block
            if self.previousBlockState() != States.QUOTE.value:
                # So we'll try to find the beginning of the quotes
                start_quote_index = self.quotes.indexIn(text, start_index)

            # Highlight all quotes within the tag
            while start_quote_index >= 0 and ((start_quote_index < end_index) or (end_index == -1)):
                end_quote_index = self.quotes.indexIn(text, start_quote_index + 1)
                if end_quote_index == -1:
                    # If a closing quotation mark is found, set the state for the block quote. 
                    self.setCurrentBlockState(States.QUOTE.value)
                    quote_length = len(text) - start_quote_index
                else:
                    quote_length = end_quote_index - start_quote_index + self.quotes.matchedLength()
            
                if (end_index > end_quote_index) or end_index == -1:
                    self.setFormat(start_quote_index, quote_length, self.quotation_format)
                    start_quote_index = self.quotes.indexIn(text, start_quote_index + quote_length)
                
                else:
                    break 
            
            # Again, look for the beginning of the tag
            start_index = self.open_tag.indexIn(text, start_index + tag_length)

        # EDGES OF TAGS
        # Processing the color tags themselves, that is, highlight words div, p, strong etc. 
        for pattern, char_format in self.start_tag_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index + 1, length - 1, char_format)
                index = expression.indexIn(text, index + length)

        for pattern, char_format in self.end_tag_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index + 1, 1, self.edge_tag_format)
                self.setFormat(index + 2, length - 2, char_format)
                index = expression.indexIn(text, index + length)
        
        # COMMENT 
        start_comment_index = 0
        # If the tag is not a previous state commentary
        if self.previousBlockState() != States.COMMENT.value:
            # Then we'll try to find the beginning of a comment
            start_comment_index = self.comment_start_expression.indexIn(text)

        # If a comment is found
        while start_comment_index >= 0:
            # We are looking for the end of the comment. 
            end_comment_index = self.comment_end_expression.indexIn(text, start_comment_index)

            # If the end is not found 
            if end_comment_index == -1:
                # Then set the state comment
                # The principle is similar to that of conventional tags
                self.setCurrentBlockState(States.COMMENT.value)
                comment_length = len(text) - start_comment_index
            else:
                comment_length = end_comment_index - start_comment_index + self.comment_end_expression.matchedLength()
            
            self.setFormat(start_comment_index, comment_length, self.multi_line_comment_format)
            start_comment_index = self.comment_start_expression.indexIn(text, start_comment_index + comment_length)

    
class HtmlWriter(QTextEdit):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._parent = parent 
        self.setStyleSheet("""
            QTextEdit 
            {
                font: 12pt;
                color: #EFEFEF;
                background-color: #232323;
                border: 1 solid #777777;
            }
            """)
        self.highlighter = HtmlHighlighter(self.document())
    
    def dialogCritical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def enterHtml(self):
        try:
            self._parent.activeNotepad().insertHtml(self.toPlainText())
        except Exception as error:
            self.dialogCritical("Failed to enter HTML: {e}".format(e=error))
