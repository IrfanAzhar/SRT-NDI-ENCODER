# SRT to NDI Desktop Encoder

A desktop application that receives SRT streams and outputs audio-only NDI streams with video display in its GUI.

## Architecture Diagram

![SRT to NDI Encoder Architecture](assets/architecture.svg)

## Features

- Connect to SRT streams via MediaMTX
- Display video using OpenCV
- Convert audio to NDI stream
- Configurable NDI stream names and discovery settings
- Automatic reconnection with retry logic
- Persistent configuration
- Logging to file

## Requirements

- Ubuntu Linux (tested on 24.04 LTS)
- Python 3.12 with OpenCV and other dependencies
- FFmpeg with libndi_newtek and libsrt support
- MediaMTX server for SRT to RTSP conversion

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd srt-ndi-desktop
