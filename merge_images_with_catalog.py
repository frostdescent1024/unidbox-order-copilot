#!/usr/bin/env python3
"""
Merge downloaded images with product catalog
"""

import json
import os
import glob
import shutil

def main():
    # Load product catalog
    with open('/home/ubuntu/unidbox_products_final.json', 'r') as f:
        products = json.load(f)
    
    print(f"Loaded {len(products)} products from catalog")
    
    # Get all downloaded images
    img_dir = '/home/ubuntu/unidbox_images'
    images = glob.glob(os.path.join(img_dir, '*.*'))
    
    print(f"Found {len(images)} downloaded images")
    
    # Create mapping of item_id to image path
    image_map = {}
    for img_path in images:
        filename = os.path.basename(img_path)
        # Extract item_id from filename (format: itemid_name.ext)
        item_id = filename.split('_')[0]
        image_map[item_id] = img_path
    
    # Match images with products
    matched = 0
    for product in products:
        item_id = product.get('item_id', '')
        if item_id in image_map:
            product['image_path'] = image_map[item_id]
            product['has_image'] = True
            matched += 1
        else:
            product['has_image'] = False
    
    print(f"Matched {matched} products with images")
    
    # Save updated catalog
    with open('/home/ubuntu/unidbox_products_with_images.json', 'w') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print("Saved updated catalog to /home/ubuntu/unidbox_products_with_images.json")
    
    # Create a summary
    print("\n=== IMAGE SUMMARY ===")
    print(f"Total products: {len(products)}")
    print(f"Products with images: {matched}")
    print(f"Products without images: {len(products) - matched}")
    
    # List products with images
    print("\n=== PRODUCTS WITH IMAGES ===")
    for p in products:
        if p.get('has_image'):
            print(f"  - {p.get('clean_name', p.get('name', ''))[:50]}")

if __name__ == "__main__":
    main()
