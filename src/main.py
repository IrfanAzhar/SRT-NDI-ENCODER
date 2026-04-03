"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""

#!/usr/bin/env python3
"""
SRT to NDI Desktop Encoder
Main entry point for the application
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    """Main application entry point"""
    
    app = QApplication(sys.argv)
    
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
