"""
Textual Web application for Bank Skills.

This uses the same Textual app as the CLI but launches in web mode.
"""

from bankskills.cli.app import BankSkillsApp


def main():
    """Entry point for web application."""
    app = BankSkillsApp()
    # Textual Web will automatically detect web mode when run with textual-web
    app.run()


if __name__ == "__main__":
    main()
