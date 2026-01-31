"""
API Routes Module for UnidBox Order Copilot

This module provides REST API endpoints that can be integrated
with the frontend web application.
"""

import os
import json
from typing import Optional, Dict, Any, List
from dataclasses import asdict

# FastAPI imports (optional - falls back to Flask if not available)
try:
    from fastapi import FastAPI, HTTPException, Request, Response, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Import backend modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.intent_parser import IntentParser
from ai.product_matcher import ProductMatcher
from ai.order_extractor import OrderExtractor
from whatsapp.whatsapp_client import WhatsAppClient
from whatsapp.message_handler import MessageHandler
from whatsapp.webhook_handler import WebhookHandler
from email.notification_service import NotificationService
from delivery_order.do_generator import DeliveryOrderGenerator
from delivery_order.pdf_generator import PDFGenerator


# Pydantic models for request/response validation
if FASTAPI_AVAILABLE:
    class ChatRequest(BaseModel):
        message: str
        session_id: Optional[str] = None
        user_id: Optional[str] = None
    
    class ChatResponse(BaseModel):
        response: str
        intent_type: str
        products: List[Dict[str, Any]]
        order_summary: Optional[Dict[str, Any]]
        needs_confirmation: bool
        session_id: str
    
    class ProductSearchRequest(BaseModel):
        query: str
        brand: Optional[str] = None
        category: Optional[str] = None
        max_results: int = 10
    
    class OrderRequest(BaseModel):
        items: List[Dict[str, Any]]
        customer_name: str
        customer_email: Optional[str] = None
        customer_phone: Optional[str] = None
        delivery_address: str
        delivery_date: Optional[str] = None
        notes: Optional[str] = None
    
    class WhatsAppWebhookVerify(BaseModel):
        hub_mode: str
        hub_verify_token: str
        hub_challenge: str


