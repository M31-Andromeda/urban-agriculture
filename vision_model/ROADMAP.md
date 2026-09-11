# Roadmap — anomaly detection → decision model → Telegram photo alert

Tracks what's left to turn the captured photos into a working `ANOMALY_DETECTED`-style signal.
Check items off (or delete them) as they land; keep this file only as long as work remains.

Decided: the model runs via the App Lab `arduino:visual_anomaly_detection` Brick (not a manual
`edge_impulse_linux` integration). Photo delivery over Telegram stays hand-rolled in `python/telegram.py`
(not the `arduino:telegram_bot` Brick), to keep one consistent Telegram implementation.

## 1. Brick / App Lab groundwork
- [x] Confirmed Brick ID: `arduino:visual_anomaly_detection` (`arduino-app-cli brick list`).
- [x] Read the real API (`arduino-app-cli brick details arduino:visual_anomaly_detection` + its API.md):
  `VisualAnomalyDetection().detect_from_file(path)` / `.detect(image_bytes, image_type)` returns
  `{"anomaly_max_score", "anomaly_mean_score", "detection": [{"class_name", "score", "bounding_box_xyxy": [x1,y1,x2,y2]}, ...]}`.
  `arduino.app_utils.image.draw_anomaly_markers(image, detection)` draws the boxes for you — no manual `cv2.rectangle` needed.
- [ ] Confirm which end of the score means "normal" vs "anomalous" — only checkable once a real (non-default) model is trained; the bundled default model is `concrete-crack-anomaly-detection.eim`, irrelevant here.
- [ ] Import the project into App Lab: `arduino-app-cli app new urban-agriculture --from-app /home/arduino/Personal/projects/urban_agriculture`. Stop `urb_agric_system.service` first — it's the same MCU/Bridge, running both at once will conflict.
- [ ] Add `arduino:visual_anomaly_detection` under `bricks:` in `app.yaml`.
- [ ] Set `URL_APPSCRIPT` / `TELEGRAM_BOT_TOKEN` as Brick Configuration env vars in the App Lab UI.

## 2. Dataset + training (Edge Impulse Studio, GUI-only)
- [ ] Check how many usable photos `vision_model/capture.py` has accumulated so far, and over how many distinct lighting conditions (a single day's worth is mostly one weather/light condition — flag this as a real quality risk, not just a checkbox).
- [ ] Upload photos to an Edge Impulse project, run the anomaly detection processing block, train.
- [ ] Confirm the trained model's score direction (0 vs 1) against a few known-normal and known-off test shots before trusting it.
- [ ] Link the trained model to the `arduino:visual_anomaly_detection` Brick from the App Lab UI (drops the `.eim` under `~/.arduino-bricks/models/`, per the Brick's compose file).

## 3. `python/vision.py` rewrite
- [ ] Replace the manual `cv2.VideoCapture` + commented-out `ImageImpulseRunner` code with `VisualAnomalyDetection` calls.
- [ ] Remove the module-level `image = ImageOrchestra(); image.delete_image()` side effect before this file is ever imported from `main.py` — it runs at import time today, which is fine only because nothing imports it yet.

## 4. Decision model wiring (already documented in the top-level `CLAUDE.md`)
- [ ] Add the anomaly score to `GardenState.keys` / `garden.sensors_readings` (e.g. `anomaly_score_(0-1)`).
- [ ] Add a threshold to `config.THRESHOLDS` (e.g. `anomaly_score_high`) and the key to `config.FEATURES`.
- [ ] Teach `SyntheticDataGenerator.sample_reading()` a plausible distribution for the new value, and `labeler()` the new `ANOMALY_DETECTED` label (or whatever name is chosen) in `decision_model_training/generate_synthetic_data.py`.
- [ ] Add the same field to the `predictor` dict in `DecisionOrchestra.predict()` (`python/decision_sys.py`).
- [ ] Regenerate + retrain: `generate_synthetic_data.py` → `train_model.py`.

## 5. Telegram photo alert (manual, not the `arduino:telegram_bot` Brick)
- [ ] `telegram.py` only has `_send_message` (text via Bot API `sendMessage`) — add a `_send_photo`-style method using the Bot API's `sendPhoto` (multipart upload).
- [ ] Feed it the image `draw_anomaly_markers()` already annotated in step 1/3 — no custom box-drawing code needed.
- [ ] Wire `ActuatorOrchestra` (or `Director`) to call the new photo-alert path when the top prediction is `ANOMALY_DETECTED`.
