"""SQLite connection and initial schema for My Project Dominion."""

# sqlite3 is Python's built-in tool for working with SQLite databases.
import sqlite3
# Path helps build file locations without hard-coding slash directions.
from pathlib import Path


# __file__ is the location of this Python file; resolve() makes it an absolute path.
PROJECT_DIR = Path(__file__).resolve().parent
# Store the database inside a folder named "database" beside this file.
DATABASE_DIR = PROJECT_DIR / "database"
# Give the SQLite file a name; SQLite creates it the first time we connect.
DATABASE_PATH = DATABASE_DIR / "dominion.db"


def get_connection():
    """Return a connection and make SQLite enforce foreign keys."""
    # Create the database folder if this is the first time the app is run.
    DATABASE_DIR.mkdir(exist_ok=True)
    # Open the database file and keep the connection in a variable.
    connection = sqlite3.connect(DATABASE_PATH)
    # This lets us read a column by name, for example row["name"].
    connection.row_factory = sqlite3.Row
    # Tell SQLite to check that foreign keys point to real rows.
    connection.execute("PRAGMA foreign_keys = ON")
    # Give this ready-to-use connection back to the caller.
    return connection


def initialize_database():
    """Create the October 7 tables if they do not already exist."""
    # The with block closes the connection and commits successful changes.
    with get_connection() as connection:
        # executescript lets us create several related tables in one call.
        connection.executescript(
            """
            -- Categories are labels that products can belong to.
            CREATE TABLE IF NOT EXISTS categories (
                -- Give every category its own automatically increasing ID.
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- A category needs a name, and no two categories may share it.
                name TEXT NOT NULL UNIQUE
            );

            -- Store each sellable item and its current stock balance.
            CREATE TABLE IF NOT EXISTS products (
                -- Unique database ID for the product.
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Shop-facing product code; it must be present and unique.
                sku TEXT NOT NULL UNIQUE,
                -- Human-readable product name.
                name TEXT NOT NULL,
                -- Price must be provided and cannot be below zero.
                price REAL NOT NULL CHECK (price >= 0),
                -- Current stock starts at zero and cannot be negative.
                quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
                -- Every product must point to a category row.
                category_id INTEGER NOT NULL,
                -- Show a low-stock warning when quantity reaches this number.
                low_stock_threshold INTEGER NOT NULL DEFAULT 5
                    CHECK (low_stock_threshold >= 0),
                -- SQLite fills in the date and time when the row is created.
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                -- Connect this product to its category.
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            );

            -- Keep a history record for every stock-in or stock-out operation.
            CREATE TABLE IF NOT EXISTS inventory_movements (
                -- Unique ID for one stock movement record.
                movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- The product whose stock changed.
                product_id INTEGER NOT NULL,
                -- Only stock coming IN or going OUT is allowed at this stage.
                movement_type TEXT NOT NULL CHECK (movement_type IN ('IN', 'OUT')),
                -- Record a positive number of units; direction is in movement_type.
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                -- Optional explanation, such as "delivery from supplier".
                note TEXT,
                -- Automatically record when this movement happened.
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                -- Connect the movement to an existing product.
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            -- One row represents one completed checkout.
            CREATE TABLE IF NOT EXISTS sales (
                sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL CHECK (total >= 0)
            );

            -- Each sale can contain one or more product lines.
            CREATE TABLE IF NOT EXISTS sale_items (
                sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                line_total REAL NOT NULL CHECK (line_total >= 0),
                FOREIGN KEY (sale_id) REFERENCES sales(sale_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );
            """
        )
        # Add one starter category; OR IGNORE avoids adding it twice.
        connection.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)", ("General",)
        )
        # Look up the ID that SQLite assigned to the General category.
        row = connection.execute(
            "SELECT category_id FROM categories WHERE name = ?", ("General",)
        ).fetchone()
        # Return that ID so product creation can use it as its category.
        return row["category_id"]


def get_default_category_id():
    """Find the General category, creating the schema first if needed."""
    # This is safe to call more than once because the tables are created only if absent.
    initialize_database()
    # Open a fresh connection to read the default category ID.
    with get_connection() as connection:
        row = connection.execute(
            "SELECT category_id FROM categories WHERE name = ?", ("General",)
        ).fetchone()
        # Return the numeric category ID, not the whole database row.
        return row["category_id"]
