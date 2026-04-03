"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""

import os
import sys
import subprocess
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
from PyQt6 import QtCore

# ----------- GLOBAL VALUES -----------------------
ORIG_X_POS = 0
ORIG_Y_POS = 0
HEIGHT_FACTOR = 100
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
BUTTON_COLOR = QColor("#FF0000")
X_FACTOR = 10
Y_FACTOR = 10
CONTAINER_HEIGHT_OVERHEAD_DIFFERENCE = 300

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.processes = []  # Store subprocess Popen objects
        self.process_cores = []  # Store which core each process is assigned to
        self.window_count = 0
        self.core_index = 0
        self.load_cpu_affinity_config()
        self.initUI()

    def load_cpu_affinity_config(self):
        """Load CPU affinity settings from config.json"""
        try:
            import json
            config_file = os.path.join(CURRENT_DIR, "config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    cpu_config = config.get("cpu_affinity", {})
                    self.cpu_affinity_enabled = cpu_config.get("enabled", True)
                    self.reserve_core_0 = cpu_config.get("reserve_core_0", True)
            else:
                self.cpu_affinity_enabled = True
                self.reserve_core_0 = True
        except:
            self.cpu_affinity_enabled = True
            self.reserve_core_0 = True
        
        # Get available CPU cores
        self.total_cores = os.cpu_count()
        if self.reserve_core_0 and self.total_cores > 1:
            self.available_cores = list(range(1, self.total_cores))
        else:
            self.available_cores = list(range(self.total_cores))
        
        print(f"CPU Cores: Total={self.total_cores}, Available for windows={len(self.available_cores)}")
        print(f"CPU Affinity: Enabled={self.cpu_affinity_enabled}, Reserve Core 0={self.reserve_core_0}")

    def get_next_core(self):
        """Get next available CPU core in round-robin fashion"""
        if not self.cpu_affinity_enabled:
            return None
        
        core = self.available_cores[self.core_index % len(self.available_cores)]
        self.core_index += 1
        return core

    def initUI(self):
        self.setWindowTitle("SRT to NDI - Container")
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnBottomHint | QtCore.Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("border: 2px solid black; border-radius: 5px; background-color: rgb(150, 150, 150);")
        self.move(50, 10)

        self.winWidth = 450
        self.winHeight = 250
        self.divisor = 1

        self.layout = QVBoxLayout()
        self.vLayout = QVBoxLayout()
        self.hLayout = QHBoxLayout()

        self.label = QLabel(" ===================  LAUNCH NEW WINDOWS OF VIDEO BEEPERS   =================== ")
        self.label.setStyleSheet("font-size: 24pt; color: black; text-align: center; font-weight: bold; font-family: 'Arial'; border: 2px solid black; border-radius: 5px; background-color: rgb(150, 150, 180); ")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.multipleFactor = '4by3'

        self.buttonMultipleWindow2by2 = QPushButton("2-by-2-WINS")
        self.buttonMultipleWindow2by2.setEnabled(True)
        self.buttonMultipleWindow2by2.setStyleSheet("background-color: rgb(150, 150, 180);")
        self.buttonMultipleWindow2by2.clicked.connect(self.launch_multiple_window_2by2)

        self.buttonMultipleWindow3by3 = QPushButton("3-by-3-WINS")
        self.buttonMultipleWindow3by3.setEnabled(False)
        self.buttonMultipleWindow3by3.setStyleSheet("background-color: rgb(150, 150, 180);")
        self.buttonMultipleWindow3by3.clicked.connect(self.launch_multiple_window_3by3)

        self.buttonMultipleWindow4by3 = QPushButton("4-by-3-WINS")
        self.buttonMultipleWindow4by3.setEnabled(False)
        self.buttonMultipleWindow4by3.setStyleSheet("background-color: rgb(150, 150, 180);")
        self.buttonMultipleWindow4by3.clicked.connect(self.launch_multiple_window_4by3)

        self.buttonSingleWindow = QPushButton("SINGLE-WINDOW")
        self.buttonSingleWindow.setEnabled(False)
        self.buttonSingleWindow.setStyleSheet("background-color: rgb(150, 150, 180);")
        self.buttonSingleWindow.clicked.connect(self.launch_single_window)
        
        self.buttonRefresh = QPushButton("REFRESH")
        self.buttonRefresh.setEnabled(True)
        self.buttonRefresh.setStyleSheet("background-color: rgb(150, 150, 180);")
        self.buttonRefresh.clicked.connect(self.refresh)
        
        self.buttonExit = QPushButton("EXIT")
        self.buttonExit.setEnabled(True)
        self.buttonExit.setStyleSheet("background-color: rgb(255, 150, 120);")
        self.buttonExit.clicked.connect(self.exitApp)        
        
        self.vLayout.addWidget(self.label)
        self.hLayout.addWidget(self.buttonMultipleWindow2by2)
        self.hLayout.addWidget(self.buttonMultipleWindow3by3)
        self.hLayout.addWidget(self.buttonMultipleWindow4by3)
        self.hLayout.addWidget(self.buttonSingleWindow)
        self.hLayout.addWidget(self.buttonRefresh)
        self.hLayout.addWidget(self.buttonExit)

        self.layout.addLayout(self.vLayout)
        self.layout.addStretch()
        self.layout.addLayout(self.hLayout)

        self.setLayout(self.layout)
        self.showMaximized()

    def findScreenResolution(self):
        try:
            from Xlib import display
            disp = display.Display()
            screen = disp.screen()
            screenWidth = screen.width_in_pixels
            screenHeight = screen.height_in_pixels - HEIGHT_FACTOR
            disp.close()
            print(f"We have read out the Screen resolution: {screenWidth}x{screenHeight}")
        except Exception as e:
            print('the screen resolution could not be determined')
            print(f'Error: {e}')
            print('we proceed with these default values')
            screenWidth = SCREEN_WIDTH
            screenHeight = SCREEN_HEIGHT - HEIGHT_FACTOR
            print(f"We use the default Screen resolution: {screenWidth}x{screenHeight}")

        return [screenWidth, screenHeight]

    def refresh(self):
        self.kill_processes()
        self.buttonMultipleWindow2by2.setEnabled(True)
        # ------  CAUTION  ----
        # Eanble the following two buttons 3by3 and 4by3 after the testing phase is over
        self.buttonMultipleWindow3by3.setEnabled(False)
        self.buttonMultipleWindow4by3.setEnabled(False)

    def launch_multiple_window_2by2(self):
        print('2-by-2 windows selected')
        self.launch_multiple_window('2by2')

    def launch_multiple_window_3by3(self):
        print('3-by-3 windows selected')
        self.launch_multiple_window('3by3')

    def launch_multiple_window_4by3(self):
        print('4-by-3 windows selected')
        self.launch_multiple_window('4by3')

    def launch_independent_window(self, title, width, height, xPos, yPos, cpu_core=None):
        """Launch a completely independent window process with optional CPU affinity"""
        
        # Path to the launcher script
        script_path = os.path.join(CURRENT_DIR, "run_stream_window.py")
        
        # Check if launcher script exists
        if not os.path.exists(script_path):
            print(f"ERROR: Launcher script not found at: {script_path}")
            return None
        
        # Build base command
        cmd = [sys.executable, script_path, title, str(width), str(height), str(xPos), str(yPos)]
        
        # If CPU core specified and affinity enabled, use taskset to pin to that core
        if cpu_core is not None and self.cpu_affinity_enabled:
            cmd = ['taskset', '-c', str(cpu_core)] + cmd
            print(f"Pinning window '{title}' to CPU core {cpu_core}")
        
        print(f'Parameters for this window: title = {title}, width = {width}, height = {height}, xPos = {xPos}, yPos = {yPos}')
        
        # Launch as separate process
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                cwd=CURRENT_DIR
            )
            
            # Store process reference and assigned core
            self.processes.append(process)
            self.process_cores.append(cpu_core)
            self.window_count += 1
            
            print(f"Launched window {self.window_count}: {title} (PID: {process.pid}, Core: {cpu_core if cpu_core is not None else 'any'})")
            return process
            
        except Exception as e:
            print(f"ERROR launching window: {e}")
            return None

    def launch_multiple_window(self, multipleFactor):
        self.buttonMultipleWindow2by2.setEnabled(False)
        self.buttonMultipleWindow3by3.setEnabled(False)
        self.buttonMultipleWindow4by3.setEnabled(False)

        if multipleFactor == '2by2':
            rowScreenCount = 2
            columnScreenCount = 2
        elif multipleFactor == '3by3':
            rowScreenCount = 3
            columnScreenCount = 3
        elif multipleFactor == '4by3':
            rowScreenCount = 4
            columnScreenCount = 3
        else:
            return

        # Get the main container window's geometry
        container_geometry = self.frameGeometry()
        container_original_x = container_geometry.x()
        container_original_y = container_geometry.y()
        container_width = container_geometry.width()
        container_height = container_geometry.height()
        
        print(f"Container window: position({container_original_x},{container_original_y}) size({container_width}x{container_height})")

        # we correct the x and y coordinates for the small windows
        container_corrected_x = container_original_x 
        container_corrected_y = container_original_y + 65
        
        # Calculate spacing (margins around the grid)
        margin_x = 20
        margin_y = 35
        
        # Available area inside the container
        available_width = container_width - (columnScreenCount * (margin_x + X_FACTOR)) 
        available_height = container_height - CONTAINER_HEIGHT_OVERHEAD_DIFFERENCE
        
        # Calculate window size based on grid
        window_width = int(available_width / columnScreenCount)
        window_height = int(available_height / rowScreenCount)
        
        print(f"Window size: {window_width}x{window_height}")
        print(f"Margins: left={margin_x}, top={margin_y}")
        
        win_counter = 0
        
        # ------  CAUTION  ----
        # Remove the following instruction after the testing phase
        #columnScreenCount = columnScreenCount - 1
        
        for row in range(rowScreenCount):
            for col in range(columnScreenCount):
                win_counter += 1
                
                # Calculate small window position relative to container
                xPos = container_corrected_x + margin_x + (col * window_width)
                yPos = container_corrected_y + margin_y + (row * window_height)
                
                if col > 0:
                    xPos = xPos + X_FACTOR
                if row > 0:
                    yPos = yPos + Y_FACTOR
                
                title = f"Video-Beeper {win_counter}"
                
                # Get next CPU core for this window (round-robin)
                assigned_core = self.get_next_core()
                
                # Launch independent window
                self.launch_independent_window(
                    title,
                    window_width,
                    window_height,
                    xPos,
                    yPos,
                    assigned_core
                )
                
                print(f"  Window {win_counter}: position({xPos},{yPos}) size({window_width}x{window_height}) Core: {assigned_core if assigned_core is not None else 'any'}")
        
        print(f"Launched {win_counter} windows")

    def launch_single_window(self):
        self.buttonMultipleWindow2by2.setEnabled(False)
        self.buttonMultipleWindow3by3.setEnabled(False)
        self.buttonMultipleWindow4by3.setEnabled(False)
        
        print("Ready to launch a new stream")
        
        # Get the main container window's geometry
        container_geometry = self.frameGeometry()
        container_x = container_geometry.x()
        container_y = container_geometry.y()
        container_width = container_geometry.width()
        container_height = container_geometry.height()
        
        # Set window size
        window_width = 300
        window_height = 400
        
        # Center the window within the container
        xPos = container_x + (container_width - window_width) // 2
        yPos = container_y + (container_height - window_height) // 2
        
        # Get next CPU core for this window
        assigned_core = self.get_next_core()
        
        # Launch single window
        self.launch_independent_window(
            "SRT to NDI Stream",
            window_width,
            window_height,
            xPos,
            yPos,
            assigned_core
        )
        
        print(f"Single window centered at ({xPos},{yPos}) size {window_width}x{window_height} Core: {assigned_core if assigned_core is not None else 'any'}")
        print("New stream launched successfully")

    
    def kill_processes(self):
        """Terminate all child processes"""
        print(f"\nTerminating {len(self.processes)} processes...")
        
        for i, process in enumerate(self.processes):
            try:
                core_info = f" (Core: {self.process_cores[i]})" if i < len(self.process_cores) and self.process_cores[i] is not None else ""
                print(f"  Terminating process {i+1} (PID: {process.pid}){core_info}...")
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print(f"    Process didn't respond, killing...")
                    process.kill()
                    process.wait()
            except Exception as e:
                print(f"    Error: {e}")
        
        self.processes.clear()
        self.process_cores.clear()
        print("All processes terminated")
        return
    
    
    def exitApp(self):
        """Terminate all child processes"""
        self.kill_processes()
        
        # Close the container window
        self.close()
        
        # Exit the application
        QApplication.quit()
