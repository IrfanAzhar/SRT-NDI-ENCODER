"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""

#!/usr/bin/env python3
"""
Video display widget using OpenCV for frame decoding and display
"""

import numpy as np
import cv2
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

class VideoDisplayWidget(QLabel):
    """Widget for displaying video using OpenCV"""
    
    frame_received = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: black;")
        #self.setMinimumSize(450, 280)
        
        self.frame_count = 0
        self.error_count = 0
        self.debug = True
        
    def update_frame(self, frame_data: bytes, width: int, height: int):
        """Update displayed frame with raw BGR data"""
        
        try:
            expected_size = width * height * 3
            
            self.frame_count += 1
            
            if len(frame_data) != expected_size:
                self.error_count += 1
                if self.debug and self.error_count <= 10:
                    print(f"[ERROR] Frame size mismatch: got {len(frame_data)}, expected {expected_size}")
                return
            
            frame_array = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame_array.reshape((height, width, 3))
            
            if self.debug and self.frame_count == 1:
                print(f"[DEBUG] First frame received! Shape: {frame.shape}")
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
            
            if self.debug and self.frame_count == 1:
                print(f"[DEBUG] First frame displayed successfully!")
                
        except Exception as e:
            self.error_count += 1
            if self.debug and self.error_count <= 10:
                print(f"[ERROR] Exception in update_frame: {e}")
    
    def set_status(self, status: str, is_error: bool = False):
        """Set status text overlay"""
        print(f"[STATUS] {status}")
        if is_error:
            self.setStyleSheet("background-color: black; color: red;")
        else:
            self.setStyleSheet("background-color: black; color: white;")
    
    def clear_display(self):
        """Clear the display"""
        self.clear()
        self.setPixmap(QPixmap())
        self.frame_count = 0
        self.error_count = 0
        print("[DEBUG] Display cleared")
    
    def resizeEvent(self, event):
        """Handle resize event to rescale video"""
        if self.pixmap() and not self.pixmap().isNull():
            scaled_pixmap = self.pixmap().scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
        super().resizeEvent(event)
