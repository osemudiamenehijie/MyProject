"""Inventory stock-in and stock-out operations."""

# Use the same SQLite connection helper as the product code.
from database import get_connection


class Inventory:
    @staticmethod
    def change_stock(product_id, quantity, movement_type, note=""):
        """Record a stock movement and update the product in one transaction."""
        # A movement must change stock by a positive whole number.
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Movement quantity must be a whole number greater than zero.")
        # Restrict the action to the two movement types supported by the database.
        if movement_type not in ("IN", "OUT"):
            raise ValueError("Movement type must be 'IN' or 'OUT'.")

        # Save the balance change and history record together in one transaction.
        with get_connection() as connection:
            # Read the current balance before calculating its new value.
            product = connection.execute(
                "SELECT quantity FROM products WHERE product_id = ?", (product_id,)
            ).fetchone()
            if product is None:
                raise ValueError("Product was not found.")
            # Get the current balance so we can calculate the new one.
            current_quantity = product["quantity"]
            if movement_type == "OUT" and quantity > current_quantity:
                raise ValueError("Cannot remove more stock than is currently available.")
            # Stock-in adds units; stock-out subtracts units.
            new_quantity = (current_quantity + quantity if movement_type == "IN"
                            else current_quantity - quantity)
            # The balance and its history are saved together as one transaction.
            # First update the product's current stock balance.
            connection.execute(
                "UPDATE products SET quantity = ? WHERE product_id = ?",
                (new_quantity, product_id),
            )
            # Then record why and how much the balance changed.
            connection.execute(
                """INSERT INTO inventory_movements
                   (product_id, movement_type, quantity, note)
                   VALUES (?, ?, ?, ?)""",
                (product_id, movement_type, quantity, note.strip() or None),
            )
            # Tell the screen the final balance so it can display it to the user.
            return new_quantity

    @staticmethod
    def get_history(product_id):
        """Return stock movement records for one product, newest first."""
        # Select this product's movements, sorting newest records to the top.
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT * FROM inventory_movements
                   WHERE product_id = ? ORDER BY movement_id DESC""",
                (product_id,),
            ).fetchall()
            # Convert SQLite rows to ordinary dictionaries for easy use in the GUI.
            return [dict(row) for row in rows]
