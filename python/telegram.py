from arduino.app_utils import *
import csv
import json
import re
import threading
import time
from datetime import datetime

import requests

import config as c

logger = Logger("Telegram")

ALERT_MESSAGES = {
    "WATER": "Watering started: soil moisture below baseline.",
    "EXCESS_WATER": "Excess soil moisture detected. Watering held off.",
    "HYDRIC_STRESS_ALERT": "⚠️ Hydric stress alert: soil moisture is critically low.",
    "FUNGI_ALERT_EXCESS_WATER": "Fungal risk: high humidity combined with excess soil moisture.",
    "VENTILATE": "Ventilation started: temperature/humidity out of range.",
    "LOW_TEMP_ALERT": "Low temperature alert.",
    "NOT_ABLE_TO_WATER": "Watering was needed but the water pump could not be activated.",
    "NOT_ABLE_TO_VENTILATE": "Ventilation was needed but the fans could not be activated.",
}


def _humanize_key(key):
    match = re.match(r"^(.*)_\((.*)\)$", key)
    name, unit = match.groups() if match else (key, "")
    return name.replace("_", " ").strip().capitalize(), unit


def _humanize_label(label):
    return label.replace("_", " ").strip().capitalize()


@brick
class TelegramDirector:
    def __init__(self, garden):
        self.garden = garden
        self._api_base = f"https://api.telegram.org/bot{c.TELEGRAM_BOT_TOKEN}"
        self._subscribers_lock = threading.Lock()
        self.subscribers = self._load_subscribers()

    @brick.execute
    def listen(self):
        if not c.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN is not set (missing environment variable); Telegram bot disabled.")
            return

        logger.info("Telegram command listener started.")
        offset = None
        while True:
            try:
                updates = self._get_updates(offset)
                for update in updates:
                    offset = update["update_id"] + 1
                    self._handle_update(update)
            except Exception as e:
                logger.error(f"Error polling Telegram updates: {e}")
                time.sleep(5)

    def notify(self, label, probability=None):
        if not c.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram alert skipped: TELEGRAM_BOT_TOKEN not set.")
            return
        with self._subscribers_lock:
            subscribers = list(self.subscribers)
        if not subscribers:
            logger.warning("Telegram alert skipped: no chat has sent /start to the bot yet.")
            return

        text = ALERT_MESSAGES.get(label, f"Garden update: {label}")
        if probability is not None:
            text += f" (confidence: {float(probability) * 100:.0f}%)"
        for chat_id in subscribers:
            self._send_message(chat_id, text)

    def _load_subscribers(self):
        if not c.telegram_subscribers_path.exists():
            return set()
        try:
            with open(c.telegram_subscribers_path) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Could not read {c.telegram_subscribers_path}, starting with no subscribers: {e}")
            return set()

    def _add_subscriber(self, chat_id):
        with self._subscribers_lock:
            if chat_id in self.subscribers:
                return False
            self.subscribers.add(chat_id)
            subscribers_copy = list(self.subscribers)
        try:
            with open(c.telegram_subscribers_path, "w") as f:
                json.dump(subscribers_copy, f)
        except OSError as e:
            logger.error(f"Could not persist Telegram subscribers: {e}")
        return True

    def _get_updates(self, offset, timeout=30):
        params = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        response = requests.get(f"{self._api_base}/getUpdates", params=params, timeout=timeout + 10)
        response.raise_for_status()
        return response.json().get("result", [])

    def _handle_update(self, update):
        message = update.get("message")
        if not message or "text" not in message:
            return
        chat_id = message["chat"]["id"]
        command, *args = message["text"].strip().split()

        if command == "/start":
            self._cmd_start(chat_id)
        elif command == "/estado":
            self._cmd_estado(chat_id, args)
        else:
            self._send_message(chat_id, "Unknown command. Available: /start, /estado [YYYY-MM-DD HH:MM]")

    def _cmd_start(self, chat_id):
        is_new = self._add_subscriber(chat_id)
        if is_new:
            logger.info(f"New Telegram subscriber registered: {chat_id}")
        self._send_message(
            chat_id,
            "Hello! I'm your smart urban garden bot.\n"
            "This chat is now registered for automatic alerts (watering, ventilation, faults...).\n\n"
            "Available commands:\n"
            "• /estado — latest sensor reading\n"
            "• /estado YYYY-MM-DD HH:MM — closest historical reading to that time"
        )

    def _cmd_estado(self, chat_id, args):
        if args:
            try:
                target_dt = datetime.strptime(" ".join(args), "%Y-%m-%d %H:%M")
            except ValueError:
                self._send_message(chat_id, "Wrong format. Usage: /estado YYYY-MM-DD HH:MM (e.g. /estado 2026-09-10 15:30)")
                return
            row = self._closest_row(target_dt)
            header = f"Closest record to {row['Time']}" if row else None
        else:
            row = self._last_row()
            header = f"Latest record — {row['Time']}" if row else None

        if row is None:
            self._send_message(chat_id, "No historical data saved yet.")
            return
        self._send_message(chat_id, self._format_row(header, row))

    def _last_row(self):
        if not c.sensors_csv_path.exists():
            return None
        last_row = None
        with open(c.sensors_csv_path, newline="") as f:
            for row in csv.DictReader(f):
                last_row = row
        return last_row

    def _closest_row(self, target_dt):
        if not c.sensors_csv_path.exists():
            return None

        best_row, best_diff = None, None
        with open(c.sensors_csv_path, newline="") as f:
            for row in csv.DictReader(f):
                try:
                    row_dt = datetime.strptime(row["Time"], "%Y-%m-%d %H:%M:%S")
                except (KeyError, ValueError):
                    continue
                diff = abs((row_dt - target_dt).total_seconds())
                if best_diff is None or diff < best_diff:
                    best_row, best_diff = row, diff
        return best_row

    def _format_row(self, header, row):
        lines = [header, ""]
        for key, value in row.items():
            if key == "Time" or key.startswith("label_"):
                continue
            label, unit = _humanize_key(key)
            lines.append(f"• {label}: {value}{unit}")

        prediction_lines = []
        for key in ("label_1", "label_2", "label_3"):
            value = row.get(key)
            if not value:
                continue
            label, _, prob = value.partition(": ")
            prediction_lines.append(f"• {_humanize_label(label)}: {prob}" if prob else f"• {value}")
        if prediction_lines:
            lines.append("")
            lines.append("Predictions:")
            lines += prediction_lines

        return "\n".join(lines)

    def _send_message(self, chat_id, text):
        try:
            response = requests.post(f"{self._api_base}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
            if response.status_code != 200:
                logger.error(f"Telegram sendMessage failed ({response.status_code}): {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
