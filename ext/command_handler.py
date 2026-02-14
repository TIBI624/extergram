# extergram/ext/command_handler.py

from .base import BaseHandler
from ..api_types import Update

class CommandHandler(BaseHandler):
    """Handler for commands starting with '/'."""
    def __init__(self, command, callback):
        super().__init__(callback)
        if isinstance(command, str):
            self.commands = [command.lower()]
        else:
            self.commands = [cmd.lower() for cmd in command]

    def check_update(self, update: Update) -> bool:
        if update.message and update.message.text:
            text = update.message.text
            if text.startswith('/'):
                parts = text.split()
                command = parts[0][1:].lower()
                return command in self.commands
        return False