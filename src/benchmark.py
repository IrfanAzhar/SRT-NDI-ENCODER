#!/usr/bin/env python3
"""
Benchmark script to measure performance improvements
"""

import subprocess
import time
import psutil
import json
import os
from datetime import datetime

def run_benchmark(num_windows=4, duration=30):
    """Run benchmark for specified number of windows"""
    
    print(f"Running benchmark with {num_windows} windows for {duration} seconds...")
    
    # Start your app (modify path as needed)
    app_process = subprocess.Popen(['python', 'MyApp_New.py'])
    
    # Wait for app to start
    time.sleep(5)
    
    # Collect data
    data = {
        'timestamp': datetime.now().isoformat(),
        'num_windows': num_windows,
        'duration': duration,
        'samples': []
    }
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        sample = {}
        
        # System CPU
        sample['system_cpu'] = psutil.cpu_percent(interval=1, percpu=True)
        
        # FFmpeg processes
        ffmpeg_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'ffmpeg' in proc.info['name'].lower():
                    ffmpeg_procs.append({
                        'pid': proc.info['pid'],
                        'cpu': proc.cpu_percent(interval=0),
                        'mem': proc.info['memory_percent']
                    })
            except:
                pass
        
        sample['ffmpeg_processes'] = ffmpeg_procs
        sample['ffmpeg_count'] = len(ffmpeg_procs)
        
        if ffmpeg_procs:
            sample['total_ffmpeg_cpu'] = sum(p['cpu'] for p in ffmpeg_procs)
        else:
            sample['total_ffmpeg_cpu'] = 0
        
        data['samples'].append(sample)
        
        time.sleep(2)
    
    # Clean up
    app_process.terminate()
    
    # Save results
    filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Benchmark completed. Results saved to {filename}")
    
    # Print summary
    avg_ffmpeg_cpu = sum(s['total_ffmpeg_cpu'] for s in data['samples']) / len(data['samples'])
    avg_ffmpeg_count = sum(s['ffmpeg_count'] for s in data['samples']) / len(data['samples'])
    
    print(f"\n--- Summary ---")
    print(f"Average FFmpeg CPU usage: {avg_ffmpeg_cpu:.1f}%")
    print(f"Average FFmpeg processes: {avg_ffmpeg_count:.0f}")
    print(f"CPU per process: {avg_ffmpeg_cpu / avg_ffmpeg_count:.1f}%")

if __name__ == "__main__":
    run_benchmark()
