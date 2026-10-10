"""Product model and product CRUD operations."""

# dataclass automatically creates a convenient constructor for these fields.
from dataclasses import dataclass

# Reuse the shared database connection and default category helper.
from database import get_connection, get_default_category_id


@dataclass
class Product:
    # These fields describe one product; the ID is None until it is saved.
    product_id: int | None
    sku: str
    name: str
    price: float
    quantity: int
    category_id: int
    low_stock_threshold: int = 5

    @staticmethod
    def _validate(sku, name, price, quantity, low_stock_threshold):
        # Check the form values before trying to save them in SQLite.
        # Reject missing or whitespace-only SKUs.
        if not sku or not sku.strip():
            raise ValueError("SKU cannot be blank.")
        # Reject missing or whitespace-only product names.
        if not name or not name.strip():
            raise ValueError("Product name cannot be blank.")
        # Prices can be zero, but never negative.
        if price < 0:
            raise ValueError("Price cannot be negative.")
        # Inventory quantities are whole numbers and cannot be negative.
        if not isinstance(quantity, int) or quantity < 0:
            raise ValueError("Quantity must be a whole number of zero or more.")
        # The low-stock warning level must also be a non-negative whole number.
        if not isinstance(low_stock_threshold, int) or low_stock_threshold < 0:
            raise ValueError("Low-stock threshold must be a whole number of zero or more.")

    @classmethod
    def create(cls, sku, name, price, quantity, category_id=None, low_stock_threshold=5):
        """Create and return a product row in the database."""
        # Validate first so bad data never reaches the database.
        cls._validate(sku, name, price, quantity, low_stock_threshold)
        # If no category was chosen, put this product in General.
        if category_id is None:
            category_id = get_default_category_id()
        # Open a connection; a successful with block commits the insert.
        with get_connection() as connection:
            # Insert one row; ? placeholders safely receive the values below.
            cursor = connection.execute(
                """INSERT INTO products
                   (sku, name, price, quantity, category_id, low_stock_threshold)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sku.strip(), name.strip(), price, quantity, category_id, low_stock_threshold),
            )
            # Read the row back using the new ID SQLite generated.
            row = connection.execute(
                "SELECT * FROM products WHERE product_id = ?", (cursor.lastrowid,)
            ).fetchone()
            # Convert the SQLite row into a Product object for the rest of the app.
            return cls._from_row(row)

    @classmethod
    def get(cls, product_id):
        """Return one product by its database ID, or None if it is missing."""
        # Search for one row using its unique database ID.
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM products WHERE product_id = ?", (product_id,)
            ).fetchone()
            # Convert a found row; return None when no such ID exists.
            return cls._from_row(row) if row else None

    @classmethod
    def get_all(cls, search=""):
        """Return all products, optionally searching SKU or name."""
        # The percent signs let the search match text anywhere in the SKU or name.
        search_text = f"%{search.strip()}%"
        # Ask the database for every row whose SKU or name matches the search.
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT * FROM products
                   WHERE sku LIKE ? OR name LIKE ?
                   ORDER BY name""",
                (search_text, search_text),
            ).fetchall()
            # Turn each database row into a Product object, then return the list.
            return [cls._from_row(row) for row in rows]

    @classmethod
    def get_low_stock(cls, search=""):
        """Return products whose quantity is at or below their warning level."""
        # Keep the same search behavior as get_all while adding a stock condition.
        search_text = f"%{search.strip()}%"
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT * FROM products
                   WHERE quantity <= low_stock_threshold
                     AND (sku LIKE ? OR name LIKE ?)
                   ORDER BY name""",
                (search_text, search_text),
            ).fetchall()
            # Convert the matching rows into Product objects.
            return [cls._from_row(row) for row in rows]

    def update(self, sku, name, price, quantity, category_id=None, low_stock_threshold=5):
        """Update this product's details and current quantity."""
        # Apply the same rules used when a product is first created.
        self._validate(sku, name, price, quantity, low_stock_threshold)
        # Use the default category if the caller did not provide one.
        if category_id is None:
            category_id = get_default_category_id()
        # Update the database row that has this product's ID.
        with get_connection() as connection:
            connection.execute(
                """UPDATE products
                   SET sku = ?, name = ?, price = ?, quantity = ?,
                       category_id = ?, low_stock_threshold = ?
                   WHERE product_id = ?""",
                (sku.strip(), name.strip(), price, quantity, category_id,
                low_stock_threshold, self.product_id),
            )
        # Keep this in-memory object in step with the database values just saved.
        self.sku = sku.strip()
        self.name = name.strip()
        self.price = price
        self.quantity = quantity
        self.category_id = category_id
        self.low_stock_threshold = low_stock_threshold

    def delete(self):
        """Delete this product if it has no movement history."""
        # Check stock and sales histories so their product links are not broken.
        with get_connection() as connection:
            movements = connection.execute(
                """SELECT 1 FROM inventory_movements WHERE product_id = ?
                   UNION ALL
                   SELECT 1 FROM sale_items WHERE product_id = ?
                   LIMIT 1""",
                (self.product_id, self.product_id),
            ).fetchone()
            # Refuse deletion when stock movements or past sales use this product.
            if movements:
                raise ValueError("This product has stock history and cannot be deleted.")
            # No history exists, so it is safe to remove the product row.
            connection.execute(
                "DELETE FROM products WHERE product_id = ?", (self.product_id,)
            )

    @classmethod
    def _from_row(cls, row):
        # Map database column names to the Product class field names.
        return cls(
            product_id=row["product_id"], sku=row["sku"], name=row["name"],
            price=row["price"], quantity=row["quantity"],
            category_id=row["category_id"],
            low_stock_threshold=row["low_stock_threshold"],
        )
