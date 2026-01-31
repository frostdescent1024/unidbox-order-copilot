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
- **WhatsApp integration** for seamless dealer communication
- **Email notifications** for order lifecycle events
- **Scalable, web-based workflow** designed for real-world deployment

## Repository Structure

```
unidbox-order-copilot/
├── backend/                           # 🆕 Python Backend Modules
│   ├── ai/                            # AI Intent Parsing
│   │   ├── intent_parser.py           # Parse natural language to structured intents
│   │   ├── product_matcher.py         # Fuzzy match products from catalog
│   │   └── order_extractor.py         # Extract complete order details
│   │
│   ├── whatsapp/                      # WhatsApp Integration
│   │   ├── whatsapp_client.py         # Send messages via WhatsApp API
│   │   ├── message_handler.py         # Process incoming messages with AI
│   │   └── webhook_handler.py         # Handle WhatsApp webhooks
│   │
│   ├── email/                         # Email Notifications
│   │   ├── email_client.py            # SMTP/SendGrid/Mailgun client
│   │   ├── templates.py               # HTML email templates
│   │   └── notification_service.py    # Order notification orchestration
│   │
│   ├── delivery_order/                # DO Generation
│   │   ├── do_generator.py            # Generate DO from orders
│   │   ├── pdf_generator.py           # PDF document generation
│   │   └── do_templates.py            # HTML templates for DO
│   │
│   ├── api/                           # REST API
│   │   └── routes.py                  # FastAPI endpoints
│   │
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment template
│   └── README.md                      # Backend documentation
│
├── data/                              # Product catalog data
│   ├── UnidBox_Product_Catalog.csv    # CSV format catalog
│   ├── UnidBox_Product_Catalog.xlsx   # Excel format with summaries
│   ├── unidbox_products_final.json    # JSON format for API use
│   └── unidbox_products_with_images.json  # Products with image paths
│
├── images/                            # Product images
│   └── [product_images].jpg           # 20 product images
│
├── scripts/                           # Utility scripts
│   ├── scrape_and_download_images.py  # Image scraping script
│   ├── create_excel_catalog.py        # Excel generation
│   └── merge_images_with_catalog.py   # Image-catalog merger
│
├── README.md                          # This file
└── .gitignore
```

## 🚀 Quick Start

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the API server
uvicorn api.routes:create_app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/chat` | POST | AI chat for order processing |
| `/api/products` | GET | List products |
| `/api/products/search` | POST | Search products |
| `/api/orders` | POST | Create order |
| `/api/webhook/whatsapp` | GET/POST | WhatsApp webhook |

### API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 🤖 AI Module

The AI module parses natural language dealer messages into structured order data.

### How It Works

1. **Intent Parsing**: Dealer message → Structured intent (order, inquiry, question)
2. **Product Matching**: Fuzzy match products from the catalog
3. **Order Extraction**: Build complete order with pricing

### Example Flow

```
Dealer: "I need 50 Acorn ceiling fans and 20 Tecno range hoods for next week"

↓ Intent Parser

{
  "intent_type": "order_inquiry",
  "products": [
    {"name": "Acorn ceiling fan", "quantity": 50},
    {"name": "Tecno range hood", "quantity": 20}
  ],
  "delivery": {"timeframe": "next week"}
}

↓ Product Matcher

[
  {"product": "Acorn DC-368 48\" VOGA Ceiling Fan", "price": 649.00, "confidence": 0.92},
  {"product": "Tecno TH 998DTC 90cm Range Hood", "price": 599.00, "confidence": 0.88}
]

↓ Order Extractor

{
  "order_id": "UB-20240131-ABC123",
  "items": [...],
  "summary": {
    "subtotal": 44450.00,
    "tax": 4000.50,
    "total": 48450.50
  }
}
```

## 📱 WhatsApp Integration

### Setup

1. Create a Meta Business Account
2. Set up WhatsApp Business API
3. Configure webhook URL: `https://your-domain.com/api/webhook/whatsapp`
4. Add credentials to `.env`

### Message Flow

```
Dealer (WhatsApp) → Webhook → Message Handler → AI Processing → Response
```

### Supported Message Types

- Text messages (order inquiries)
- Interactive buttons (confirmations)
- Template messages (notifications)

## 📧 Email Notifications

### Supported Events

| Event | Customer Email | Admin Alert |
|-------|----------------|-------------|
| Order Confirmed | ✅ | ✅ |
| Order Shipped | ✅ | - |
| Order Delivered | ✅ | - |
| DO Generated | ✅ (with PDF) | - |

### Supported Providers

- SMTP (Gmail, Outlook, custom)
- SendGrid
- Mailgun

## 📄 Delivery Order Generation

Automatically generates professional DO documents:

- PDF format with company branding
- Itemized product list with pricing
- Delivery details and terms
- Signature sections

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

## 🔧 Integration with Frontend

### For Manus Web App Integration

The backend API is designed to integrate with the Manus web application. To connect:

1. **Set API URL**: Configure `VITE_API_URL` in frontend to point to this backend
2. **Chat Integration**: Use `/api/chat` endpoint for AI chatbot
3. **Products**: Use `/api/products` for catalog browsing
4. **Orders**: Use `/api/orders` for checkout flow

### Example tRPC Integration

```typescript
// In server/routers.ts
export const aiRouter = router({
  chat: publicProcedure
    .input(z.object({ message: z.string(), sessionId: z.string().optional() }))
    .mutation(async ({ input }) => {
      const response = await fetch(`${process.env.AI_BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input.message, session_id: input.sessionId })
      });
      return response.json();
    })
});
```

## 📋 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI parsing | Yes |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business API token | For WhatsApp |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | For WhatsApp |
| `EMAIL_PROVIDER` | Email provider (smtp/sendgrid/mailgun) | For Email |
| `SMTP_HOST` | SMTP server host | For SMTP |
| `ADMIN_EMAIL` | Admin notification email | Recommended |

See `backend/.env.example` for complete list.

## Project Roadmap

- [x] Scrape product catalog from Lazada
- [x] Download product images
- [x] Create structured data formats (CSV, JSON, Excel)
- [x] **AI Intent Parsing Module**
- [x] **Product Matching with Fuzzy Search**
- [x] **Order Extraction and Pricing**
- [x] **WhatsApp Integration Module**
- [x] **Email Notification Module**
- [x] **Delivery Order PDF Generation**
- [x] **REST API Endpoints**
- [ ] Scrape complete catalog (currently 160/800 products)
- [ ] Build Order Copilot web interface
- [ ] Admin dashboard for order validation
- [ ] Database integration for order persistence

## Data Sources

- **Lazada**: [UnidBox Hardware Lazada Store](https://www.lazada.sg/unidbox-hardware-pte-ltd/)
- **Shopee**: [UnidBox Hardware Shopee Store](https://shopee.sg/unidbox_hardware)

## Contributing

This repository is designed to be collaborative. Other Manus AI sessions can:
1. Add more products from other sources
2. Improve product categorization
3. Build the Order Copilot web application
4. Enhance AI parsing accuracy
5. Add more notification channels

## License

This project is part of the UnidBox Order Copilot hackathon project.

---

*Part of the UnidBox Order Copilot project - AI-Powered Wholesale Order Automation*

*Last updated: January 31, 2026*
