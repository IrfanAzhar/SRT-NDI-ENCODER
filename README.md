# SRT to NDI Desktop Encoder

A desktop application that receives SRT streams and outputs audio-only NDI streams with video display.

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
   
## Operation

- python main_window.py runs the individual instance
- python MyApp_New.py runs the multiple instances with help of a launcher app
- REFRESH button of launcher app terminates all individual instances
- One may modify the code to enable 3 * 3 and 4 * 3 buttons to laucnch as many instances
- It is not recommended to run multiple instances beyond 2 * 2 due to resource contraints
- If the stream is not displayed at initial CONNECT, then DISCONECT, wait for the proper cleanup at side of MediaMTX and press CONNECT again.
- This encoder is tested in following configuartion:
    * Encoder running on one UBUNTU setup
    * MediaMTX runnnig on local machine
    * Encoder reads one SRT stream = ikram, it is displayed and its audio is converted to NDI stream named 'ikram'.
    * RTSP version of the same 'ikram' SRT stream is read in vMIX running in a PCR (Production COntrol Room) of a broadcast setup
    * Audio-only NDI stream=ikram is read in REAPER DAW in the same PCR
    * Video leads the audio by 7000 msec.
    * According to above-mentioned setup, this encoder is suitable for simplex mode (one way processing) of any Broadcast setup
    
## Dsiclaimer

- This is an academic project and it is free for all to test and learn. Commercial applications of this code are not allowed without explicit permission of the author
- No explicit or implicit liability is atributable to the author for this code used by anyone.
- Trademarks and any/every IP (intellecutal property) mentioned anywhere in this project belong to their rightful owners. 
