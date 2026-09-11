# Dataset — vision model capture

Photos for training a garden-monitoring vision model that will feed a score into the decision system.
This directory is standalone — `capture.py` doesn't import `arduino.app_utils`, so it runs independently
of the main garden App.

> **Decided (2026-09-11): anomaly detection, trained in Edge Impulse Studio.** This started as a plan to
> train a custom Edge Impulse object-detection model for a single `hoja_seca` (dry leaf) class, but that's
> been dropped in favor of anomaly detection over the whole frame — faster to get to a working model,
> since it doesn't need staged defect examples or bounding-box labeling (see the "Decided" section below).
> Training itself happens in the Edge Impulse Studio web UI, not from this repo.

## Capturing

```bash
# Manual single shot (ignores the active-hours window)
/home/arduino/arduino_env/bin/python3 capture.py --once

# Runs forever in the foreground: one photo every 5 min, only between 07:00-22:00
# local time (a plain USB webcam has no night vision -- shots taken in the dark
# are just black frames, so capture.py skips them instead of wasting storage/
# labeling time). For unattended background use, see the systemd service below.
/home/arduino/arduino_env/bin/python3 capture.py
```

Photos land in `images/` as `YYYYMMDD_HHMMSS.jpg`, 1920x1080 (max MJPG resolution the Brio 105 reports),
quality 95. That directory is gitignored.

### Running unattended (systemd system service)

The interval and active-hours logic live in `capture.py` itself (a plain `while True` loop with
`time.sleep`) — systemd's only job is to keep that one process alive across reboots/crashes, so there's
just one unit, no timer. It's installed as a **system** service (`/etc/systemd/system/`, like the main
`urb_agric_system.service`), not a user service — that way it survives reboots with no login-session
tricks needed:

```bash
sudo cp systemd/urb_agric_photo_capture.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now urb_agric_photo_capture.service

# Check it's actually running:
systemctl status urb_agric_photo_capture.service
journalctl -u urb_agric_photo_capture.service -f
```

To stop: `sudo systemctl disable --now urb_agric_photo_capture.service`.

## What makes a capture session useful (general, applies either way)

A day of passive, untouched shots mostly buys you **lighting/color variety** (dawn, midday glare, dusk),
which is genuinely useful regardless of the final ML approach — natural light changes color balance a lot,
and a model trained on only one lighting condition tends to only work in that condition. Two things found
while testing the capture pipeline itself (these are about image quality, not about labeling, so they hold
no matter what gets trained):

1. **A test shot came out overexposed in direct sun** (clipped white highlights, hard shadows) — traced to
   the Brio 105's `backlight_compensation` control (on by default): it pushes exposure up whenever a bright
   patch is in frame (here, the light-colored board behind the plants), clipping the plant/leaf area around
   it regardless of actual ambient light level. `capture.py` now forces `backlight_compensation=0` via
   `v4l2-ctl` before every shot. Verified to help under overcast light; not yet confirmed under harsh direct
   midday sun — check a real midday shot before calling this fully solved.
2. **A test shot near dusk (~22:00) came out too dark to tell leaf color apart**, with visible sensor
   noise — this is why `ACTIVE_HOUR_END` in `capture.py` was tightened; re-check it still matches actual
   usable daylight as the seasons change.
3. Nudge the camera angle or rotate the pot every so often. A model trained on one fixed framing tends to
   only work in that exact framing.

## Decided: anomaly detection over the whole frame

Trained in Edge Impulse Studio (web UI), not scripted from this repo. Wants mostly "normal" garden photos
and little or no labeling — it learns what normal looks like and flags deviation — so **no staged defect
examples needed** (that was only relevant to the object-detection plan, now dropped). Capture keeps running
as-is: one photo every 5 min, all active hours, for lighting/framing variety.

Inference side is expected to run via the `arduino:visual_anomaly_detection` Brick once this is imported
into App Lab — check its README on the board (`arduino-app-cli brick details
arduino:visual_anomaly_detection`) for the exact input/output format before wiring it up.

**Output**: a continuous score in **0–1** measuring anomaly level (confirm the direction — i.e. whether 1
means "normal" or "anomalous" — against the actual trained model before writing any threshold logic against
it). This score is meant to become a new feature in the decision model (see "Extending the decision model
with a new feature" in the top-level `CLAUDE.md`): a new `garden.sensors_readings` key, a `config.THRESHOLDS`
entry, taught to `SyntheticDataGenerator`/`labeler()` in `decision_model_training/generate_synthetic_data.py`,
added to the `predictor` dict in `python/decision_sys.py`, then `decision_model.joblib` regenerated and
retrained.
