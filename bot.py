# bot.py
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

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = int(os.environ['ADMIN_ID'])
GROUP_ID = -1003069423158

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("VisionCourseSupport")
    assign_ws = sheet.worksheet("Assignments")
    wins_ws = sheet.worksheet("Wins")
except Exception as e:
    logger.error(f"Error initializing Google Sheets: {e}")

# Encouragements
encouragements = ["Crushing it! 🚀", "You're on fire! 🌟", "Keep it up! 🎉", "Amazing work! 💪"]

# Keyboard
def get_keyboard(is_admin=False):
    keyboard = [
        [KeyboardButton("Submit Assignment 📝"), KeyboardButton("Share Small Win 🎉")],
        [KeyboardButton("Check Status 📊")],
    ]
    if is_admin:
        keyboard.append([KeyboardButton("Grade (Admin) 🖊️")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# /start and /menu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    is_admin = update.effective_user.id == ADMIN_ID
    markup = get_keyboard(is_admin)
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=markup)

# /remove
async def remove_keyboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Keyboard removed.", reply_markup=ReplyKeyboardRemove())

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# Assignment Conversation
MODULE, CONTENT = range(2)

async def start_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Enter module number (4, 7, 10):")
    return MODULE

async def get_module(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    module = update.message.text.strip()
    if module not in ['4', '7', '10']:
        await update.message.reply_text("Invalid module. Only 4, 7, 10 allowed. Try again.")
        return MODULE
    context.user_data['module'] = module
    await update.message.reply_text("Send your submission (text, photo, or video):")
    return CONTENT

async def get_assignment_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    username = user.username or f"user{user.id}"
    userid = user.id
    module = context.user_data['module']
    try:
        if update.message.photo:
            photo_id = update.message.photo[-1].file_id
            caption = f"Module {module} submission by @{username}"
            if update.message.caption:
                caption += f"\n{update.message.caption}"
            sent_msg = await context.bot.send_photo(chat_id=GROUP_ID, photo=photo_id, caption=caption)
        elif update.message.video:
            video_id = update.message.video.file_id
            caption = f"Module {module} submission by @{username}"
            if update.message.caption:
                caption += f"\n{update.message.caption}"
            sent_msg = await context.bot.send_video(chat_id=GROUP_ID, video=video_id, caption=caption)
        elif update.message.text:
            text = update.message.text
            sent_msg = await context.bot.send_message(chat_id=GROUP_ID, text=f"Module {module} submission by @{username}:\n{text}")
        else:
            await update.message.reply_text("Unsupported content type. Please send text, photo, or video.")
            return CONTENT

        msg_id = sent_msg.message_id
        content = f"telegram:{GROUP_ID}:{msg_id}"
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        assign_ws.append_row([str(userid), username, module, date, content, "pending", ""])
        enc = random.choice(encouragements)
        await update.message.reply_text(f"Submission received! {enc}")
    except Exception as e:
        logger.error(f"Error in assignment submission: {e}")
        await update.message.reply_text("An error occurred during submission. Please try again.")
    return ConversationHandler.END

# Win Conversation
WIN_TYPE, WIN_CONTENT = range(2)

async def start_win(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Is this a small win or major win/testimonial? Reply with 'small' or 'major'.")
    return WIN_TYPE

async def get_win_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    win_type = update.message.text.strip().lower()
    if win_type not in ['small', 'major']:
        await update.message.reply_text("Invalid type. Please reply with 'small' or 'major'.")
        return WIN_TYPE
    context.user_data['win_type'] = win_type
    await update.message.reply_text("Send your win (text, photo, or video):")
    return WIN_CONTENT

async def get_win_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    username = user.username or f"user{user.id}"
    userid = user.id
    win_type = context.user_data['win_type'].capitalize()
    try:
        if update.message.photo:
            photo_id = update.message.photo[-1].file_id
            caption = f"{win_type} win by @{username}"
            if update.message.caption:
                caption += f"\n{update.message.caption}"
            sent_msg = await context.bot.send_photo(chat_id=GROUP_ID, photo=photo_id, caption=caption)
        elif update.message.video:
            video_id = update.message.video.file_id
            caption = f"{win_type} win by @{username}"
            if update.message.caption:
                caption += f"\n{update.message.caption}"
            sent_msg = await context.bot.send_video(chat_id=GROUP_ID, video=video_id, caption=caption)
        elif update.message.text:
            text = update.message.text
            sent_msg = await context.bot.send_message(chat_id=GROUP_ID, text=f"{win_type} win by @{username}:\n{text}")
        else:
            await update.message.reply_text("Unsupported content type. Please send text, photo, or video.")
            return WIN_CONTENT

        msg_id = sent_msg.message_id
        content = f"telegram:{GROUP_ID}:{msg_id}"
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        wins_ws.append_row([str(userid), username, win_type.lower(), date, content])
        enc = random.choice(encouragements)
        await update.message.reply_text(f"Win shared! {enc}")
    except Exception as e:
        logger.error(f"Error in win submission: {e}")
        await update.message.reply_text("An error occurred during submission. Please try again.")
    return ConversationHandler.END

# Check Status
async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    userid = str(update.effective_user.id)
    try:
        assign_rows = assign_ws.get_all_values()[1:]  # Skip header
        wins_rows = wins_ws.get_all_values()[1:]
        user_assigns = [row for row in assign_rows if row[0] == userid]
        user_wins = [row for row in wins_rows if row[0] == userid]
        if not user_assigns and not user_wins:
            await update.message.reply_text("You have no submissions yet.")
            return
        msg = "Your status:\n\nAssignments:\n"
        for row in user_assigns:
            module, date, status, notes = row[2], row[3], row[5], row[6]
            msg += f"Module {module} ({date}): {status} {notes}\n"
        msg += "\nWins:\n"
        for row in user_wins:
            win_type, date = row[2].capitalize(), row[3]
            msg += f"{win_type} win ({date})\n"
        await update.message.reply_text(msg)
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        await update.message.reply_text("An error occurred while checking status.")

# Grade Conversation
G_USERNAME, G_MODULE, G_STATUS, G_NOTES = range(4)

async def start_grade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("This feature is admin-only.")
        return ConversationHandler.END
    await update.message.reply_text("Enter username (without @):")
    return G_USERNAME

async def get_g_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['g_username'] = update.message.text.strip()
    await update.message.reply_text("Enter module number:")
    return G_MODULE

async def get_g_module(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['g_module'] = update.message.text.strip()
    username = context.user_data['g_username']
    module = context.user_data['g_module']
    try:
        rows = assign_ws.get_all_values()
        for idx, row in enumerate(rows[1:], start=2):
            if row[1] == username and row[2] == module:
                context.user_data['g_row'] = idx
                content = row[4]
                if content.startswith('telegram:'):
                    _, g_id, m_id = content.split(':')
                    await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=int(g_id), message_id=int(m_id))
                else:
                    await update.message.reply_text(f"Content: {content}")
                await update.message.reply_text("Set status (approved/rejected/pending):")
                return G_STATUS
        await update.message.reply_text("No submission found for this user and module.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in grading: {e}")
        await update.message.reply_text("An error occurred.")
        return ConversationHandler.END

async def get_g_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    status = update.message.text.strip().lower()
    if status not in ['approved', 'rejected', 'pending']:
        await update.message.reply_text("Invalid status. Use approved, rejected, or pending.")
        return G_STATUS
    context.user_data['g_status'] = status
    await update.message.reply_text("Enter notes (or 'none' for no notes):")
    return G_NOTES

async def get_g_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    notes = update.message.text.strip()
    if notes.lower() == 'none':
        notes = ''
    row = context.user_data['g_row']
    try:
        assign_ws.update_cell(row, 6, context.user_data['g_status'])
        assign_ws.update_cell(row, 7, notes)
        await update.message.reply_text("Submission graded successfully!")
    except Exception as e:
        logger.error(f"Error updating grade: {e}")
        await update.message.reply_text("An error occurred while updating the grade.")
    return ConversationHandler.END

# /getmedia
async def get_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /getmedia @username <module>")
        return
    username = args[0].lstrip('@')
    module = args[1]
    try:
        rows = assign_ws.get_all_values()
        for row in rows[1:]:
            if row[1] == username and row[2] == module:
                content = row[4]
                if content.startswith('telegram:'):
                    _, g_id, m_id = content.split(':')
                    await context.bot.forward_message(chat_id=update.effective_chat.id, from_chat_id=int(g_id), message_id=int(m_id))
                    return
        await update.message.reply_text("No media found for this submission.")
    except Exception as e:
        logger.error(f"Error in getmedia: {e}")
        await update.message.reply_text("An error occurred.")

# Daily Reminder
async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(chat_id=GROUP_ID, text="Daily reminder: Submit or share a win! 🚀")

def run_schedule():
    def job():
        application.job_queue.run_once(send_daily_reminder, when=0)
    schedule.every().day.at("08:00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Main
if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('menu', start))
    application.add_handler(CommandHandler('remove', remove_keyboard))
    application.add_handler(CommandHandler('getmedia', get_media))

    assign_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^Submit Assignment 📝$'), start_assignment)],
        states={
            MODULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_module)],
            CONTENT: [MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, get_assignment_content)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(assign_conv)

    win_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^Share Small Win 🎉$'), start_win)],
        states={
            WIN_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_win_type)],
            WIN_CONTENT: [MessageHandler(filters.TEXT | filters.PHOTO | filters.VIDEO, get_win_content)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(win_conv)

    grade_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(r'^Grade \(Admin\) 🖊️$'), start_grade)],
        states={
            G_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_g_username)],
            G_MODULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_g_module)],
            G_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_g_status)],
            G_NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_g_notes)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    application.add_handler(grade_conv)

    status_handler = MessageHandler(filters.Regex(r'^Check Status 📊$'), check_status)
    application.add_handler(status_handler)

    # Keep-alive
    from keep_alive import run as keep_alive_run
    Thread(target=keep_alive_run).start()

    # Scheduler
    Thread(target=run_schedule).start()

    # Run bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)