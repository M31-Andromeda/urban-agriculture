import cv2
from arduino.app_utils import *
from edge_impulse_linux.image import ImageImpulseRunner
import subprocess
import sys
import time

from datetime import datetime

import config as c

logger = Logger("VisionSystem")

class ImageOrchestra:

    def __init__(self, garden):
        self.model = ImageImpulseRunner(c.image_model_path)
        self.model.init()

        self.garden = garden

    def disable_backlight_compensation(self):
        try:
            v4l2_device = f"/dev/video{c.CAMERA_SETTINGS['camera_index']}"
            subprocess.run(
                ["v4l2-ctl", "-d", v4l2_device, "--set-ctrl=backlight_compensation=0"],
                check=True, capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Could not set backlight_compensation=0: {e}")

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
            logger.warning("Camera did not return a frame")
            return False

        #Checks if the directory exists, if not it creates one
        c.data_directory.mkdir(parents=True, exist_ok=True)

        imagePath = c.raw_image_path
        self.store_foto(imagePath, frame)
        
        logger.debug(f"{datetime.now()} - Saved {imagePath.name}")
        return True
    

    def delete_image(self, imagePath):
        imagePath.unlink(missing_ok=True)

    def store_foto(self, imagePath, image):
        cv2.imwrite(str(imagePath), image, [cv2.IMWRITE_JPEG_QUALITY, c.CAMERA_SETTINGS["jpeg_quality"]])


    def _grid_to_boxes(self, grid, orig_width, orig_height):
        """Scale FOMO-AD grid cells (in the model's squashed input space, e.g. 96x96) to xyxy boxes
        in the original photo. 'squash' resize mode has no crop/letterbox offset, so this is a plain
        linear scale."""
        scale_x = orig_width / self.model.dim[0]
        scale_y = orig_height / self.model.dim[1]
        boxes = []
        for cell in grid:
            x1 = int(cell["x"] * scale_x)
            y1 = int(cell["y"] * scale_y)
            x2 = int((cell["x"] + cell["width"]) * scale_x)
            y2 = int((cell["y"] + cell["height"]) * scale_y)
            boxes.append({"bounding_box_xyxy": [x1, y1, x2, y2], "score": cell["value"]})
        return boxes

    def _draw_boxes(self, image, boxes, max_score, mean_score):
        for box in boxes:
            x1, y1, x2, y2 = box["bounding_box_xyxy"]
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
        label = f"max={max_score:.1f} mean={mean_score:.1f}"
        cv2.putText(image, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

    def _analyze(self, image):
        """Run anomaly detection on a BGR image (as read by cv2), draw the result and save it as
        _output_image. Returns the raw scores plus the (already image-space) detection boxes."""
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # cv2 works with bgr, the model expects rgb

        # The model itself resizes/squashes the image to its own input size
        features, cropped_img = self.model.get_features_from_image_auto_studio_settings(image_rgb)
        result = self.model.classify(features)["result"]

        max_score = result["visual_anomaly_max"]
        mean_score = result["visual_anomaly_mean"]
        boxes = self._grid_to_boxes(result["visual_anomaly_grid"], image.shape[1], image.shape[0])

        self._draw_boxes(image, boxes, max_score, mean_score)
        output_path = c.output_image_path
        self.store_foto(output_path, image)

        logger.info(f"[{datetime.now()}] anomaly_max={max_score:.1f} anomaly_mean={mean_score:.1f} "
              f"boxes={len(boxes)} -> {output_path.name}")


        output_dict = {
            "anomaly_max_score": max_score,
            "anomaly_mean_score": mean_score,
            "detection": boxes,
            "output_image": str(output_path),
        }
        
        with self.garden.lock:
            self.garden.image_readings = output_dict

    def detect_anomaly(self):

        with self.garden.lock:
            light = self.garden.sensors_readings["light_intensity_(lux)"]
        
        if light > c.THRESHOLDS["camera_lux_threshold"]:
            self.delete_image(c.raw_image_path)
            self.delete_image(c.output_image_path)  # it's ok if the image does not exist
            if not self.take_photo():
                return None

            image = cv2.imread(str(c.raw_image_path))
            self._analyze(image)
            
        else:
            logger.info(f"Skipping vision system: not enough light ({light:.1f} lux <= "
                        f"{c.THRESHOLDS['camera_lux_threshold']} lux threshold).")
            with self.garden.lock:
                self.garden.image_readings = {
                    "anomaly_max_score": 0.0,
                    "anomaly_mean_score": 0.0,
                    "detection": [],
                    "output_image": " ",
                }

    def detect_anomaly_from_file(self, image_path):
        """Run detection on an existing photo instead of the live camera - useful to test against
        the sample photos in vision_model/images/ without a camera attached."""
        image = cv2.imread(str(image_path))
        if image is None:
            logger.warning(f"ERROR: could not read {image_path}")
        self._analyze(image)

    def close(self):
        self.model.stop()


# if __name__ == "__main__":
#     # Isolated manual test, not wired into main.py yet. Usage:
#     #   python3 vision.py                  -> takes a live photo and analyzes it
#     #   python3 vision.py path/to/photo.jpg -> analyzes an existing photo instead
#     orchestra = ImageOrchestra(None)
#     try:
#         if len(sys.argv) > 1:
#             out = orchestra.detect_anomaly_from_file(sys.argv[1])
#         else:
#             out = orchestra.detect_anomaly()
#         print(out)
#     finally:
#         orchestra.close()

