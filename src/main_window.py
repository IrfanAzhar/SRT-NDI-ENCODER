"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""
#!/usr/bin/env python3
"""
Main window for SRT to NDI Desktop Application
"""

import sys
import time
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QGroupBox,
    QFormLayout, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6 import QtCore

from video_display import VideoDisplayWidget
from ffmpeg_manager import FFmpegManager
from config_manager import ConfigManager
from logger import AppLogger

class VideoReaderThread(QThread):
    """Thread for reading video frames from FFmpeg with frame accumulation"""
    
    frame_ready = pyqtSignal(bytes, int, int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, ffmpeg_manager):
        super().__init__()
        print("VideoReaderThread constructor initialized")
        self.ffmpeg = ffmpeg_manager
        self.running = False
        self.frame_width = 0
        self.frame_height = 0
        self.frame_count = 0
        self.buffer = bytearray()
    
    def set_frame_size(self, width, height):
        """Set expected frame dimensions"""
        self.frame_width = width
        self.frame_height = height
        print(f"[DEBUG] VideoReader: Set frame size to {width}x{height}")
    
    def run(self):
        """Main thread loop with frame accumulation"""
        self.running = True
        frame_size = self.frame_width * self.frame_height * 3
        print(f"[DEBUG] VideoReader: Starting with frame size {frame_size} bytes")
        
        while self.running and self.ffmpeg.is_video_running():
            chunk = self.ffmpeg.read_video_chunk(16384)
            if chunk and len(chunk) > 0:
                self.buffer.extend(chunk)
                
                while len(self.buffer) >= frame_size:
                    frame_data = bytes(self.buffer[:frame_size])
                    self.buffer = self.buffer[frame_size:]
                    
                    self.frame_count += 1
                    if self.frame_count % 100 == 0:
                        print(f"[DEBUG] VideoReader: Assembled {self.frame_count} complete frames")
                    
                    self.frame_ready.emit(frame_data, self.frame_width, self.frame_height)
            else:
                # No data, small delay
                time.sleep(0.001)
        
        print(f"[DEBUG] VideoReader: Stopped after {self.frame_count} frames")
    
    def stop(self):
        """Stop the thread"""
        self.running = False
        self.wait()

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, title="SRT to NDI Desktop Encoder", width=200, height=450, xPos=10, yPos=10):
        super().__init__()
        print("Main Window class constructor initialized")
        
        self.window_title = title
        self.window_x = int(xPos)
        self.window_y = int(yPos)
        self.window_width = int(width)
        self.window_height = int(height)
        
        self.logger = AppLogger()
        self.config = ConfigManager()
        self.ffmpeg = FFmpegManager(self.logger, self.config.get("ffmpeg_path"))
        
        self.is_connected = False
        self.is_ndi_on = False
        self.video_width = 256
        self.video_height = 144
        
        self.video_reader = None
        
        self.setup_ui()
        self.load_settings()
        self.show()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)
        
        # Frame count timer (to show FPS)
        self.frame_count_timer = QTimer()
        self.frame_count_timer.timeout.connect(self.update_frame_info)
        self.frame_count_timer.start(2000)
        
        self.logger.info(f"Application started: {self.window_title}")
        print(f"Main Window constructor finished")
    
    def setup_ui(self):
        """Setup the user interface"""
        print("Main Window setup.ui starts")
        self.setWindowTitle(self.window_title)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Video display
        video_group = QGroupBox("Video Display")
        video_layout = QVBoxLayout()
        self.video_widget = VideoDisplayWidget()
        self.video_widget.setMinimumSize(320, 180)
        video_layout.addWidget(self.video_widget)
        video_group.setLayout(video_layout)
        main_layout.addWidget(video_group, stretch=2)
        
        # Configuration panel
        config_group = QGroupBox("Stream Configuration")
        config_layout = QFormLayout()
        
        self.srt_url_edit = QLineEdit()
        self.srt_url_edit.setPlaceholderText("srt://ip:port?streamid=read:name")
        config_layout.addRow("SRT URL:", self.srt_url_edit)
        
        self.ndi_name_edit = QLineEdit()
        self.ndi_name_edit.setPlaceholderText("NDI Stream Name")
        config_layout.addRow("NDI Stream Name:", self.ndi_name_edit)
        
        main_layout.addLayout(config_layout)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("CONNECT")
        self.connect_btn.clicked.connect(self.on_connect)
        self.connect_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("DISCONNECT")
        self.disconnect_btn.clicked.connect(self.on_disconnect)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.disconnect_btn)
        
        self.refresh_btn = QPushButton("REFRESH")
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 8px;")
        #button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        # Audio status button
        self.audio_status_btn = QPushButton("AUDIO ?")
        self.audio_status_btn.setEnabled(False)
        self.audio_status_btn.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.audio_status_btn)
        
        # NDI buttons
        self.ndi_on_btn = QPushButton("NDI ON")
        self.ndi_on_btn.clicked.connect(self.on_ndi_on)
        self.ndi_on_btn.setEnabled(False)
        self.ndi_on_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.ndi_on_btn)
        
        self.ndi_off_btn = QPushButton("NDI OFF")
        self.ndi_off_btn.clicked.connect(self.on_ndi_off)
        self.ndi_off_btn.setEnabled(False)
        self.ndi_off_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.ndi_off_btn)
        
        # EXIT button
        self.exit_btn = QPushButton("EXIT")
        self.exit_btn.clicked.connect(self.on_exit)
        self.exit_btn.setEnabled(True)
        self.exit_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.exit_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status panel
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        status_layout.addWidget(self.status_label)
        
        self.ndi_status_label = QLabel("NDI: Off")
        self.ndi_status_label.setStyleSheet("color: #95a5a6;")
        status_layout.addWidget(self.ndi_status_label)
        
        self.resolution_label = QLabel("Resolution: Not connected")
        self.resolution_label.setStyleSheet("color: #7f8c8d;")
        status_layout.addWidget(self.resolution_label)
        
        self.frame_info_label = QLabel("Frames: 0")
        self.frame_info_label.setStyleSheet("color: #7f8c8d;")
        status_layout.addWidget(self.frame_info_label)
        
        main_layout.addWidget(status_group)
        
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
        """)
        print("Main Window setup.ui finished")
    
    def load_settings(self):
        """Load settings from config"""
        self.srt_url_edit.setText(self.config.get("srt_url"))
        self.ndi_name_edit.setText(self.config.get("ndi_stream_name"))
    
    def save_settings(self):
        """Save settings to config"""
        self.config.set("srt_url", self.srt_url_edit.text())
        self.config.set("ndi_stream_name", self.ndi_name_edit.text())
    
    def update_status(self):
        """Update status display"""
        if self.is_connected:
            if self.is_ndi_on:
                ndi_name = self.ndi_name_edit.text().strip()
                self.ndi_status_label.setText(f"NDI: ON - {ndi_name}")
                self.ndi_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                self.ndi_status_label.setText("NDI: OFF")
                self.ndi_status_label.setStyleSheet("color: #95a5a6;")
            
            self.resolution_label.setText(f"Resolution: {self.video_width}x{self.video_height}")
            
            # Update audio status
            if self.ffmpeg.has_audio_stream():
                self.audio_status_btn.setText("AUDIO ✓")
                self.audio_status_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
            else:
                self.audio_status_btn.setText("NO AUDIO")
                self.audio_status_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 8px;")
        else:
            self.ndi_status_label.setText("NDI: Off")
            self.resolution_label.setText("Resolution: Not connected")
            self.audio_status_btn.setText("AUDIO ?")
            self.audio_status_btn.setStyleSheet("background-color: #95a5a6; color: white; font-weight: bold; padding: 8px;")
    
    def update_frame_info(self):
        """Update frame count display"""
        if self.is_connected:
            frame_count = self.ffmpeg.get_frame_count()
            self.frame_info_label.setText(f"Frames decoded: {frame_count}")
    
    def on_connect(self):
        """Handle connect button click"""
        srt_url = self.srt_url_edit.text().strip()
        if not srt_url:
            QMessageBox.warning(self, "Error", "Please enter an SRT URL")
            return
        
        self.logger.info(f"Connecting to {srt_url}")
        self.status_label.setText("Status: Connecting...")
        self.status_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        QApplication.processEvents()
        
        success = self.ffmpeg.start_video(srt_url)
        
        if success:
            time.sleep(2)
            
            if self.ffmpeg.is_video_running():
                self.is_connected = True
                self.is_ndi_on = False
                
                self.video_reader = VideoReaderThread(self.ffmpeg)
                self.video_reader.frame_ready.connect(self.video_widget.update_frame)
                self.video_reader.set_frame_size(self.video_width, self.video_height)
                self.video_reader.start()
                
                self.update_ui_state()
                self.status_label.setText("Status: Connected")
                self.status_label.setStyleSheet("font-weight: bold; color: #27ae60;")
                self.logger.info(f"Connected successfully")
                print("[INFO] Video reader started, waiting for frames...")
            else:
                self.status_label.setText("Status: Connection Failed")
                self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
                self.logger.error("FFmpeg process exited unexpectedly")
        else:
            self.status_label.setText("Status: Connection Failed")
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            self.logger.error("Failed to start FFmpeg")
    
    def on_disconnect(self):
        """Handle disconnect button click"""
        self.logger.info("Disconnecting...")
        self.status_label.setText("Status: Disconnecting...")
        self.status_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        
        if self.video_reader:
            self.video_reader.stop()
            self.video_reader = None
        
        self.ffmpeg.stop_all()
        
        self.is_connected = False
        self.is_ndi_on = False
        
        self.update_ui_state()
        self.video_widget.clear_display()
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        self.logger.info("Disconnected")
    
    def on_refresh(self):
        """Handle refresh button click"""
        self.logger.info("Refreshing stream...")
        self.status_label.setText("Status: Refreshing...")
        self.status_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        
        ndi_was_on = self.is_ndi_on
        ndi_name = self.ndi_name_edit.text().strip() if ndi_was_on else None
        srt_url = self.srt_url_edit.text().strip()
        
        if self.video_reader:
            self.video_reader.stop()
            self.video_reader = None
        
        self.ffmpeg.stop_all()
        time.sleep(2)
        
        success = self.ffmpeg.start_video(srt_url)
        
        if success:
            time.sleep(2)
            if self.ffmpeg.is_video_running():
                self.is_connected = True
                
                self.video_reader = VideoReaderThread(self.ffmpeg)
                self.video_reader.frame_ready.connect(self.video_widget.update_frame)
                self.video_reader.set_frame_size(self.video_width, self.video_height)
                self.video_reader.start()
                
                if ndi_was_on and ndi_name:
                    ndi_success = self.ffmpeg.start_ndi(
                        srt_url, ndi_name,
                        ndi_group=self.config.get("ndi_group"),
                        discovery_ip=self.config.get("ndi_discovery_ip"),
                        broadcast=self.config.get("ndi_broadcast")
                    )
                    if ndi_success:
                        self.is_ndi_on = True
                        self.logger.info("NDI restarted after refresh")
                    else:
                        self.is_ndi_on = False
                else:
                    self.is_ndi_on = False
                
                self.update_ui_state()
                self.status_label.setText("Status: Connected")
                self.status_label.setStyleSheet("font-weight: bold; color: #27ae60;")
                self.logger.info("Refresh completed")
            else:
                self.status_label.setText("Status: Refresh Failed")
                self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        else:
            self.status_label.setText("Status: Refresh Failed")
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
    
    def on_ndi_on(self):
        """Handle NDI ON button click"""
        if not self.is_connected:
            QMessageBox.warning(self, "Error", "Please connect to SRT stream first")
            return
        
        ndi_name = self.ndi_name_edit.text().strip()
        if not ndi_name:
            QMessageBox.warning(self, "Error", "Please enter an NDI stream name")
            return
        
        self.logger.info(f"Enabling NDI with name: {ndi_name}")
        self.status_label.setText("Status: Starting NDI...")
        self.status_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        QApplication.processEvents()
        
        srt_url = self.srt_url_edit.text().strip()
        
        success = self.ffmpeg.start_ndi(
            srt_url, ndi_name,
            ndi_group=self.config.get("ndi_group"),
            discovery_ip=self.config.get("ndi_discovery_ip"),
            broadcast=self.config.get("ndi_broadcast")
        )
        
        if success:
            self.is_ndi_on = True
            self.update_ui_state()
            self.status_label.setText("Status: Connected - NDI Active")
            self.status_label.setStyleSheet("font-weight: bold; color: #27ae60;")
            self.ndi_status_label.setText(f"NDI: ON - {ndi_name}")
            self.ndi_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.logger.info("NDI streaming started")
            print(f"[INFO] NDI streaming started: {ndi_name}")
        else:
            self.status_label.setText("Status: NDI Start Failed")
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            self.logger.error("Failed to start NDI")
            QMessageBox.warning(self, "Error", "Failed to start NDI stream. Check if FFmpeg has NDI support.")
    
    def on_ndi_off(self):
        """Handle NDI OFF button click"""
        self.logger.info("Disabling NDI")
        self.status_label.setText("Status: Stopping NDI...")
        self.status_label.setStyleSheet("font-weight: bold; color: #f39c12;")
        QApplication.processEvents()
        
        self.ffmpeg.stop_ndi()
        
        self.is_ndi_on = False
        self.update_ui_state()
        self.status_label.setText("Status: Connected")
        self.status_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        self.ndi_status_label.setText("NDI: OFF")
        self.ndi_status_label.setStyleSheet("color: #95a5a6;")
        self.logger.info("NDI stopped")
        print("[INFO] NDI streaming stopped")
    
    def on_exit(self):
        """Handle EXIT button click"""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?\n\nAll streams will be stopped.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("Exit requested, shutting down...")
            self.close()
    
    def update_ui_state(self):
        if self.is_connected:
            self.connect_btn.setEnabled(False)
            self.connect_btn.setStyleSheet("background-color: lightgray; color: white; font-weight: bold; padding: 8px;")
            self.disconnect_btn.setEnabled(True)
            self.disconnect_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
            if self.is_ndi_on:
                self.ndi_on_btn.setEnabled(False)
                self.ndi_on_btn.setStyleSheet("background-color: lightgray; color: white; font-weight: bold; padding: 8px;")
                self.ndi_off_btn.setEnabled(True)
                self.ndi_off_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
            else:
                self.ndi_on_btn.setEnabled(True)
                self.ndi_on_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
                self.ndi_off_btn.setEnabled(False)
                self.ndi_off_btn.setStyleSheet("background-color: lightgray; color: white; font-weight: bold; padding: 8px;")
            
            self.srt_url_edit.setEnabled(True)
            self.ndi_name_edit.setEnabled(not self.is_ndi_on)
        else:
            self.connect_btn.setEnabled(True)
            self.connect_btn.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px;")
            self.disconnect_btn.setEnabled(False)
            self.disconnect_btn.setStyleSheet("background-color: lightgray; color: white; font-weight: bold; padding: 8px;")
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setStyleSheet("background-color: lightgray; color: white; font-weight: bold; padding: 8px;")
            self.ndi_on_btn.setEnabled(False)
            self.ndi_off_btn.setEnabled(False)
            self.srt_url_edit.setEnabled(True)
            self.ndi_name_edit.setEnabled(True)
    
    def closeEvent(self, event):
        """Handle application close"""
        self.logger.info("Application closing...")
        
        if self.video_reader:
            self.video_reader.stop()
        
        self.ffmpeg.stop_all()
        self.save_settings()
        
        self.logger.info("Application closed")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())
