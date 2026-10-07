# Business requirements

## Problem

Small shops can lose track of stock, sales, and items that need restocking when they rely on handwritten records or scattered notes. Mistakes can lead to inaccurate stock counts, missed sales, or running out of popular products.

## Business objective

Provide a simple desktop tool that lets a shop record products, stock changes, and sales in one place. The tool should make current stock visible, warn when an item is low, and provide basic sales summaries that help the owner review activity.

## Stakeholders

- **Shop owner:** needs reliable stock information and sales summaries.
- **Shop staff:** need a quick way to look up products and record stock changes or sales.
- **Instructor/reviewer:** needs to see a working, documented software project and its development history.

## Business needs

| ID | Need | How the application supports it |
| --- | --- | --- |
| BR-1 | Keep a consistent product list | Store each product with a unique SKU and its details. |
| BR-2 | Know the available quantity | Update stock when stock comes in, stock goes out, or a sale is recorded. |
| BR-3 | Understand why stock changed | Keep a dated record of stock movements. |
| BR-4 | Avoid selling more than is available | Check the available quantity before completing a sale. |
| BR-5 | Notice items that need restocking | Compare each product's quantity with its low-stock threshold. |
| BR-6 | Review sales activity | Provide daily and monthly totals. |
| BR-7 | Reuse or share records | Export product and sales data to CSV. |

## Success measures

- A user can add, find, update, and remove a product.
- Stock changes are reflected in the product's available quantity and have a movement record.
- Invalid prices, quantities, and sales are rejected with a clear message.
- Data is still available after closing and reopening the application.
- The completed project demonstrates the brief's workflow: product creation → stock-in → sale → stock update → report.
