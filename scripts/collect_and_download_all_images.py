#!/usr/bin/env python3
"""
Collect all image URLs from console outputs and download them
"""

import json
import os
import re
import requests
import time
import glob

def extract_images_from_file(filepath):
    """Extract image data from console output file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find JSON arrays in the content
        images = []
        
        # Try to find JSON array pattern
        pattern = r'\[\s*\{[^]]+\}\s*\]'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                for item in data:
                    if isinstance(item, dict) and 'item_id' in item and 'image_url' in item:
                        img_url = item.get('image_url', '')
                        if img_url and not img_url.startswith('data:'):
                            images.append(item)
            except:
                pass
        
        return images
    except Exception as e:
        return []

def download_image(item_id, image_url, name, img_dir):
    """Download a single image"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Referer': 'https://www.lazada.sg/'
    }
    
    # Fix double extension
    image_url = image_url.replace('.jpg.jpg', '.jpg')
    image_url = image_url.replace('.png_200x200q80.png', '.png')
    
    # Create safe filename
    safe_name = re.sub(r'[^\w\-]', '_', name)[:40]
    
    # Determine extension
    ext = '.jpg'
    if '.png' in image_url:
        ext = '.png'
    
    save_path = os.path.join(img_dir, f"{item_id}_{safe_name}{ext}")
    
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
    # Collect all images from console outputs
    console_dir = '/home/ubuntu/console_outputs/'
    all_images = []
    seen_ids = set()
    
    for filepath in glob.glob(os.path.join(console_dir, '*.txt')):
        images = extract_images_from_file(filepath)
        for img in images:
            item_id = img.get('item_id', '')
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                all_images.append(img)
    
    # Also load from page1_images.json
    try:
        with open('/home/ubuntu/page1_images.json', 'r') as f:
            page1 = json.load(f)
            for img in page1:
                item_id = img.get('item_id', '')
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    all_images.append(img)
    except:
        pass
    
    print(f"Found {len(all_images)} unique products with images")
    
    # Save all image URLs
    with open('/home/ubuntu/all_image_urls.json', 'w') as f:
        json.dump(all_images, f, indent=2)
    
    # Download images
    img_dir = '/home/ubuntu/unidbox_images'
    os.makedirs(img_dir, exist_ok=True)
    
    results = {'success': 0, 'failed': 0, 'exists': 0}
    image_paths = {}
    
    for i, item in enumerate(all_images):
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
            print(f"[{i+1}/{len(all_images)}] ✓ {item.get('name', '')[:40]}")
        else:
            print(f"[{i+1}/{len(all_images)}] ✗ {item.get('name', '')[:40]} - {result.get('error', '')}")
        
        if status == 'success':
            time.sleep(0.2)
    
    print(f"\nResults: {results['success']} downloaded, {results['exists']} existed, {results['failed']} failed")
    
    # Save image paths
    with open('/home/ubuntu/image_paths.json', 'w') as f:
        json.dump(image_paths, f, indent=2)
    
    print(f"\nImages saved to {img_dir}/")
    print(f"Image paths saved to /home/ubuntu/image_paths.json")

if __name__ == "__main__":
    main()
