"""
LEGAL 
**************************************************************************************************************************************
Permission is hereby granted, free of charge, to any person obtaining a copy of this 
software and associated documentation files (the "Software"), to deal in the Software 
without restriction, including without limitation the rights to use, copy, modify, 
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to the following 
conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR 
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE 
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
**************************************************************************************************************************************
"""

###################################################
"""
    *** SMART NOTES *** 

    Author: Jason Reek
"""
###################################################
"""
    Features to add:
    --------------------------
        -Settings menu
        -More formatting tools.
        -GUI friendly table support. 
        -GUI friendly image support.
        -and more...
    
    Features to correct:
    ---------------------------
        -Sticky text cursor when switching from 
         the findText entry to the active document. 
"""

import sys
import os 
from PySide2.QtWidgets import (QApplication)
from PySide2.QtGui import QIcon
from sn_gui import MainWindow
 
def main():
    qss_loc = "qss/style.qss"
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.setWindowIcon(QIcon(os.path.join('images', 'SmartNote.png')))
    
    with open(qss_loc, 'r') as main_qss:
        main_style = main_qss.read()
    app.setStyleSheet(main_style)

    mw = MainWindow()
    mw.showMaximized() 
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()