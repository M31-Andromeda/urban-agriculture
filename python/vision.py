import cv2
#from edge_impulse_linux.image import ImageImpulseRunner
from pathlib import Path
import subprocess
import sys
import time

from datetime import datetime

import config as c

class ImageOrchestra:

    _image_name = "currentImage.jpg"

    def __init__(self):

        self.output_path = Path(__file__).resolve().parent.parent / "data"

        #self.model = ImageImpulseRunner(c.IMAGE_MODEL_PATH)
        #self.model.init()

    def disable_backlight_compensation(self):
        try:
            v4l2_device = f"/dev/video{c.CAMERA_SETTINGS['camera_index']}"
            subprocess.run(
                ["v4l2-ctl", "-d", v4l2_device, "--set-ctrl=backlight_compensation=0"],
                check=True, capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"WARNING: could not set backlight_compensation=0: {e}", file=sys.stderr)

    def take_photo(self):
        self.disable_backlight_compensation()

        cap = cv2.VideoCapture(c.CAMERA_SETTINGS["camera_index"], cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, c.CAMERA_SETTINGS["resolution"][0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, c.CAMERA_SETTINGS["resolution"][1])

        for _ in range(5):
            cap.read()
            time.sleep(0.05)
        ok, frame = cap.read()
        cap.release()

        if not ok or frame is None:
            print("ERROR: camera did not return a frame", file=sys.stderr)
            return False


        self.output_path.mkdir(parents=True, exist_ok=True)

        now = datetime.now()
        filename = self.output_path / self._image_name
        cv2.imwrite(str(filename), frame, [cv2.IMWRITE_JPEG_QUALITY, c.CAMERA_SETTINGS["jpeg_quality"]])
        print(f"[{now}] Saved {filename.name}")
        return True

    def delete_image(self):
        image_path = self.output_path / self._image_name
        image_path.unlink(missing_ok=True)

    def detect_anomaly(self):
        return


image = ImageOrchestra()
image.delete_image()
