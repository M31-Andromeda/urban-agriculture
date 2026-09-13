# 🌱 Urban Agriculture — Development of a Smart Edge-AI Garden
a project by:
- **Roger Botana Miralles** (GEI UPC) roger.botana@estudiantat.upc.edu  
- **Pol Ruiz Prieto** (GEI UPC) pol.ruiz.prieto@estudiantat.upc.edu 
- **Hugo Andreu Sobrino** (GIA UPC) hugo.andreu.sobrino@estudiantat.upc.edu 


An end-to-end monitoring and decision system for a real urban garden, built entirely by the Urban Agriculture
Group — hardware and software both — around an **Arduino UNO Q**, over the summer of 2026. Every part of the 
physical build (the wooden enclosure included) and the software arquitecture has been designed and written 
by our team from scratch.

The system reads environmental, soil, light, and power-consumption sensors every cycle, runs a trained
classifier to decide what the garden needs, watches the plants through a camera to catch anything visually
out of the ordinary, and reports everything back through a Telegram bot and a Google Sheet — with the water
pump and fans ready to act automatically when the decision system calls for it.

## What it does

- **Reads five physical sensors every cycle** (`BEAT`, 20 minutes by default): a BME680 for ambient
  temperature/humidity/pressure, an SHT30 pressed against the plants for leaf-level temperature/humidity, a
  bank of capacitive soil-moisture probes, a Modulino ambient-light sensor, and an INA219 tracking the power
  draw of the solar system.
- **Takes a photo and screens it for anomalies.** A custom FOMO-AD model, trained in Edge Impulse Studio and
  run locally through the `edge_impulse_linux` runtime (no Docker, no App Lab — just the exported `.eim`
  called directly from Python), scores each daylight photo and flags the regions that look statistically
  off compared to what a healthy garden normally looks like.
- **Decides what the garden needs.** A `RandomForestClassifier`, trained on a synthetic, rule-labeled
  dataset (more on why below), takes the current sensor reading plus the anomaly score and predicts the
  most likely outcome — water, ventilate, a fungal-risk warning, a visual anomaly, or just "everything's
  fine" — with a confidence score for its top three guesses.
