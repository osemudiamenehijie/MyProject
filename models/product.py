"""Product model and product CRUD operations."""

from dataclasses import dataclass

from database import get_connection, get_default_category_id


@dataclass
class Product:
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
        if not sku or not sku.strip():
            raise ValueError("SKU cannot be blank.")
        if not name or not name.strip():
            raise ValueError("Product name cannot be blank.")
        if price < 0:
            raise ValueError("Price cannot be negative.")
        if not isinstance(quantity, int) or quantity < 0:
            raise ValueError("Quantity must be a whole number of zero or more.")
        if not isinstance(low_stock_threshold, int) or low_stock_threshold < 0:
            raise ValueError("Low-stock threshold must be a whole number of zero or more.")

    @classmethod
    def create(cls, sku, name, price, quantity, category_id=None, low_stock_threshold=5):
        """Create and return a product row in the database."""
        cls._validate(sku, name, price, quantity, low_stock_threshold)
        if category_id is None:
            category_id = get_default_category_id()
        with get_connection() as connection:
            cursor = connection.execute(
                """INSERT INTO products
                   (sku, name, price, quantity, category_id, low_stock_threshold)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (sku.strip(), name.strip(), price, quantity, category_id, low_stock_threshold),
            )
            row = connection.execute(
                "SELECT * FROM products WHERE product_id = ?", (cursor.lastrowid,)
            ).fetchone()
            return cls._from_row(row)

    @classmethod
    def get(cls, product_id):
        """Return one product by its database ID, or None if it is missing."""
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM products WHERE product_id = ?", (product_id,)
            ).fetchone()
            return cls._from_row(row) if row else None

    @classmethod
    def get_all(cls, search=""):
        """Return all products, optionally searching SKU or name."""
        # The percent signs let the search match text anywhere in the SKU or name.
        search_text = f"%{search.strip()}%"
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT * FROM products
                   WHERE sku LIKE ? OR name LIKE ?
                   ORDER BY name""",
                (search_text, search_text),
            ).fetchall()
            return [cls._from_row(row) for row in rows]

    @classmethod
    def get_low_stock(cls, search=""):
        """Return products whose quantity is at or below their warning level."""
        search_text = f"%{search.strip()}%"
        with get_connection() as connection:
            rows = connection.execute(
                """SELECT * FROM products
                   WHERE quantity <= low_stock_threshold
                     AND (sku LIKE ? OR name LIKE ?)
                   ORDER BY name""",
                (search_text, search_text),
            ).fetchall()
            return [cls._from_row(row) for row in rows]

    def update(self, sku, name, price, quantity, category_id=None, low_stock_threshold=5):
        """Update this product's details and current quantity."""
        self._validate(sku, name, price, quantity, low_stock_threshold)
        if category_id is None:
            category_id = get_default_category_id()
        with get_connection() as connection:
            connection.execute(
                """UPDATE products
                   SET sku = ?, name = ?, price = ?, quantity = ?,
                       category_id = ?, low_stock_threshold = ?
                   WHERE product_id = ?""",
                (sku.strip(), name.strip(), price, quantity, category_id,
                 low_stock_threshold, self.product_id),
            )
        self.sku = sku.strip()
        self.name = name.strip()
        self.price = price
        self.quantity = quantity
        self.category_id = category_id
        self.low_stock_threshold = low_stock_threshold

    def delete(self):
        """Delete this product if it has no movement history."""
        with get_connection() as connection:
            movements = connection.execute(
                "SELECT 1 FROM inventory_movements WHERE product_id = ? LIMIT 1",
                (self.product_id,),
            ).fetchone()
            if movements:
                raise ValueError("This product has stock history and cannot be deleted.")
            connection.execute(
                "DELETE FROM products WHERE product_id = ?", (self.product_id,)
            )

    @classmethod
    def _from_row(cls, row):
        return cls(
            product_id=row["product_id"], sku=row["sku"], name=row["name"],
            price=row["price"], quantity=row["quantity"],
            category_id=row["category_id"],
            low_stock_threshold=row["low_stock_threshold"],
        )
