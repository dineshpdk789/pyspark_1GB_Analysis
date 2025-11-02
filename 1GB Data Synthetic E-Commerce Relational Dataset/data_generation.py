import importlib
import subprocess
import sys
import random
from pathlib import Path
import argparse


def check_package(package_name, import_name=None):
    """
    check and install the package if it is not exisits (to avoid ImportError)
        package_name: name to install with pip
        import_name: name to import (if different from package_name)
    """
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
    except ImportError:
        print(f'Installing {package_name}...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', package_name])
        print(f'\nPlease restart the script after {package_name} installation.\n')
        sys.exit(0)

# Customers Generator Function
def generate_customers(n, pd, fake):
    """returns n rows of customers' data as dataframe"""
    return pd.DataFrame([{
        'customer_id': i,
        'name': fake.name(),
        'email': fake.email(),
        'gender': random.choice(['Male', 'Female', 'Other']),
        'signup_date': fake.date_between(start_date='-5y', end_date='today'),
        'country': fake.country()
    } for i in range(1, n + 1)])

# Products Generator Function
def generate_products(n, pd, fake):
    """returns n rows of products' data as dataframe"""
    categories = ['Electronics', 'Books', 'Clothing', 'Toys', 'Home', 'Beauty']
    brands = ['BrandA', 'BrandB', 'BrandC', 'BrandD']
    return pd.DataFrame([{
        'product_id': i,
        'product_name': fake.word().capitalize() + ' ' + fake.word().capitalize(),
        'category': random.choice(categories),
        'price': round(random.uniform(5.0, 500.0), 2),
        'stock_quantity': random.randint(0, 1000),
        'brand': random.choice(brands)
    } for i in range(1, n + 1)])

# Orders Generator Function
def generate_orders(n, customer_ids, pd, fake):
    """returns n rows of orders' data as dataframe"""
    return pd.DataFrame([{
        'order_id': i,
        'customer_id': random.choice(customer_ids),
        'order_date': fake.date_between(start_date='-4y', end_date='today'),
        'total_amount': 0.0,  # Will update after generating items
        'payment_method': random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Cash']),
        'shipping_country': fake.country()
    } for i in range(1, n + 1)])

# Order_Items Generator Function
def generate_order_items(n, order_ids, product_ids, product_df, pd):
    """returns n rows of order items' data as dataframe"""
    items = []
    for i in range(1, n + 1):
        order_id = random.choice(order_ids)
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 5)
        unit_price = float(product_df.loc[product_id - 1, 'price'])
        items.append({
            'order_item_id': i,
            'order_id': order_id,
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price
        })
    return pd.DataFrame(items)

# Product_Reviews Generator Function
def generate_reviews(n, customer_ids, product_ids, pd, fake):
    """returns n rows of reviews' data as dataframe"""
    return pd.DataFrame([{
        'review_id': i,
        'product_id': random.choice(product_ids),
        'customer_id': random.choice(customer_ids),
        'rating': random.randint(1, 5),
        'review_text': fake.sentence(nb_words=10),
        'review_date': fake.date_between(start_date='-4y', end_date='today')
    } for i in range(1, n + 1)])



def main(customers_row_count, products_row_count, orders_row_count, 
         order_items_row_count, reviews_row_count, path):

    # check and import modules
    check_package('Faker', 'faker')
    from faker import Faker
    check_package('pandas')
    import pandas as pd
    import numpy as np
    check_package('pyarrow')
    import pyarrow
    
    # Initializa and set seeds
    fake = Faker()
    Faker.seed(42)
    random.seed(42)
    np.random.seed(42)

    # Generate the 5 datasets
    customers_df = generate_customers(customers_row_count, pd, fake)
    print('customers generated')

    products_df = generate_products(products_row_count, pd, fake)
    print('products generated')

    orders_df = generate_orders(orders_row_count, customers_df['customer_id'].tolist(), pd, fake)
    print('orders generated')

    order_items_df = generate_order_items(order_items_row_count, orders_df['order_id'].tolist(), products_df['product_id'].tolist(), products_df, pd)
    print('order items generated')

    reviews_df = generate_reviews(reviews_row_count, customers_df['customer_id'].tolist(), products_df['product_id'].tolist(), pd, fake)
    print('reviews generated')

    # Calculate and update order total amounts
    order_totals = order_items_df.assign(total=lambda df: df['quantity'] * df['unit_price']).groupby('order_id')['total'].sum()
    orders_df['total_amount'] = orders_df['order_id'].map(order_totals).fillna(0).round(2)

    # create csv and parquet folders inside path
    Path(f'{path}/csv').mkdir(parents=True, exist_ok=True)
    Path(f'{path}/parquet').mkdir(parents=True, exist_ok=True)

    # Save to csv
    customers_df.to_csv(f'{path}/csv/customers.csv', index=False)
    products_df.to_csv(f'{path}/csv/products.csv', index=False)
    orders_df.to_csv(f'{path}/csv/orders.csv', index=False)
    order_items_df.to_csv(f'{path}/csv/order_items.csv', index=False)
    reviews_df.to_csv(f'{path}/csv/product_reviews.csv', index=False)
    print('CSV saved')

    # Save to parquet
    customers_df.to_parquet(f'{path}/parquet/customers.parquet', index=False)
    products_df.to_parquet(f'{path}/parquet/products.parquet', index=False)
    orders_df.to_parquet(f'{path}/parquet/orders.parquet', index=False)
    order_items_df.to_parquet(f'{path}/parquet/order_items.parquet', index=False)
    reviews_df.to_parquet(f'{path}/parquet/product_reviews.parquet', index=False)
    print('Parquet saved')

    print('finished :)')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic e-commerce datasets.")
    parser.add_argument("--customers", type=int, default=1000000, help="Number of customers")
    parser.add_argument("--products", type=int, default=10000, help="Number of products")
    parser.add_argument("--orders", type=int, default=4000000, help="Number of orders")
    parser.add_argument("--order-items", type=int, default=10000000, help="Number of order items")
    parser.add_argument("--reviews", type=int, default=2000000, help="Number of product reviews")
    parser.add_argument("--path", type=Path, default=Path('.'), help="Output directory")
    parser.add_argument("--quick", action="store_true", help="Generate a small quick sample dataset")


    args = parser.parse_args()

    if args.quick:
        print("Quick mode enabled: using small dataset sizes.")
        args.customers = 100
        args.products = 10
        args.orders = 200
        args.order_items = 500
        args.reviews = 100

    main(
        customers_row_count=args.customers,
        products_row_count=args.products,
        orders_row_count=args.orders,
        order_items_row_count=args.order_items,
        reviews_row_count=args.reviews,
        path=args.path
    )