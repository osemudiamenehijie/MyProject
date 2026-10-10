"""Simple product management window built with Tkinter."""

# sqlite3 errors are caught so duplicate SKUs can be explained to the user.
import sqlite3
# tkinter creates windows; tk holds basic widgets and variables.
import tkinter as tk
# messagebox shows alerts; simpledialog asks for input; ttk provides styled widgets.
from tkinter import messagebox, simpledialog, ttk

# Import the inventory rules and the product database operations used by this screen.
from models.inventory import Inventory
from models.product import Product
from gui.sales import SaleWindow


class ProductManagementApp:
    def __init__(self):
        # Create the main application window.
        self.root = tk.Tk()
        # Set the title displayed along the top of the window.
        self.root.title("My Project Dominion - Products")
        # Set the first window size in width-by-height pixels.
        self.root.geometry("980x650")
        # Stop the user from shrinking the window too small to use.
        self.root.minsize(800, 560)
        # Remember which product the user has selected; none is selected initially.
        self.selected_product_id = None

        # Create the widgets, then load the current products into the table.
        self._build_screen()
        self.refresh_products()

    def _build_screen(self):
        """Create the search bar, product table, and product form."""
        # This outer frame holds all screen sections and expands with the window.
        page = ttk.Frame(self.root, padding=16)
        page.pack(fill="both", expand=True)

        # The header contains the screen title and the low-stock count.
        header = ttk.Frame(page)
        header.pack(fill="x", pady=(0, 10))
        # Show a large title aligned to the left of the header.
        ttk.Label(header, text="Product Management", font=("Segoe UI", 18, "bold")).pack(
            side="left"
        )
        # This label will later show the number of products below their stock threshold.
        self.low_stock_summary = ttk.Label(header, text="")
        self.low_stock_summary.pack(side="right")

        # Put the text search and the low-stock checkbox on one row.
        search_row = ttk.Frame(page)
        search_row.pack(fill="x", pady=(0, 10))
        # Tell the user what the search field looks through.
        ttk.Label(search_row, text="Search by SKU or name:").pack(side="left")
        # StringVar keeps the search text available to Python code.
        self.search_text = tk.StringVar()
        # Link the visible entry box to that StringVar.
        search_box = ttk.Entry(search_row, textvariable=self.search_text, width=36)
        search_box.pack(side="left", padx=(8, 0))
        # Whenever search_text changes, refresh the table automatically.
        self.search_text.trace_add("write", self._search_changed)
        # BooleanVar remembers whether the user checked "Show low-stock only".
        self.low_stock_only = tk.BooleanVar(value=False)
        # Add a checkbox; changing it tells the screen to reload the table.
        ttk.Checkbutton(
            search_row, text="Show low-stock only", variable=self.low_stock_only,
            command=self.refresh_products,
        ).pack(side="left", padx=(18, 0))

        # The table frame keeps the product list and its scrollbar together.
        table_frame = ttk.Frame(page)
        table_frame.pack(fill="both", expand=True)
        # These names identify the columns that each product row will display.
        columns = ("sku", "name", "price", "quantity", "threshold", "status")
        # Treeview is the table widget; show= headings hides the unused first column.
        self.product_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        # For each column, define its visible heading and approximate width.
        headings = {
            "sku": ("SKU", 120), "name": ("Product name", 230),
            "price": ("Price", 100), "quantity": ("Quantity", 100),
            "threshold": ("Low-stock level", 130),
            "status": ("Stock status", 120),
        }
        # Loop through the heading settings so each column is configured the same way.
        for column, (label, width) in headings.items():
            # Set the heading text at the top of the column.
            self.product_table.heading(column, text=label)
            # Set column width and align its values to the left.
            self.product_table.column(column, width=width, anchor="w")
        # Create a vertical scrollbar connected to the table's y-axis.
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.product_table.yview
        )
        # Let the table move the scrollbar thumb as the user scrolls through rows.
        self.product_table.configure(yscrollcommand=scrollbar.set)
        # Place the table on the left and let it use available space.
        self.product_table.pack(side="left", fill="both", expand=True)
        # Place the scrollbar beside the table from top to bottom.
        scrollbar.pack(side="right", fill="y")
        # A colored status makes low stock visible without opening another screen.
        self.product_table.tag_configure("low_stock", foreground="#b42318")
        # When the user selects a row, copy that product into the form below.
        self.product_table.bind("<<TreeviewSelect>>", self._product_selected)

        # Add a labeled frame around the fields used to add or edit a product.
        form = ttk.LabelFrame(page, text="Product details", padding=10)
        form.pack(fill="x", pady=(12, 0))
        # Each StringVar stores what the user types in its matching field.
        self.sku_text = tk.StringVar()
        self.name_text = tk.StringVar()
        self.price_text = tk.StringVar()
        self.quantity_text = tk.StringVar(value="0")
        self.threshold_text = tk.StringVar(value="5")

        # Pair each form label with the variable used to hold its text.
        fields = [
            ("SKU", self.sku_text), ("Name", self.name_text),
            ("Price", self.price_text), ("Quantity", self.quantity_text),
            ("Low-stock level", self.threshold_text),
        ]
        # Build the form fields from the list instead of writing each one separately.
        for index, (label, variable) in enumerate(fields):
            # Place three fields on each row: divmod gives a row and column number.
            row, column = divmod(index, 3)
            # Each field gets its own small frame so label and entry stay together.
            cell = ttk.Frame(form)
            cell.grid(row=row, column=column, sticky="ew", padx=6, pady=5)
            # Display the field name above its text box.
            ttk.Label(cell, text=label).pack(anchor="w")
            # Let the entry fill the width of this field's frame.
            ttk.Entry(cell, textvariable=variable).pack(fill="x", pady=(3, 0))
            # Let this grid column expand when the window gets wider.
            form.columnconfigure(column, weight=1)

        # Put action buttons in their own row below the form.
        buttons = ttk.Frame(page)
        buttons.pack(fill="x", pady=(10, 0))
        # Each button calls the named method when clicked.
        ttk.Button(buttons, text="Add product", command=self.add_product).pack(side="left")
        ttk.Button(buttons, text="Save changes", command=self.update_product).pack(
            side="left", padx=8
        )
        ttk.Button(buttons, text="Delete selected", command=self.delete_product).pack(
            side="left"
        )
        ttk.Button(buttons, text="Stock in", command=lambda: self.change_selected_stock("IN")).pack(
            side="left", padx=(18, 4)
        )
        ttk.Button(buttons, text="Stock out", command=lambda: self.change_selected_stock("OUT")).pack(
            side="left"
        )
        # Open a separate checkout window for recording one or more sale items.
        ttk.Button(buttons, text="Record sale", command=lambda: SaleWindow(self)).pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(buttons, text="Clear form", command=self.clear_form).pack(side="right")

    def _search_changed(self, *_):
        """Refresh the table whenever the user changes the search text."""
        # The asterisk accepts extra details Tkinter supplies with a change event.
        # We do not need those details, so reload based on the current field values.
        self.refresh_products()

    def refresh_products(self):
        """Show matching products and update the low-stock count."""
        # Remove old rows first so the table won't show duplicates after refreshing.
        for item in self.product_table.get_children():
            self.product_table.delete(item)
        # Read the current search phrase from the entry box.
        search = self.search_text.get()
        # The checkbox switches between the full list and just products needing attention.
        # A checked box uses the low-stock query; otherwise show all search matches.
        products = (Product.get_low_stock(search) if self.low_stock_only.get()
                    else Product.get_all(search))
        # Add one visible table row for each product returned from the database.
        for product in products:
            # A product is low when its quantity reaches or falls below its threshold.
            is_low = product.quantity <= product.low_stock_threshold
            # Use the database ID as the row ID so it can be fetched when selected.
            self.product_table.insert(
                "", "end", iid=str(product.product_id),
                values=(product.sku, product.name, f"{product.price:.2f}",
                        product.quantity, product.low_stock_threshold,
                        "LOW STOCK" if is_low else "In stock"),
                tags=("low_stock",) if is_low else (),
            )
        # Count all low-stock products, even when the table is currently filtered.
        low_count = len(Product.get_low_stock())
        # Display the count in the header above the table.
        self.low_stock_summary.configure(text=f"Low-stock products: {low_count}")

    def _product_selected(self, _event):
        """Copy the selected table row into the form for editing."""
        # Treeview returns a tuple of selected row IDs; we allow one selected row.
        selected = self.product_table.selection()
        if not selected:
            return
        # Convert the row ID to an integer and fetch the full product from SQLite.
        product = Product.get(int(selected[0]))
        if product is None:
            return
        # Remember the ID so Save, Delete, Stock in, and Stock out know the target.
        self.selected_product_id = product.product_id
        # Copy the product fields into the editable form; entries display text.
        self.sku_text.set(product.sku)
        self.name_text.set(product.name)
        self.price_text.set(str(product.price))
        self.quantity_text.set(str(product.quantity))
        self.threshold_text.set(str(product.low_stock_threshold))

    def _form_values(self):
        """Read and convert form text into values the Product class expects."""
        try:
            # Text boxes contain strings, so convert numbers before saving them.
            price = float(self.price_text.get())
            quantity = int(self.quantity_text.get())
            threshold = int(self.threshold_text.get())
        # int/float conversion fails when the user types text in a number field.
        except ValueError as error:
            raise ValueError("Price must be a number; quantities must be whole numbers.") from error
        # Return all fields together in the order expected by Product.create/update.
        return self.sku_text.get(), self.name_text.get(), price, quantity, threshold

    def add_product(self):
        """Validate the form and save a new product."""
        try:
            # Read the form and ask the Product class to validate and insert the row.
            sku, name, price, quantity, threshold = self._form_values()
            Product.create(sku, name, price, quantity, low_stock_threshold=threshold)
        # Show friendly errors for invalid values or database rules such as duplicate SKU.
        except (ValueError, sqlite3.IntegrityError) as error:
            messagebox.showerror("Could not add product", str(error), parent=self.root)
            return
        # On success, reset the form, reload the table, and confirm the save.
        self.clear_form()
        self.refresh_products()
        messagebox.showinfo("Product added", "The product was saved.", parent=self.root)

    def update_product(self):
        """Save changes to the product currently selected in the table."""
        # Editing requires a selected row so we know which database row to update.
        if self.selected_product_id is None:
            messagebox.showwarning("Select a product", "Choose a product in the table first.",
                                   parent=self.root)
            return
        try:
            # Get the original product and apply the values currently in the form.
            product = Product.get(self.selected_product_id)
            sku, name, price, quantity, threshold = self._form_values()
            product.update(sku, name, price, quantity, low_stock_threshold=threshold)
        # Keep the window open and show a message if validation or saving fails.
        except (ValueError, sqlite3.IntegrityError) as error:
            messagebox.showerror("Could not save changes", str(error), parent=self.root)
            return
        # Show the edited values in the table, then tell the user it worked.
        self.refresh_products()
        messagebox.showinfo("Changes saved", "The product was updated.", parent=self.root)

    def delete_product(self):
        """Ask before deleting the selected product."""
        # Do not try to delete when there is no selected product.
        if self.selected_product_id is None:
            messagebox.showwarning("Select a product", "Choose a product in the table first.",
                                   parent=self.root)
            return
        # Ask for confirmation because deleting a row is difficult to undo.
        if not messagebox.askyesno("Delete product", "Delete this product?", parent=self.root):
            return
        try:
            # Fetch the row and let Product.delete check for stock history first.
            product = Product.get(self.selected_product_id)
            product.delete()
        # Show why deletion failed, for example if the product has movement history.
        except (ValueError, sqlite3.IntegrityError) as error:
            messagebox.showerror("Could not delete product", str(error), parent=self.root)
            return
        # After deletion, clear the old details and remove the old table row.
        self.clear_form()
        self.refresh_products()

    def change_selected_stock(self, movement_type):
        """Ask how many units moved, then save the stock change and its history."""
        # Stock can only change for a product selected from the list.
        if self.selected_product_id is None:
            messagebox.showwarning("Select a product", "Choose a product in the table first.",
                                   parent=self.root)
            return

        # Pick a readable question based on which stock button the user clicked.
        action = "add to stock" if movement_type == "IN" else "remove from stock"
        # Canceling this dialog leaves the product unchanged.
        quantity = simpledialog.askinteger(
            "Stock movement", f"How many units do you want to {action}?",
            minvalue=1, parent=self.root,
        )
        # None means the user pressed Cancel; do not change anything.
        if quantity is None:
            return
        note = simpledialog.askstring(
            "Movement note", "Add an optional note for this stock movement:",
            parent=self.root,
        )
        # A canceled optional note is treated like an empty note.
        if note is None:
            note = ""

        try:
            # Inventory applies the stock rules and records the movement in SQLite.
            new_quantity = Inventory.change_stock(
                self.selected_product_id, quantity, movement_type, note
            )
        # For example, stock-out may fail if the requested amount is unavailable.
        except ValueError as error:
            messagebox.showerror("Stock was not changed", str(error), parent=self.root)
            return

        # Refresh the table so the new balance and low-stock status appear immediately.
        self.refresh_products()
        messagebox.showinfo(
            "Stock updated", f"The new available quantity is {new_quantity}.",
            parent=self.root,
        )

    def clear_form(self):
        """Clear the fields and forget which product was selected."""
        # Forget the selected database ID so the next action won't edit the old row.
        self.selected_product_id = None
        # Remove the highlight from the table selection.
        self.product_table.selection_remove(self.product_table.selection())
        # Empty text fields and restore sensible numeric defaults.
        self.sku_text.set("")
        self.name_text.set("")
        self.price_text.set("")
        self.quantity_text.set("0")
        self.threshold_text.set("5")

    def run(self):
        # Tkinter waits here for typing, button clicks, and window events.
        self.root.mainloop()
