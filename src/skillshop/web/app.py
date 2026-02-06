"""
Textual Web application for Skill Shop.

This uses the same Textual app as the CLI but launches in web mode.
"""

from skillshop.cli.app import SkillShopApp


def main():
    """Entry point for web application."""
    app = SkillShopApp()
    # Textual Web will automatically detect web mode when run with textual-web
    app.run()


if __name__ == "__main__":
    main()
