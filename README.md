# UnidBox Order Copilot

**AI-Powered Wholesale Order Automation System**

## Project Overview

UnidBox Order Copilot is an AI-powered wholesale ordering system designed to transform informal dealer inquiries into structured, scalable business operations.

Today, wholesale dealers contact UnidBox through unstructured channels such as WhatsApp messages, phone calls, and ad-hoc texts. While convenient for dealers, this places a heavy cognitive and administrative burden on UnidBox's operations team, who must manually interpret intent, clarify missing details, consolidate information, and generate delivery documents. As the business scales, this manual interpretation layer becomes a critical bottleneck.

Order Copilot introduces an **intent-first ordering workflow**. Instead of forcing dealers to adapt to rigid forms, the system uses AI to adapt to how dealers naturally communicate.

## Key Features

- **Invisible AI-driven structuring** of informal wholesale inquiries
- **Consistent AI-powered responses** for pricing and availability
- **Confidence-scored, human-approved** order validation
- **Automated Delivery Order (DO) generation** with full traceability
- **Scalable, web-based workflow** designed for real-world deployment

## Repository Structure

```
unidbox-order-copilot/
├── data/                              # Product catalog data
│   ├── UnidBox_Product_Catalog.csv    # CSV format catalog
│   ├── UnidBox_Product_Catalog.xlsx   # Excel format with summaries
│   ├── unidbox_products_final.json    # JSON format for API use
│   └── unidbox_products_with_images.json  # Products with image paths
├── images/                            # Product images
│   └── [product_images].jpg           # 20 product images
├── scripts/                           # Utility scripts
│   ├── scrape_and_download_images.py  # Image scraping script
│   ├── collect_and_download_all_images.py
│   ├── create_excel_catalog.py        # Excel generation
│   └── merge_images_with_catalog.py   # Image-catalog merger
├── README.md                          # This file
└── .gitignore
```

## Product Catalog Summary

| Metric | Value |
|--------|-------|
| Total Products | 160 |
| Total Brands | 19 |
| Total Categories | 14 |
| Price Range | $40.06 - $1,449.00 SGD |
| Average Price | $491.80 SGD |

### Products by Category

| Category | Count |
|----------|-------|
| Ceiling Fans | 53 |
| Range Hoods | 35 |
| Hobs & Stoves | 17 |
| Basin Taps | 13 |
| Power Tools | 11 |
| Kitchen Taps | 8 |
| Other | 8 |
| Bathroom Fixtures | 4 |
| Kitchen Sinks | 3 |
| Bathroom Cabinets | 2 |
| Hand Tools | 2 |
| Ovens | 2 |
| Storage & Organization | 1 |
| Water Heaters | 1 |

### Top Brands

| Brand | Products |
|-------|----------|
| Tecno | 26 |
| EF | 22 |
| Pozzi | 21 |
| Spin | 18 |
| Acorn | 15 |
| Crestar | 8 |
| WORX | 7 |
| Fanco | 7 |
| Makita | 6 |

## Data Schema

Each product in the JSON files contains:

```json
{
  "item_id": "279923374",
  "name": "Spin Savannah SAMRT WIFI Ceiling Fan NO LIGHT",
  "clean_name": "Spin Savannah SAMRT WIFI Ceiling Fan NO LIGHT",
  "price": "$950.00",
  "price_numeric": 950.0,
  "original_price": "$1,000.00",
  "discount": "5%",
  "sold": "2",
  "rating": "2",
  "url": "https://www.lazada.sg/products/pdp-i279923374.html",
  "has_image": true,
  "image_path": "/path/to/image.jpg"
}
```

## Data Sources

- **Lazada**: Product catalog scraped from [UnidBox Hardware Lazada Store](https://www.lazada.sg/unidbox-hardware-pte-ltd/)
- **Shopee**: Additional products available at [UnidBox Hardware Shopee Store](https://shopee.sg/unidbox_hardware)

## How to Use This Data

### For Order Copilot Integration

The product catalog can be used to:
1. **Match dealer inquiries** to specific products using fuzzy matching
2. **Provide accurate pricing** based on current catalog data
3. **Validate product availability** and specifications
4. **Generate Delivery Orders** with correct product details

### Loading the Data (Python)

```python
import json
import pandas as pd

# Load JSON format
with open('data/unidbox_products_final.json', 'r') as f:
    products = json.load(f)

# Load CSV format
df = pd.read_csv('data/UnidBox_Product_Catalog.csv')

# Filter by category
ceiling_fans = [p for p in products if 'ceiling fan' in p['name'].lower()]

# Access product info
for product in products:
    print(f"{product['name']} - ${product['price']}")
```

### Example Use Case

```
Dealer: "I need 5 Acorn ceiling fans for a condo project"

Order Copilot matches:
- Acorn DC-368 48" VOGA Ceiling Fan - $649.00
- Acorn DC-356 46" ceiling fan - $589.00
- Acorn Petalo DC-325 46" - $469.00
```

## Contributing

This repository is designed to be collaborative. Other Manus AI sessions can:
1. Add more products from other sources (Shopee, etc.)
2. Improve product categorization and descriptions
3. Add product specifications
4. Build the Order Copilot web application
5. Create the AI intent parsing system
6. Develop the Delivery Order generation module

## Project Roadmap

- [x] Scrape product catalog from Lazada
- [x] Download product images
- [x] Create structured data formats (CSV, JSON, Excel)
- [ ] Scrape complete catalog (currently 160/800 products)
- [ ] Scrape Shopee product catalog
- [ ] Build Order Copilot web interface
- [ ] Implement AI intent parsing
- [ ] Create Delivery Order generation system
- [ ] Admin dashboard for order validation
- [ ] WhatsApp integration

## Running the Scripts

```bash
# Install dependencies
pip install pandas openpyxl requests

# Create Excel catalog from JSON
python scripts/create_excel_catalog.py

# Merge images with catalog
python scripts/merge_images_with_catalog.py
```

## Notes

- Due to Lazada's anti-bot protection, only 20 product images were downloaded
- For complete image coverage, consider exporting from Lazada Seller Center
- Prices are in Singapore Dollars (SGD)

## License

This project is part of the UnidBox Order Copilot hackathon project.

---

*Part of the UnidBox Order Copilot project - AI-Powered Wholesale Order Automation*

*Last updated: January 31, 2026*
