"""
Main Textual CLI application for Skill Shop.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static


class SkillShopApp(App):
    """
    Main Textual application for the Skill Shop CLI.
    
    Provides a terminal UI for:
    - Browsing available skills
    - Running skills
    - Viewing outputs
    - Managing skill registry
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .main-container {
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container(classes="main-container"):
            yield Static("Skill Shop CLI - Coming Soon", id="main-content")
        yield Footer()
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
    
    def action_refresh(self) -> None:
        """Refresh the skill list."""
        # TODO: Implement skill list refresh
        pass


def main():
    """Entry point for CLI application."""
    app = SkillShopApp()
    app.run()


if __name__ == "__main__":
    main()
