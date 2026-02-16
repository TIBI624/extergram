# extergram/docs.py

class Docs:
    """
    Access to the library's documentation.
    Since README.md is not included in the installed package,
    this class provides a link to the online documentation.
    """

    GITHUB_URL = "https://github.com/TIBI624/extergram#readme"

    @staticmethod
    def get_docs() -> str:
        """
        Returns a message with a link to the online documentation.
        """
        return (
            "📚 **Extergram Documentation**\n\n"
            "The full documentation is available online at:\n"
            f"{Docs.GITHUB_URL}\n\n"
            "You can also view the README directly on GitHub."
        )

    @staticmethod
    def print_docs():
        """Prints the documentation link to the console."""
        print(Docs.get_docs())