- **Acts and reports.** The water pump and fans switch on automatically when the decision calls for it;
  every cycle is logged to a local CSV and pushed to a Google Sheet; and a Telegram bot pushes alerts
  (with the annotated photo attached, when it's a visual anomaly) and answers on-demand commands —
  `/estado` or `/status` for the latest reading, `/picture`/`/foto` and `/anomaly_picture`/`/foto_anomalia`
  to pull the latest photos straight from the chat.

## Using the Telegram bot

No setup needed — anyone can check on the garden straight from Telegram:

1. Open Telegram and search for **[@UGardenbot](https://t.me/UGardenbot)**.
2. Send **`/start`**. That's it — your chat is now subscribed to automatic alerts (watering,
   ventilation, faults, visual anomalies...).

From there, these commands work any time:

| Command | What it does |
|---|---|
| `/estado` or `/status` | Latest sensor reading and the model's current prediction |
| `/estado YYYY-MM-DD HH:MM` | Closest historical reading to that date/time |
| `/picture` or `/foto` | Latest photo of the garden |
| `/anomaly_picture` or `/foto_anomalia` | Latest anomaly-detection photo (with boxes drawn) |

## Architecture

```
              ┌───────────────────────────── MCU (Zephyr sketch) ───────────────────────────────┐
              │  sht_30.ino · bme680.ino · modulino_light.ino · ina219.ino · moisture_v1.2.ino  │
              │  actuator.ino (water pump / fans)                                               │
              └──────────────────────────────────┬──────────────────────────────────────────────┘
                                          Router Bridge (RPC)
              ┌──────────────────────────────────┴─────────────────────────────────────────────────┐
              │                          MPU (Python, python/main.py)                              │
              │                                                                                    │
              │   SensorOrchestra ──► GardenState ◄── ImageOrchestra (FOMO-AD, Edge Impulse)       │
              │                            │                                                       │
              │                    DecisionOrchestra (RandomForest)                                │
              │                            │                                                       │
              │             ┌──────────────┼──────────────┐                                        │
              │      ActuatorOrchestra  DataOrchestra  TelegramDirector                            │
              │      (pump/fans)      (CSV + Sheets)   (alerts + bot commands)                     │
              └────────────────────────────────────────────────────────────────────────────────────┘
```

Every orchestra owns one concern and reads/writes a single shared `GardenState` object under a lock — no
orchestra reaches into another's data directly.

## How it actually runs on the board

`main.py` builds three objects — `GardenState`, `TelegramDirector`, `Director` — and calls `App.run()`. That
one call is doing more than it looks like: `Director` and `TelegramDirector` are both decorated with
`@brick` (from `arduino.app_utils`), which auto-registers every instance with a central `AppController` the
moment it's constructed. When `App.run()` fires, the controller starts each registered brick in turn:

1. It calls that brick's `start()` method once, if it has one. This is where `Director.start()` builds all
   five orchestras a single time — important for `ImageOrchestra`, since spinning up the Edge Impulse
   runtime is too expensive to repeat every cycle.
2. It then looks for methods marked `@brick.loop` or `@brick.execute` and gives each its **own background
   thread**. `Director.run()` is `@brick.loop`: the framework calls it over and over automatically, and the
   `time.sleep(c.BEAT)` at the end of the method is what paces each cycle. `TelegramDirector.listen()` is
   `@brick.execute`: it runs once, in its own thread, and manages its own internal polling loop for Telegram
   updates.

The upshot: the sensor → decision → actuation cycle and the Telegram bot run fully concurrently and
independently, without either one having to manage its own threads — the framework does that, our code just
declares what should loop and what should run once.

In production this whole process runs as the `urb_agric_system.service` **systemd** unit (`Type=simple`,
`Restart=always`) — always on, restarting automatically on a crash and surviving reboots without anyone
needing to log in and start it by hand.

### Why not App Lab

The project still follows the standard App Lab layout (`app.yaml`, `sketch/`, `python/`) and can be imported
 later with `arduino-app-cli app new --from-app`, but day-to-day development happens with a plain
`arduino-cli` setup and a Python virtual environment instead — see `documentacion` for why.

## Tech stack

| Layer | Tech |
|---|---|
| MCU | Zephyr sketch (`arduino:zephyr`), Arduino Router Bridge, Adafruit BME680/INA219 libraries |
| MPU runtime | Python 3.13, `arduino.app_utils` (`App`, `Bridge`, `Logger`, `@brick`) |
| Decision model | `scikit-learn` `RandomForestClassifier`, trained on a synthetic, rule-labeled dataset |
| Vision | Edge Impulse Studio (FOMO-AD), run locally via `edge_impulse_linux`, OpenCV for capture/annotation |
| Reporting | Google Sheets (Apps Script webhook), Telegram Bot API (hand-rolled client) |
| Deployment | systemd service, always-on on the board |

## Running it manually (no Applab)

```bash
# Environment and dependencies
python3 -m venv arduino_env
source arduino_env/bin/activate
pip install -r requirements.txt

# MCU side — compile and flash
cd sketch
arduino-cli compile --upload --fqbn arduino:zephyr:unoq .

# MPU side — run the app
source arduino_env/bin/activate
cd python
export URL_APPSCRIPT="https://script.google.com/macros/s/XXX/exec"
export TELEGRAM_BOT_TOKEN="123456:ABC-your-bot-token"
python3 main.py
```

Both environment variables are optional at startup — if either is missing, that one feature (Sheets
logging or the Telegram bot) logs a warning and quietly no-ops, and the rest of the system keeps running.

The repository of this project, has a complete copy of the arduino app_utils class, that enable to use locally
functionalities stored in arduino.app_utils

To retrain the decision model:

```bash
cd decision_model_training
python3 generate_synthetic_data.py   # writes synthetic_dataset.csv
python3 train_model.py               # writes decision_model.joblib
```

## Known limitations & lessons learned

Worth being upfront about these rather than hiding them behind a demo that happens to work on the day.

**The decision model never sees real sensor data.** Getting a trustworthy ground truth — the actually
correct action for a given past moment — would mean an expert manually reviewing a long history of logs,
which wasn't realistic within this project's scope. Instead, the training set is entirely synthetic: a
rule-based labeler (driven by the same thresholds the rest of the app uses) generates thousands of
plausible sensor readings and their "correct" outcome, and the Random Forest learns to reproduce and
interpolate that logic. It's a deliberate trade-off — the model is only ever as good as the thresholds we
hand-coded, and it has never been validated against real, messy, correlated garden data — but it gave us a
working, probabilistic decision layer instead of a brittle if/else chain.

**The vision model detects anomalies, not specific problems.** The original plan was a model that could
point at a specific issue — a dry or diseased leaf — but that requires a labeled dataset built by hand,
region by region, for each defect. We went with unsupervised anomaly detection instead: it only needs
photos of a normal, healthy garden to train on, and flags whatever doesn't statistically match, with none
of that manual labeling effort. The trade-off is real: in testing, it reliably reacts to a foreign object
appearing in frame, but a moderately dry leaf blends into the natural color variation the model already
treats as normal, so it won't reliably catch the exact problem we originally wanted it to. On top of that,
the webcam's autofocus wasn't always reliable at the working distance we mounted it at, which cost us some
of the sharpness the model could have used.

**The capacitive soil-moisture probes are the weakest link in the sensor stack.** They drift over time and
are noisy enough that we average multiple readings and reject outliers in the sketch just to get a usable
signal — and even then, the absolute values shouldn't be trusted too far. For a next hardware revision, a
more stable and better-calibrated soil sensor is a priority.

**The water pumps are consumer-grade and it shows.** We hit multiple failures during development with the
low-cost pumps we had on hand — not a software problem, but real enough that the actuator code logs and
alerts on a failed activation rather than assuming it worked, and it's the first thing we'd upgrade in a
physical rebuild.

**Battery life is tight for what we're asking of it.** Between the board itself, the camera doing periodic
inference, and the pump/fans drawing current when active, the current battery setup is undersized for
sustained, unattended operation — fine for a demo window, not yet for a real deployment cycle.

See `documentacion` for the rest of the technical postmortem (sensor/firmware quirks, integration
issues, and the physical build in more detail) — still being filled in with photos and screenshots.

## What's next

- Swap the soil-moisture probes for a more stable sensor and recalibrate.
- Move to a proper irrigation pump and validate battery autonomy under real load.
- Collect a real (not synthetic) labeled dataset over a full growing cycle, for both the decision model and
  a future defect-specific vision model.

## Acknowledgments

Claude AI was used for targeted debugging questions and Q&A support at a few points during development.
Architecture decisions, and the physical hardware were designed and built by our team.
