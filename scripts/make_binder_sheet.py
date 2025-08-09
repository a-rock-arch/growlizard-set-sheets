import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image

image_folder = "images"
output_folder = "binder_sheets"
os.makedirs(output_folder, exist_ok=True)

pdf_path = os.path.join(output_folder, "Destined_Rivals_Binder.pdf")
c = canvas.Canvas(pdf_path, pagesize=letter)

x, y = 0.5 * inch, 10 * inch
count = 0

for img_file in sorted(os.listdir(image_folder)):
    if img_file.lower().endswith((".jpg", ".png")):
        img_path = os.path.join(image_folder, img_file)

        try:
            with Image.open(img_path) as img:
                img.thumbnail((2.5 * inch, 3.5 * inch))
                c.drawImage(img_path, x, y, width=2.5 * inch, height=3.5 * inch)

            x += 2.7 * inch
            count += 1
            if count % 3 == 0:
                x = 0.5 * inch
                y -= 3.7 * inch
            if count % 9 == 0:
                c.showPage()
                x, y = 0.5 * inch, 10 * inch

        except Exception as e:
            print(f"Could not process {img_file}: {e}")

c.save()
