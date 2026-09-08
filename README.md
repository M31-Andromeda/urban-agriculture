# Urban Agriculture

An Arduino UNO Q-based monitoring system for an urban garden. It reads
environmental, soil, light, and power-consumption sensors, logs the data
locally and to a Google Sheet, and can drive a water pump and fans.

The project follows the standard App Lab App layout (`app.yaml`, `sketch/`,
`python/`), but day-to-day development happens **outside** App Lab, using a
local `arduino-cli` setup and a Python virtual environment. The App can be
imported into App Lab at any time without any restructuring — for example,
to add camera/vision bricks later on.

## Manual development workflow

Requires the Arduino libraries listed in `sketch/sketch.yaml` (already
installed via `arduino-cli`) and the `arduino_env` virtual environment, which
resolves `arduino.app_utils` via `/home/arduino/Personal/libs_personales_py`.

```bash
# Sketch (MCU side)
cd sketch
arduino-cli compile --upload --fqbn arduino:zephyr:unoq .

# App (MPU side)
source ~/arduino_env/bin/activate
cd ../python
export URL_APPSCRIPT="https://script.google.com/macros/s/XXX/exec"  # see below
python3 main.py
```

## Required environment variable

`URL_APPSCRIPT` (the Apps Script endpoint that writes to the Google Sheet) is
a secret and is not committed to the repository. Export it before launching
`main.py` (e.g. from the venv activation script). If it is not set, the
online save step is skipped with a log warning, while the rest of the App
keeps running normally.

## Importing into App Lab

To manage this project with `arduino-app-cli` / App Lab (e.g. to add
`arduino:video_object_detection` or another vision brick), import this
folder as an App:

```bash
arduino-app-cli app new urban-agriculture --from-app /home/arduino/Personal/projects/urban_agriculture
```

Then set `URL_APPSCRIPT` as an environment variable in the App's Brick
Configuration.