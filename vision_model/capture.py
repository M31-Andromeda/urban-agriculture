#!/usr/bin/env python3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

CAMERA_INDEX = 0
RESOLUTION = (1920, 1080)
JPEG_QUALITY = 95
OUTPUT_DIR = Path(__file__).resolve().parent / "images"
CAPTURE_INTERVAL = 5 * 60
V4L2_DEVICE = f"/dev/video{CAMERA_INDEX}"

ACTIVE_HOUR_START = 6
ACTIVE_HOUR_END = 21


def disable_backlight_compensation():
    try:
        subprocess.run(
            ["v4l2-ctl", "-d", V4L2_DEVICE, "--set-ctrl=backlight_compensation=0"],
            check=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"WARNING: could not set backlight_compensation=0: {e}", file=sys.stderr)


def take_photo():
    disable_backlight_compensation()
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])

    for _ in range(5):
        cap.read()
        time.sleep(0.05)
    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        print("ERROR: camera did not return a frame", file=sys.stderr)
        return False

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    filename = OUTPUT_DIR / f"{now.strftime('%Y%m%d_%H%M%S')}.jpg"
    cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    print(f"[{now}] Saved {filename.name}")
    return True


def main():
    if "--once" in sys.argv:
        take_photo()
        return

    print(f"Capture loop started: one photo every {CAPTURE_INTERVAL}s, {ACTIVE_HOUR_START}-{ACTIVE_HOUR_END}h.")
    while True:
        now = datetime.now()
        if ACTIVE_HOUR_START <= now.hour < ACTIVE_HOUR_END:
            take_photo()
        else:
            print(f"[{now}] Outside active window; skipping.")
        time.sleep(CAPTURE_INTERVAL)


if __name__ == "__main__":
    main()
