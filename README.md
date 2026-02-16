# Extergram — Asynchronous Telegram Bot Framework

*Disclaimer: This project is an independent open-source library and is not affiliated with, associated with, authorized by, endorsed by, or in any way officially connected with Telegram FZ-LLC or any of its subsidiaries or its affiliates.*

**Extergram** is a modern, simple, and fully asynchronous library for creating Telegram bots in Python using `httpx`. It provides a clean API, built-in FSM (Finite State Machine), anti-flood protection, and a variety of handlers for messages, commands, and callbacks.

**Current Version:** 0.8.1

---

## 🚀 Installation

Extergram requires **Python 3.8+**.

```bash
pip install extergram
```

---

## ⚡ Quick Start

A minimal echo bot:

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
    bot = Bot(token="YOUR_BOT_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(echo))
    await bot.polling()

if __name__ == "__main__":
    asyncio.run(main())
```
---

## 📚 API Reference

### Core Concepts

- **Bot** – the main class that interacts with Telegram API.
- **ContextTypes** – passed to handlers, provides access to bot, update, and FSM.
- **Handlers** – define how to process updates (messages, commands, callbacks). Handlers are checked sequentially; the first matching handler is executed.
- **FSM** – built-in finite state machine for multi-step dialogs.

---

### 1. Bot Class

#### Constructor
```python
Bot(token: str, default_parse_mode: str = None)
```
- `token` – your bot token from BotFather.
- `default_parse_mode` – default parse mode for messages (`"HTML"` or `"MarkdownV2"`). If not set, parse mode must be specified explicitly in each call.

#### Methods

##### `async polling(timeout: int = 30)`
Starts long polling. This coroutine runs forever until interrupted.

##### `add_handler(handler: BaseHandler)`
Registers a handler. Must be an instance of `BaseHandler`.

##### `async get_updates(offset: int = None, timeout: int = 30) -> List[dict]`
Fetches updates from Telegram. Normally you don't need to call this directly.

##### Sending Messages
```python
async send_message(
    chat_id: int,
    text: str,
    parse_mode: str = None,
    disable_web_page_preview: bool = None,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    reply_markup = None
) -> dict
```
- `reply_markup` can be a `ButtonsDesign` instance or a dict.

##### Editing Messages
```pythonasync edit_message_text(
    chat_id: int,
    message_id: int,
    text: str,
    parse_mode: str = None,
    reply_markup = None
) -> dict
```

##### Deleting Messages
```python
async delete_message(chat_id: int, message_id: int) -> dict
```

##### Answering Callback Queries
```python
async answer_callback_query(
    callback_query_id: str,
    text: str = None,
    show_alert: bool = False,
    url: str = None,
    cache_time: int = None
) -> dict
```

##### Sending Media
All media methods accept a file path (local) or URL. Local files are read into memory and sent as multipart/form-data.

- `send_photo(chat_id, photo, caption=None, parse_mode=None, reply_markup=None)`
- `send_document(chat_id, document, caption=None, parse_mode=None, reply_markup=None)`
- `send_video(chat_id, video, caption=None, parse_mode=None, reply_markup=None)`
- `send_voice(chat_id, voice, caption=None, parse_mode=None, reply_markup=None)`
- `send_video_note(chat_id, video_note, reply_markup=None)`
- `send_animation(chat_id, animation, caption=None, parse_mode=None, reply_markup=None)`

##### Editing Reply Markup
```python
async edit_message_reply_markup(chat_id: int, message_id: int, reply_markup=None) -> dict
```

##### Setting Bot Commands
```python
async set_my_commands(commands: List[BotCommand]) -> dict
```
`BotCommand` is a simple class with `command` and `description` attributes.

##### Administration Methods
- `ban_chat_member(chat_id, user_id, until_date=None, revoke_messages=None)`
- `unban_chat_member(chat_id, user_id, only_if_banned=None)`
- `restrict_chat_member(chat_id, user_id, permissions: ChatPermissions, until_date=None)`- `promote_chat_member(chat_id, user_id, **permissions)`
- `approve_chat_join_request(chat_id, user_id)`
- `decline_chat_join_request(chat_id, user_id)`

`ChatPermissions` is a class that allows setting specific permissions (see below).

##### Anti-Flood
The bot automatically manages request delays to avoid hitting Telegram limits. No configuration needed.

---

### 2. ContextTypes

Passed to handlers (new style). Provides:

- `bot` – the Bot instance.
- `update` – the raw Update object.
- `message` – the Message object (if present).
- `callback_query` – the CallbackQuery object (if present).
- `effective_user` – the user who triggered the update.
- `effective_chat` – the chat where the update occurred.
- `state` – an `FSMContext` instance for the current user/chat.

---

### 3. Data Classes

These classes mirror Telegram API objects. They are created automatically from incoming updates.

- **User**: `id`, `is_bot`, `first_name`, `last_name`, `username`
- **Chat**: `id`, `type`, `title`, `username`
- **Message**: `message_id`, `from_user`, `chat`, `date`, `text`, `caption`
- **CallbackQuery**: `id`, `from_user`, `message`, `data`
- **Update**: `update_id`, `message`, `edited_message`, `callback_query`
- **BotCommand**: simple container for commands.
- **ChatPermissions**: used with `restrict_chat_member`. All permissions default to `None` (meaning "don't change"). Use `True` to allow, `False` to disallow.

Example:
```python
perms = ChatPermissions(can_send_messages=False, can_send_media_messages=False)
```

---

### 4. UI: ButtonsDesign

Build inline keyboards.

```python
from extergram.ui import ButtonsDesign
kb = ButtonsDesign()
kb.add_row(
    ButtonsDesign.create_button("Click me", "callback_data"),
    ButtonsDesign.create_url_button("GitHub", "https://github.com")
)
# Use in send_message: reply_markup=kb
```

- `create_button(text, callback_data)`
- `create_url_button(text, url)`
- `add_row(*buttons)` – adds a row of buttons.
- `to_dict()` – returns the keyboard as a dict for the API.

---

### 5. Utilities

#### Markdown Helper

Safely builds MarkdownV2 strings with automatic escaping.

```python
from extergram.utils import Markdown

text = str(
    Markdown("Hello ")
    .bold("World")
    .text(" this is ")
    .italic("escaped")
)
await bot.send_message(chat_id, text, parse_mode="MarkdownV2")
```

Methods:
- `text(text)` – appends plain text (escaped).
- `bold(text)` – appends bold text.
- `italic(text)` – appends italic text.
- `__str__()` – returns the final string.

#### escape_markdown_v2(text)
Low-level function to escape MarkdownV2 special characters.

---

### 6. Documentation Access

```python
from extergram import Docs
print(Docs.get_docs())   # returns a link to GitHub README
Docs.print_docs()        # prints the link
```

---

### 7. Handlers (extergram.ext)

All handlers inherit from `BaseHandler` and must implement `check_update`. They are registered via `bot.add_handler()`.

- **BaseHandler** – abstract base class.
- **MessageHandler** – triggers on any text message.
- **CommandHandler(command, callback)** – triggers on a command (e.g., `/start`). Accepts a single command or a list.
- **CallbackQueryHandler** – triggers on any callback query.
- **StateHandler(state, handler)** – wraps another handler and only triggers if the user is in a specific FSM state. Must be used with `MemoryFSMStorage`.

Example:
```python
from extergram.ext import StateHandler, MessageHandler

bot.add_handler(StateHandler("waiting_for_name", MessageHandler(process_name)))
```

---

### 8. FSM (Finite State Machine)

Extergram provides a simple in-memory FSM.

#### Storage
- `MemoryFSMStorage` – default storage used by Bot.

#### FSMContext
Obtained via `context.state`. Methods:

- `async get_state() -> Optional[str]`
- `async set_state(state: Optional[str])`
- `async get_data() -> dict`
- `async set_data(data: dict)`
- `async update_data(**kwargs)`
- `async clear()`

---

### 9. Exceptions

All exceptions inherit from `extergram.errors.ExtergramError`.

- `APIError` – base for API errors.
- `NetworkError` – network-related issues.- `BadRequestError` (400)
- `UnauthorizedError` (401)
- `ForbiddenError` (403)
- `NotFoundError` (404)
- `ConflictError` (409) – another instance is running.
- `EntityTooLargeError` (413)
- `InternalServerError` (500)
- `BadGatewayError` (502)
- `TelegramAdminError` – insufficient rights for admin actions.

---

## 🧪 Examples

### Example 1: Echo Bot with Commands

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler, MessageHandler

async def start(context: ContextTypes):
    await context.bot.send_message(
        context.message.chat.id,
        "Welcome! Send me any text and I'll echo it."
    )

async def echo(context: ContextTypes):
    await context.bot.send_message(
        context.message.chat.id,
        f"Echo: {context.message.text}"
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(MessageHandler(echo))
    await bot.polling()

asyncio.run(main())
```

### Example 2: Inline Keyboard with Callback

```python
import asyncio
from extergram import Bot, ContextTypes, ButtonsDesign
from extergram.ext import CommandHandler, CallbackQueryHandler

async def start(context: ContextTypes):    kb = ButtonsDesign().add_row(
        ButtonsDesign.create_button("Green", "color_green"),
        ButtonsDesign.create_button("Red", "color_red")
    )
    await context.bot.send_message(
        context.message.chat.id,
        "Choose a color:",
        reply_markup=kb
    )

async def button_handler(context: ContextTypes):
    query = context.callback_query
    color = query.data.split('_')[1]
    await context.bot.answer_callback_query(query.id, text=f"You chose {color}")
    await context.bot.send_message(
        query.message.chat.id,
        f"Your favorite color is {color}!"
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CallbackQueryHandler(button_handler))
    await bot.polling()

asyncio.run(main())
```

### Example 3: FSM – Collecting User Info

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler, MessageHandler, StateHandler

async def start(context: ContextTypes):
    await context.state.set_state("waiting_for_name")
    await context.bot.send_message(
        context.message.chat.id,
        "What's your name?"
    )

async def process_name(context: ContextTypes):
    name = context.message.text
    await context.state.update_data(name=name)
    await context.state.set_state("waiting_for_age")
    await context.bot.send_message(
        context.message.chat.id,
        f"Nice to meet you, {name}! How old are you?"
    )
async def process_age(context: ContextTypes):
    try:
        age = int(context.message.text)
    except ValueError:
        await context.bot.send_message(
            context.message.chat.id,
            "Please enter a number."
        )
        return
    data = await context.state.get_data()
    name = data.get("name")
    await context.state.clear()
    await context.bot.send_message(
        context.message.chat.id,
        f"Thank you! You are {name}, {age} years old."
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(StateHandler("waiting_for_name", MessageHandler(process_name)))
    bot.add_handler(StateHandler("waiting_for_age", MessageHandler(process_age)))
    await bot.polling()

asyncio.run(main())
```

### Example 4: Sending Photo and Document

```python
import asyncio
from extergram import Bot, ContextTypes
from extergram.ext import CommandHandler

async def photo(context: ContextTypes):
    await context.bot.send_photo(
        context.message.chat.id,
        photo="https://picsum.photos/400/300",
        caption="Random photo"
    )

async def doc(context: ContextTypes):
    await context.bot.send_document(
        context.message.chat.id,
        document="/path/to/file.pdf",
        caption="My document"
    )

async def main():    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("photo", photo))
    bot.add_handler(CommandHandler("doc", doc))
    await bot.polling()

asyncio.run(main())
```

### Example 5: Admin Command – Kick User

```python
import asyncio
from extergram import Bot, ContextTypes, errors
from extergram.ext import CommandHandler

async def kick(context: ContextTypes):
    if not context.message.reply_to_message:
        await context.bot.send_message(
            context.message.chat.id,
            "Reply to a user's message to kick them."
        )
        return
    user_id = context.message.reply_to_message.from_user.id
    try:
        await context.bot.ban_chat_member(context.message.chat.id, user_id)
        await context.bot.send_message(
            context.message.chat.id,
            f"User {user_id} has been kicked."
        )
    except errors.TelegramAdminError as e:
        await context.bot.send_message(
            context.message.chat.id,
            f"Failed: {e}"
        )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("kick", kick))
    await bot.polling()

asyncio.run(main())
```

### Example 6: Using Markdown for Formatting

```python
import asyncio
from extergram import Bot, ContextTypes, Markdown
from extergram.ext import CommandHandler
async def start(context: ContextTypes):
    text = str(
        Markdown("Welcome to ")
        .bold("Extergram")
        .text("!\n")
        .italic("The async bot framework")
    )
    await context.bot.send_message(
        context.message.chat.id,
        text,
        parse_mode="MarkdownV2"
    )

async def main():
    bot = Bot(token="YOUR_TOKEN")
    bot.add_handler(CommandHandler("start", start))
    await bot.polling()

asyncio.run(main())
```

---

## 🛡 Anti-Flood System

Extergram automatically tracks request frequency and introduces dynamic delays when approaching Telegram's rate limits. This helps prevent `429 Too Many Requests` errors. No configuration is needed.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 🌐 Links

- **GitHub**: [https://github.com/TIBI624/extergram](https://github.com/TIBI624/extergram)
- **Issue Tracker**: [https://github.com/TIBI624/extergram/issues](https://github.com/TIBI624/extergram/issues)
- **PyPI**: [https://pypi.org/project/extergram/](https://pypi.org/project/extergram/)
- **Contribute**: We welcome bug reports and pull requests! ❤️