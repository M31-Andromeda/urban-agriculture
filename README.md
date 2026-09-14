# 🌱 Urban Agriculture — Development of a Smart Edge-AI Garden
a project by:
- **Roger Botana Miralles** (GEI UPC) roger.botana@estudiantat.upc.edu  
- **Pol Ruiz Prieto** (GEI UPC) pol.ruiz.prieto@estudiantat.upc.edu 
- **Hugo Andreu Sobrino** (GIA UPC) hugo.andreu.sobrino@estudiantat.upc.edu 


An end-to-end monitoring and decision system for a real urban garden, built entirely by the Urban Agriculture
Group — hardware and software both — around an **Arduino UNO Q**, over the summer of 2026. Every part of the 
physical build (the wooden enclosure included) and the software architecture has been designed and written 
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
`arduino-cli` setup and a Python virtual environment instead — see the
[project documentation](UrbanAgriculture_project_documentation.pdf) for why.

## Tech stack

| Layer | Tech |
|---|---|
| MCU | Zephyr sketch (`arduino:zephyr`), Arduino Router Bridge, Adafruit BME680/INA219 libraries |
| MPU runtime | Python 3.13, `arduino.app_utils` (`App`, `Bridge`, `Logger`, `@brick`) |
| Decision model | `scikit-learn` `RandomForestClassifier`, trained on a synthetic, rule-labeled dataset |
| Vision | Edge Impulse Studio (FOMO-AD), run locally via `edge_impulse_linux`, OpenCV for capture/annotation |
| Reporting | Google Sheets (Apps Script webhook), Telegram Bot API (hand-rolled client) |
| Deployment | systemd service, always-on on the board |

## Running it manually (no App Lab, no systemctl)

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
export URL_APPSCRIPT="EXAMPLE"
export TELEGRAM_BOT_TOKEN="EXAMPLE"
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

## Acknowledgments

Claude AI was used for targeted debugging questions and Q&A support at a few points during development.
Architecture decisions, and the physical hardware were designed and built by our team.
