#!/usr/bin/env python3
"""
Create a comprehensive Excel product catalog for UnidBox Hardware
"""

import json
import pandas as pd
import re

def clean_product_name(name):
    """Extract clean product name and category info"""
    # Remove common suffixes
    parts = name.split('/')
    main_name = parts[0].strip()
    return main_name

def extract_brand(name):
    """Extract brand from product name"""
    name_lower = name.lower()
    brands = {
        'spin': 'Spin',
        'acorn': 'Acorn',
        'alaska': 'Alaska',
        'crestar': 'Crestar',
        'fanco': 'Fanco',
        'tecno': 'Tecno',
        'ef ': 'EF',
        'pozzi': 'Pozzi',
        'makita': 'Makita',
        'worx': 'WORX',
        'ingco': 'INGCO',
        'boshsini': 'Boshsini',
        'aerogaz': 'Aerogaz',
        'mayer': 'Mayer',
        'fujioh': 'Fujioh',
        'grohe': 'Grohe',
        'schneider': 'Schneider',
        'alpha': 'Alpha',
        'kolm': 'KOLM',
        'arino': 'Arino',
        'rubine': 'Rubine',
        'vita': 'VITA',
        'decco': 'Decco'
    }
    
    for key, brand in brands.items():
        if key in name_lower:
            return brand
    return 'Other'

def extract_category(name):
    """Extract product category"""
    name_lower = name.lower()
    
    if 'ceiling fan' in name_lower or ('fan' in name_lower and 'corner' in name_lower):
        return 'Ceiling Fans'
    elif 'hood' in name_lower or 'chimney' in name_lower:
        return 'Range Hoods'
    elif 'hob' in name_lower or 'stove' in name_lower:
        return 'Hobs & Stoves'
    elif 'basin tap' in name_lower or 'basin faucet' in name_lower or 'basin mixer' in name_lower:
        return 'Basin Taps'
    elif 'kitchen tap' in name_lower or 'kitchen faucet' in name_lower or 'kitchen sink tap' in name_lower or 'kitchen mixer' in name_lower:
        return 'Kitchen Taps'
    elif 'bath mixer' in name_lower or 'shower' in name_lower:
        return 'Bathroom Fixtures'
    elif 'sink' in name_lower:
        return 'Kitchen Sinks'
    elif 'oven' in name_lower:
        return 'Ovens'
    elif 'water heater' in name_lower:
        return 'Water Heaters'
    elif 'trimmer' in name_lower or 'blower' in name_lower or 'washer' in name_lower or 'grinder' in name_lower:
        return 'Power Tools'
    elif 'spanner' in name_lower or 'tool' in name_lower:
        return 'Hand Tools'
    elif 'rack' in name_lower or 'shelf' in name_lower or 'hanger' in name_lower:
        return 'Storage & Organization'
    elif 'mcb' in name_lower or 'socket' in name_lower:
        return 'Electrical'
    elif 'cabinet' in name_lower or 'vanity' in name_lower:
        return 'Bathroom Cabinets'
    elif 'light' in name_lower or 'chandelier' in name_lower or 'pendant' in name_lower:
        return 'Lighting'
    elif 'radio' in name_lower:
        return 'Power Tools'
    else:
        return 'Other'

def parse_price(price_str):
    """Parse price string to float"""
    if not price_str:
        return 0.0
    try:
        return float(price_str.replace('$', '').replace(',', ''))
    except:
        return 0.0

def main():
    # Load products
    with open('/home/ubuntu/unidbox_products_final.json', 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"Processing {len(products)} products...")
    
    # Process each product
    processed = []
    for p in products:
        name = p.get('name', '')
        price = parse_price(p.get('price', ''))
        original_price = parse_price(p.get('original_price', ''))
        
        # Calculate discount percentage if not provided
        discount = p.get('discount', '')
        if not discount and original_price > 0 and price > 0:
            discount_pct = ((original_price - price) / original_price) * 100
            if discount_pct > 0:
                discount = f"{discount_pct:.0f}%"
        
        processed.append({
            'Item ID': p.get('item_id', ''),
            'Product Name': clean_product_name(name),
            'Full Name': name,
            'Brand': extract_brand(name),
            'Category': extract_category(name),
            'Price (SGD)': price,
            'Original Price (SGD)': original_price if original_price > 0 else '',
            'Discount': discount,
            'Sold': p.get('sold', ''),
            'Rating': p.get('rating', ''),
            'URL': p.get('url', '')
        })
    
    # Create DataFrame
    df = pd.DataFrame(processed)
    
    # Sort by Category, then Brand, then Price
    df = df.sort_values(['Category', 'Brand', 'Price (SGD)'], ascending=[True, True, False])
    
    # Save to Excel
    excel_path = '/home/ubuntu/UnidBox_Product_Catalog.xlsx'
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Main catalog sheet
        df.to_excel(writer, sheet_name='All Products', index=False)
        
        # Category summary sheet
        category_summary = df.groupby('Category').agg({
            'Item ID': 'count',
            'Price (SGD)': ['min', 'max', 'mean']
        }).round(2)
        category_summary.columns = ['Product Count', 'Min Price', 'Max Price', 'Avg Price']
        category_summary = category_summary.sort_values('Product Count', ascending=False)
        category_summary.to_excel(writer, sheet_name='Category Summary')
        
        # Brand summary sheet
        brand_summary = df.groupby('Brand').agg({
            'Item ID': 'count',
            'Price (SGD)': ['min', 'max', 'mean']
        }).round(2)
        brand_summary.columns = ['Product Count', 'Min Price', 'Max Price', 'Avg Price']
        brand_summary = brand_summary.sort_values('Product Count', ascending=False)
        brand_summary.to_excel(writer, sheet_name='Brand Summary')
    
    print(f"Saved Excel catalog to: {excel_path}")
    
    # Also save as CSV for easy import
    csv_path = '/home/ubuntu/UnidBox_Product_Catalog.csv'
    df.to_csv(csv_path, index=False)
    print(f"Saved CSV catalog to: {csv_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("UNIDBOX HARDWARE PRODUCT CATALOG SUMMARY")
    print("="*60)
    print(f"Total Products: {len(df)}")
    print(f"Total Brands: {df['Brand'].nunique()}")
    print(f"Total Categories: {df['Category'].nunique()}")
    print(f"Price Range: ${df['Price (SGD)'].min():.2f} - ${df['Price (SGD)'].max():.2f}")
    print(f"Average Price: ${df['Price (SGD)'].mean():.2f}")
    
    print("\n--- Products by Category ---")
    for cat, count in df['Category'].value_counts().items():
        print(f"  {cat}: {count}")
    
    print("\n--- Products by Brand ---")
    for brand, count in df['Brand'].value_counts().head(10).items():
        print(f"  {brand}: {count}")

if __name__ == "__main__":
    main()
