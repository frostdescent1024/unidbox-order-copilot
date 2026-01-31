"""
Intent Parser Module for UnidBox Order Copilot

This module uses LLM to parse informal dealer messages and extract structured order intent.
It identifies products, quantities, delivery preferences, and any clarification needs.
"""

import json
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class IntentType(Enum):
    """Types of intents that can be detected from dealer messages"""
    ORDER_INQUIRY = "order_inquiry"  # Dealer wants to place an order
    PRICE_CHECK = "price_check"      # Dealer asking about prices
    STOCK_CHECK = "stock_check"      # Dealer checking availability
    ORDER_STATUS = "order_status"    # Dealer checking order status
    GENERAL_QUESTION = "general_question"  # General product questions
    UNCLEAR = "unclear"              # Intent is not clear


@dataclass
class ProductIntent:
    """Represents a product mentioned in the dealer's message"""
    raw_text: str                    # Original text from message
    product_name: Optional[str]      # Parsed product name
    quantity: Optional[int]          # Requested quantity
    brand: Optional[str]             # Brand if mentioned
    category: Optional[str]          # Category if mentioned
    specifications: Dict[str, Any]   # Any specifications mentioned
    confidence: float                # Confidence score 0-1


@dataclass
class DeliveryIntent:
    """Represents delivery preferences from the message"""
    address: Optional[str]           # Delivery address if mentioned
    date: Optional[str]              # Preferred delivery date
    urgency: Optional[str]           # urgent, normal, flexible
    notes: Optional[str]             # Additional delivery notes


@dataclass
class ParsedIntent:
    """Complete parsed intent from a dealer message"""
    intent_type: IntentType
    products: List[ProductIntent]
    delivery: Optional[DeliveryIntent]
    customer_name: Optional[str]
    contact_info: Optional[str]
    raw_message: str
    confidence_score: float
    needs_clarification: bool
    clarification_questions: List[str]
    summary: str


