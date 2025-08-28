import logging
import random
import os
import time
import schedule
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from threading import Thread
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Sheets setup
try:
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', scope)
    client = gspread.authorize(creds)
    assignment_sheet = client.open("VisionCourseSupport").worksheet(
        "Assignments")
    wins_sheet = client.open("VisionCourseSupport").worksheet("Wins")
    logger.info("Connected to Google Sheets successfully")
except Exception as e:
    logger.error(f"Failed to connect to Google Sheets: {e}")
    raise

# Configuration
TOKEN = "8138720265:AAGvACO_aPmvcJDpY3ugyM3AV1cmZUJ4RTU"
ADMIN_ID = os.environ.get('ADMIN_ID', '7109534825')
GROUP_CHAT_ID = " -1003036481382"
VALID_MODULES = [4, 7, 10]
ENCOURAGEMENTS = [
    "Crushing it! 🚀", "Shining bright! 🌟", "On fire! 🔥", "Next-level! 💪"
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username or str(
        update.message.from_user.id)
    keyboard = [["Submit Assignment 📝", "Share Small Win 🎉"],
                ["Check Status 📊", "Grade (Admin) 🖊️"]]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard=True,
                                       one_time_keyboard=False)
    await update.message.reply_text(
        f"@{user}, welcome! Use the buttons below! 🚀",
        reply_markup=reply_markup)
    logger.info(
        f"Start command executed for @{user} (ID {update.message.from_user.id})"
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username or str(
        update.message.from_user.id)
    keyboard = [["Submit Assignment 📝", "Share Small Win 🎉"],
                ["Check Status 📊", "Grade (Admin) 🖊️"]]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       resize_keyboard=True,
                                       one_time_keyboard=False)
    await update.message.reply_text(f"@{user}, choose an option! 🚀",
                                    reply_markup=reply_markup)
    logger.info(
        f"Menu command executed for @{user} (ID {update.message.from_user.id})"
    )


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username or str(
        update.message.from_user.id)
    await update.message.reply_text(
        f"@{user}, keyboard removed! Use /menu to bring it back. 😄",
        reply_markup=ReplyKeyboardRemove())
    logger.info(
        f"Remove command executed for @{user} (ID {update.message.from_user.id})"
    )


import os
import logging
import random
from datetime import datetime
from threading import Thread
import schedule
import time
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import gspread
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = int(os.environ['ADMIN_ID'])
GROUP_ID = -1003069423158
VALID_MODULES = [4, 7, 10]
ENCOURAGING_RESPONSES = ["Crushing it! 🚀", "Great job! 🌟", "Keep it up! 💪"]

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open("VisionCourseSupport")
assign_ws = sheet.worksheet("Assignments")
wins_ws = sheet.worksheet("Wins")

