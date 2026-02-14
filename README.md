# Extergram — Asynchronous Telegram Bot Framework

*Disclaimer: This project is an independent open-source library and is not affiliated with, associated with, authorized by, endorsed by, or in any way officially connected with Telegram FZ-LLC or any of its subsidiaries or its affiliates.*

**Extergram** is a modern, simple, and fully asynchronous library for creating Telegram bots in Python using `httpx`.

**Current Version:** 0.8.0

---

## 🚀 Installation

Extergram requires **Python 3.8+**.

```bash
pip install extergram
```

---

## ⚡ Quick Start

The following example demonstrates the updated "New Style" handler pattern using `ContextTypes`.

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler, MessageHandler

async def start(context: ContextTypes):
    await context.bot.send_message(
        chat_id=context.message.chat.id, 
        text="Hello! I am an Extergram bot."
    )

async def echo(context: ContextTypes):
    await context.bot.send_message(
        chat_id=context.message.chat.id, 
        text=f"You said: {context.message.text}"
    )

async def main():
    # Initialize the bot with your token
    bot = Bot(token="YOUR_BOT_TOKEN")

    # Register handlers
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(echo))

    # Start polling    
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧠 Finite State Machine (FSM)

Extergram v0.8.0 includes a built-in FSM using `MemoryFSMStorage`. You can manage user states and data directly through the handler context.

### Using States
```python
from extergram.ext import StateHandler, MessageHandler

# Define a state-based handler
async def process_name(context: ContextTypes):
    name = context.message.text
    await context.state.update_data(name=name)
    await context.state.set_state("waiting_for_age")
    await context.bot.send_message(context.message.chat.id, f"Nice to meet you, {name}! How old are you?")

# Registering a state handler
bot.add_handler(StateHandler("waiting_for_name", MessageHandler(process_name)))
```

### Context FSM Methods:
- `await context.state.set_state(state: str)`: Set the current state.
- `await context.state.get_state()`: Retrieve the current state.
- `await context.state.update_data(**kwargs)`: Update stored data.
- `await context.state.get_data()`: Get all data for the current user/chat.
- `await context.state.clear()`: Reset state and data.

---

## ⌨️ User Interface (Inline Keyboards)

The `ButtonsDesign` class allows for easy creation of inline keyboards.

```python
from extergram.ui import ButtonsDesign

ui = ButtonsDesign()
# Add a row with a callback button and a URL button
ui.add_row(
    ButtonsDesign.create_button("Click Me", "callback_data_1"),
    ButtonsDesign.create_url_button("Open Google", "https://google.com")
)
await bot.send_message(chat_id, "Choose an option:", reply_markup=ui)
```

---

## 📝 Markdown Utility

The `Markdown` class provides automatic escaping for Telegram's **MarkdownV2**.

```python
from extergram.utils import Markdown

text = (
    Markdown("Hello ")
    .bold("World")
    .italic(" this is safely escaped!")
)

# Resulting string is automatically escaped for MarkdownV2
await bot.send_message(chat_id, str(text), parse_mode="MarkdownV2")
```

---

## 🛠 Bot Methods (API Reference)

The `Bot` class supports a wide range of Telegram API methods:

| Method | Description |
| :--- | :--- |
| `send_message` | Sends a text message. Supports `ButtonsDesign`. |
| `send_photo` | Sends a photo (URL or local path). |
| `send_document` | Sends a document/file. |
| `send_video` | Sends a video file. |
| `send_voice` | Sends a voice note (.ogg). |
| `send_video_note` | Sends a rounded video note. |
| `edit_message_text`| Edits the text of an existing message. |
| `delete_message` | Deletes a message. |
| `answer_callback_query`| Responds to an inline button click. |
| `set_my_commands` | Sets the bot's command list in the menu. |

### Administration Methods:
- `ban_chat_member`
- `unban_chat_member`
- `restrict_chat_member` (using `ChatPermissions` class)
- `promote_chat_member`
- `approve_chat_join_request`
- `decline_chat_join_request`

---
## 🛡 Anti-Flood System
Extergram features an internal **anti-flood system** that dynamically adjusts request delays if it detects high frequency to avoid hitting Telegram API limits.

## 🚦 Error Handling
The library includes custom exceptions for specific API errors:
- `errors.BadRequestError` (400)
- `errors.UnauthorizedError` (401)
- `errors.ForbiddenError` (403)
- `errors.ConflictError` (409) - *Triggered if multiple instances of the bot are running.*
- `errors.TelegramAdminError` - *Triggered if the bot lacks required permissions.*