#!/usr/bin/env python3
"""
test_display.py - Test different display methods for SRT stream
"""

import sys
import time
import vlc
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import QTimer

# Your SRT URL (adjust if needed)
SRT_URL = "srt://192.168.3.108:8890?streamid=read:ikram"

def test_vlc_standalone():
    """Test VLC can play SRT stream in standalone window"""
    print("\n=== Testing VLC Standalone ===")
    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(SRT_URL)
    player.set_media(media)
    
    print(f"Playing: {SRT_URL}")
    print("VLC window should appear. Close after 10 seconds...")
    player.play()
    
    # Let it play for 10 seconds
    time.sleep(10)
    player.stop()
    print("VLC test complete\n")

def test_pyqt_vlc_widget():
    """Test VLC embedded in PyQt window"""
    print("\n=== Testing PyQt + VLC Embedded ===")
    
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("SRT Stream Test - VLC Embedded")
    window.resize(800, 600)
    
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    
    # Create VLC widget
    vlc_instance = vlc.Instance()
    player = vlc_instance.media_player_new()
    
    # For embedding, we need to create a widget later
    # This is a simplified test - full embedding requires platform-specific code
    print("Creating VLC media player...")
    media = vlc_instance.media_new(SRT_URL)
    player.set_media(media)
    
    print(f"Playing SRT stream from: {SRT_URL}")
    player.play()
    
    window.show()
    
    # Auto-close after 15 seconds
    QTimer.singleShot(15000, app.quit)
    
    print("Window should appear. Closing after 15 seconds...")
    sys.exit(app.exec())

def test_qtmultimedia():
    """Test PyQt6's QtMultimedia"""
    print("\n=== Testing QtMultimedia ===")
    try:
        from PyQt6.QtMultimedia import QMediaPlayer
        from PyQt6.QtMultimediaWidgets import QVideoWidget
        from PyQt6.QtCore import QUrl
        
        app = QApplication(sys.argv)
        window = QMainWindow()
        window.setWindowTitle("SRT Stream Test - QtMultimedia")
        window.resize(800, 600)
        
        central = QWidget()
        window.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        video_widget = QVideoWidget()
        layout.addWidget(video_widget)
        
        player = QMediaPlayer()
        player.setVideoOutput(video_widget)
        player.setSource(QUrl(SRT_URL))
        
        print(f"Playing: {SRT_URL}")
        player.play()
        
        window.show()
        
        QTimer.singleShot(15000, app.quit)
        print("Window should appear. Closing after 15 seconds...")
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"QtMultimedia failed: {e}")
        return False

if __name__ == "__main__":
    print("SRT Display Test Suite")
    print("=" * 50)
    print(f"Testing SRT URL: {SRT_URL}")
    print("=" * 50)
    
    # First test VLC standalone (quickest to verify stream works)
    try:
        test_vlc_standalone()
    except Exception as e:
        print(f"VLC standalone test failed: {e}")
    
    # Ask which test to run
    print("\nSelect test to run:")
    print("1 - PyQt + VLC Embedded")
    print("2 - QtMultimedia")
    choice = input("Choice (1/2): ").strip()
    
    if choice == "1":
        test_pyqt_vlc_widget()
    elif choice == "2":
        test_qtmultimedia()
    else:
        print("Invalid choice")
