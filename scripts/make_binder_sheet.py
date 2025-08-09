import os
import json
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image

image_folder = "images"
output_folder = "binder_sheets"
meta_file = "card_meta.json"

os.makedirs(output_folder, exist_ok=True)

with open(meta_file, "r", encoding="utf-8") as mf:
    meta_data = json.load(mf)

pdf_path = os.path.join(output_folder, "Destined_Rivals_Binder.pdf")
c = canvas.Canvas(pdf_path, pagesize=letter)

x, y = 0.5 * inch, 10 * inch
count = 0

for img_file in sorted(os.listdir(image_folder)):
    if img_file.lower().endswith((".jpg", ".png")):
        product_id = os.path.splitext(img_file)[0]
        card_info = meta_data.get(product_id, {})
        card_name = card_info.get("name", "Unknown")
        price = card_info.get("price", "N/A")

        try:
            # Draw image
            with Image.open(os.path.join(image_folder, img_file)) as img:
                img.thumbnail((2.5 * inch, 3.5 * inch))
                c.drawImage(
                    os.path.join(image_folder, img_file),
                    x, y,
                    width=2.5 * inch,
                    height=3.5 * inch
                )

            # Wrap card name to max width under image
            wrapped_name = textwrap.wrap(card_name, width=20)  # adjust width for font size
            text_y = y - 0.2 * inch
            c.setFont("Helvetica-Bold", 8)
            for line in wrapped_name:
                c.drawString(x, text_y, line)
                text_y -= 0.12 * inch  # space between lines

            # Draw price below the name
            c.setFont("Helvetica", 7)
            c.drawString(x, text_y - 0.05 * inch, f"Price: ${price}"*_
