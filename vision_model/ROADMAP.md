# Roadmap — anomaly detection → decision model → Telegram photo alert

Tracks what's left to turn the captured photos into a working `ANOMALY_DETECTED`-style signal.
Check items off (or delete them) as they land; keep this file only as long as work remains.

## 1. Brick / App Lab groundwork
- [ ] On the board: `arduino-app-cli brick list` — confirm the exact Brick ID (expected `arduino:visual_anomaly_detection`).
- [ ] `arduino-app-cli brick details arduino:visual_anomaly_detection` — read the real API: input format, output format (single score? per-region grid?), and **which end of 0–1 means "normal" vs "anomalous"**. Do not assume.
- [ ] Import the project into App Lab: `arduino-app-cli app new urban-agriculture --from-app /home/arduino/Personal/projects/urban_agriculture`.
- [ ] Add `arduino:visual_anomaly_detection` under `bricks:` in `app.yaml`.
- [ ] Set `URL_APPSCRIPT` / `TELEGRAM_BOT_TOKEN` as Brick Configuration env vars in the App Lab UI.

## 2. Dataset + training (Edge Impulse Studio, GUI-only)
- [ ] Check how many usable photos `vision_model/capture.py` has accumulated so far, and over how many distinct lighting conditions (a single day's worth is mostly one weather/light condition — flag this as a real quality risk, not just a checkbox).
- [ ] Upload photos to an Edge Impulse project, run the anomaly detection processing block, train.
- [ ] Confirm the trained model's score direction (0 vs 1) against a few known-normal and known-off test shots before trusting it.
- [ ] Link the trained model to the `arduino:visual_anomaly_detection` Brick from the App Lab UI.

## 3. `python/vision.py` rewrite
- [ ] Replace the manual `cv2.VideoCapture` + commented-out `ImageImpulseRunner` code with calls into the Brick's real API (per step 1's `brick details` output).
- [ ] Remove the module-level `image = ImageOrchestra(); image.delete_image()` side effect before this file is ever imported from `main.py` — it runs at import time today, which is fine only because nothing imports it yet.
- [ ] Confirm whether the Brick's output includes per-region coordinates (needed to draw boxes) or only a single frame-level score — this decides whether "boxes" are literally available or need to be approximated from a coarse anomaly grid.

## 4. Decision model wiring (already documented in the top-level `CLAUDE.md`)
- [ ] Add the anomaly score to `GardenState.keys` / `garden.sensors_readings` (e.g. `anomaly_score_(0-1)`).
- [ ] Add a threshold to `config.THRESHOLDS` (e.g. `anomaly_score_high`) and the key to `config.FEATURES`.
- [ ] Teach `SyntheticDataGenerator.sample_reading()` a plausible distribution for the new value, and `labeler()` the new `ANOMALY_DETECTED` label (or whatever name is chosen) in `decision_model_training/generate_synthetic_data.py`.
- [ ] Add the same field to the `predictor` dict in `DecisionOrchestra.predict()` (`python/decision_sys.py`).
- [ ] Regenerate + retrain: `generate_synthetic_data.py` → `train_model.py`.

## 5. Telegram photo alert
- [ ] `telegram.py` only has `_send_message` (text via Bot API `sendMessage`) — add a `_send_photo`-style method using the Bot API's `sendPhoto` (multipart upload), since a new capability, not just a new message string, is needed.
- [ ] Draw the anomaly region(s) on the saved frame (`cv2.rectangle` or similar) before sending, using whatever coordinates step 3 confirmed are available.
- [ ] Wire `ActuatorOrchestra` (or `Director`) to call the new photo-alert path when the top prediction is `ANOMALY_DETECTED`.
