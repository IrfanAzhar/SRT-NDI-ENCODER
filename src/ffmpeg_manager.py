"""
This Linux desktop SRT to NDI encoder is built by Dr Irfan Azhar, between 03 March and 03 April 2026.
It is free for all without any explicit or implicit liablity to the author.
"""

#!/usr/bin/env python3
"""
FFmpeg manager for handling streaming processes
"""

import subprocess
import threading
import time
import queue
import os
import fcntl
from typing import Optional

class FFmpegManager:
    """Manages FFmpeg processes for streaming"""
    
    def __init__(self, logger, ffmpeg_path="/usr/local/bin/ffmpeg"):
        self.logger = logger
        self.ffmpeg_path = ffmpeg_path
        self.video_process = None
        self.ndi_process = None
        self.video_monitor_thread = None
        self.ndi_monitor_thread = None
        self.stop_monitor = False
        self.error_queue = queue.Queue()
        
        # For tracking FFmpeg activity
        self.last_frame_log = 0
        self.ffmpeg_active = False
        self.audio_detected = False
        self.frame_count = 0
        
        # Get optimal thread count for FFmpeg
        self.total_cores = os.cpu_count()
        self.ffmpeg_threads = self.get_optimal_threads()
        self.logger.info(f"FFmpeg will use {self.ffmpeg_threads} threads per process")
    
    def get_optimal_threads(self):
        """Get optimal thread count for FFmpeg"""
        try:
            import json
            config_file = "config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    cpu_config = config.get("cpu_affinity", {})
                    threads = cpu_config.get("ffmpeg_threads", 2)
                    return threads
        except:
            pass
        return min(2, max(1, self.total_cores // 2))
    
    def _enhance_srt_url(self, srt_url: str) -> str:
        if '?' in srt_url:
            return f"{srt_url}&transtype=live&latency=200"
        else:
            return f"{srt_url}?transtype=live&latency=200"
    
    def _set_nonblocking(self, fd):
        """Set file descriptor to non-blocking mode"""
        try:
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        except:
            pass
    
    def start_video(self, srt_url: str) -> bool:
        if self.video_process and self.video_process.poll() is None:
            self.logger.warning("Video FFmpeg already running")
            return False
        
        enhanced_url = self._enhance_srt_url(srt_url)
        
        video_cmd = [
            self.ffmpeg_path,
            '-hide_banner',
            '-re',
            '-timeout', '5000000',
            '-flush_packets', '1',
            '-threads', str(self.ffmpeg_threads),
            '-i', enhanced_url,
            '-map', '0:v',
            '-c:v', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-f', 'rawvideo',
            'pipe:1'
        ]
        
        self.logger.info(f"Starting video FFmpeg with {self.ffmpeg_threads} threads")
        self.ffmpeg_active = False
        self.audio_detected = False
        self.last_frame_log = time.time()
        self.frame_count = 0
        
        try:
            self.video_process = subprocess.Popen(
                video_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # Set stdout to non-blocking
            self._set_nonblocking(self.video_process.stdout.fileno())
            
            self.stop_monitor = False
            self.video_monitor_thread = threading.Thread(target=self._monitor_video_process)
            self.video_monitor_thread.start()
            
            self.logger.info("Video FFmpeg started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start video FFmpeg: {e}")
            return False
    
    def start_ndi(self, srt_url: str, ndi_name: str,
                  ndi_group: str = "SRT2NDI", discovery_ip: str = "192.168.3.110",
                  broadcast: bool = True) -> bool:
        """Start separate FFmpeg process for audio-only NDI output"""
        
        # Stop existing NDI process if any
        self.stop_ndi()
        
        enhanced_url = self._enhance_srt_url(srt_url)
        
        # Build NDI output URL in correct format
        ndi_output = f"ndi://{ndi_name}"
        
        # Add discovery parameters if not using broadcast
        if not broadcast and discovery_ip:
            ndi_output = f"ndi://{ndi_name}?discovery={discovery_ip}"
        
        ndi_cmd = [
            self.ffmpeg_path,
            '-hide_banner',
            '-re',
            '-timeout', '5000000',
            '-threads', str(self.ffmpeg_threads),
            '-i', enhanced_url,
            '-map', '0:a:0',
            '-c:a', 'pcm_s16le',
            '-ar', '48000',
            '-ac', '2',
            '-f', 'libndi_newtek',
            ndi_output
        ]
        
        self.logger.info(f"Starting NDI FFmpeg for stream: {ndi_name} with {self.ffmpeg_threads} threads")
        
        try:
            self.ndi_process = subprocess.Popen(
                ndi_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            self.ndi_monitor_thread = threading.Thread(target=self._monitor_ndi_process)
            self.ndi_monitor_thread.start()
            
            self.logger.info(f"NDI streaming started - Name: {ndi_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start NDI FFmpeg: {e}")
            return False
    
    def stop_video(self):
        if self.video_process:
            self.logger.info("Stopping video FFmpeg process...")
            try:
                self.video_process.terminate()
                time.sleep(2)
                if self.video_process.poll() is None:
                    self.video_process.kill()
                self.video_process.wait(timeout=5)
                self.logger.info("Video FFmpeg stopped")
            except Exception as e:
                self.logger.error(f"Error stopping video FFmpeg: {e}")
            finally:
                self.video_process = None
        
        if self.video_monitor_thread and self.video_monitor_thread.is_alive():
            self.video_monitor_thread.join(timeout=3)
    
    def stop_ndi(self):
        if self.ndi_process:
            self.logger.info("Stopping NDI FFmpeg process...")
            try:
                self.ndi_process.terminate()
                time.sleep(2)
                if self.ndi_process.poll() is None:
                    self.ndi_process.kill()
                self.ndi_process.wait(timeout=5)
                self.logger.info("NDI FFmpeg stopped")
            except Exception as e:
                self.logger.error(f"Error stopping NDI FFmpeg: {e}")
            finally:
                self.ndi_process = None
        
        if self.ndi_monitor_thread and self.ndi_monitor_thread.is_alive():
            self.ndi_monitor_thread.join(timeout=3)
    
    def stop_all(self):
        self.stop_monitor = True
        self.stop_ndi()
        self.stop_video()
    
    def _monitor_video_process(self):
        """Monitor video FFmpeg stderr"""
        
        while not self.stop_monitor and self.video_process:
            try:
                line = self.video_process.stderr.readline()
                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        # Check for audio stream
                        if 'Stream #0:1' in decoded and 'Audio' in decoded:
                            if not self.audio_detected:
                                self.audio_detected = True
                                self.logger.info("Audio stream detected in SRT input")
                        
                        # Check for frame statistics
                        if 'frame=' in decoded:
                            self.ffmpeg_active = True
                            self.last_frame_log = time.time()
                            # Parse frame count
                            import re
                            match = re.search(r'frame=\s*(\d+)', decoded)
                            if match:
                                self.frame_count = int(match.group(1))
                                if self.frame_count % 30 == 0:
                                    print(f"[FFmpeg] {decoded}")
                        
                        # Log errors
                        if 'error' in decoded.lower() or 'fail' in decoded.lower():
                            self.logger.error(f"Video FFmpeg: {decoded}")
                            self.error_queue.put(decoded)
                
                if self.video_process.poll() is not None:
                    self.logger.warning(f"Video FFmpeg process ended with code: {self.video_process.returncode}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error monitoring video FFmpeg: {e}")
                break
        
        self.logger.debug("Video FFmpeg monitor thread stopped")
    
    def _monitor_ndi_process(self):
        while not self.stop_monitor and self.ndi_process:
            try:
                line = self.ndi_process.stderr.readline()
                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        if 'error' in decoded.lower() or 'fail' in decoded.lower():
                            self.logger.error(f"NDI FFmpeg: {decoded}")
                            self.error_queue.put(decoded)
                        else:
                            self.logger.debug(f"NDI FFmpeg: {decoded}")
                
                if self.ndi_process.poll() is not None:
                    self.logger.warning(f"NDI FFmpeg process ended with code: {self.ndi_process.returncode}")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error monitoring NDI FFmpeg: {e}")
                break
        
        self.logger.debug("NDI FFmpeg monitor thread stopped")
    
    def read_video_chunk(self, chunk_size: int = 16384) -> Optional[bytes]:
        """Read raw video data (non-blocking)"""
        if not self.video_process or self.video_process.poll() is not None:
            return None
        
        try:
            data = self.video_process.stdout.read(chunk_size)
            return data if data else b''
        except BlockingIOError:
            return b''
        except Exception as e:
            self.logger.error(f"Error reading video chunk: {e}")
            return None
    
    def is_video_running(self) -> bool:
        return self.video_process is not None and self.video_process.poll() is None
    
    def is_ndi_running(self) -> bool:
        return self.ndi_process is not None and self.ndi_process.poll() is None
    
    def has_audio_stream(self) -> bool:
        return self.audio_detected
    
    def get_frame_count(self) -> int:
        return self.frame_count
    
    def get_last_error(self) -> Optional[str]:
        try:
            return self.error_queue.get_nowait()
        except queue.Empty:
            return None