def get_keyboard():
    keyboard = [
        [KeyboardButton("Submit Assignment 📝"), KeyboardButton("Share Small Win 🎉")],
        [KeyboardButton("Check Status 📊")]
    ]
    if ADMIN_ID:
        keyboard.append([KeyboardButton("Grade (Admin) 🖊️")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Checking status for user: {user_id}")
    try:
        assignments = assign_ws.get_all_values()[1:]  # Skip header
        wins = wins_ws.get_all_values()[1:]
        user_assignments = [row for row in assignments if row[0] == str(user_id)]
        user_wins = [row for row in wins if row[0] == str(user_id)]
        if not user_assignments and not user_wins:
            await update.message.reply_text("No submissions yet.")
            return
        response = "Your submissions:\n"
        for row in user_assignments:
            response += f"Module {row[2]} ({row[3]}): {row[5]}\n"
        for row in user_wins:
            response += f"Win {row[2]} ({row[3]}): {row[4]}\n"
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error in check_status: {e}")
        await update.message.reply_text("Error retrieving status. Please try again.")

async def handle_submission(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user.username or str(
        update.message.from_user.id)
    content_type = "Text" if update.message.text else "Video" if update.message.video else "Photo" if update.message.photo else "Link"
    content = update.message.text or f"Media/Link (ID: {update.message.message_id})"
    encouragement = random.choice(ENCOURAGEMENTS)
    mode = context.user_data.get('mode', '')

    if update.message.chat.type == 'private':
        if mode == 'assignment':
            module = context.user_data.get('module', 'Unknown')
            status = "Submitted"
            grade = "Auto-Graded: 8/10" if content_type == "Video" else "Auto-Graded: 6/10"
            try:
                if content_type in ["Video", "Photo"]:
                    file_id = update.message.video.file_id if content_type == "Video" else update.message.photo[
                        -1].file_id
                    sent_message = await context.bot.send_message(
                        GROUP_CHAT_ID,
                        f"{content_type} from @{user} for Module {module}")
                    message_id = sent_message.message_id
                    content = f"telegram:{GROUP_CHAT_ID}:{message_id}"
                    if content_type == "Video":
                        await context.bot.send_video(
                            GROUP_CHAT_ID,
                            video=file_id,
                            caption=f"Module {module} by @{user}")
                    else:
                        await context.bot.send_photo(
                            GROUP_CHAT_ID,
                            photo=file_id,
                            caption=f"Module {module} by @{user}")
                assignment_sheet.append_row([
                    user, module, status, content_type, content, grade,
                    time.strftime('%Y-%m-%d %H:%M:%S')
                ])
                logger.info(f"Assignment saved for @{user} in Module {module}")
                await update.message.reply_text(
                    f"@{user}, Module {module} {content_type.lower()} submitted! {grade} {encouragement} 🎉"
                )
            except Exception as e:
                logger.error(f"Assignment error for @{user}: {e}")
                await update.message.reply_text(
                    f"@{user}, submission failed. Try again! 😓")
            finally:
                context.user_data.pop('mode', None)
                context.user_data.pop('module', None)
        elif mode == 'small_win':
            try:
                if content_type in ["Video", "Photo"]:
                    file_id = update.message.video.file_id if content_type == "Video" else update.message.photo[
                        -1].file_id
                    sent_message = await context.bot.send_message(
                        GROUP_CHAT_ID, f"Small win from @{user}")
                    message_id = sent_message.message_id
                    content = f"telegram:{GROUP_CHAT_ID}:{message_id}"
                    if content_type == "Video":
                        await context.bot.send_video(
                            GROUP_CHAT_ID,
                            video=file_id,
                            caption=f"Small win by @{user}")
                    else:
                        await context.bot.send_photo(
                            GROUP_CHAT_ID,
                            photo=file_id,
                            caption=f"Small win by @{user}")
                wins_sheet.append_row([
                    user, "Small " + content_type, content,
                    time.strftime('%Y-%m-%d %H:%M:%S')
                ])
                logger.info(f"Small win saved for @{user}")
                await update.message.reply_text(
                    f"@{user}, small win shared! {encouragement} 😄")
            except Exception as e:
                logger.error(f"Small win error for @{user}: {e}")
                await update.message.reply_text(
                    f"@{user}, error sharing win. Try again! 😓")
            finally:
                context.user_data.pop('mode', None)
    elif update.message.chat.type in ['group', 'supergroup']:
        if update.message.text and any(
                keyword in update.message.text.lower()
                for keyword in ["major win", "testimonial"]):
            try:
                if content_type in ["Video", "Photo"]:
                    file_id = update.message.video.file_id if content_type == "Video" else update.message.photo[
                        -1].file_id
                    sent_message = await context.bot.send_message(
                        GROUP_CHAT_ID, f"Major win/testimonial from @{user}")
                    message_id = sent_message.message_id
                    content = f"telegram:{GROUP_CHAT_ID}:{message_id}"
                    if content_type == "Video":
                        await context.bot.send_video(
                            GROUP_CHAT_ID,
                            video=file_id,
                            caption=f"Major win by @{user}")
                    else:
                        await context.bot.send_photo(
                            GROUP_CHAT_ID,
                            photo=file_id,
                            caption=f"Major win by @{user}")
                wins_sheet.append_row([
                    user, "Major " + content_type, content,
                    time.strftime('%Y-%m-%d %H:%M:%S')
                ])
                logger.info(f"Major win saved for @{user}")
                await update.message.reply_text(
                    f"@{user}, amazing Major Win/Testimonial! 🎉 {encouragement} 👍🎈"
                )
            except Exception as e:
                logger.error(f"Major win error for @{user}: {e}")
                await update.message.reply_text(
                    f"@{user}, error saving. Try again! 😓")


async def getmedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    logger.info(f"Processing /getmedia: {context.args}")
    try:
        if len(context.args) != 2:
            await update.message.reply_text("Usage: /getmedia @username module_number")
            return
        username, module = context.args
        username = username.lstrip('@')
        assignments = assign_ws.get_all_values()[1:]
        for row in assignments:
            if row[1] == username and row[2] == module:
                content = row[4]
                if content.startswith("telegram:"):
                    _, chat_id, message_id = content.split(":")
                    await context.bot.forward_message(
                        chat_id=update.effective_chat.id,
                        from_chat_id=int(chat_id),
                        message_id=int(message_id)
                    )
                    logger.info(f"Forwarded media for {username}, module {module}")
                    return
        await update.message.reply_text("No media found for this user and module.")
    except Exception as e:
        logger.error(f"Error in getmedia: {e}")
        await update.message.reply_text("Error retrieving media. Please try again.")


def run_scheduler(application):

    def job():
        logger.info("Sending daily reminder")
        application.bot.send_message(
            GROUP_CHAT_ID, "Daily reminder: Submit your assignment or share a win! 🚀")

    schedule.every().day.at("08:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    logger.info("Starting Telegram bot application")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("remove", remove))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(
        MessageHandler(filters.PHOTO | filters.VIDEO | filters.TEXT,
                       handle_submission))
    application.add_handler(CommandHandler("getmedia", get_media))
    keep_alive_thread = Thread(target=keep_alive_run)
    keep_alive_thread.start()
    logger.info("Keep-alive thread started")
    scheduler_thread = Thread(target=run_scheduler, args=(application, ))
    scheduler_thread.start()
    logger.info("Scheduler thread started")
    application.run_polling()
    logger.info("Polling started")

from keep_alive import run as keep_alive_run

if __name__ == '__main__':
    main()

def main():
    application = Application.builder().token(TOKEN).build()

    # ... (handler setup) ...

    # Keep-alive
    from keep_alive import run as keep_alive_run
    keep_alive_thread = Thread(target=keep_alive_run)
    keep_alive_thread.start()

    # Scheduler
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)