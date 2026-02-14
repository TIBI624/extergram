# extergram/ui.py

class ButtonsDesign:
    """
    A builder for creating inline keyboards.
    """
    def __init__(self, inline_keyboard: list = None):
        self.keyboard = inline_keyboard if inline_keyboard else []

    def add_row(self, *buttons):
        """
        Adds a row of buttons to the keyboard.
        """
        self.keyboard.append(list(buttons))
        return self

    def to_dict(self):
        """
        Returns the keyboard as a dictionary for the API.
        """
        return {"inline_keyboard": self.keyboard}

    @staticmethod
    def create_button(text: str, callback_data: str):
        """
        Creates a button for an inline keyboard.
        """
        return {"text": text, "callback_data": callback_data}

    @staticmethod
    def create_url_button(text: str, url: str):
        """
        Creates a URL button.
        """
        return {"text": text, "url": url}