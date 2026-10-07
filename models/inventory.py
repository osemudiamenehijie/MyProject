"""Inventory stock-in and stock-out operations."""

from database import get_connection


class Inventory:
    @staticmethod
    def change_stock(product_id, quantity, movement_type, note=""):
        """Record a stock movement and update the product in one transaction."""
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Movement quantity must be a whole number greater than zero.")
        if movement_type not in ("IN", "OUT"):
            raise ValueError("Movement type must be 'IN' or 'OUT'.")

        with get_connection() as connection:
            product = connection.execute(
                "SELECT quantity FROM products WHERE product_id = ?", (product_id,)
            ).fetchone()
            if product is None:
                raise ValueError("Product was not found.")
            current_quantity = product["quantity"]
            if movement_type == "OUT" and quantity > current_quantity:
                raise ValueError("Cannot remove more stock than is currently available.")
            new_quantity = (current_quantity + quantity if movement_type == "IN"
                            else current_quantity - quantity)
            connection.execute(
                "UPDATE products SET quantity = ? WHERE product_id = ?",
                (new_quantity, product_id),
            )
            connection.execute(
                """INSERT INTO inventory_movements
                   (product_id, movement_type, quantity, note)
                   VALUES (?, ?, ?, ?)""",
                (product_id, movement_type, quantity, note.strip() or None),
            )
            return new_quantity

    @staticmethod
    def get_history(product_id):
        """Return stock movement records for one product, newest first."""
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT * FROM inventory_movements
                   WHERE product_id = ? ORDER BY movement_id DESC""",
                (product_id,),
            ).fetchall()
            return [dict(row) for row in rows]
