"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""

import sys
import os
from MyAppClass import MyApp
from PyQt6.QtWidgets import QApplication

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec())
