"""Start the My Project Dominion desktop application."""

from database import initialize_database
from gui.products import ProductManagementApp


def main():
    initialize_database()
    ProductManagementApp().run()


if __name__ == "__main__":
    main()
