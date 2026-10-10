"""Start the My Project Dominion desktop application."""

# Import the function that creates the database tables and default category.
from database import initialize_database
# Import the class that builds and runs the product screen.
from gui.products import ProductManagementApp


def main():
    # Prepare the data store before any screen tries to read from it.
    initialize_database()
    # Build the window, then keep it running until the user closes it.
    ProductManagementApp().run()


# This condition is true when you run main.py directly from VS Code or Command Prompt.
# It prevents the window from opening just because another file imports main.py.
if __name__ == "__main__":
    # Start the application by calling the function defined above.
    main()
