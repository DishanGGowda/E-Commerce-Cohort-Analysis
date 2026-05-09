import pandas as pd, sqlite3

conn = sqlite3.connect("data/ecommerce.db")
df = pd.read_sql("SELECT * FROM sales_data", conn)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])

print(f"Before cleaning: {len(df):,} rows")

# Remove cancellations (InvoiceNo starts with 'C')
df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]

# Remove zero/negative quantity and price
df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]

print(f"After cleaning:  {len(df):,} rows")

# Save cleaned version
df.to_sql("sales_clean", conn, if_exists="replace", index=False)
df.to_csv("data/processed/sales_clean.csv", index=False)
conn.close()
print("Cleaned data saved.")