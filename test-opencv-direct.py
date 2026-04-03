# test_opencv_direct.py
import cv2
import time

url = "srt://192.168.3.108:8890?streamid=read:ikram&transtype=live&latency=200"
print(f"Opening: {url}")

cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("Failed to open stream")
    exit(1)

print("Stream opened, reading frames...")
frame_count = 0

for i in range(100):
    ret, frame = cap.read()
    if ret:
        frame_count += 1
        if frame_count % 10 == 0:
            print(f"Frame {frame_count}: shape {frame.shape}")
            cv2.imshow('Test', frame)
            cv2.waitKey(1)
    else:
        print("No frame")
    time.sleep(0.033)

cap.release()
cv2.destroyAllWindows()
print(f"Total frames: {frame_count}")
