#!/usr/bin/env python3
"""
generate_pdf.py
Fetches TCGCSV daily CSV (from a private URL), filters for a set (Destined Rivals),
and creates a printable PDF of card placeholders (3 cols x 6 rows per page).
Uses env var TCGCSV_URL (required) and optional SET_NAME / OUTPUT_PATH.
"""

import os
import io
import sys
import re
import requests
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Config from env
TCGCSV_URL = os.environ.get("TCGCSV_URL")
SET_NAME = os.environ.get("SET_NAME", "Destined Rivals")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "outputs/destined_rivals_placeholders.pdf")

if not TCGCSV_URL:
    print("Error: set the TCGCSV_URL environment variable (your private CSV link).")
    sys.exit(1)

def fetch_csv_text(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    # decode robustly
    text = r.content.decode('utf-8', errors='replace')
    return text

def find_column(df, possible_names):
    # case-insensitive strip match
    lc_map = {c.lower().strip(): c for c in df.columns}
    for name in possible_names:
        key = name.lower().strip()
        if key in lc_map:
            return lc_map[key]
    return None

def load_and_filter(csv_text, set_name):
    df = pd.read_csv(io.StringIO(csv_text))
    # Identify columns
    game_col = find_column(df, ["Game", "game", "categoryId"])
    set_col = find_column(df, ["Set Name", "Set", "set name", "groupId"])
    name_col = find_column(df, ["name", "Name", "Card name"])
    num_col = find_column(df, ["extNumber", "Card Number", "number"])
    price_col = find_column(df, ["marketPrice", "MarketPrice", "market price", "market_price", "Market"])
    image_col = find_column(df, ["imageUrl"])

    if not (game_col and set_col and name_col):
        print("CSV missing expected columns. Found columns:", df.columns.tolist())
        raise SystemExit("CSV does not contain required columns (Game / Set Name / Card Name)")

    # Normalize strings and filter
    df[game_col] = df[game_col].astype(str).str.strip()
    df[set_col] = df[set_col].astype(str).str.strip()
# Filter Pokemon and set (case-insensitive)
    df_filtered = df[df[game_col].str.lower().str.contains("pokemon")]
    df_filtered = df_filtered[df_filtered[set_col].str.lower() == set_name.lower()]

    # Build clean output columns
    df_out = pd.DataFrame()
    df_out["card_name"] = df_filtered[name_col].astype(str)
    df_out["card_number"] = df_filtered[num_col].astype(str) if num_col else ""
    if price_col:
        df_out["market_price_raw"] = df_filtered[price_col].astype(str)
    else:
        df_out["market_price_raw"] = ""
    return df_out

def parse_price(raw):
    if not raw or pd.isna(raw):
        return None
    # remove $ and commas, keep digits and dot
    cleaned = re.sub(r"[^\d\.]", "", str(raw))
    try:
        return float(cleaned) if cleaned else None
    except:
        return None

def draw_pdf(df, set_name, out_path):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    width, height = letter  # points: 612 x 792
    c = canvas.Canvas(out_path, pagesize=letter)

    margin = 0.5 * inch
    cols = 3
    rows = 6
    card_w = (width - 2*margin) / cols
    card_h = (height - 2*margin) / rows

    # header on first page
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - margin/2, f"{set_name} - Printable Binder Placeholder Sheet")
    c.setFont("Helvetica", 8)

    usable_x0 = margin
    usable_y0 = height - margin

    items = df.to_dict("records")
    if not items:
        print("No items to render.")
        return

    for i, item in enumerate(items):
        page_idx = i // (cols*rows)
        pos = i % (cols*rows)
        row = pos // cols
        col = pos % cols

        x = usable_x0 + col * card_w
        y_top = usable_y0 - page_idx * height - row * card_h  # adjust for page_idx as showPage resets coords

        # Important: when creating multiple pages, we call showPage() at end of page; simpler approach below:
        # Instead, compute local coords for each page and use showPage at page boundaries.

    # simpler: loop pages
    per_page = cols*rows
    total_pages = (len(items) + per_page - 1) // per_page
    item_idx = 0
    for p in range(total_pages):
        # Header on each page
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, height - margin/2, f"{set_name} - Printable Binder Placeholder Sheet")
        # Draw each card for this page
        for pos in range(per_page):
            if item_idx >= len(items):
                break
            item = items[item_idx]
            row = pos // cols
            col = pos % cols
            x = margin + col * card_w
            y = height - margin - (row+1) * card_h

            pad = 8
            # card outer
            c.roundRect(x+pad, y+pad, card_w-2*pad, card_h-2*pad, 6, stroke=1, fill=0)
            # image placeholder (top ~55% of card)
            img_h = (card_h - 3*pad) * 0.55
            img_w = card_w - 4*pad
            img_x = x + 2*pad
            img_y = y + card_h - 2*pad - img_h
            c.rect(img_x, img_y, img_w, img_h, stroke=1, fill=0)
            c.setFont("Helvetica-Oblique", 7)
            c.drawCentredString(img_x + img_w/2, img_y + img_h/2, "AI Art Here (drop in image in Canva)")

            # text fields
            text_y = img_y - 12
            c.setFont("Helvetica-Bold", 8)
            name = item.get("card_name", "")[:45]
            num = item.get("card_number", "")
            c.drawString(img_x + 4, text_y, f"{name}  #{num}")

            # price on right
            raw = item.get("market_price_raw", "")
            price_val = parse_price(raw)
            if price_val is not None:
                price_str = f"~ ${price_val:,.2f}"
            else:
                price_str = raw if raw else "~ $0.00"
            c.setFont("Helvetica", 8)
            c.drawRightString(x + card_w - 2*pad - 4, text_y, price_str)

            # checkboxes bottom-left
            cb_y = y + pad + 8
            c.rect(img_x + 2, cb_y, 8, 8, stroke=1, fill=0)
            c.drawString(img_x + 12, cb_y, "Want")
            c.rect(img_x + 56, cb_y, 8, 8, stroke=1, fill=0)
            c.drawString(img_x + 70, cb_y, "Own")

            item_idx += 1

        # footer brand
        c.setFont("Helvetica-Oblique", 7)
        c.drawString(margin, margin/2, "GrowliZard")
        c.showPage()

    c.save()
    print("Saved PDF to:", out_path)

def main():
    print("Fetching CSV...")
    csv_text = fetch_csv_text(TCGCSV_URL)
    print("Loading and filtering for set:", SET_NAME)
    df = load_and_filter(csv_text, SET_NAME)
    if df.empty:
        print("No matching rows found for set. Exiting.")
        sys.exit(0)
    # Optional: sort by number if numeric
    try:
        df['card_number_num'] = pd.to_numeric(df['card_number'], errors='coerce')
        df = df.sort_values(by=['card_number_num', 'card_name'])
    except:
        df = df.sort_values(by=['card_name'])
    draw_pdf(df, SET_NAME, OUTPUT_PATH)

if __name__ == "__main__":
    main()
