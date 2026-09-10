#!/usr/bin/env python3
"""Continuous capture loop for building the dry-leaf detection dataset.

Standalone: no arduino.app_utils/Bridge import, so it runs independently of the
main garden App. A systemd service (vision_model/systemd/) just keeps it alive.

Usage:
    python3 capture.py          # loop forever: one photo every CAPTURE_INTERVAL seconds
    python3 capture.py --once   # single manual test shot, ignores the active-hours window
"""

import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

CAMERA_INDEX = 0  # /dev/video0 (Brio 105); re-check with `v4l2-ctl --list-devices` if this stops working
RESOLUTION = (1920, 1080)  # max MJPG resolution the Brio 105 reports
JPEG_QUALITY = 95
OUTPUT_DIR = Path(__file__).resolve().parent / "images"
CAPTURE_INTERVAL = 5 * 60  # seconds between shots

# A plain USB webcam has no night vision, so skip shots outside this local-time
# window -- they'd just be black frames wasting storage/labeling effort.
ACTIVE_HOUR_START = 6
ACTIVE_HOUR_END = 21


def take_photo():
    """Grab one frame and save it to OUTPUT_DIR. Returns True on success."""
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])

    # Discard the first frames: right after opening, before auto-exposure settles,
    # USB webcams often return a stale or under-exposed frame.
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
