import logging
from datetime import datetime, timedelta, timezone
from aiohttp import web
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram.request import HTTPXRequest

import sys
from pathlib import Path
sys.path.append("/home/arduino/Personal/varios/bot_sheets_info")

from credenciales import TOKEN_TELEGRAM, URL_GOOGLE_SHEETS

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GLOBAL STATES ---
# Store the Chat IDs of users who have started the bot to know who to notify
SUBSCRIBED_CHATS = set()

# Alert control to prevent spam
ALERT_STATE = {
    "last_label": None,
    "last_time": None
}

COOLDOWN_HOURS = 2  # Minimum time before notifying about the SAME label again

def parse_sheet_date(raw_date):
    """Converts the Google Sheets date string to a datetime object in UTC+2."""
    try:
        dt = datetime.fromisoformat(raw_date.replace('Z', '+00:00'))
        return dt.astimezone(timezone(timedelta(hours=2)))
    except Exception:
        return None

# --- BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    await update.message.reply_text(
        "Hello! I am your smart urban garden bot 🌿.\n"
        "I have registered this chat to send you plant health alerts.\n\n"
        "Available commands:\n"
        "• /status - View the latest sensor record\n"
        "• /status HH:MM/DD:MM:YYYY - View record closest to a specific time"
    )

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save the ID in case the user hasn't used /start yet
    SUBSCRIBED_CHATS.add(update.effective_chat.id)
    
    try:
        # 1. CHECK IF THE USER HAS SPECIFIED A DATE
        if context.args:
            hora_str = context.args[0]
            try:
                # Parse the user input: HH:MM/DD:MM:YYYY
                target_dt = datetime.strptime(hora_str, "%H:%M/%d:%m:%Y")
                # Assign the local time zone (UTC+2) for proper comparison
                target_dt = target_dt.replace(tzinfo=timezone(timedelta(hours=2)))
                # Convert to milliseconds (Epoch) so Google Sheets can compare it accurately
                target_ms = int(target_dt.timestamp() * 1000)
            except ValueError:
                await update.message.reply_text(
                    "❌ Incorrect date format.\n"
                    "Correct usage: /status HH:MM/DD:MM:YYYY\n"
                    "Example: /status 15:30/10:09:2026"
                )
                return

            # Request data from Google Sheets sending the target_ms parameter
            response = requests.get(f"{URL_GOOGLE_SHEETS}?target_ms={target_ms}")
            prefix = f"⏳ **Record closest to {hora_str}**"
            
        # 2. IF NO DATE IS PROVIDED, RETURN THE LATEST RECORD (LIVE)
        else:
            response = requests.get(URL_GOOGLE_SHEETS)
            prefix = "📊 **Live Garden Status:**"

        if response.status_code != 200:
            await update.message.reply_text("❌ Error querying Google Sheets.")
            return
            
        d = response.json()
        
        if "error" in d:
            await update.message.reply_text("❌ No records found in the database.")
            return

        # 3. FORMAT THE DATE OF THE RETRIEVED RECORD
        dt = parse_sheet_date(d.get('date_time', ''))
        formatted_date = dt.strftime('%d/%m/%Y %H:%M:%S') if dt else d.get('date_time', 'N/A')

        # 4. RETURN ALL DATA GROUPED AND FORMATTED
        message = (
            f"{prefix}\n"
            f"🕒 Record Time: {formatted_date}\n\n"
            
            f"🌡️ **Environmental Conditions**:\n"
            f"   • Env. Temp.: {d.get('env_temperature_(ºC)', 'N/A')} °C\n"
            f"   • Env. Humidity: {d.get('env_humidity_(%)', 'N/A')} %\n"
            f"   • Pressure: {d.get('pressure_(hPa)', 'N/A')} hPa\n\n"
            
            f"🌱 **Plant & Soil Status**:\n"
            f"   • Soil Moisture: {d.get('soil_moisture_(%)', 'N/A')} %\n"
            f"   • Plant Temp.: {d.get('plants_temp_(ºC)', 'N/A')} °C\n"
            f"   • Plant Humidity: {d.get('plants_hum_(%)', 'N/A')} %\n\n"
            
            f"☀️ **Lighting**:\n"
            f"   • Light: {d.get('light_intensity_(lux)', 'N/A')} lux\n"
            f"   • IR (Raw): {d.get('ir_(raw)', 'N/A')}\n\n"
            
            f"⚡ **Energy Consumption (Panel/Battery)**:\n"
            f"   • Current: {d.get('current_(mA)', 'N/A')} mA\n"
            f"   • Voltage: {d.get('voltage_(V)', 'N/A')} V\n"
            f"   • Power: {d.get('power_(W)', 'N/A')} W\n\n"
            
            f"🏷️ **AI Model Predictions**:\n"
            f"   • {d.get('label1', 'No data')}\n"
            f"   • {d.get('label2', 'No data')}\n"
            f"   • {d.get('label3', 'No data')}"
        )
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ An unexpected error occurred: {e}")

