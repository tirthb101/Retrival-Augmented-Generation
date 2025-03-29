import mysql.connector
from dotenv import load_dotenv
import os
from EngToSql import getQueryResult


load_dotenv()

def create_complex_database_with_data():
    """
    Creates a complex database, tables, and inserts sample data.
    """
    try:
        mydb = mysql.connector.connect(
            host=os.getenv("SQLHOST"),
            user=os.getenv("SQLUSER"),
            password=os.getenv("PASSWORD")
        )
        mycursor = mydb.cursor()

        
        database_name = os.getenv("DB")

        mycursor.execute(f"drop database {database_name};")
        mycursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        mycursor.execute(f"USE {database_name}")

        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customerid INT AUTO_INCREMENT PRIMARY KEY,
                firstname VARCHAR(255) NOT NULL,
                lastname VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE,
                phone VARCHAR(20),
                address VARCHAR(255),
                city VARCHAR(100),
                state VARCHAR(100),
                zipcode VARCHAR(20)
            )
        """)

        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                productid INT AUTO_INCREMENT PRIMARY KEY,
                productname VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                stockquantity INT
            )
        """)

        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                orderid INT AUTO_INCREMENT PRIMARY KEY,
                customerid INT,
                orderdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                totalamount DECIMAL(10, 2),
                FOREIGN KEY (customerid) REFERENCES customers(customerid)
            )
        """)

        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS orderitems (
                orderitemid INT AUTO_INCREMENT PRIMARY KEY,
                orderid INT,
                productid INT,
                quantity INT,
                unitprice DECIMAL(10, 2),
                FOREIGN KEY (orderid) REFERENCES orders(orderid),
                FOREIGN KEY (productid) REFERENCES products(productid)
            )
        """)

        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                categoryid INT AUTO_INCREMENT PRIMARY KEY,
                categoryname VARCHAR(255) NOT NULL,
                description TEXT
            )
        """)

        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS productcategories (
                productid INT,
                categoryid INT,
                PRIMARY KEY (productid, categoryid),
                FOREIGN KEY (productid) REFERENCES products(productid),
                FOREIGN KEY (categoryid) REFERENCES categories(categoryid)
            )
        """)

        mycursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                reviewid INT AUTO_INCREMENT PRIMARY KEY,
                productid INT,
                customerid INT,
                rating INT,
                comment TEXT,
                reviewdate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (productid) REFERENCES products(productid),
                FOREIGN KEY (customerid) REFERENCES customers(customerid)
            )
        """)
        # --- Insert Sample Data ---

        customers_data = [
            ("Alice", "Smith", "alice@example.com", "123-456-7890", "123 Main St", "Anytown", "CA", "90210"),
            ("Bob", "Johnson", "bob@example.com", "987-654-3210", "456 Oak Ave", "Sometown", "NY", "10001"),
            ("Charlie", "Williams", "charlie@example.com", "555-123-4567", "789 Pine Ln", "Othertown", "TX", "75000"),
        ]

        products_data = [
            ("Laptop", "Powerful laptop", 1200.00, 100),
            ("Mouse", "Wireless mouse", 25.00, 500),
            ("Keyboard", "Ergonomic keyboard", 75.00, 200),
            ("Monitor", "4k Monitor", 300.00, 50)
        ]

        orders_data = [
            (1, 1200.00),  # Alice's order
            (2, 25.00),    # Bob's order
            (3, 375.00), # Charlie's order
        ]

        order_items_data = [
            (1, 1, 1, 1200.00), # order 1, product 1, qty 1, price 1200
            (2, 2, 1, 25.00), # order 2, product 2, qty 1, price 25
            (3, 3, 5, 75.00), # order 3, product 3, qty 5, price 75
        ]

        categories_data = [
            ("Electronics", "Electronic devices"),
            ("Peripherals", "Computer peripherals"),
        ]

        product_categories_data = [
            (1, 1),  # Laptop in Electronics
            (2, 2),  # Mouse in Peripherals
            (3, 2),  # Keyboard in Peripherals
            (4, 1), # Monitor in Electronics.
        ]

        reviews_data = [
            (1, 1, 5, "Great laptop!", "2023-10-27 10:00:00"),
            (2, 1, 4, "Good mouse", "2023-10-28 12:00:00"),
            (3, 3, 3, "Decent keyboard", "2023-10-29 14:00:00"),
        ]

        for data in customers_data:
            mycursor.execute("INSERT INTO customers (firstname, lastname, email, phone, address, city, state, zipcode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", data)

        for data in products_data:
            mycursor.execute("INSERT INTO products (productname, description, price, stockquantity) VALUES (%s, %s, %s, %s)", data)

        for data in orders_data:
            mycursor.execute("INSERT INTO orders (customerid, totalamount) VALUES (%s, %s)", data)

        for data in order_items_data:
            mycursor.execute("INSERT INTO orderitems (orderid, productid, quantity, unitprice) VALUES (%s, %s, %s, %s)", data)

        for data in categories_data:
            mycursor.execute("INSERT INTO categories (categoryname, description) VALUES (%s, %s)", data)

        for data in product_categories_data:
            mycursor.execute("INSERT INTO productcategories (productid, categoryid) VALUES (%s, %s)", data)

        for data in reviews_data:
            mycursor.execute("INSERT INTO reviews (productid, customerid, rating, comment, reviewdate) VALUES (%s, %s, %s, %s, %s)", data)

        mydb.commit()  # Commit the changes

        print(f"Database '{database_name}' and tables created with sample data.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'mydb' in locals() and mydb.is_connected():
            mycursor.close()
            mydb.close()
            print("MySQL connection closed.")

def generateSchema():
    with open("schema.txt", "w") as f:
        for table in getQueryResult("show tables;"):
            tablename = table[0]
            f.write(f"{getQueryResult(f"show create table {tablename};")}\n")
        


if __name__ == "__main__":
    # create_complex_database_with_data()
    generateSchema()
    pass