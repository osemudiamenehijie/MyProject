"""Sale operations that save the sale and reduce stock together."""

# Reuse the shared connection so sale records and stock updates use one database.
from database import get_connection


class Sale:
    @staticmethod
    def record_sale(cart):
        """Save a cart and reduce the quantity of each product in it.

        The cart is a dictionary in the form {product_id: quantity}.
        Return the new sale ID and the total amount charged.
        """
        # A sale must contain at least one product.
        if not cart:
            raise ValueError("Add at least one product before completing the sale.")

        # Check the quantities before opening the database transaction.
        for product_id, quantity in cart.items():
            if not isinstance(quantity, int) or quantity <= 0:
                raise ValueError("Every sale quantity must be a whole number above zero.")

        # BEGIN IMMEDIATE locks the database for writing while we check and update stock.
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")

            # Keep the product details and prices that will be saved on this sale.
            sale_lines = []
            sale_total = 0.0

            # Check every item first so an invalid cart does not create a partial sale.
            for product_id, quantity in cart.items():
                product = connection.execute(
                    "SELECT name, price, quantity FROM products WHERE product_id = ?",
                    (product_id,),
                ).fetchone()

                # Stop if the cart refers to a product that no longer exists.
                if product is None:
                    raise ValueError("A product in this sale could not be found.")

                # Never allow a sale to take more units than the shop has in stock.
                if quantity > product["quantity"]:
                    raise ValueError(
                        f"Not enough stock for {product['name']}. "
                        f"Available: {product['quantity']}."
                    )

                # Store the current price so later price changes do not rewrite this sale.
                unit_price = product["price"]
                line_total = unit_price * quantity
                sale_total += line_total
                sale_lines.append((product_id, quantity, unit_price, line_total))

            # Create the sale header after all products have passed validation.
            sale_cursor = connection.execute(
                "INSERT INTO sales (total) VALUES (?)", (sale_total,)
            )
            sale_id = sale_cursor.lastrowid

            # Save each item and deduct its quantity from the product balance.
            for product_id, quantity, unit_price, line_total in sale_lines:
                connection.execute(
                    """INSERT INTO sale_items
                       (sale_id, product_id, quantity, unit_price, line_total)
                       VALUES (?, ?, ?, ?, ?)""",
                    (sale_id, product_id, quantity, unit_price, line_total),
                )
                connection.execute(
                    "UPDATE products SET quantity = quantity - ? WHERE product_id = ?",
                    (quantity, product_id),
                )

            # Leaving the with block commits all sale rows and stock changes together.
            return sale_id, sale_total
