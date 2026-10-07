"""Entry point for My Project Dominion."""

from database import initialize_database


def main():
    category_id = initialize_database()
    print("My Project Dominion database is ready.")
    print(f"Default category ID: {category_id}")
    print("Product and inventory CRUD are available through the models package.")


if __name__ == "__main__":
    main()
