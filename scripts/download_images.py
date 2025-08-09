import csv
import os
import requests
import json

csv_file = "data.csv"
image_folder = "images"
meta_file = "card_meta.json"

os.makedirs(image_folder, exist_ok=True)

meta_data = {}

with open(csv_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        image_url = row.get("imageUrl")
        card_name = row.get("productName")
        product_id = row.get("productId")
        price = row.get("marketPrice", "N/A")

        meta_data[product_id] = {
            "name": card_name,
            "price": price
        }

        if image_url:
            filename = f"{product_id}.jpg"
            filepath = os.path.join(image_folder, filename)

            if not os.path.exists(filepath):
                print(f"Downloading {card_name}...")
                try:
                    r = requests.get(image_url, stream=True, timeout=10)
                    if r.status_code == 200:
                        with open(filepath, "wb") as img_file:
                            img_file.write(r.content)
                except Exception as e:
                    print(f"Error downloading {card_name}: {e}")

# Save metadata
with open(meta_file, "w", encoding="utf-8") as mf:
    json.dump(meta_data, mf, indent=2)
