# Project requirements

## Purpose

Build a desktop application that helps small shops keep accurate product, stock, and sales records. It should make it easier to see what is available, record changes, and spot items that need restocking.

## Users

- Owners and staff at retail shops
- Mini-mart operators
- Small distributors

## Functional requirements

1. The user can register a product with a unique SKU, name, price, quantity, and category.
2. The user can view and search the product list.
3. The user can edit and remove products.
4. The user can record stock coming in and stock going out.
5. The application keeps a history of stock movements.
6. The user can record a sale; the application reduces stock automatically.
7. The application prevents a sale when the requested quantity exceeds available stock.
8. The application identifies products whose quantity is at or below their low-stock threshold.
9. The user can view daily and monthly sales summaries.
10. The user can export product and sales records to CSV files.
11. Product, movement, and sales records persist in a relational SQLite database after the application closes.

## Validation requirements

- SKU must be present and unique.
- Product name and category must not be blank.
- Price must be a valid non-negative amount.
- Quantities must be whole numbers; stock movement quantities must be greater than zero.
- Stock must not become negative.
- A sale must not exceed the current available stock.

## Quality requirements

- The application runs locally on a desktop using Python.
- The interface should be understandable to a first-time small-shop user.
- Database updates that affect stock and a movement or sale record must be kept consistent.
- The project should include a README, `requirements.txt`, `.gitignore`, and visible Git history.

## Technology

- Python and object-oriented programming
- Tkinter for the desktop interface
- SQLite for relational data storage
- SQL aggregation for sales summaries
- CSV for exports
- Git and GitHub for version history and submission

## Out of scope for the first version

- Online accounts or cloud synchronization
- Multiple store locations
- Barcode scanning or payment processing