def create_app(catalog_path: Optional[str] = None) -> 'FastAPI':
    """
    Create and configure the FastAPI application.
    
    Args:
        catalog_path: Path to the product catalog JSON file
        
    Returns:
        Configured FastAPI application
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")
    
    app = FastAPI(
        title="UnidBox Order Copilot API",
        description="AI-powered wholesale order automation API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services
    catalog_file = catalog_path or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "unidbox_products_final.json"
    )
    
    intent_parser = IntentParser()
    product_matcher = ProductMatcher(catalog_file)
    order_extractor = OrderExtractor()
    message_handler = MessageHandler(intent_parser, product_matcher, order_extractor, catalog_file)
    webhook_handler = WebhookHandler()
    do_generator = DeliveryOrderGenerator()
    pdf_generator = PDFGenerator()
    
    # Store services in app state
    app.state.intent_parser = intent_parser
    app.state.product_matcher = product_matcher
    app.state.order_extractor = order_extractor
    app.state.message_handler = message_handler
    app.state.webhook_handler = webhook_handler
    app.state.do_generator = do_generator
    app.state.pdf_generator = pdf_generator
    
    # Include routes
    app.include_router(api_router)
    
    return app


# API Router
if FASTAPI_AVAILABLE:
    from fastapi import APIRouter
    api_router = APIRouter(prefix="/api", tags=["api"])
    
    @api_router.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "service": "UnidBox Order Copilot"}
    
    @api_router.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest, req: Request):
        """
        Process a chat message and return AI response.
        
        This endpoint handles natural language order inquiries,
        parses intent, matches products, and returns structured responses.
        """
        message_handler: MessageHandler = req.app.state.message_handler
        
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{hash(request.message)}"
        
        # Process the message
        result = await message_handler.handle_message(
            phone_number=session_id,
            message_text=request.message
        )
        
        # Get context for additional info
        context = message_handler.conversations.get(session_id)
        
        return ChatResponse(
            response=result.get("message", ""),
            intent_type=context.parsed_intent.get("intent_type", "unclear") if context and context.parsed_intent else "unclear",
            products=context.matched_products or [] if context else [],
            order_summary=context.extracted_order if context else None,
            needs_confirmation=result.get("action") == "send_interactive",
            session_id=session_id
        )
    
    @api_router.post("/products/search")
    async def search_products(request: ProductSearchRequest, req: Request):
        """
        Search for products in the catalog.
        
        Supports fuzzy matching, brand filtering, and category filtering.
        """
        product_matcher: ProductMatcher = req.app.state.product_matcher
        
        result = product_matcher.match(
            query=request.query,
            brand=request.brand,
            category=request.category,
            max_results=request.max_results
        )
        
        return product_matcher.to_dict(result)
    
    @api_router.get("/products")
    async def list_products(
        req: Request,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        limit: int = 50
    ):
        """
        List products with optional filtering.
        """
        product_matcher: ProductMatcher = req.app.state.product_matcher
        
        if category:
            products = product_matcher.get_by_category(category, limit)
        elif brand:
            products = product_matcher.get_by_brand(brand, limit)
        else:
            # Return all products (limited)
            products = [
                product_matcher._to_matched_product(p, 1.0, "Listed")
                for p in product_matcher.catalog[:limit]
            ]
        
        return {
            "products": [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "clean_name": p.clean_name,
                    "price": p.price,
                    "original_price": p.original_price,
                    "brand": p.brand,
                    "category": p.category,
                    "url": p.url,
                    "image_path": p.image_path
                }
                for p in products
            ],
            "total": len(products)
        }
    
    @api_router.get("/products/{product_id}")
    async def get_product(product_id: str, req: Request):
        """Get a specific product by ID"""
        product_matcher: ProductMatcher = req.app.state.product_matcher
        
        product = product_matcher.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "product_id": product.product_id,
            "name": product.name,
            "clean_name": product.clean_name,
            "price": product.price,
            "original_price": product.original_price,
            "brand": product.brand,
            "category": product.category,
            "url": product.url,
            "image_path": product.image_path
        }
    
    @api_router.get("/categories")
    async def list_categories():
        """List available product categories"""
        return {
            "categories": [
                "Ceiling Fans",
                "Range Hoods",
                "Hobs & Stoves",
                "Kitchen Taps",
                "Basin Taps",
                "Power Tools",
                "Kitchen Sinks",
                "Bathroom Fixtures",
                "Water Heaters"
            ]
        }
    
    @api_router.get("/brands")
    async def list_brands():
        """List available product brands"""
        return {
            "brands": [
                "Acorn", "Spin", "Fanco", "Crestar", "Alaska",
                "Tecno", "EF", "KA", "Pozzi", "WORX", "Makita"
            ]
        }
    
    @api_router.post("/orders")
    async def create_order(request: OrderRequest, req: Request):
        """
        Create a new order.
        
        This endpoint creates an order from the provided items and
        customer information, generates a DO, and sends notifications.
        """
        order_extractor: OrderExtractor = req.app.state.order_extractor
        do_generator: DeliveryOrderGenerator = req.app.state.do_generator
        
        # Build order data
        order_data = {
            "items": request.items,
            "customer_name": request.customer_name,
            "customer_email": request.customer_email,
            "customer_contact": request.customer_phone,
            "delivery": {
                "address": request.delivery_address,
                "date": request.delivery_date,
                "notes": request.notes
            },
            "summary": {
                "subtotal": sum(item.get("total_price", 0) for item in request.items),
                "tax": sum(item.get("total_price", 0) for item in request.items) * 0.09,
                "shipping": 0 if sum(item.get("total_price", 0) for item in request.items) >= 500 else 50,
                "total": 0,
                "currency": "SGD"
            }
        }
        
        # Calculate total
        order_data["summary"]["total"] = (
            order_data["summary"]["subtotal"] +
            order_data["summary"]["tax"] +
            order_data["summary"]["shipping"]
        )
        
        # Generate order ID
        from datetime import datetime
        import uuid
        order_data["order_id"] = f"UB-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        order_data["created_at"] = datetime.utcnow().isoformat()
        order_data["status"] = "confirmed"
        
        # Generate DO
        do = do_generator.generate(order_data)
        do_dict = do_generator.to_dict(do)
        
        return {
            "success": True,
            "order": order_data,
            "delivery_order": do_dict
        }
    
    @api_router.get("/orders/{order_id}/do")
    async def get_delivery_order_pdf(order_id: str, req: Request):
        """
        Generate and return the Delivery Order PDF for an order.
        """
        # In production, fetch order from database
        # For now, return a placeholder response
        raise HTTPException(
            status_code=501,
            detail="PDF generation requires order data from database"
        )
    
    # WhatsApp webhook endpoints
    @api_router.get("/webhook/whatsapp")
    async def verify_whatsapp_webhook(
        req: Request,
        hub_mode: str = None,
        hub_verify_token: str = None,
        hub_challenge: str = None
    ):
        """Verify WhatsApp webhook subscription"""
        webhook_handler: WebhookHandler = req.app.state.webhook_handler
        
        # Get query params (FastAPI naming convention)
        mode = req.query_params.get("hub.mode", hub_mode)
        token = req.query_params.get("hub.verify_token", hub_verify_token)
        challenge = req.query_params.get("hub.challenge", hub_challenge)
        
        result = webhook_handler.verify_webhook(mode, token, challenge)
        if result:
            return Response(content=result, media_type="text/plain")
        
        raise HTTPException(status_code=403, detail="Verification failed")
    
    @api_router.post("/webhook/whatsapp")
    async def handle_whatsapp_webhook(req: Request):
        """Handle incoming WhatsApp messages"""
        webhook_handler: WebhookHandler = req.app.state.webhook_handler
        message_handler: MessageHandler = req.app.state.message_handler
        
        # Get raw body for signature validation
        body = await req.body()
        signature = req.headers.get("x-hub-signature-256", "")
        
        if not webhook_handler.validate_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse payload
        payload = json.loads(body)
        
        # Set up message callback
        async def on_message(incoming):
            result = await message_handler.handle_message(
                phone_number=incoming.from_number,
                message_text=incoming.text or "",
                message_type=incoming.message_type
            )
            # In production, send response via WhatsApp client
            return result
        
        webhook_handler.set_message_callback(on_message)
        
        # Process webhook
        result = await webhook_handler.handle_webhook(payload)
        
        return result

else:
    # Fallback for when FastAPI is not available
    api_router = None
    
    def create_app(catalog_path=None):
        raise ImportError("FastAPI is required. Install with: pip install fastapi uvicorn")


# Standalone runner
if __name__ == "__main__":
    import uvicorn
    
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
