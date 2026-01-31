# UnidBox Order Copilot - Backend

AI-powered wholesale order automation backend for UnidBox Hardware. This module handles AI intent parsing, WhatsApp integration, email notifications, and Delivery Order generation.

## 📁 Directory Structure

```
backend/
├── ai/                         # AI Intent Parsing Module
│   ├── __init__.py
│   ├── intent_parser.py        # Parse natural language into structured intents
│   ├── product_matcher.py      # Fuzzy match products from catalog
│   └── order_extractor.py      # Extract complete order details
│
├── whatsapp/                   # WhatsApp Integration Module
│   ├── __init__.py
│   ├── whatsapp_client.py      # Send messages via WhatsApp Business API
│   ├── message_handler.py      # Process incoming messages with AI
│   └── webhook_handler.py      # Handle WhatsApp webhooks
│
├── email/                      # Email Notification Module
│   ├── __init__.py
│   ├── email_client.py         # Send emails via SMTP/SendGrid/Mailgun
│   ├── templates.py            # HTML email templates
│   └── notification_service.py # Orchestrate order notifications
│
├── delivery_order/             # Delivery Order Generation Module
│   ├── __init__.py
│   ├── do_generator.py         # Generate DO from confirmed orders
│   ├── pdf_generator.py        # Generate PDF documents
│   └── do_templates.py         # HTML templates for DO
│
├── api/                        # REST API Module
│   ├── __init__.py
│   └── routes.py               # FastAPI endpoints
│
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys and configuration
nano .env
```

### 3. Run the API Server

```bash
# Development mode
uvicorn api.routes:create_app --reload --host 0.0.0.0 --port 8000

# Or using Python directly
python -m api.routes
```

### 4. Access the API

- API Documentation: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/api/health

## 🤖 AI Module

The AI module parses natural language dealer messages into structured order data.

### Intent Parser

```python
from ai.intent_parser import IntentParser

parser = IntentParser()
result = await parser.parse("I need 50 units of Acorn ceiling fan and 20 Tecno range hoods")

# Result:
# {
#     "intent_type": "order_inquiry",
#     "products": [
#         {"name": "Acorn ceiling fan", "quantity": 50},
#         {"name": "Tecno range hood", "quantity": 20}
#     ],
#     "confidence": 0.95
# }
```

### Product Matcher

```python
from ai.product_matcher import ProductMatcher

matcher = ProductMatcher("../data/unidbox_products_final.json")
result = matcher.match("acorn ceiling fan", max_results=5)

# Returns matched products with confidence scores
```

### Order Extractor

```python
from ai.order_extractor import OrderExtractor

extractor = OrderExtractor()
order = await extractor.extract(
    parsed_intent=parsed_intent,
    matched_products=matched_products
)

# Returns complete order with pricing and summary
```

## 📱 WhatsApp Module

Integrates with WhatsApp Business API for dealer communication.

### Sending Messages

```python
from whatsapp.whatsapp_client import WhatsAppClient

client = WhatsAppClient()
await client.send_text("+6512345678", "Your order has been confirmed!")
await client.send_template("+6512345678", "order_confirmation", {"order_id": "UB-123"})
```

### Handling Incoming Messages

```python
from whatsapp.message_handler import MessageHandler

handler = MessageHandler(intent_parser, product_matcher, order_extractor)
response = await handler.handle_message(
    phone_number="+6512345678",
    message_text="I want to order 10 ceiling fans"
)
```

### Webhook Setup

1. Set up a webhook endpoint at `/api/webhook/whatsapp`
2. Configure the verify token in `.env`
3. Register the webhook URL in Meta Business Manager

## 📧 Email Module

Sends order notifications to customers and admin.

### Sending Notifications

```python
from email.notification_service import NotificationService

service = NotificationService()

# Order confirmation
await service.notify_order_confirmed(order_data, "customer@email.com")

# Order shipped
await service.notify_order_shipped(order_data, tracking_number="TRK123")

# Delivery Order with PDF
await service.send_delivery_order(order_data, pdf_content)
```

### Supported Providers

- **SMTP**: Gmail, Outlook, custom SMTP servers
- **SendGrid**: API-based sending
- **Mailgun**: API-based sending

## 📄 Delivery Order Module

Generates professional Delivery Order documents.

### Generating a DO

```python
from delivery_order.do_generator import DeliveryOrderGenerator
from delivery_order.pdf_generator import PDFGenerator

# Generate DO from order
generator = DeliveryOrderGenerator()
do = generator.generate(order_data)

# Generate PDF
pdf_gen = PDFGenerator()
pdf_bytes = pdf_gen.generate(do)

# Save to file
pdf_gen.save_to_file(do, "DO-20240131-ABC123.pdf")
```

## 🔌 API Endpoints

### Chat / AI Processing

```
POST /api/chat
{
    "message": "I need 50 ceiling fans",
    "session_id": "optional-session-id"
}
```

### Products

```
GET /api/products                    # List all products
GET /api/products/{product_id}       # Get specific product
POST /api/products/search            # Search products
GET /api/categories                  # List categories
GET /api/brands                      # List brands
```

### Orders

```
POST /api/orders                     # Create new order
GET /api/orders/{order_id}/do        # Get DO PDF
```

### WhatsApp Webhook

```
GET /api/webhook/whatsapp            # Verify webhook
POST /api/webhook/whatsapp           # Handle incoming messages
```

## 🔧 Integration with Frontend

### For the Manus Web App

The backend API is designed to work seamlessly with the Manus web application. To integrate:

1. **API Base URL**: Set `VITE_API_URL` in the frontend to point to this backend
2. **Chat Integration**: Use `/api/chat` for the AI chatbot
3. **Product Catalog**: Use `/api/products` for the catalog page
4. **Order Creation**: Use `/api/orders` for checkout

### Example Frontend Integration (tRPC)

```typescript
// In server/routers.ts, add a proxy to the Python backend:

import { z } from "zod";
import { publicProcedure, router } from "./_core/trpc";

export const aiRouter = router({
  chat: publicProcedure
    .input(z.object({
      message: z.string(),
      sessionId: z.string().optional()
    }))
    .mutation(async ({ input }) => {
      const response = await fetch(`${process.env.AI_BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input.message,
          session_id: input.sessionId
        })
      });
      return response.json();
    })
});
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific module tests
pytest ai/tests/
pytest whatsapp/tests/
pytest email/tests/

# With coverage
pytest --cov=.
```

## 📋 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI parsing | Yes |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business API token | For WhatsApp |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp phone number ID | For WhatsApp |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verification token | For WhatsApp |
| `EMAIL_PROVIDER` | Email provider (smtp/sendgrid/mailgun) | For Email |
| `SMTP_HOST` | SMTP server host | For SMTP |
| `SMTP_USERNAME` | SMTP username | For SMTP |
| `SMTP_PASSWORD` | SMTP password | For SMTP |
| `ADMIN_EMAIL` | Admin notification email | Recommended |

## 🔒 Security Notes

1. **Never commit `.env` files** - Use `.env.example` as a template
2. **Validate webhook signatures** - The WhatsApp webhook handler validates signatures
3. **Use HTTPS in production** - All API endpoints should be served over HTTPS
4. **Rate limiting** - Consider adding rate limiting for production

## 📝 License

MIT License - See LICENSE file for details.
