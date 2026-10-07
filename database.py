"""SQLite connection and initial schema for My Project Dominion."""

import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_DIR = PROJECT_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "dominion.db"


def get_connection():
    """Return a connection and make SQLite enforce foreign keys."""
    DATABASE_DIR.mkdir(exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    """Create the October 7 tables if they do not already exist."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
                category_id INTEGER NOT NULL,
                low_stock_threshold INTEGER NOT NULL DEFAULT 5
                    CHECK (low_stock_threshold >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            );

            CREATE TABLE IF NOT EXISTS inventory_movements (
                movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL CHECK (movement_type IN ('IN', 'OUT')),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)", ("General",)
        )
        row = connection.execute(
            "SELECT category_id FROM categories WHERE name = ?", ("General",)
        ).fetchone()
        return row["category_id"]


def get_default_category_id():
    """Find the General category, creating the schema first if needed."""
    initialize_database()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT category_id FROM categories WHERE name = ?", ("General",)
        ).fetchone()
        return row["category_id"]
