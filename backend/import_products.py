
import pandas as pd
import mysql.connector

df = pd.read_csv("../data/products.csv")

print("CSV loaded successfully")
print(df.head())

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="6618",
    database="warehouse_twin"
)

cursor = db.cursor()

query = """
INSERT INTO products (
    product_id,
    product_name,
    brand,
    category,
    sub_category,
    price,
    rating,
    review_count,
    stock_status,
    tags,
    description
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df.iterrows():

    values = (
        int(row["product_id"]),
        row["product_name"],
        row["brand"],
        row["category"],
        row["sub_category"],
        row["price"],
        row["rating"],
        row["review_count"],
        row["stock_status"],
        row["tags"],
        row["description"]
    )

    cursor.execute(query, values)

db.commit()

cursor.close()
db.close()

print("Products inserted successfully")