"""Simple product management window built with Tkinter."""

import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from models.inventory import Inventory
from models.product import Product


class ProductManagementApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("My Project Dominion - Products")
        self.root.geometry("980x650")
        self.root.minsize(800, 560)
        self.selected_product_id = None

        self._build_screen()
        self.refresh_products()

    def _build_screen(self):
        """Create the search bar, product table, and product form."""
        page = ttk.Frame(self.root, padding=16)
        page.pack(fill="both", expand=True)

        header = ttk.Frame(page)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="Product Management", font=("Segoe UI", 18, "bold")).pack(
            side="left"
        )
        self.low_stock_summary = ttk.Label(header, text="")
        self.low_stock_summary.pack(side="right")

        search_row = ttk.Frame(page)
        search_row.pack(fill="x", pady=(0, 10))
        ttk.Label(search_row, text="Search by SKU or name:").pack(side="left")
        self.search_text = tk.StringVar()
        search_box = ttk.Entry(search_row, textvariable=self.search_text, width=36)
        search_box.pack(side="left", padx=(8, 0))
        self.search_text.trace_add("write", self._search_changed)
        self.low_stock_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            search_row, text="Show low-stock only", variable=self.low_stock_only,
            command=self.refresh_products,
        ).pack(side="left", padx=(18, 0))

        table_frame = ttk.Frame(page)
        table_frame.pack(fill="both", expand=True)
        columns = ("sku", "name", "price", "quantity", "threshold", "status")
        self.product_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        headings = {
            "sku": ("SKU", 120), "name": ("Product name", 230),
            "price": ("Price", 100), "quantity": ("Quantity", 100),
            "threshold": ("Low-stock level", 130),
            "status": ("Stock status", 120),
        }
        for column, (label, width) in headings.items():
            self.product_table.heading(column, text=label)
            self.product_table.column(column, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(
            table_frame, orient="vertical", command=self.product_table.yview
        )
        self.product_table.configure(yscrollcommand=scrollbar.set)
        self.product_table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # A colored status makes low stock visible without opening another screen.
        self.product_table.tag_configure("low_stock", foreground="#b42318")
        self.product_table.bind("<<TreeviewSelect>>", self._product_selected)

        form = ttk.LabelFrame(page, text="Product details", padding=10)
        form.pack(fill="x", pady=(12, 0))
        self.sku_text = tk.StringVar()
        self.name_text = tk.StringVar()
        self.price_text = tk.StringVar()
        self.quantity_text = tk.StringVar(value="0")
        self.threshold_text = tk.StringVar(value="5")

        fields = [
            ("SKU", self.sku_text), ("Name", self.name_text),
            ("Price", self.price_text), ("Quantity", self.quantity_text),
            ("Low-stock level", self.threshold_text),
        ]
        for index, (label, variable) in enumerate(fields):
            row, column = divmod(index, 3)
            cell = ttk.Frame(form)
            cell.grid(row=row, column=column, sticky="ew", padx=6, pady=5)
            ttk.Label(cell, text=label).pack(anchor="w")
            ttk.Entry(cell, textvariable=variable).pack(fill="x", pady=(3, 0))
            form.columnconfigure(column, weight=1)

        buttons = ttk.Frame(page)
        buttons.pack(fill="x", pady=(10, 0))
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
        ttk.Button(buttons, text="Clear form", command=self.clear_form).pack(side="right")

    def _search_changed(self, *_):
        """Refresh the table whenever the user changes the search text."""
        self.refresh_products()

    def refresh_products(self):
        """Show matching products and update the low-stock count."""
        for item in self.product_table.get_children():
            self.product_table.delete(item)
        search = self.search_text.get()
        # The checkbox switches between the full list and just products needing attention.
        products = (Product.get_low_stock(search) if self.low_stock_only.get()
                    else Product.get_all(search))
        for product in products:
            is_low = product.quantity <= product.low_stock_threshold
            self.product_table.insert(
                "", "end", iid=str(product.product_id),
                values=(product.sku, product.name, f"{product.price:.2f}",
                        product.quantity, product.low_stock_threshold,
                        "LOW STOCK" if is_low else "In stock"),
                tags=("low_stock",) if is_low else (),
            )
        low_count = len(Product.get_low_stock())
        self.low_stock_summary.configure(text=f"Low-stock products: {low_count}")

    def _product_selected(self, _event):
        """Copy the selected table row into the form for editing."""
        selected = self.product_table.selection()
        if not selected:
            return
        product = Product.get(int(selected[0]))
        if product is None:
            return
        self.selected_product_id = product.product_id
        self.sku_text.set(product.sku)
        self.name_text.set(product.name)
        self.price_text.set(str(product.price))
        self.quantity_text.set(str(product.quantity))
        self.threshold_text.set(str(product.low_stock_threshold))

    def _form_values(self):
        """Read and convert form text into values the Product class expects."""
        try:
            price = float(self.price_text.get())
            quantity = int(self.quantity_text.get())
            threshold = int(self.threshold_text.get())
        except ValueError as error:
            raise ValueError("Price must be a number; quantities must be whole numbers.") from error
        return self.sku_text.get(), self.name_text.get(), price, quantity, threshold

    def add_product(self):
        """Validate the form and save a new product."""
        try:
            sku, name, price, quantity, threshold = self._form_values()
            Product.create(sku, name, price, quantity, low_stock_threshold=threshold)
        except (ValueError, sqlite3.IntegrityError) as error:
            messagebox.showerror("Could not add product", str(error), parent=self.root)
            return
        self.clear_form()
        self.refresh_products()
        messagebox.showinfo("Product added", "The product was saved.", parent=self.root)

    def update_product(self):
        """Save changes to the product currently selected in the table."""
        if self.selected_product_id is None:
            messagebox.showwarning("Select a product", "Choose a product in the table first.",
                                   parent=self.root)
            return
        try:
            product = Product.get(self.selected_product_id)
            sku, name, price, quantity, threshold = self._form_values()
            product.update(sku, name, price, quantity, low_stock_threshold=threshold)
        except (ValueError, sqlite3.IntegrityError) as error:
            messagebox.showerror("Could not save changes", str(error), parent=self.root)
            return
        self.refresh_products()
        messagebox.showinfo("Changes saved", "The product was updated.", parent=self.root)

    def delete_product(self):
        """Ask before deleting the selected product."""
        if self.selected_product_id is None:
            messagebox.showwarning("Select a product", "Choose a product in the table first.",
                                   parent=self.root)
            return
        if not messagebox.askyesno("Delete product", "Delete this product?", parent=self.root):
            return
        try:
            product = Product.get(self.selected_product_id)
            product.delete()
        except (ValueError, sqlite3.IntegrityError) as error:
            messagebox.showerror("Could not delete product", str(error), parent=self.root)
            return
        self.clear_form()
        self.refresh_products()

    def change_selected_stock(self, movement_type):
        """Ask how many units moved, then save the stock change and its history."""
        if self.selected_product_id is None:
            messagebox.showwarning("Select a product", "Choose a product in the table first.",
                                   parent=self.root)
            return

        action = "add to stock" if movement_type == "IN" else "remove from stock"
        # Canceling this dialog leaves the product unchanged.
        quantity = simpledialog.askinteger(
            "Stock movement", f"How many units do you want to {action}?",
            minvalue=1, parent=self.root,
        )
        if quantity is None:
            return
        note = simpledialog.askstring(
            "Movement note", "Add an optional note for this stock movement:",
            parent=self.root,
        )
        if note is None:
            note = ""

        try:
            new_quantity = Inventory.change_stock(
                self.selected_product_id, quantity, movement_type, note
            )
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
        self.selected_product_id = None
        self.product_table.selection_remove(self.product_table.selection())
        self.sku_text.set("")
        self.name_text.set("")
        self.price_text.set("")
        self.quantity_text.set("0")
        self.threshold_text.set("5")

    def run(self):
        self.root.mainloop()
