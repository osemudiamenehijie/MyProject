# My Project Dominion

Small Business Inventory & Sales Tracker

## Project overview

My Project Dominion is a beginner-friendly desktop application for small retail shops, mini-marts, and small distributors. It will replace handwritten stock records with a searchable product list, recorded stock movements, sales, low-stock warnings, sales summaries, and CSV exports.

The project uses Python, Tkinter, and SQLite. Tkinter and SQLite are included with Python, so the first version needs no third-party packages.

## Planned features

- Register and manage products with a SKU, name, price, quantity, category, and low-stock threshold.
- Record stock coming in and going out.
- Record sales and reduce stock automatically, while preventing sales above available stock.
- Search products and identify items at or below their low-stock threshold.
- Summarize sales by day and month.
- Export product and sales data to CSV.

## Project progress

- October 6: requirements, business requirements, user stories, and database design.
- October 7: product and inventory classes, SQLite schema, and CRUD operations.
- October 8: product management window with live search by SKU or name.
- October 9: stock-in/stock-out controls, movement notes, and low-stock filtering.
- October 10–14: remaining milestones are listed in `docs/project_schedule.md`.

## Run

From this folder, run:

```text
python main.py
```

The database is created automatically at `database/dominion.db` when the application starts.

## Current scope

The current implementation covers product management, product search, stock-in/stock-out records, and a low-stock view. Sales, reports, and CSV export are later milestones.

## Requirements and design

See `docs/requirements.md`, `docs/business_requirements.md`, `docs/user_stories.md`, and `docs/database_design.md`.

## Testing

The brief calls for checks covering available stock, insufficient-stock prevention, valid prices and quantities, stock updates, reports, and database persistence. Those checks are planned for the October 12 milestone.
