# Dataset — dry-leaf detector

Photos for training the custom Edge Impulse object-detection model (single class, working name
`hoja_seca`) that will feed a "dry leaf score" into the decision system. This directory is standalone —
`capture.py` doesn't import `arduino.app_utils`, so it runs independently of the main garden App.

## Capturing

```bash
# Manual single shot (ignores the active-hours window)
/home/arduino/arduino_env/bin/python3 capture.py --force

# Automatic, every 5 minutes, only between 07:00-22:00 local time
# (a plain USB webcam has no night vision -- shots taken in the dark are just
# black frames, so capture.py skips them instead of wasting storage/labeling time)
```

Photos land in `images/` as `YYYYMMDD_HHMMSS.jpg`, 1280x720. That directory is gitignored.

### Running unattended (systemd user timer)

```bash
mkdir -p ~/.config/systemd/user
cp systemd/dry_leaf_dataset_capture.service systemd/dry_leaf_dataset_capture.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now dry_leaf_dataset_capture.timer

# Required for the timer to keep firing after you log out / the terminal closes:
sudo loginctl enable-linger arduino

# Check it's actually running:
systemctl --user list-timers dry_leaf_dataset_capture.timer
journalctl --user -u dry_leaf_dataset_capture.service -f
```

To stop: `systemctl --user disable --now dry_leaf_dataset_capture.timer`.

## Building a dataset that's actually useful

A day of passive, untouched shots mostly buys you **lighting/color variety** (dawn, midday glare, dusk),
which is genuinely useful — natural light changes color balance a lot. It does **not** by itself give the
model anything to learn about dry leaves, for two reasons found while testing this:

1. **The test shot came out overexposed in direct sun** (clipped white highlights, hard shadows) — in that
   light, dry and healthy leaves can both look washed-out white. Try to get at least some shots with the
   camera not staring straight into direct sun, or with the plant partially shaded, so leaf color survives.
2. **If no dry leaf is ever in frame, there's nothing to label.** During the 24h window, deliberately:
   - Place a couple of real dry/wilted leaves (plucked from this or another plant) in view for part of the
     day, then remove them for the rest — so the dataset has a real mix of "present" and "absent" frames.
   - Nudge the camera angle or rotate the pot 2-3 times over the day. A detector trained on one fixed
     framing tends to only work in that exact framing.

Aim for on the order of 150-300 usable images this way (5-minute cadence over ~14 active hours already
gets you there); that's enough for a hackathon-quality FOMO model, not a research dataset.

## Labeling in Edge Impulse Studio

- Create impulse → **Image** processing block → **Object Detection** learning block, target hardware
  **Arduino UNO Q**.
- One class, `hoja_seca`. Draw the box tightly around the actual dry/brown/curled region, not the whole
  leaf, when a leaf is only partially dry.
- Discard clipped/overexposed shots where you can't tell the leaf color apart — labeling those teaches the
  model noise.
- Train with **FOMO MobileNetV2 0.35** (fast, meant for exactly this kind of small edge object-detection
  task), then Deploy targeting UNO Q.
- Back in App Lab: the trained model shows up under the `object_detection` Brick's **AI models** tab —
  download it, select it in Brick Configuration, save. `app.yaml` gets updated automatically.
