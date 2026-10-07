# Database design

SQLite stores the application's records on the shop computer. The design separates products, categories, stock movements, sales, and sale line items so the same product details do not have to be copied into every record.

## Tables

### categories

- `category_id` — primary key
- `name` — required unique category name

### products

- `product_id` — primary key
- `sku` — required unique stock keeping unit
- `name` — required product name
- `price` — non-negative unit price
- `quantity` — current on-hand whole number, zero or greater
- `category_id` — category foreign key
- `low_stock_threshold` — quantity at which the product should be flagged
- `created_at` — creation timestamp

### inventory_movements

- `movement_id` — primary key
- `product_id` — product foreign key
- `movement_type` — `IN`, `OUT`, or (later) `SALE`
- `quantity` — positive whole number moved
- `note` — optional reason or explanation
- `created_at` — movement timestamp

### sales (later milestone)

- `sale_id` — primary key
- `sold_at` — sale timestamp
- `total` — total sale amount

### sale_items (later milestone)

- `sale_item_id` — primary key
- `sale_id` — sale foreign key
- `product_id` — product foreign key
- `quantity` — number of units sold
- `unit_price` — price captured at sale time
- `line_total` — quantity multiplied by unit price

## Relationships

- One category can have many products.
- One product can have many inventory movements.
- One sale can contain many sale items.
- One product can appear in many sale items.

## Rules

- A product SKU is unique.
- Foreign keys are enabled for each database connection.
- Product price and quantities cannot be negative.
- Stock movement quantity must be positive.
- Updating stock and inserting its movement record happen together in a database transaction.
- Sale and sale-item tables are reserved for the October 10 sales milestone.

## October 7 implementation

The first schema creates `categories`, `products`, and `inventory_movements`. The sales tables are design-only until their scheduled milestone. `products.quantity` gives a quick current balance; `inventory_movements` provides the change history.