# --- WEBHOOK FOR ARDUINO ALERTS ---
async def alert_handler(request):
    """Receives alerts from the Arduino/Edge-AI board via HTTP POST requests (localhost)."""
    try:
        data = await request.json()
        label = data.get("label", "Unknown")
        probability = float(data.get("probabilidad", 0.0))
    except Exception:
        return web.json_response({"status": "error", "message": "Invalid data format"}, status=400)

    now = datetime.now()

    # Notification logic (if it's the same label as the previous one and the cooldown hasn't passed, ignore it)
    if ALERT_STATE["last_label"] == label:
        if ALERT_STATE["last_time"]:
            time_elapsed = now - ALERT_STATE["last_time"]
            if time_elapsed < timedelta(hours=COOLDOWN_HOURS):
                return web.json_response({"status": "ignored", "reason": "cooldown active"})

    # Update alert state
    ALERT_STATE["last_label"] = label
    ALERT_STATE["last_time"] = now

    # Send message to all subscribed users
    bot = request.app["bot"]
    for chat_id in SUBSCRIBED_CHATS:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🚨 **GARDEN ALERT!** 🚨\n\nThe vision algorithm has detected anomalies in the leaves:\n"
                     f"⚠️ **{label}** (Probability: {probability*100:.1f}%)\n\n"
                     f"Please check the condition of the plants soon."
            )
        except Exception as e:
            logger.error(f"Error sending alert to {chat_id}: {e}")

    return web.json_response({"status": "alert_sent"})

async def start_webhook(application: ApplicationBuilder):
    """Starts the local aiohttp web server on port 8080 to listen for incoming board requests."""
    app = web.Application()
    app["bot"] = application.bot
    app.router.add_post('/alert', alert_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Internal alert server listening on http://localhost:8080/alert")


    
if __name__ == '__main__':
    custom_request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    
    # Register the internal webhook server to start alongside the Telegram bot
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).request(custom_request).post_init(start_webhook).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("estado", estado))

    print("🤖 Bot initialized and listening for commands and local alerts...")
    app.run_polling()




"""

funcion a implementar en los modulos de toma de decision o de calculo de probabilidad
de peligros varios para avisar al bot y que ese notifique a los usuarios.

import requests
import logging

logger = logging.getLogger("DecisionSystem")

def evaluate_vision_and_alert(self, label: str, probability: float, threshold: float = 0.75):

    # Evaluates the image model prediction and triggers a local alert to the Telegram bot
    # if a concerning label exceeds the probability threshold.

    # Define which labels indicate a health problem (adjust based on your CV model)
    alert_labels = ["Mildew", "Leaf_Spot", "Pest_Damage", "Dehydrated"]
    
    if label in alert_labels and probability >= threshold:
        try:
            # Send the POST request to the Telegram bot's local webhook (port 8080)
            payload = {"label": label, "probabilidad": probability}
            response = requests.post("http://localhost:8080/alert", json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"Alert sent to Telegram bot for anomaly: {label}")
            else:
                logger.warning(f"Telegram webhook rejected the alert. Status: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to connect to the Telegram local webhook: {e}")

"""
