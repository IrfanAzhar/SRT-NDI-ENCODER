"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""

#!/usr/bin/env python3
"""
Standalone launcher for a single SRT to NDI window
Called by the main container app
"""

import sys
import os
import psutil
from PyQt6.QtWidgets import QApplication

# Add the current directory to path so we can import main_window
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_window import MainWindow

def set_current_process_affinity(cpu_core):
    """Set CPU affinity for the current process if a core is specified"""
    if cpu_core is not None and psutil is not None:
        try:
            # Check if taskset was used (indicated by environment)
            # If we're already pinned by taskset, don't override
            import os
            if 'TASKSET_PINNED' not in os.environ:
                p = psutil.Process()
                p.cpu_affinity([cpu_core])
                print(f"Process {p.pid} pinned to CPU core {cpu_core}")
        except Exception as e:
            print(f"Could not set CPU affinity: {e}")

def main():
    # Parse command line arguments
    title = sys.argv[1] if len(sys.argv) > 1 else "SRT to NDI Stream"
    width = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    height = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    xPos = int(sys.argv[4]) if len(sys.argv) > 4 else 100
    yPos = int(sys.argv[5]) if len(sys.argv) > 5 else 100
    
    # CPU core assignment (if passed via environment or taskset)
    # taskset handles the actual pinning, so we just log it
    try:
        import os
        affinity = os.sched_getaffinity(0)
        if len(affinity) == 1:
            print(f"Process pinned to CPU core: {list(affinity)[0]}")
    except:
        pass
    
    # Create QApplication for this window only
    app = QApplication(sys.argv)
    
    # Create and configure the main window
    window = MainWindow(title, width, height, xPos, yPos)
    window.show()
    
    # Run the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
