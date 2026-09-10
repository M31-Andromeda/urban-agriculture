#!/usr/bin/env python3
"""Single-shot capture for building the dry-leaf detection dataset.

Standalone on purpose: it does not import `arduino.app_utils` and does not touch
the Bridge, so it can run on its own timer (via systemd, see dataset/systemd/)
independently of whether the main garden App is running.

Usage:
    python3 capture.py            # takes one photo, unless it's outside the active window
    python3 capture.py --force    # ignore the active-hours window (manual test shot)
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

CAMERA_INDEX = 2  # /dev/video2 (Brio 105) -- verified working; video3 is a metadata-only node
RESOLUTION = (1280, 720)
OUTPUT_DIR = Path(__file__).resolve().parent / "images"

# Skip captures outside this local-time window: a plain USB webcam has no night
# vision, so shots taken while it's dark are just black frames that waste
# storage and labeling effort. Adjust to match when the garden actually has light.
ACTIVE_HOUR_START = 7
ACTIVE_HOUR_END = 22


def capture_frame():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera at index {CAMERA_INDEX}")

    # Discard the first couple of frames: USB webcams often return a stale or
    # under-exposed frame immediately after opening, before auto-exposure settles.
    for _ in range(5):
        cap.read()
        time.sleep(0.05)

    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        raise RuntimeError("Camera opened but did not return a frame")

    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Ignore the active-hours window")
    args = parser.parse_args()

    now = datetime.now()
    if not args.force and not (ACTIVE_HOUR_START <= now.hour < ACTIVE_HOUR_END):
        print(f"[{now}] Outside active window ({ACTIVE_HOUR_START}-{ACTIVE_HOUR_END}h); skipping.")
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = OUTPUT_DIR / f"{now.strftime('%Y%m%d_%H%M%S')}.jpg"

    try:
        frame = capture_frame()
    except RuntimeError as e:
        print(f"[{now}] ERROR: {e}", file=sys.stderr)
        return 1

    cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"[{now}] Saved {filename.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
