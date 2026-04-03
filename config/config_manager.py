"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""

#!/usr/bin/env python3
"""
Configuration manager for loading/saving app settings
"""

import json
import os

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "srt_url": "srt://192.168.3.108:8890?streamid=read:ikram",
            "rtsp_url": "rtsp://192.168.3.108:8554/ikram",
            "ndi_stream_name": "SRT2NDI_1",
            "ndi_group": "SRT2NDI",
            "ndi_discovery_ip": "192.168.3.110",
            "ndi_broadcast": True,
            "ffmpeg_path": "/usr/local/bin/ffmpeg",
            "retry_attempts": 3,
            "retry_delay": 2,
            "window_geometry": {"x": 100, "y": 100, "width": 1024, "height": 768}
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
                    return default_config
            except Exception as e:
                print(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save_config()
