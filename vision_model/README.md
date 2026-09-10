# Dataset — vision model capture

Photos for training a garden-monitoring vision model that will feed a score into the decision system.
This directory is standalone — `capture.py` doesn't import `arduino.app_utils`, so it runs independently
of the main garden App.

> **The exact ML approach is not decided yet.** This started as a plan to train a custom Edge Impulse
> object-detection model for a single `hoja_seca` (dry leaf) class; it's currently being reconsidered in
> favor of some form of anomaly detection instead, but nothing beyond "capture photos every 5 minutes" is
> settled. Treat everything below the `## Capturing` section as notes/options, not a spec — re-check with
> whoever owns this feature before assuming any of it is the actual plan, and update this file once a
> direction is picked instead of leaving stale instructions here.

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

1. **A test shot came out overexposed in direct sun** (clipped white highlights, hard shadows) — try to get
   at least some shots with the camera not staring straight into direct sun, or with the plant partially
   shaded, so leaf color survives.
2. **A test shot near dusk (~22:00) came out too dark to tell leaf color apart**, with visible sensor
   noise — this is why `ACTIVE_HOUR_END` in `capture.py` was tightened; re-check it still matches actual
   usable daylight as the seasons change.
3. Nudge the camera angle or rotate the pot every so often. A model trained on one fixed framing tends to
   only work in that exact framing.

## Open question: what to actually train, and how

Not decided yet — options seen discussed so far, listed without commitment to either:

- **Object detection for a specific defect class** (the original `hoja_seca` plan): needs bounding-box
  labels around the defect in every photo that has one, and deliberately stages "positive" examples (e.g.
  placing real dry/wilted leaves in frame for part of a session) so there's something to label at all.
  Edge Impulse's Object Detection block + FOMO MobileNetV2, deployed via the `object_detection` Brick, was
  the tool chain considered for this.
- **Anomaly detection over the whole frame**: typically wants mostly "normal" garden photos and few or no
  labels at all (it learns what normal looks like and flags deviation), so the staged-defect-examples
  advice above would **not** apply — check the `arduino:visual_anomaly_detection` Brick's own README on
  the board (`arduino-app-cli brick details arduino:visual_anomaly_detection`) for what data format it
  actually expects before assuming anything here.

Whichever gets picked changes what "a good capture session" means (staged defects vs. just normal
operation) and the whole labeling workflow — rewrite this section for real once that's settled, rather than
patching it further.
