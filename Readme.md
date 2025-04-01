# Task Master Bot

A Telegram bot for managing your tasks and reminders.

## Features

- 📝 Add tasks to your personal task list
- 📋 View all your current tasks
- 🗑️ Delete tasks with interactive buttons
- ⏰ Set reminders with flexible time formats

## Commands

- `/start` - Get started with Task Master
- `/addtask` - Add a new task to your list
- `/tasks` - View all your current tasks
- `/deletetask` - Delete a task from your list
- `/remindme` - Set a reminder for a task

## Time Formats for Reminders

- `30m` - 30 minutes
- `2h` - 2 hours
- `tomorrow` - Next day

## Setup

1. Clone this repository
2. Create a `.env` file with your bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_token_here
   ```
3. Install dependencies:
   ```
   pip install python-telegram-bot python-dotenv
   ```
4. Run the bot:
   ```
   python main.py
   ```

## Example Usage

```
/addtask Buy groceries
/remindme 2h Buy groceries
/tasks
/deletetask 1
```