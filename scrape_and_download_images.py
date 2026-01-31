#!/usr/bin/env python3
"""
Download product images using the image URLs we have from page 1
Then merge with product catalog
"""

import json
import os
import requests
import time
import re

def download_image(item_id, image_url, name, img_dir):
    """Download a single image"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Referer': 'https://www.lazada.sg/'
    }
    
    # Fix double .jpg extension
    image_url = image_url.replace('.jpg.jpg', '.jpg')
    
    # Create safe filename
    safe_name = re.sub(r'[^\w\-]', '_', name)[:40]
    save_path = os.path.join(img_dir, f"{item_id}_{safe_name}.jpg")
    
    if os.path.exists(save_path):
        return {'item_id': item_id, 'status': 'exists', 'path': save_path}
    
    try:
        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return {'item_id': item_id, 'status': 'success', 'path': save_path}
        else:
            return {'item_id': item_id, 'status': 'failed', 'error': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'item_id': item_id, 'status': 'failed', 'error': str(e)}

def main():
    # Load page 1 images
    with open('/home/ubuntu/page1_images.json', 'r') as f:
        image_data = json.load(f)
    
    print(f"Processing {len(image_data)} products from page 1...")
    
    img_dir = '/home/ubuntu/unidbox_images'
    os.makedirs(img_dir, exist_ok=True)
    
    results = {'success': 0, 'failed': 0, 'exists': 0}
    image_paths = {}
    
    for i, item in enumerate(image_data):
        result = download_image(
            item['item_id'],
            item['image_url'],
            item.get('name', ''),
            img_dir
        )
        
        status = result['status']
        results[status] = results.get(status, 0) + 1
        
        if status in ['success', 'exists']:
            image_paths[result['item_id']] = result['path']
            print(f"[{i+1}/{len(image_data)}] ✓ {item.get('name', '')[:40]}")
        else:
            print(f"[{i+1}/{len(image_data)}] ✗ {item.get('name', '')[:40]} - {result.get('error', '')}")
        
        time.sleep(0.2)
    
    print(f"\nResults: {results['success']} downloaded, {results['exists']} existed, {results['failed']} failed")
    
    # Save image paths mapping
    with open('/home/ubuntu/image_paths.json', 'w') as f:
        json.dump(image_paths, f, indent=2)
    
    print(f"\nImages saved to {img_dir}/")
    print(f"Image paths saved to /home/ubuntu/image_paths.json")

if __name__ == "__main__":
    main()
