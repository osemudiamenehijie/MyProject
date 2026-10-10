"""A small checkout window for recording a sale."""

# sqlite3.IntegrityError lets the screen display database errors as friendly messages.
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# The model checks stock and saves a completed sale.
from models.sale import Sale
# Product provides the current product list and stock values.
from models.product import Product


class SaleWindow:
    def __init__(self, parent_app):
        # Keep a reference to the product screen so we can refresh it after checkout.
        self.parent_app = parent_app
        # Create this checkout as a second window owned by the main app.
        self.window = tk.Toplevel(parent_app.root)
        self.window.title("Record a Sale")
        self.window.geometry("700x500")
        self.window.minsize(600, 420)

        # The cart stores product IDs and quantities until the sale is completed.
        self.cart = {}
        # This mapping connects the product name shown in the dropdown to its object.
        self.product_choices = {}

        # Build the checkout controls, then load available products into the dropdown.
        self._build_screen()
        self.refresh_product_choices()

    def _build_screen(self):
        """Create the product picker, cart table, and checkout button."""
        # Use one padded frame to hold all controls in the checkout window.
        page = ttk.Frame(self.window, padding=16)
        page.pack(fill="both", expand=True)

        # Explain what this screen is for.
        ttk.Label(page, text="Record a Sale", font=("Segoe UI", 18, "bold")).pack(
            anchor="w", pady=(0, 12)
        )

        # Row for choosing a product and the number of units to add.
        picker = ttk.Frame(page)
        picker.pack(fill="x", pady=(0, 12))
        ttk.Label(picker, text="Product:").pack(side="left")
        # product_text holds the selected dropdown option.
        self.product_text = tk.StringVar()
        # A read-only combo box prevents typing a product that is not in the database.
        self.product_box = ttk.Combobox(
            picker, textvariable=self.product_text, state="readonly", width=38
        )
        self.product_box.pack(side="left", padx=(8, 12))

        # quantity_text stores what the user types for the number of units.
        ttk.Label(picker, text="Quantity:").pack(side="left")
        self.quantity_text = tk.StringVar(value="1")
        ttk.Entry(picker, textvariable=self.quantity_text, width=7).pack(
            side="left", padx=(8, 12)
        )

        # Add the selected product and quantity to the temporary cart.
        ttk.Button(picker, text="Add to sale", command=self.add_to_cart).pack(side="left")
        # Let the user reload the dropdown if products were added in the other window.
        ttk.Button(picker, text="Refresh products", command=self.refresh_product_choices).pack(
            side="left", padx=(8, 0)
        )

        # Create the table that shows everything currently in the cart.
        columns = ("product", "quantity", "unit_price", "line_total")
        self.cart_table = ttk.Treeview(page, columns=columns, show="headings", height=10)
        # Set a readable title and width for each cart column.
        self.cart_table.heading("product", text="Product")
        self.cart_table.heading("quantity", text="Quantity")
        self.cart_table.heading("unit_price", text="Unit price")
        self.cart_table.heading("line_total", text="Line total")
        self.cart_table.column("product", width=280, anchor="w")
        self.cart_table.column("quantity", width=90, anchor="center")
        self.cart_table.column("unit_price", width=110, anchor="e")
        self.cart_table.column("line_total", width=110, anchor="e")
        self.cart_table.pack(fill="both", expand=True)

        # Show the combined cost of all cart rows.
        self.total_text = tk.StringVar(value="Sale total: 0.00")
        ttk.Label(page, textvariable=self.total_text, font=("Segoe UI", 12, "bold")).pack(
            anchor="e", pady=12
        )

        # Complete the sale and save it to the database.
        ttk.Button(page, text="Complete sale", command=self.complete_sale).pack(anchor="e")

    def refresh_product_choices(self):
        """Load current products into the product dropdown."""
        # Read all products from SQLite and create display labels for the dropdown.
        products = Product.get_all()
        self.product_choices = {
            f"{product.sku} - {product.name}": product for product in products
        }
        # Update what the user can choose.
        options = list(self.product_choices.keys())
        self.product_box["values"] = options

        # Select the first item when products exist and no current choice remains.
        if options and self.product_text.get() not in self.product_choices:
            self.product_text.set(options[0])
        elif not options:
            # Leave the dropdown blank when the shop has no products yet.
            self.product_text.set("")

    def add_to_cart(self):
        """Check stock and add the selected product to the temporary cart."""
        # Look up the Product object that matches the visible dropdown text.
        product = self.product_choices.get(self.product_text.get())
        if product is None:
            messagebox.showwarning("Choose a product", "Select a product first.",
                                   parent=self.window)
            return

        # Convert the quantity entry from text into an integer.
        try:
            quantity = int(self.quantity_text.get())
        except ValueError:
            messagebox.showerror("Invalid quantity", "Enter a whole number.",
                                 parent=self.window)
            return

        # A sale line must always be at least one unit.
        if quantity <= 0:
            messagebox.showerror("Invalid quantity", "Quantity must be above zero.",
                                 parent=self.window)
            return

        # Fetch the latest quantity in case stock changed after this window opened.
        current_product = Product.get(product.product_id)
        if current_product is None:
            messagebox.showerror("Product missing", "Refresh the product list and try again.",
                                 parent=self.window)
            self.refresh_product_choices()
            return

        # Include any units already in the cart when checking available stock.
        cart_quantity = self.cart.get(current_product.product_id, 0)
        if cart_quantity + quantity > current_product.quantity:
            messagebox.showerror(
                "Not enough stock",
                f"Available: {current_product.quantity}. Already in sale: {cart_quantity}.",
                parent=self.window,
            )
            return

        # Add to any existing cart quantity for the same product.
        self.cart[current_product.product_id] = cart_quantity + quantity
        # Refresh the cart table and restore the quantity box to one unit.
        self.refresh_cart()
        self.quantity_text.set("1")

    def refresh_cart(self):
        """Redraw the cart table and recalculate its displayed total."""
        # Remove the previous display rows before drawing the latest cart contents.
        for item in self.cart_table.get_children():
            self.cart_table.delete(item)

        total = 0.0
        # Each dictionary entry is one product ID and its quantity in the cart.
        for product_id, quantity in self.cart.items():
            product = Product.get(product_id)
            if product is None:
                continue

            # Calculate this row's amount, then add it to the sale total.
            line_total = product.price * quantity
            total += line_total
            # Display the product, amount, price per unit, and row total.
            self.cart_table.insert(
                "", "end", iid=str(product_id),
                values=(product.name, quantity, f"{product.price:.2f}",
                        f"{line_total:.2f}"),
            )

        # Update the label below the table with the recalculated total.
        self.total_text.set(f"Sale total: {total:.2f}")

    def complete_sale(self):
        """Save the sale and let the inventory model deduct stock."""
        # Sale.record_sale checks the cart again and saves it transactionally.
        try:
            sale_id, total = Sale.record_sale(self.cart)
        except (ValueError, sqlite3.IntegrityError) as error:
            # If anything is invalid or stock changed, explain why checkout stopped.
            messagebox.showerror("Sale could not be completed", str(error),
                                 parent=self.window)
            return

        # Clear this cart only after the sale has been saved successfully.
        self.cart.clear()
        self.refresh_cart()
        # Refresh the product screen so it shows the reduced stock quantity.
        self.parent_app.refresh_products()
        # Tell the user the sale was recorded and show its ID and amount.
        messagebox.showinfo(
            "Sale completed", f"Sale #{sale_id} saved. Total: {total:.2f}",
            parent=self.window,
        )
