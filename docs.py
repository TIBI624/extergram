# extergram/docs.py

import os

class Docs:
    """A class to access the library's documentation."""

    @staticmethod
    def get_docs() -> str:
        """
        Reads and returns the content of the README.md file.
        The README content is adapted for console output (removes Markdown syntax).
        """
        try:
            # Construct path to README.md relative to this file's location
            dir_path = os.path.dirname(os.path.realpath(__file__))
            readme_path = os.path.join(dir_path, '..', 'README.md') # Go up one level

            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple replacements for console readability
            content = content.replace('`', '')
            content = content.replace('### ', '')
            content = content.replace('## ', '')
            content = content.replace('# ', '')
            content = content.replace('**', '')
            
            return content
        except FileNotFoundError:
            return "Could not find the README.md file."
        except Exception as e:
            return f"An error occurred while reading the documentation: {e}"

    @staticmethod
    def print_docs():
        """Prints the documentation directly to the console."""
        print(Docs.get_docs())