class IntentParser:
    """
    Parses informal dealer messages to extract structured order intent.
    
    This class uses LLM to understand natural language inquiries and
    extract product requests, quantities, and delivery preferences.
    """
    
    SYSTEM_PROMPT = """You are an AI assistant for UnidBox Hardware, a wholesale hardware supplier in Singapore.
Your job is to parse informal dealer messages and extract structured order information.

UnidBox sells:
- Ceiling Fans (brands: Acorn, Spin, Fanco, Crestar, Alaska)
- Range Hoods/Chimney Hoods (brands: Tecno, EF, KA)
- Hobs & Stoves (brands: Tecno, EF)
- Kitchen & Basin Taps (brands: Pozzi)
- Power Tools (brands: WORX, Makita)
- Bathroom Fixtures
- Kitchen Sinks
- Water Heaters

When parsing messages:
1. Identify the main intent (order, price check, stock check, etc.)
2. Extract all products mentioned with quantities
3. Note any delivery preferences (location, date, urgency)
4. Flag if clarification is needed
5. Provide a confidence score

Respond in JSON format only."""

    PARSE_PROMPT = """Parse the following dealer message and extract structured information.

Message: "{message}"

Respond with a JSON object containing:
{{
    "intent_type": "order_inquiry" | "price_check" | "stock_check" | "order_status" | "general_question" | "unclear",
    "products": [
        {{
            "raw_text": "original text mentioning this product",
            "product_name": "parsed product name",
            "quantity": number or null,
            "brand": "brand name or null",
            "category": "category or null",
            "specifications": {{}},
            "confidence": 0.0-1.0
        }}
    ],
    "delivery": {{
        "address": "address or null",
        "date": "date or null",
        "urgency": "urgent" | "normal" | "flexible" | null,
        "notes": "any notes or null"
    }},
    "customer_name": "name if mentioned or null",
    "contact_info": "phone/email if mentioned or null",
    "confidence_score": 0.0-1.0,
    "needs_clarification": true | false,
    "clarification_questions": ["list of questions to ask if needed"],
    "summary": "brief summary of the request"
}}"""

    def __init__(self, llm_client=None, api_key: Optional[str] = None):
        """
        Initialize the IntentParser.
        
        Args:
            llm_client: Optional LLM client instance (for dependency injection)
            api_key: Optional API key for LLM service
        """
        self.llm_client = llm_client
        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('BUILT_IN_FORGE_API_KEY')
    
    async def parse(self, message: str) -> ParsedIntent:
        """
        Parse a dealer message and extract structured intent.
        
        Args:
            message: The raw dealer message to parse
            
        Returns:
            ParsedIntent object with extracted information
        """
        if not message or not message.strip():
            return self._empty_intent(message)
        
        try:
            # Call LLM to parse the message
            response = await self._call_llm(message)
            return self._parse_response(response, message)
        except Exception as e:
            print(f"Error parsing intent: {e}")
            return self._fallback_parse(message)
    
    def parse_sync(self, message: str) -> ParsedIntent:
        """
        Synchronous version of parse for non-async contexts.
        Uses basic pattern matching as fallback.
        """
        return self._fallback_parse(message)
    
    async def _call_llm(self, message: str) -> Dict[str, Any]:
        """Call the LLM to parse the message"""
        if self.llm_client:
            # Use injected LLM client
            response = await self.llm_client.invoke({
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": self.PARSE_PROMPT.format(message=message)}
                ],
                "response_format": {"type": "json_object"}
            })
            return json.loads(response.choices[0].message.content)
        else:
            # Fallback to pattern matching
            return self._pattern_match(message)
    
    def _pattern_match(self, message: str) -> Dict[str, Any]:
        """Basic pattern matching for when LLM is not available"""
        message_lower = message.lower()
        
        # Detect intent type
        intent_type = "order_inquiry"
        if any(word in message_lower for word in ["price", "cost", "how much"]):
            intent_type = "price_check"
        elif any(word in message_lower for word in ["stock", "available", "availability"]):
            intent_type = "stock_check"
        elif any(word in message_lower for word in ["status", "where is", "tracking"]):
            intent_type = "order_status"
        
        # Extract products (basic pattern matching)
        products = []
        
        # Common product keywords
        product_keywords = {
            "ceiling fan": "Ceiling Fans",
            "fan": "Ceiling Fans",
            "hood": "Range Hoods",
            "chimney": "Range Hoods",
            "hob": "Hobs & Stoves",
            "stove": "Hobs & Stoves",
            "tap": "Kitchen Taps",
            "sink": "Kitchen Sinks",
            "drill": "Power Tools",
            "power tool": "Power Tools",
        }
        
        # Brand keywords
        brands = ["acorn", "spin", "fanco", "crestar", "tecno", "ef", "pozzi", "worx", "makita", "alaska"]
        
        detected_brand = None
        detected_category = None
        
        for brand in brands:
            if brand in message_lower:
                detected_brand = brand.title()
                break
        
        for keyword, category in product_keywords.items():
            if keyword in message_lower:
                detected_category = category
                break
        
        # Extract quantity (look for numbers followed by "unit", "pcs", etc.)
        import re
        quantity_match = re.search(r'(\d+)\s*(units?|pcs?|pieces?|sets?)?', message_lower)
        quantity = int(quantity_match.group(1)) if quantity_match else None
        
        if detected_category or detected_brand:
            products.append({
                "raw_text": message,
                "product_name": None,
                "quantity": quantity,
                "brand": detected_brand,
                "category": detected_category,
                "specifications": {},
                "confidence": 0.6
            })
        
        # Extract delivery info
        delivery = {
            "address": None,
            "date": None,
            "urgency": None,
            "notes": None
        }
        
        if any(word in message_lower for word in ["urgent", "asap", "rush"]):
            delivery["urgency"] = "urgent"
        elif any(word in message_lower for word in ["next week", "no rush"]):
            delivery["urgency"] = "flexible"
        
        # Check for Singapore locations
        sg_areas = ["hougang", "kovan", "macpherson", "bedok", "tampines", "jurong", "woodlands", "yishun"]
        for area in sg_areas:
            if area in message_lower:
                delivery["address"] = area.title()
                break
        
        return {
            "intent_type": intent_type,
            "products": products,
            "delivery": delivery,
            "customer_name": None,
            "contact_info": None,
            "confidence_score": 0.5,
            "needs_clarification": len(products) == 0 or quantity is None,
            "clarification_questions": self._generate_clarification_questions(products, quantity),
            "summary": f"Request for {detected_category or 'products'}" + (f" from {detected_brand}" if detected_brand else "")
        }
    
    def _generate_clarification_questions(self, products: List[Dict], quantity: Optional[int]) -> List[str]:
        """Generate clarification questions based on what's missing"""
        questions = []
        
        if not products:
            questions.append("Could you please specify which products you're interested in?")
        elif not products[0].get("product_name"):
            questions.append("Could you provide more details about the specific model you need?")
        
        if quantity is None:
            questions.append("How many units do you need?")
        
        return questions
    
    def _parse_response(self, response: Dict[str, Any], original_message: str) -> ParsedIntent:
        """Parse the LLM response into a ParsedIntent object"""
        products = [
            ProductIntent(
                raw_text=p.get("raw_text", ""),
                product_name=p.get("product_name"),
                quantity=p.get("quantity"),
                brand=p.get("brand"),
                category=p.get("category"),
                specifications=p.get("specifications", {}),
                confidence=p.get("confidence", 0.5)
            )
            for p in response.get("products", [])
        ]
        
        delivery_data = response.get("delivery", {})
        delivery = DeliveryIntent(
            address=delivery_data.get("address"),
            date=delivery_data.get("date"),
            urgency=delivery_data.get("urgency"),
            notes=delivery_data.get("notes")
        ) if delivery_data else None
        
        return ParsedIntent(
            intent_type=IntentType(response.get("intent_type", "unclear")),
            products=products,
            delivery=delivery,
            customer_name=response.get("customer_name"),
            contact_info=response.get("contact_info"),
            raw_message=original_message,
            confidence_score=response.get("confidence_score", 0.5),
            needs_clarification=response.get("needs_clarification", False),
            clarification_questions=response.get("clarification_questions", []),
            summary=response.get("summary", "")
        )
    
    def _fallback_parse(self, message: str) -> ParsedIntent:
        """Fallback parsing using pattern matching"""
        result = self._pattern_match(message)
        return self._parse_response(result, message)
    
    def _empty_intent(self, message: str) -> ParsedIntent:
        """Return an empty intent for empty messages"""
        return ParsedIntent(
            intent_type=IntentType.UNCLEAR,
            products=[],
            delivery=None,
            customer_name=None,
            contact_info=None,
            raw_message=message,
            confidence_score=0.0,
            needs_clarification=True,
            clarification_questions=["Could you please describe what you're looking for?"],
            summary="Empty or unclear message"
        )
    
    def to_dict(self, intent: ParsedIntent) -> Dict[str, Any]:
        """Convert ParsedIntent to dictionary for JSON serialization"""
        return {
            "intent_type": intent.intent_type.value,
            "products": [asdict(p) for p in intent.products],
            "delivery": asdict(intent.delivery) if intent.delivery else None,
            "customer_name": intent.customer_name,
            "contact_info": intent.contact_info,
            "raw_message": intent.raw_message,
            "confidence_score": intent.confidence_score,
            "needs_clarification": intent.needs_clarification,
            "clarification_questions": intent.clarification_questions,
            "summary": intent.summary
        }
