import datetime
import os
import re
from datetime import timedelta

from dotenv import load_dotenv
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def setup_commands(application: Application) -> None:
    """Set up the bot commands in the Telegram UI."""
    commands = [
        BotCommand("start", "Get started with Task Master"),
        BotCommand("addtask", "Add a new task to your list"),
        BotCommand("tasks", "View all your current tasks"),
        BotCommand("deletetask", "Delete a task from your list"),
        BotCommand("remindme", "Set a reminder for a task"),
    ]
    await application.bot.set_my_commands(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message to the user."""
    welcome_text = (
        "👋 *Welcome to Task Master!*\n\n"
        "I can help you manage your tasks and reminders:\n"
        "📝 /addtask - Add a new task\n"
        "📋 /tasks - See your task list\n"
        "🗑️ /deletetask - Delete a task\n"
        "⏰ /remindme - Set a reminder"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adds a task to the user's task list."""
    task = " ".join(context.args) if context.args else ""
    if not task:
        await update.message.reply_text(
            "⚠️ Please provide a task description.\nExample: /addtask Buy groceries"
        )
        return

    user_data = context.user_data
    if "tasks" not in user_data:
        user_data["tasks"] = []

    user_data["tasks"].append(task)
    await update.message.reply_text(f"✅ Task added: *{task}*", parse_mode="Markdown")


async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the user's task list."""
    user_data = context.user_data
    if "tasks" not in user_data or not user_data["tasks"]:
        await update.message.reply_text("📭 Your task list is empty.")
        return

    task_list = "\n".join(
        [f"{i+1}. {task}" for i, task in enumerate(user_data["tasks"])]
    )
    await update.message.reply_text(
        f"📋 *Your Tasks:*\n\n{task_list}", parse_mode="Markdown"
    )


async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deletes a task from the user's task list."""
    user_data = context.user_data

    # Check if user has any tasks
    if "tasks" not in user_data or not user_data["tasks"]:
        await update.message.reply_text("📭 You don't have any tasks to delete.")
        return

    # If task number is provided as an argument
    if context.args:
        try:
            task_num = int(context.args[0]) - 1
            if 0 <= task_num < len(user_data["tasks"]):
                deleted_task = user_data["tasks"].pop(task_num)
                await update.message.reply_text(
                    f"🗑️ Deleted task: *{deleted_task}*", parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    "⚠️ Invalid task number. Use /tasks to see your task list."
                )
        except ValueError:
            await update.message.reply_text(
                "⚠️ Please provide a valid task number.\nExample: /deletetask 2"
            )
        return

    # If no arguments, show interactive buttons to select a task
    keyboard = []
    for i, task in enumerate(user_data["tasks"]):
        # Limit task preview length for button display
        task_preview = task[:20] + "..." if len(task) > 20 else task
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{i+1}. {task_preview}", callback_data=f"delete_{i}"
                )
            ]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🗑️ Select a task to delete:", reply_markup=reply_markup
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses for task deletion."""
    query = update.callback_query
    await query.answer()

    # Extract task index from callback data
    if query.data.startswith("delete_"):
        task_index = int(query.data.split("_")[1])
        user_data = context.user_data

        if "tasks" in user_data and 0 <= task_index < len(user_data["tasks"]):
            deleted_task = user_data["tasks"].pop(task_index)
            await query.edit_message_text(
                f"✅ Deleted task: *{deleted_task}*", parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("⚠️ Error: Task not found or already deleted.")


async def send_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the reminder when the time comes."""
    job_data = context.job.data
    await context.bot.send_message(
        chat_id=job_data["chat_id"],
        text=f"⏰ *REMINDER*: {job_data['text']}",
        parse_mode="Markdown",
    )

    # Remove completed reminder from user data
    user_data = context.application.user_data.get(job_data["user_id"], {})
    if "reminders" in user_data:
        # Find and remove the reminder (only the first match)
        for i, reminder in enumerate(user_data["reminders"]):
            if reminder["reminder_text"] == job_data["text"]:
                user_data["reminders"].pop(i)
                break


async def remind_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets a reminder for a task."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Please provide a time and reminder text.\n"
            "Examples:\n"
            "• /remindme 30m Buy groceries\n"
            "• /remindme 2h Call mom\n"
            "• /remindme tomorrow Submit report"
        )
        return

    time_arg = context.args[0].lower()
    reminder_text = " ".join(context.args[1:])

    now = datetime.datetime.now()
    reminder_time = None

    if re.match(r"^\d+m$", time_arg):  # Format: 30m (30 minutes)
        minutes = int(time_arg[:-1])
        reminder_time = now + timedelta(minutes=minutes)
    elif re.match(r"^\d+h$", time_arg):  # Format: 2h (2 hours)
        hours = int(time_arg[:-1])
        reminder_time = now + timedelta(hours=hours)
    elif time_arg == "tomorrow":
        reminder_time = now + timedelta(days=1)
    else:
        await update.message.reply_text(
            "⚠️ Invalid time format. Please use:\n"
            "• 30m (30 minutes)\n"
            "• 2h (2 hours)\n"
            "• tomorrow"
        )
        return

    seconds_until_reminder = (reminder_time - now).total_seconds()
    formatted_time = reminder_time.strftime("%H:%M:%S on %Y-%m-%d")

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if "reminders" not in context.user_data:
        context.user_data["reminders"] = []

    reminder_info = {
        "chat_id": chat_id,
        "reminder_text": reminder_text,
        "reminder_time": reminder_time,
    }

    context.user_data["reminders"].append(reminder_info)

    await update.message.reply_text(
        f"⏰ Reminder set for *{formatted_time}*:\n" f"*{reminder_text}*",
        parse_mode="Markdown",
    )

    context.job_queue.run_once(
        send_reminder,
        seconds_until_reminder,
        {"chat_id": chat_id, "text": reminder_text, "user_id": user_id},
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles unknown commands."""
    await update.message.reply_text(
        "❓ Sorry, I didn't understand that command.\nTry /start to see available commands."
    )


def main() -> None:
    """Starts the bot."""
    application = Application.builder().token(TOKEN).build()

    application.post_init = setup_commands

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addtask", add_task))
    application.add_handler(CommandHandler("tasks", show_tasks))
    application.add_handler(CommandHandler("deletetask", delete_task))
    application.add_handler(CommandHandler("remindme", remind_me))

    # Add callback query handler for button presses
    application.add_handler(CallbackQueryHandler(button_callback))

    # Add fallback for unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Start the bot
    print("🤖 Task Master Bot is starting...")
    application.run_polling()


if __name__ == "__main__":
    main()
